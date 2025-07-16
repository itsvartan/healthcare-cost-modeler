import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Hospital Construction Cost Modeling Tool",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for smooth transitions
st.markdown("""
<style>
    /* Smooth transitions for all elements */
    .stSlider > div > div {
        transition: all 0.5s ease-in-out;
    }
    
    .element-container {
        transition: all 0.3s ease-in-out;
    }
    
    /* Smooth number transitions */
    .metric-container {
        transition: all 0.5s ease-in-out;
    }
    
    /* Animate plotly charts */
    .js-plotly-plot {
        transition: all 0.5s ease-in-out;
    }
    
    /* Smooth sidebar transitions */
    section[data-testid="stSidebar"] > div {
        transition: all 0.3s ease-in-out;
    }
    
    /* Progress bar style */
    .stProgress > div > div {
        background-color: #2ecc71;
        transition: width 0.5s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

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

# Interdependency Matrix
INTERDEPENDENCY_MATRIX = {
    "envelope_mechanical": {
        "substructure": 0,
        "superstructure": -2,
        "enclosure": 25,
        "roofing": 15,
        "interiors": 0,
        "conveying": 0,
        "plumbing": -5,
        "mechanical": -20,
        "fire_protection": 0,
        "electrical": -10,
        "equipment": 5,
        "contractor_fees": 3
    },
    "structural_innovation": {
        "substructure": 15,
        "superstructure": 20,
        "enclosure": -5,
        "roofing": -8,
        "interiors": -10,
        "conveying": 5,
        "plumbing": -3,
        "mechanical": -8,
        "fire_protection": 2,
        "electrical": -5,
        "equipment": 0,
        "contractor_fees": 5
    },
    "waste_heat_recovery": {
        "substructure": 2,
        "superstructure": 0,
        "enclosure": 5,
        "roofing": 8,
        "interiors": 0,
        "conveying": 0,
        "plumbing": 15,
        "mechanical": 10,
        "fire_protection": 0,
        "electrical": -15,
        "equipment": 20,
        "contractor_fees": 8
    }
}

# Initialize session state
if 'manual_mode' not in st.session_state:
    st.session_state.manual_mode = False
if 'manual_adjustments' not in st.session_state:
    st.session_state.manual_adjustments = {div: 0 for div in CSI_DIVISIONS.keys()}
if 'strategy_adjustments' not in st.session_state:
    st.session_state.strategy_adjustments = {div: 0 for div in CSI_DIVISIONS.keys()}
if 'target_adjustments' not in st.session_state:
    st.session_state.target_adjustments = {div: 0 for div in CSI_DIVISIONS.keys()}
if 'selected_strategies' not in st.session_state:
    st.session_state.selected_strategies = []
if 'building_area' not in st.session_state:
    st.session_state.building_area = 250000
if 'transition_progress' not in st.session_state:
    st.session_state.transition_progress = 0

# Helper function for smooth interpolation
def interpolate_value(current, target, progress):
    """Smoothly interpolate between current and target value"""
    return current + (target - current) * progress

# Calculate target adjustments based on strategies
def calculate_target_adjustments(selected_strategies):
    """Calculate the target percentage adjustments for each division"""
    target = {div: 0 for div in CSI_DIVISIONS.keys()}
    
    if selected_strategies:
        for strategy in selected_strategies:
            for division, effect in INTERDEPENDENCY_MATRIX[strategy].items():
                target[division] += effect
    
    return target

# Helper Functions
def calculate_costs_with_adjustments(building_area, manual_mode):
    """Calculate costs with manual adjustments or strategy effects"""
    base_costs = {div: info["base_cost_psf"] * building_area 
                  for div, info in CSI_DIVISIONS.items()}
    
    if manual_mode:
        # Apply manual percentage adjustments
        adjusted_costs = {}
        for div, base_cost in base_costs.items():
            adjustment = st.session_state.manual_adjustments.get(div, 0)
            adjusted_costs[div] = base_cost * (1 + adjustment / 100)
        return {"manual": adjusted_costs, "baseline": base_costs}
    else:
        # Apply strategy-based adjustments
        results = {"baseline": base_costs}
        
        # Combined effect for all selected strategies
        if st.session_state.selected_strategies or any(adj != 0 for adj in st.session_state.strategy_adjustments.values()):
            combined_costs = base_costs.copy()
            
            # Apply interpolated adjustments
            for division in CSI_DIVISIONS.keys():
                adjustment = st.session_state.strategy_adjustments.get(division, 0)
                combined_costs[division] *= (1 + adjustment / 100)
            
            results["combined"] = combined_costs
        
        return results

# Main App
st.title("🏥 Hospital Construction Cost Modeling Tool")
st.markdown("Model cost impacts across CSI divisions with smooth transitions")

# Mode Toggle
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    mode = st.radio(
        "Adjustment Mode",
        ["Strategy-Based", "Manual Sliders"],
        horizontal=True
    )
    st.session_state.manual_mode = (mode == "Manual Sliders")

# Strategy change detection and animation
if not st.session_state.manual_mode:
    # Calculate new target adjustments
    new_targets = calculate_target_adjustments(st.session_state.selected_strategies)
    
    # Check if targets have changed
    if new_targets != st.session_state.target_adjustments:
        st.session_state.target_adjustments = new_targets
        st.session_state.transition_progress = 0

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
    
    st.divider()
    
    if st.session_state.manual_mode:
        st.subheader("🎚️ Manual Cost Adjustments")
        st.markdown("Adjust each category's cost percentage")
        
        # Create sliders for each CSI division with unique keys
        for div_id, div_info in CSI_DIVISIONS.items():
            # Use a unique key that includes mode to avoid conflicts
            slider_value = st.slider(
                div_info["name"],
                min_value=-50,
                max_value=50,
                value=st.session_state.manual_adjustments.get(div_id, 0),
                step=1,
                format="%d%%",
                key=f"manual_slider_{div_id}",  # Changed key to include 'manual_'
                help=f"Base: ${div_info['base_cost_psf']}/sqft"
            )
            st.session_state.manual_adjustments[div_id] = slider_value
        
        if st.button("Reset All to Baseline", key="reset_manual"):
            for div_id in CSI_DIVISIONS.keys():
                st.session_state.manual_adjustments[div_id] = 0
            st.rerun()
    
    else:
        st.subheader("📋 Select Design Strategies")
        
        # Show transition progress if animating
        if st.session_state.transition_progress < 1:
            progress_container = st.empty()
            with progress_container:
                st.progress(st.session_state.transition_progress, "Applying changes...")
        
        selected_strategies = []
        for strat_id, strat_info in STRATEGIES.items():
            if st.checkbox(
                strat_info["name"],
                key=f"strategy_checkbox_{strat_id}",  # Unique key for checkboxes
                help=strat_info["description"]
            ):
                selected_strategies.append(strat_id)
        
        st.session_state.selected_strategies = selected_strategies
        
        # Display current adjustment values (animated)
        st.divider()
        st.markdown("**Current Adjustments:**")
        
        # Animate the transition
        if st.session_state.transition_progress < 1:
            # Update progress
            st.session_state.transition_progress = min(1.0, st.session_state.transition_progress + 0.1)
            
            # Interpolate values
            for div_id in CSI_DIVISIONS.keys():
                current = st.session_state.strategy_adjustments[div_id]
                target = st.session_state.target_adjustments[div_id]
                new_value = interpolate_value(current, target, st.session_state.transition_progress)
                st.session_state.strategy_adjustments[div_id] = new_value
            
            # Trigger rerun for animation
            time.sleep(0.05)  # Small delay for smooth animation
            st.rerun()
        
        # Show animated values
        for div_id, div_info in CSI_DIVISIONS.items():
            current_adj = st.session_state.strategy_adjustments.get(div_id, 0)
            if abs(current_adj) > 0.1:
                color = "🟢" if current_adj < 0 else "🔴"
                st.caption(f"{color} {div_info['name']}: {current_adj:+.1f}%")
    
    st.divider()
    
    # Cost summary with animation
    costs = calculate_costs_with_adjustments(building_area, st.session_state.manual_mode)
    
    baseline_total = sum(costs["baseline"].values())
    
    if st.session_state.manual_mode:
        current_total = sum(costs.get("manual", costs["baseline"]).values())
    else:
        current_total = sum(costs.get("combined", costs["baseline"]).values())
    
    delta = current_total - baseline_total
    delta_pct = (delta / baseline_total) * 100 if baseline_total > 0 else 0
    
    # Animated metric
    metric_container = st.container()
    with metric_container:
        st.metric(
            "Total Project Cost",
            f"${current_total:,.0f}",
            f"{delta_pct:+.1f}% (${delta:+,.0f})"
        )

# Main Content Area with animated charts
tab1, tab2, tab3 = st.tabs([
    "Cost Comparison", 
    "Trade-off Analysis", 
    "Impact Visualization"
])

with tab1:
    st.subheader("Cost Comparison by CSI Division")
    
    costs = calculate_costs_with_adjustments(building_area, st.session_state.manual_mode)
    
    # Prepare data for visualization
    divisions = list(CSI_DIVISIONS.keys())
    division_names = [CSI_DIVISIONS[d]["name"] for d in divisions]
    
    fig = go.Figure()
    
    # Add baseline
    baseline_values = [costs["baseline"][d] / 1e6 for d in divisions]
    fig.add_trace(go.Bar(
        name="Baseline",
        x=division_names,
        y=baseline_values,
        marker_color="lightgray",
        text=[f"${v:.1f}M" for v in baseline_values],
        textposition="outside"
    ))
    
    # Add adjusted values with animation
    if st.session_state.manual_mode:
        if "manual" in costs:
            adjusted_values = [costs["manual"][d] / 1e6 for d in divisions]
            fig.add_trace(go.Bar(
                name="Manually Adjusted",
                x=division_names,
                y=adjusted_values,
                marker_color="#e74c3c",
                text=[f"${v:.1f}M" for v in adjusted_values],
                textposition="outside"
            ))
    else:
        if "combined" in costs:
            combined_values = [costs["combined"][d] / 1e6 for d in divisions]
            fig.add_trace(go.Bar(
                name="With Strategies",
                x=division_names,
                y=combined_values,
                marker_color="#2ecc71",
                text=[f"${v:.1f}M" for v in combined_values],
                textposition="outside"
            ))
    
    # Add smooth transition animation
    fig.update_layout(
        title="Cost by CSI Division",
        xaxis_title="CSI Division",
        yaxis_title="Cost (Millions $)",
        barmode="group",
        height=600,
        xaxis={'tickangle': -45},
        transition={
            'duration': 500,
            'easing': 'cubic-in-out'
        },
        showlegend=True
    )
    
    # Enable animation on data updates
    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>Cost: $%{y:.1f}M<extra></extra>'
    )
    
    chart_container = st.container()
    with chart_container:
        st.plotly_chart(fig, use_container_width=True, key="main_chart")
    
    # Delta table with fade-in effect
    st.subheader("Cost Changes from Baseline")
    
    delta_data = []
    current_costs = costs.get("manual" if st.session_state.manual_mode else "combined", costs["baseline"])
    
    for div in divisions:
        base = costs["baseline"][div]
        current = current_costs[div]
        delta = current - base
        delta_pct = (delta / base * 100) if base > 0 else 0
        
        delta_data.append({
            "Division": CSI_DIVISIONS[div]["name"],
            "Baseline": f"${base:,.0f}",
            "Current": f"${current:,.0f}",
            "Change $": f"${delta:+,.0f}",
            "Change %": f"{delta_pct:+.1f}%"
        })
    
    df_delta = pd.DataFrame(delta_data)
    st.dataframe(df_delta, use_container_width=True)

with tab2:
    st.subheader("Trade-off Analysis")
    
    current_costs = costs.get("manual" if st.session_state.manual_mode else "combined", costs["baseline"])
    
    # Calculate deltas for waterfall
    deltas = []
    for div in CSI_DIVISIONS.keys():
        delta = current_costs[div] - costs["baseline"][div]
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
            increasing={"marker": {"color": "#e74c3c"}},
            decreasing={"marker": {"color": "#2ecc71"}},
            connector={"line": {"color": "gray", "dash": "dot"}}
        ))
        
        fig.update_layout(
            title="Cost Impact Analysis",
            yaxis_title="Cost Change ($)",
            height=500,
            showlegend=False,
            transition={
                'duration': 500,
                'easing': 'cubic-in-out'
            }
        )
        
        st.plotly_chart(fig, use_container_width=True, key="waterfall_chart")
    else:
        st.info("🎯 Adjust costs or select strategies to see trade-offs")

with tab3:
    st.subheader("Impact Visualization")
    
    # Create animated treemap
    data = []
    current_costs = costs.get("manual" if st.session_state.manual_mode else "combined", costs["baseline"])
    
    for div, info in CSI_DIVISIONS.items():
        amount = current_costs[div]
        pct_of_total = (amount / sum(current_costs.values())) * 100
        data.append({
            "Division": info["name"],
            "Amount": amount,
            "Percentage": pct_of_total,
            "Color": info["color"]
        })
    
    df = pd.DataFrame(data)
    
    fig = go.Figure(go.Treemap(
        labels=df["Division"],
        values=df["Amount"],
        parents=[""] * len(df),
        text=[f"{div}<br>${amt:,.0f}<br>{pct:.1f}% of total" 
              for div, amt, pct in zip(df["Division"], df["Amount"], df["Percentage"])],
        marker=dict(
            colors=df["Color"],
            line=dict(width=2, color="white")
        ),
        textfont=dict(size=14, color="white")
    ))
    
    fig.update_layout(
        title=f"Cost Distribution (Total: ${sum(current_costs.values()):,.0f})",
        height=600,
        transition={
            'duration': 500,
            'easing': 'cubic-in-out'
        }
    )
    
    st.plotly_chart(fig, use_container_width=True, key="treemap_chart")

# Export section
st.divider()
st.subheader("Export Options")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export Data to CSV", key="export_csv_btn"):
        export_data = []
        current_costs = costs.get("manual" if st.session_state.manual_mode else "combined", costs["baseline"])
        
        for div in CSI_DIVISIONS.keys():
            row = {
                "Division": CSI_DIVISIONS[div]["name"],
                "Baseline Cost": costs["baseline"][div],
                "Current Cost": current_costs[div],
                "Change $": current_costs[div] - costs["baseline"][div],
                "Change %": ((current_costs[div] - costs["baseline"][div]) / costs["baseline"][div] * 100)
            }
            export_data.append(row)
        
        df_export = pd.DataFrame(export_data)
        csv = df_export.to_csv(index=False)
        
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"hospital_cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_csv_btn"
        )

# Footer with animation hint
st.markdown("---")
st.markdown(
    "**Hospital Construction Cost Modeling Tool** | "
    "✨ Now with smooth transitions | "
    "Watch values animate when switching strategies!"
)