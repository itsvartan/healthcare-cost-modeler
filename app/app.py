import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from app.models import CostModel
from app.config import COST_CATEGORIES, DEFAULT_PROJECT_COST
from app.export_utils import export_to_csv, export_chart_to_image, create_pdf_report, create_download_link
import json
import base64
import io
from datetime import datetime

# Initialize Dash app
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)
app.title = "Healthcare Architecture Cost Modeling Tool"

# Serve local CSS
app.server.static_folder = 'static'

# Initialize cost model
cost_model = CostModel(DEFAULT_PROJECT_COST)

# Expose the server for deployment
server = app.server

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Healthcare Architecture Cost Modeling Tool", className="text-center mb-4"),
            html.P("Adjust cost allocations to see trade-offs across building systems", 
                   className="text-center text-muted mb-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Project Settings"),
                dbc.CardBody([
                    dbc.Label("Total Project Cost ($)"),
                    dbc.Input(
                        id="total-cost-input",
                        type="number",
                        value=DEFAULT_PROJECT_COST,
                        step=1000000,
                        className="mb-3"
                    ),
                    dbc.Button("Reset to Baseline", id="reset-btn", color="secondary", size="sm")
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Cost Category Adjustments"),
                dbc.CardBody([
                    html.Div(id="sliders-container")
                ])
            ])
        ], width=9)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Comparison View", tab_id="comparison"),
                dbc.Tab(label="Detailed Breakdown", tab_id="breakdown"),
                dbc.Tab(label="Trade-off Analysis", tab_id="tradeoff")
            ], id="view-tabs", active_tab="comparison")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div(id="charts-container", className="mt-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Export Options"),
                dbc.CardBody([
                    dbc.ButtonGroup([
                        dbc.Button("Export to CSV", id="export-csv-btn", color="primary", size="sm"),
                        dbc.Button("Export Charts as PNG", id="export-png-btn", color="primary", size="sm"),
                        dbc.Button("Generate PDF Report", id="export-pdf-btn", color="primary", size="sm"),
                    ]),
                    html.Div(id="download-links", className="mt-3")
                ])
            ])
        ])
    ], className="mt-4"),
    
    # Hidden div to store model state
    html.Div(id="model-state", style={"display": "none"}),
    
    # Hidden div to store current chart
    html.Div(id="current-chart", style={"display": "none"})
], fluid=True)

@app.callback(
    Output("sliders-container", "children"),
    Input("total-cost-input", "value")
)
def create_sliders(_):
    sliders = []
    for category in COST_CATEGORIES:
        slider_group = dbc.Row([
            dbc.Col([
                dbc.Label(category["name"], style={"font-weight": "bold"}),
                dcc.Slider(
                    id=f"slider-{category['id']}",
                    min=0,
                    max=30,
                    step=0.5,
                    value=category["base_percentage"],
                    marks={i: f"{i}%" for i in range(0, 31, 5)},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Div(id=f"delta-{category['id']}", className="text-muted small")
            ])
        ], className="mb-3")
        sliders.append(slider_group)
    return sliders

@app.callback(
    [Output(f"slider-{cat['id']}", "value") for cat in COST_CATEGORIES] +
    [Output(f"delta-{cat['id']}", "children") for cat in COST_CATEGORIES] +
    [Output("model-state", "children")],
    [Input(f"slider-{cat['id']}", "value") for cat in COST_CATEGORIES] +
    [Input("reset-btn", "n_clicks")],
    [State("total-cost-input", "value")],
    prevent_initial_call=False
)
def update_model(*args):
    ctx = dash.callback_context
    slider_values = args[:len(COST_CATEGORIES)]
    reset_clicks = args[len(COST_CATEGORIES)]
    total_cost = args[-1]
    
    # Update cost model with new total
    cost_model.total_project_cost = total_cost
    
    # Check if reset button was clicked
    if ctx.triggered and ctx.triggered[0]["prop_id"] == "reset-btn.n_clicks":
        cost_model.reset()
        output_values = [cat["base_percentage"] for cat in COST_CATEGORIES]
        deltas = [""] * len(COST_CATEGORIES)
    else:
        # Find which slider changed
        if ctx.triggered:
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if trigger_id.startswith("slider-"):
                category_id = trigger_id.replace("slider-", "")
                idx = next(i for i, cat in enumerate(COST_CATEGORIES) if cat["id"] == category_id)
                new_value = slider_values[idx]
                
                # Update model
                cost_model.update_allocation(category_id, new_value)
        
        # Get current allocations
        output_values = [cost_model.current_allocations[cat["id"]] for cat in COST_CATEGORIES]
        
        # Calculate deltas
        deltas = []
        dollar_deltas = cost_model.get_deltas()
        for cat in COST_CATEGORIES:
            delta = cost_model.adjustments[cat["id"]]
            dollar_delta = dollar_deltas[cat["id"]]
            if abs(delta) > 0.1:
                sign = "+" if delta > 0 else ""
                deltas.append(f"{sign}{delta:.1f}% (${dollar_delta:,.0f})")
            else:
                deltas.append("")
    
    # Store model state
    model_state = json.dumps({
        "allocations": cost_model.current_allocations,
        "adjustments": cost_model.adjustments,
        "total_cost": total_cost
    })
    
    return output_values + deltas + [model_state]

@app.callback(
    [Output("charts-container", "children"),
     Output("current-chart", "children")],
    [Input("model-state", "children"),
     Input("view-tabs", "active_tab")]
)
def update_charts(model_state_json, active_tab):
    if not model_state_json:
        return html.Div(), ""
    
    model_state = json.loads(model_state_json)
    
    if active_tab == "comparison":
        chart = create_comparison_chart(model_state)
        return chart, active_tab
    elif active_tab == "breakdown":
        chart = create_breakdown_chart(model_state)
        return chart, active_tab
    elif active_tab == "tradeoff":
        chart = create_tradeoff_chart(model_state)
        return chart, active_tab

def create_comparison_chart(model_state):
    categories = [cat["name"] for cat in COST_CATEGORIES]
    baseline = [cat["base_percentage"] for cat in COST_CATEGORIES]
    current = [model_state["allocations"][cat["id"]] for cat in COST_CATEGORIES]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name="Baseline",
        x=categories,
        y=baseline,
        marker_color="lightgray",
        text=[f"{v:.1f}%" for v in baseline],
        textposition="outside"
    ))
    
    fig.add_trace(go.Bar(
        name="Adjusted",
        x=categories,
        y=current,
        marker_color=[cat["color"] for cat in COST_CATEGORIES],
        text=[f"{v:.1f}%" for v in current],
        textposition="outside"
    ))
    
    fig.update_layout(
        title="Cost Allocation Comparison",
        xaxis_title="Category",
        yaxis_title="Percentage of Total Cost",
        barmode="group",
        height=500,
        showlegend=True
    )
    
    return dcc.Graph(figure=fig)

