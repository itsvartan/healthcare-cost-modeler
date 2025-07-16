import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Hospital Construction Cost Modeling Tool",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Data Structure: CSI Divisions and Base Costs
CSI_DIVISIONS = {
    "substructure": {"name": "Substructure", "base_cost_psf": 18, "color": "#1f77b4"},
    "superstructure": {"name": "Superstructure", "base_cost_psf": 95, "color": "#ff7f0e"},
    "enclosure": {"name": "Enclosure", "base_cost_psf": 45, "color": "#2ca02c"},
    "roofing": {"name": "Roofing", "base_cost_psf": 12, "color": "#d62728"},
    "interiors": {"name": "Interiors", "base_cost_psf": 85, "color": "#9467bd"},
    "conveying": {"name": "Conveying", "base_cost_psf": 15, "color": "#8c564b"},
    "plumbing": {"name": "Plumbing", "base_cost_psf": 25, "color": "#e377c2"},
    "mechanical": {"name": "Mechanical", "base_cost_psf": 110, "color": "#7f7f7f"},
    "fire_protection": {"name": "Fire Protection", "base_cost_psf": 8, "color": "#bcbd22"},
    "electrical": {"name": "Electrical", "base_cost_psf": 65, "color": "#17becf"},
    "equipment": {"name": "Equipment/Furnishing", "base_cost_psf": 45, "color": "#aec7e8"},
    "contractor_fees": {"name": "Contractor/A/E", "base_cost_psf": 78, "color": "#ffbb78"}
}

# Design Strategies Configuration
STRATEGIES = {
    "envelope_mechanical": {
        "name": "Envelope/Mechanical",
        "color": "#2ecc71",
        "description": "High-performance envelope with optimized HVAC"
    },
    "structural_innovation": {
        "name": "Structural Innovation", 
        "color": "#9b59b6",
        "description": "Advanced structural systems for flexibility"
    },
    "waste_heat_recovery": {
        "name": "Waste Heat Recovery",
        "color": "#3498db", 
        "description": "Energy recovery and sustainable systems"
    }
}

# Interdependency Matrix: How strategies affect each CSI division
# Values represent percentage change from base cost
INTERDEPENDENCY_MATRIX = {
    "envelope_mechanical": {
        "substructure": 0,
        "superstructure": -2,  # Lighter mechanical loads
        "enclosure": 25,       # High-performance envelope costs more
        "roofing": 15,         # Better roofing for thermal performance
        "interiors": 0,
        "conveying": 0,
        "plumbing": -5,        # Slight reduction due to integration
        "mechanical": -20,     # Major savings in mechanical
        "fire_protection": 0,
        "electrical": -10,     # Reduced electrical loads
        "equipment": 5,        # Better controls
        "contractor_fees": 3   # Slightly higher coordination
    },
    "structural_innovation": {
        "substructure": 15,    # Advanced foundations
        "superstructure": 20,  # Premium structural systems
        "enclosure": -5,       # Simpler attachment systems
        "roofing": -8,         # Integrated structural roof
        "interiors": -10,      # Open floor plans save costs
        "conveying": 5,        # Better integration
        "plumbing": -3,        # Easier routing
        "mechanical": -8,      # Better distribution
        "fire_protection": 2,  # Additional considerations
        "electrical": -5,      # Easier cable management
        "equipment": 0,
        "contractor_fees": 5   # Innovation premium
    },
    "waste_heat_recovery": {
        "substructure": 2,     # Equipment pad requirements
        "superstructure": 0,
        "enclosure": 5,        # Additional penetrations
        "roofing": 8,          # Rooftop equipment
        "interiors": 0,
        "conveying": 0,
        "plumbing": 15,        # Heat recovery piping
        "mechanical": 10,      # Recovery equipment
        "fire_protection": 0,
        "electrical": -15,     # Energy savings
        "equipment": 20,       # Recovery equipment
        "contractor_fees": 8   # Specialized coordination
    }
}

