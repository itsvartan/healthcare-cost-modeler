import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

def create_presentation_layout(app, cost_model, COST_CATEGORIES):
    """Create a clean presentation interface"""
    
    presentation_layout = html.Div([
        # Header with minimal controls
        dbc.Navbar([
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.H3("Healthcare Cost Model", className="text-white mb-0")
                    ], width=6),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button("Edit Mode", id="edit-mode-btn", size="sm", outline=True, color="light"),
                            dbc.Button("Previous", id="prev-slide-btn", size="sm", outline=True, color="light"),
                            dbc.Button("Next", id="next-slide-btn", size="sm", outline=True, color="light"),
                        ], className="float-end")
                    ], width=6)
                ], align="center")
            ], fluid=True)
        ], color="dark", dark=True, className="mb-4"),
        
        # Main presentation area
        html.Div(id="presentation-content", className="presentation-content"),
        
        # Footer with page indicator
        html.Div([
            html.Span(id="slide-indicator", className="text-muted")
        ], className="fixed-bottom text-center p-3")
    ], className="presentation-mode")
    
    return presentation_layout

def create_presentation_slides(model_state, COST_CATEGORIES):
    """Generate presentation slides based on current model state"""
    
    slides = []
    
    # Slide 1: Title slide
    slide1 = html.Div([
        html.Div([
            html.H1("Healthcare Architecture Cost Modeling", className="display-3 text-center mb-4"),
            html.H3("First-Cost Trade-off Analysis", className="text-center text-muted mb-5"),
            html.Hr(),
            html.P(f"Total Project Cost: ${model_state['total_cost']:,.0f}", 
                   className="text-center lead")
        ], className="d-flex flex-column justify-content-center", style={"height": "70vh"})
    ])
    slides.append(slide1)
    
    # Slide 2: Current allocation overview
    slide2 = html.Div([
        html.H2("Current Cost Allocation", className="text-center mb-4"),
        html.Div(id="allocation-overview-chart", style={"height": "60vh"})
    ])
    slides.append(slide2)
    
    # Slide 3: Trade-offs visualization
    if any(abs(adj) > 0.1 for adj in model_state["adjustments"].values()):
        slide3 = html.Div([
            html.H2("Cost Trade-offs from Baseline", className="text-center mb-4"),
            html.Div(id="tradeoffs-viz", style={"height": "60vh"})
        ])
        slides.append(slide3)
    
    # Slide 4: Key insights
    insights = generate_insights(model_state, COST_CATEGORIES)
    if insights:
        slide4 = html.Div([
            html.H2("Key Insights", className="text-center mb-5"),
            html.Div([
                html.Div([
                    html.I(className="bi bi-check-circle-fill text-success me-2"),
                    html.P(insight, className="lead d-inline")
                ], className="mb-3") for insight in insights
            ], className="px-5")
        ], className="d-flex flex-column justify-content-center", style={"height": "70vh"})
        slides.append(slide4)
    
    return slides

def generate_insights(model_state, COST_CATEGORIES):
    """Generate insights based on model adjustments"""
    insights = []
    
    adjustments = model_state["adjustments"]
    total_cost = model_state["total_cost"]
    
    # Find biggest changes
    max_increase = max(adjustments.items(), key=lambda x: x[1])
    max_decrease = min(adjustments.items(), key=lambda x: x[1])
    
    if max_increase[1] > 0.5:
        cat_name = next(c["name"] for c in COST_CATEGORIES if c["id"] == max_increase[0])
        dollar_amt = total_cost * (max_increase[1] / 100)
        insights.append(f"Investing ${dollar_amt:,.0f} more in {cat_name} ({max_increase[1]:+.1f}%)")
    
    if max_decrease[1] < -0.5:
        cat_name = next(c["name"] for c in COST_CATEGORIES if c["id"] == max_decrease[0])
        dollar_amt = abs(total_cost * (max_decrease[1] / 100))
        insights.append(f"Saves ${dollar_amt:,.0f} in {cat_name} ({max_decrease[1]:.1f}%)")
    
    # Calculate net impact
    total_mechanical_savings = adjustments.get("mechanical", 0) * total_cost / 100
    total_electrical_savings = adjustments.get("electrical", 0) * total_cost / 100
    
    if total_mechanical_savings < -100000 or total_electrical_savings < -100000:
        total_mep_savings = abs(total_mechanical_savings + total_electrical_savings)
        insights.append(f"Total MEP savings: ${total_mep_savings:,.0f}")
    
    return insights