def create_breakdown_chart(model_state):
    total_cost = model_state["total_cost"]
    
    data = []
    for cat in COST_CATEGORIES:
        pct = model_state["allocations"][cat["id"]]
        amount = total_cost * (pct / 100)
        data.append({
            "Category": cat["name"],
            "Amount": amount,
            "Percentage": pct,
            "Color": cat["color"]
        })
    
    df = pd.DataFrame(data)
    
    fig = px.treemap(
        df,
        path=["Category"],
        values="Amount",
        color="Percentage",
        color_continuous_scale="RdYlBu_r",
        custom_data=["Percentage"]
    )
    
    fig.update_traces(
        text=[f"{cat}<br>${amt:,.0f}<br>{pct:.1f}%" 
              for cat, amt, pct in zip(df["Category"], df["Amount"], df["Percentage"])],
        textposition="middle center",
        hovertemplate="<b>%{label}</b><br>Amount: $%{value:,.0f}<br>Percentage: %{customdata[0]:.1f}%<extra></extra>"
    )
    
    fig.update_layout(
        title=f"Project Cost Breakdown (Total: ${total_cost:,.0f})",
        height=600
    )
    
    return dcc.Graph(figure=fig)

def create_tradeoff_chart(model_state):
    adjustments = model_state["adjustments"]
    total_cost = model_state["total_cost"]
    
    # Filter to show only categories with significant changes
    data = []
    for cat in COST_CATEGORIES:
        adj = adjustments[cat["id"]]
        if abs(adj) > 0.1:
            dollar_change = total_cost * (adj / 100)
            data.append({
                "Category": cat["name"],
                "Change_Pct": adj,
                "Change_Dollar": dollar_change,
                "Color": "increase" if adj > 0 else "decrease"
            })
    
    if not data:
        return html.Div("No significant trade-offs to display. Adjust sliders to see impacts.", 
                        className="text-center text-muted mt-5")
    
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Waterfall(
        name="Trade-offs",
        orientation="v",
        measure=["relative"] * len(df),
        x=df["Category"],
        y=df["Change_Dollar"],
        text=[f"{pct:+.1f}%<br>${amt:+,.0f}" 
              for pct, amt in zip(df["Change_Pct"], df["Change_Dollar"])],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "green"}},
        decreasing={"marker": {"color": "red"}}
    ))
    
    fig.update_layout(
        title="Cost Trade-off Analysis",
        xaxis_title="Category",
        yaxis_title="Change from Baseline ($)",
        height=500,
        showlegend=False
    )
    
    return dcc.Graph(figure=fig)