# Combination Effects: Additional adjustments when strategies are combined
COMBINATION_EFFECTS = {
    ("envelope_mechanical", "structural_innovation"): {
        "superstructure": -3,
        "mechanical": -5,
        "contractor_fees": -2
    },
    ("envelope_mechanical", "waste_heat_recovery"): {
        "mechanical": -8,
        "electrical": -5,
        "equipment": -3
    },
    ("structural_innovation", "waste_heat_recovery"): {
        "superstructure": 2,
        "plumbing": -2,
        "mechanical": -3
    }
}

# Initialize session state
if 'selected_strategies' not in st.session_state:
    st.session_state.selected_strategies = []
if 'building_area' not in st.session_state:
    st.session_state.building_area = 250000  # Default 250k sqft hospital

# Helper Functions
def calculate_strategy_costs(selected_strategies, building_area):
    """Calculate costs for each CSI division based on selected strategies"""
    results = {}
    
    # Base costs
    base_costs = {div: info["base_cost_psf"] * building_area 
                  for div, info in CSI_DIVISIONS.items()}
    
    # Calculate for each strategy
    for strategy in STRATEGIES.keys():
        strategy_costs = base_costs.copy()
        
        if strategy in selected_strategies:
            # Apply primary effects
            for division, effect in INTERDEPENDENCY_MATRIX[strategy].items():
                strategy_costs[division] *= (1 + effect / 100)
            
            # Apply combination effects
            for other_strategy in selected_strategies:
                if other_strategy != strategy:
                    combo_key = tuple(sorted([strategy, other_strategy]))
                    if combo_key in COMBINATION_EFFECTS:
                        for division, effect in COMBINATION_EFFECTS[combo_key].items():
                            strategy_costs[division] *= (1 + effect / 100)
        
        results[strategy] = strategy_costs
    
    # Add baseline for comparison
    results["baseline"] = base_costs
    
    return results

def create_dependency_network():
    """Create network visualization of dependencies"""
    # Create nodes for divisions and strategies
    nodes = []
    edges = []
    
    # Division nodes
    for i, (div_id, div_info) in enumerate(CSI_DIVISIONS.items()):
        nodes.append({
            "id": div_id,
            "label": div_info["name"],
            "group": "division",
            "x": np.cos(2 * np.pi * i / len(CSI_DIVISIONS)) * 300,
            "y": np.sin(2 * np.pi * i / len(CSI_DIVISIONS)) * 300
        })
    
    # Strategy nodes
    for i, (strat_id, strat_info) in enumerate(STRATEGIES.items()):
        nodes.append({
            "id": strat_id,
            "label": strat_info["name"],
            "group": "strategy",
            "x": np.cos(2 * np.pi * i / len(STRATEGIES)) * 100,
            "y": np.sin(2 * np.pi * i / len(STRATEGIES)) * 100
        })
    
    # Create edges based on significant dependencies
    for strategy, effects in INTERDEPENDENCY_MATRIX.items():
        for division, effect in effects.items():
            if abs(effect) > 5:  # Only show significant effects
                edges.append({
                    "source": strategy,
                    "target": division,
                    "value": effect,
                    "color": "green" if effect < 0 else "red"
                })
    
    return nodes, edges

# Main App
st.title("🏥 Hospital Construction Cost Modeling Tool")
st.markdown("Model cost impacts of design strategies across CSI divisions")

# Sidebar Configuration
with st.sidebar:
    st.header("Project Configuration")
    
    building_area = st.number_input(
        "Building Area (sq ft)",
        min_value=50000,
        max_value=1000000,
        value=st.session_state.building_area,
        step=10000,
        help="Total gross square footage"
    )
    st.session_state.building_area = building_area
    
    st.subheader("Select Design Strategies")
    selected_strategies = []
    for strat_id, strat_info in STRATEGIES.items():
        if st.checkbox(
            strat_info["name"],
            key=f"strat_{strat_id}",
            help=strat_info["description"]
        ):
            selected_strategies.append(strat_id)
    
    st.session_state.selected_strategies = selected_strategies
    
    st.divider()
    
    # Display total costs summary
    if selected_strategies:
        costs = calculate_strategy_costs(selected_strategies, building_area)
        baseline_total = sum(costs["baseline"].values())
        
        st.subheader("Cost Impact Summary")
        for strategy in selected_strategies:
            strategy_total = sum(costs[strategy].values())
            delta = strategy_total - baseline_total
            delta_pct = (delta / baseline_total) * 100
            
            st.metric(
                STRATEGIES[strategy]["name"],
                f"${strategy_total:,.0f}",
                f"{delta_pct:+.1f}% (${delta:+,.0f})"
            )