@app.callback(
    Output("download-links", "children"),
    [Input("export-csv-btn", "n_clicks"),
     Input("export-png-btn", "n_clicks"),
     Input("export-pdf-btn", "n_clicks")],
    [State("model-state", "children"),
     State("current-chart", "children"),
     State("charts-container", "children")]
)
def handle_exports(csv_clicks, png_clicks, pdf_clicks, model_state_json, active_tab, chart_container):
    if not model_state_json:
        return ""
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    model_state = json.loads(model_state_json)
    
    if trigger_id == "export-csv-btn":
        csv_data = export_to_csv(model_state)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cost_model_export_{timestamp}.csv"
        
        b64 = base64.b64encode(csv_data.encode()).decode()
        href = f'data:text/csv;base64,{b64}'
        
        return html.A("Download CSV", href=href, download=filename, className="btn btn-success btn-sm")
    
    elif trigger_id == "export-png-btn":
        # Get the current chart figure
        if active_tab == "comparison":
            fig = create_comparison_figure(model_state)
        elif active_tab == "breakdown":
            fig = create_breakdown_figure(model_state)
        elif active_tab == "tradeoff":
            fig = create_tradeoff_figure(model_state)
        else:
            return "No chart to export"
        
        img_bytes = export_chart_to_image(fig)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cost_model_chart_{timestamp}.png"
        
        b64 = base64.b64encode(img_bytes).decode()
        href = f'data:image/png;base64,{b64}'
        
        return html.A("Download PNG", href=href, download=filename, className="btn btn-success btn-sm")
    
    elif trigger_id == "export-pdf-btn":
        # Generate all charts
        charts_data = {}
        
        fig1 = create_comparison_figure(model_state)
        charts_data["Comparison Chart"] = export_chart_to_image(fig1, width=800, height=500)
        
        fig2 = create_breakdown_figure(model_state)
        charts_data["Breakdown Chart"] = export_chart_to_image(fig2, width=800, height=600)
        
        fig3 = create_tradeoff_figure(model_state)
        if fig3:  # Trade-off chart might not exist if no changes
            charts_data["Trade-off Analysis"] = export_chart_to_image(fig3, width=800, height=500)
        
        pdf_bytes = create_pdf_report(model_state, charts_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cost_model_report_{timestamp}.pdf"
        
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'data:application/pdf;base64,{b64}'
        
        return html.A("Download PDF Report", href=href, download=filename, className="btn btn-success btn-sm")
    
    return ""

# Helper functions to create figures (not wrapped in dcc.Graph)
def create_comparison_figure(model_state):
    categories = [cat["name"] for cat in COST_CATEGORIES]
    baseline = [cat["base_percentage"] for cat in COST_CATEGORIES]
    current = [model_state["allocations"][cat["id"]] for cat in COST_CATEGORIES]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name="Baseline",
        x=categories,
        y=baseline,
        marker_color="lightgray",
        text=[f"{v:.1f}%" for v in baseline],
        textposition="outside"
    ))
    
    fig.add_trace(go.Bar(
        name="Adjusted",
        x=categories,
        y=current,
        marker_color=[cat["color"] for cat in COST_CATEGORIES],
        text=[f"{v:.1f}%" for v in current],
        textposition="outside"
    ))
    
    fig.update_layout(
        title="Cost Allocation Comparison",
        xaxis_title="Category",
        yaxis_title="Percentage of Total Cost",
        barmode="group",
        height=500,
        showlegend=True
    )
    
    return fig

def create_breakdown_figure(model_state):
    total_cost = model_state["total_cost"]
    
    data = []
    for cat in COST_CATEGORIES:
        pct = model_state["allocations"][cat["id"]]
        amount = total_cost * (pct / 100)
        data.append({
            "Category": cat["name"],
            "Amount": amount,
            "Percentage": pct,
            "Color": cat["color"]
        })
    
    df = pd.DataFrame(data)
    
    fig = px.treemap(
        df,
        path=["Category"],
        values="Amount",
        color="Percentage",
        color_continuous_scale="RdYlBu_r",
        custom_data=["Percentage"]
    )
    
    fig.update_traces(
        text=[f"{cat}<br>${amt:,.0f}<br>{pct:.1f}%" 
              for cat, amt, pct in zip(df["Category"], df["Amount"], df["Percentage"])],
        textposition="middle center",
        hovertemplate="<b>%{label}</b><br>Amount: $%{value:,.0f}<br>Percentage: %{customdata[0]:.1f}%<extra></extra>"
    )
    
    fig.update_layout(
        title=f"Project Cost Breakdown (Total: ${total_cost:,.0f})",
        height=600
    )
    
    return fig

def create_tradeoff_figure(model_state):
    adjustments = model_state["adjustments"]
    total_cost = model_state["total_cost"]
    
    # Filter to show only categories with significant changes
    data = []
    for cat in COST_CATEGORIES:
        adj = adjustments[cat["id"]]
        if abs(adj) > 0.1:
            dollar_change = total_cost * (adj / 100)
            data.append({
                "Category": cat["name"],
                "Change_Pct": adj,
                "Change_Dollar": dollar_change,
                "Color": "increase" if adj > 0 else "decrease"
            })
    
    if not data:
        return None
    
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Waterfall(
        name="Trade-offs",
        orientation="v",
        measure=["relative"] * len(df),
        x=df["Category"],
        y=df["Change_Dollar"],
        text=[f"{pct:+.1f}%<br>${amt:+,.0f}" 
              for pct, amt in zip(df["Change_Pct"], df["Change_Dollar"])],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "green"}},
        decreasing={"marker": {"color": "red"}}
    ))
    
    fig.update_layout(
        title="Cost Trade-off Analysis",
        xaxis_title="Category",
        yaxis_title="Change from Baseline ($)",
        height=500,
        showlegend=False
    )
    
    return fig

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)