# Main Content Area
tab1, tab2, tab3, tab4 = st.tabs([
    "Cost Comparison", 
    "Trade-off Analysis", 
    "Dependency Network",
    "Scenario Simulator"
])

with tab1:
    st.subheader("Cost Comparison by CSI Division")
    
    if not selected_strategies:
        st.info("👈 Select design strategies from the sidebar to begin")
    else:
        costs = calculate_strategy_costs(selected_strategies, building_area)
        
        # Prepare data for grouped bar chart
        divisions = list(CSI_DIVISIONS.keys())
        division_names = [CSI_DIVISIONS[d]["name"] for d in divisions]
        
        fig = go.Figure()
        
        # Add baseline
        baseline_values = [costs["baseline"][d] / 1e6 for d in divisions]  # Convert to millions
        fig.add_trace(go.Bar(
            name="Baseline",
            x=division_names,
            y=baseline_values,
            marker_color="lightgray",
            text=[f"${v:.1f}M" for v in baseline_values],
            textposition="outside"
        ))
        
        # Add each selected strategy
        for strategy in selected_strategies:
            strategy_values = [costs[strategy][d] / 1e6 for d in divisions]
            fig.add_trace(go.Bar(
                name=STRATEGIES[strategy]["name"],
                x=division_names,
                y=strategy_values,
                marker_color=STRATEGIES[strategy]["color"],
                text=[f"${v:.1f}M" for v in strategy_values],
                textposition="outside"
            ))
        
        fig.update_layout(
            title="Cost by CSI Division",
            xaxis_title="CSI Division",
            yaxis_title="Cost (Millions $)",
            barmode="group",
            height=600,
            showlegend=True,
            xaxis={'tickangle': -45}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Cost delta table
        st.subheader("Cost Changes from Baseline")
        
        delta_data = []
        for div in divisions:
            row = {"Division": CSI_DIVISIONS[div]["name"]}
            for strategy in selected_strategies:
                delta = costs[strategy][div] - costs["baseline"][div]
                delta_pct = (delta / costs["baseline"][div]) * 100
                row[STRATEGIES[strategy]["name"]] = f"{delta_pct:+.1f}% (${delta:+,.0f})"
            delta_data.append(row)
        
        df_delta = pd.DataFrame(delta_data)
        st.dataframe(df_delta, use_container_width=True)

with tab2:
    st.subheader("Trade-off Analysis")
    
    if not selected_strategies:
        st.info("👈 Select design strategies to see trade-offs")
    else:
        costs = calculate_strategy_costs(selected_strategies, building_area)
        
        # Create waterfall chart for each strategy
        for strategy in selected_strategies:
            st.markdown(f"### {STRATEGIES[strategy]['name']}")
            
            # Calculate deltas
            deltas = []
            for div in CSI_DIVISIONS.keys():
                delta = costs[strategy][div] - costs["baseline"][div]
                if abs(delta) > 10000:  # Only show significant changes
                    deltas.append({
                        "Division": CSI_DIVISIONS[div]["name"],
                        "Delta": delta,
                        "Percentage": (delta / costs["baseline"][div]) * 100
                    })
            
            if deltas:
                df_deltas = pd.DataFrame(deltas)
                df_deltas = df_deltas.sort_values("Delta")
                
                fig = go.Figure(go.Waterfall(
                    x=df_deltas["Division"],
                    y=df_deltas["Delta"],
                    text=[f"{p:+.1f}%<br>${d:+,.0f}" 
                          for p, d in zip(df_deltas["Percentage"], df_deltas["Delta"])],
                    textposition="outside",
                    increasing={"marker": {"color": "red"}},
                    decreasing={"marker": {"color": "green"}},
                    connector={"line": {"color": "gray"}}
                ))
                
                fig.update_layout(
                    title=f"Cost Impact: {STRATEGIES[strategy]['name']}",
                    yaxis_title="Cost Change ($)",
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Dependency Network Visualization")
    
    # Create Sankey diagram
    if selected_strategies:
        # Prepare data for Sankey
        source = []
        target = []
        value = []
        labels = []
        
        # Create label mapping
        label_map = {}
        idx = 0
        
        # Add strategies as sources
        for strat in selected_strategies:
            label_map[strat] = idx
            labels.append(STRATEGIES[strat]["name"])
            idx += 1
        
        # Add divisions as targets
        for div, info in CSI_DIVISIONS.items():
            label_map[div] = idx
            labels.append(info["name"])
            idx += 1
        
        # Create flows
        for strat in selected_strategies:
            for div, effect in INTERDEPENDENCY_MATRIX[strat].items():
                if abs(effect) > 3:  # Only significant effects
                    source.append(label_map[strat])
                    target.append(label_map[div])
                    value.append(abs(effect))
        
        # Create Sankey
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color=["#2ecc71", "#9b59b6", "#3498db"][:len(selected_strategies)] + 
                      [CSI_DIVISIONS[d]["color"] for d in CSI_DIVISIONS.keys()]
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color=[
                    "rgba(46, 204, 113, 0.4)" if INTERDEPENDENCY_MATRIX[
                        list(selected_strategies)[s]][list(CSI_DIVISIONS.keys())[
                            t - len(selected_strategies)]] < 0 
                    else "rgba(231, 76, 60, 0.4)"
                    for s, t in zip(source, target)
                ]
            )
        )])
        
        fig.update_layout(
            title="Strategy Impact Flow",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Impact matrix heatmap
        st.subheader("Impact Intensity Matrix")
        
        matrix_data = []
        for div in CSI_DIVISIONS.keys():
            row = []
            for strat in selected_strategies:
                row.append(INTERDEPENDENCY_MATRIX[strat][div])
            matrix_data.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix_data,
            x=[STRATEGIES[s]["name"] for s in selected_strategies],
            y=[CSI_DIVISIONS[d]["name"] for d in CSI_DIVISIONS.keys()],
            colorscale="RdBu_r",
            zmid=0,
            text=[[f"{v:+.0f}%" for v in row] for row in matrix_data],
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title="Cost Impact Percentage by Division",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👈 Select strategies to view dependencies")

with tab4:
    st.subheader("Scenario Simulator")
    
    # Scenario comparison tool
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Create Scenarios")
        
        # Scenario 1
        st.markdown("**Scenario A**")
        scenario_a = []
        for strat_id, strat_info in STRATEGIES.items():
            if st.checkbox(strat_info["name"], key=f"scen_a_{strat_id}"):
                scenario_a.append(strat_id)
        
        st.divider()
        
        # Scenario 2
        st.markdown("**Scenario B**")
        scenario_b = []
        for strat_id, strat_info in STRATEGIES.items():
            if st.checkbox(strat_info["name"], key=f"scen_b_{strat_id}"):
                scenario_b.append(strat_id)
    
    with col2:
        if scenario_a or scenario_b:
            st.markdown("### Scenario Comparison")
            
            # Calculate costs for both scenarios
            costs_a = calculate_strategy_costs(scenario_a, building_area) if scenario_a else {"baseline": calculate_strategy_costs([], building_area)["baseline"]}
            costs_b = calculate_strategy_costs(scenario_b, building_area) if scenario_b else {"baseline": calculate_strategy_costs([], building_area)["baseline"]}
            
            # Total costs
            total_a = sum(costs_a[scenario_a[0] if scenario_a else "baseline"].values())
            total_b = sum(costs_b[scenario_b[0] if scenario_b else "baseline"].values())
            baseline_total = sum(costs_a["baseline"].values())
            
            # Display metrics
            col1_m, col2_m, col3_m = st.columns(3)
            
            with col1_m:
                st.metric(
                    "Scenario A Total",
                    f"${total_a:,.0f}",
                    f"{((total_a - baseline_total) / baseline_total * 100):+.1f}% vs baseline"
                )
            
            with col2_m:
                st.metric(
                    "Scenario B Total",
                    f"${total_b:,.0f}",
                    f"{((total_b - baseline_total) / baseline_total * 100):+.1f}% vs baseline"
                )
            
            with col3_m:
                st.metric(
                    "A vs B Difference",
                    f"${abs(total_a - total_b):,.0f}",
                    f"{((total_a - total_b) / total_b * 100):+.1f}%"
                )
            
            # Detailed comparison chart
            divisions = list(CSI_DIVISIONS.keys())
            division_names = [CSI_DIVISIONS[d]["name"] for d in divisions]
            
            values_a = [costs_a[scenario_a[0] if scenario_a else "baseline"][d] / 1e6 for d in divisions]
            values_b = [costs_b[scenario_b[0] if scenario_b else "baseline"][d] / 1e6 for d in divisions]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name="Scenario A",
                x=division_names,
                y=values_a,
                marker_color="#e74c3c",
                text=[f"${v:.1f}M" for v in values_a],
                textposition="outside"
            ))
            
            fig.add_trace(go.Bar(
                name="Scenario B",
                x=division_names,
                y=values_b,
                marker_color="#3498db",
                text=[f"${v:.1f}M" for v in values_b],
                textposition="outside"
            ))
            
            fig.update_layout(
                title="Scenario Cost Comparison by Division",
                xaxis_title="CSI Division",
                yaxis_title="Cost (Millions $)",
                barmode="group",
                height=500,
                xaxis={'tickangle': -45}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Difference analysis
            st.markdown("### Division-by-Division Difference")
            
            diff_data = []
            for div in divisions:
                val_a = costs_a[scenario_a[0] if scenario_a else "baseline"][div]
                val_b = costs_b[scenario_b[0] if scenario_b else "baseline"][div]
                diff = val_a - val_b
                diff_pct = (diff / val_b * 100) if val_b != 0 else 0
                
                diff_data.append({
                    "Division": CSI_DIVISIONS[div]["name"],
                    "Scenario A": f"${val_a:,.0f}",
                    "Scenario B": f"${val_b:,.0f}",
                    "Difference": f"${diff:+,.0f}",
                    "% Difference": f"{diff_pct:+.1f}%"
                })
            
            df_diff = pd.DataFrame(diff_data)
            st.dataframe(df_diff, use_container_width=True)

# Export section
st.divider()
st.subheader("Export Options")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export Data to CSV"):
        if st.session_state.selected_strategies:
            costs = calculate_strategy_costs(st.session_state.selected_strategies, building_area)
            
            # Create comprehensive export
            export_data = []
            for div in CSI_DIVISIONS.keys():
                row = {
                    "Division": CSI_DIVISIONS[div]["name"],
                    "Baseline Cost": costs["baseline"][div],
                    "Baseline $/sqft": costs["baseline"][div] / building_area
                }
                
                for strat in st.session_state.selected_strategies:
                    row[f"{STRATEGIES[strat]['name']} Cost"] = costs[strat][div]
                    row[f"{STRATEGIES[strat]['name']} $/sqft"] = costs[strat][div] / building_area
                    row[f"{STRATEGIES[strat]['name']} % Change"] = (
                        (costs[strat][div] - costs["baseline"][div]) / costs["baseline"][div] * 100
                    )
                
                export_data.append(row)
            
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False)
            
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"hospital_cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

with col2:
    st.button("🖼️ Export Charts", disabled=True, help="Use browser screenshot tools")

with col3:
    if st.button("📄 Generate Report"):
        st.info("Report generation coming soon")

# Footer
st.markdown("---")
st.markdown(
    "**Hospital Construction Cost Modeling Tool** | "
    "CSI-based divisions with strategy interdependencies | "
    "Designed for healthcare facility planning"
)