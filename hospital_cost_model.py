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

# Custom CSS for smooth transitions and presentation mode
st.markdown("""
<style>
    /* Dark mode for presentations */
    .presentation-mode {
        background-color: #1a1a1a;
        color: white;
    }
    
    /* Smooth transitions for all elements */
    .stSlider > div > div {
        transition: all 0.5s ease-in-out;
    }
    
    .element-container {
        transition: all 0.3s ease-in-out;
    }
    
    /* Animation for bars */
    @keyframes slideIn {
        from {
            transform: translateY(20px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    .animated-bar {
        animation: slideIn 0.5s ease-out;
    }
    
    /* Progress bar style */
    .stProgress > div > div {
        background-color: #2ecc71;
        transition: width 0.5s ease-in-out;
    }
    
    /* Remove radial fade backgrounds */
    .js-plotly-plot .plotly {
        background: transparent !important;
    }
    
    /* Presentation controls */
    .presentation-controls {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# Data Structure: CSI Divisions with hospital-specific costs
# Based on $400M hospital budget mentioned in transcript
CSI_DIVISIONS = {
    "substructure": {"name": "Substructure", "base_pct": 4.5, "base_cost_psf": 18, "color": "#1f77b4"},
    "superstructure": {"name": "Superstructure", "base_pct": 23.75, "base_cost_psf": 95, "color": "#ff7f0e"},
    "enclosure": {"name": "Enclosure", "base_pct": 11.25, "base_cost_psf": 45, "color": "#2ca02c"},
    "roofing": {"name": "Roofing", "base_pct": 3.0, "base_cost_psf": 12, "color": "#d62728"},
    "interiors": {"name": "Interiors", "base_pct": 21.25, "base_cost_psf": 85, "color": "#9467bd"},
    "conveying": {"name": "Conveying", "base_pct": 3.75, "base_cost_psf": 15, "color": "#8c564b"},
    "plumbing": {"name": "Plumbing", "base_pct": 6.25, "base_cost_psf": 25, "color": "#e377c2"},
    "mechanical": {"name": "Mechanical", "base_pct": 27.5, "base_cost_psf": 110, "color": "#7f7f7f"},
    "fire_protection": {"name": "Fire Protection", "base_pct": 2.0, "base_cost_psf": 8, "color": "#bcbd22"},
    "electrical": {"name": "Electrical", "base_pct": 16.25, "base_cost_psf": 65, "color": "#17becf"},
    "equipment": {"name": "Equipment/Furnishing", "base_pct": 11.25, "base_cost_psf": 45, "color": "#aec7e8"},
    "contractor_architect": {"name": "Contractor/Architect", "base_pct": 19.5, "base_cost_psf": 78, "color": "#ffbb78"}
}

# Design Strategies as mentioned by Duncan
STRATEGIES = {
    "envelope_mechanical": {
        "name": "Envelope/Mechanical",
        "color": "#2ecc71",
        "description": "Slight improvement to enclosure cost reduces mechanical capacity needs",
        "click_sequence": ["enclosure", "mechanical", "electrical"]  # Animation sequence
    },
    "structural_innovation": {
        "name": "Structural Innovation (Mass Timber)", 
        "color": "#9b59b6",
        "description": "Mass timber increases superstructure but reduces substructure and contractor time",
        "click_sequence": ["superstructure", "substructure", "contractor_architect"]
    },
    "waste_heat_recovery": {
        "name": "Waste Heat Recovery",
        "color": "#3498db", 
        "description": "Slight increase in plumbing/equipment, greater reduction in mechanical/electrical",
        "click_sequence": ["plumbing", "equipment", "mechanical", "electrical"]
    }
}

# Interdependency Matrix based on Duncan's descriptions
INTERDEPENDENCY_MATRIX = {
    "envelope_mechanical": {
        "enclosure": 10,  # "slight improvement to the cost"
        "mechanical": -20,  # "reduce the cost of mechanical by reducing capacity"
        "electrical": -10,  # Related reduction
        # All others remain at 0
    },
    "structural_innovation": {
        "superstructure": 10,  # "might increase the cost of superstructure slightly"
        "substructure": -15,  # "bring the cost of the substructure down"
        "contractor_architect": -10,  # "reduce the time a contractor spends on-site"
        "interiors": -5,  # Prefab benefits
    },
    "waste_heat_recovery": {
        "plumbing": 8,  # "slight increase in plumbing"
        "equipment": 10,  # "equipment costs"
        "mechanical": -15,  # "greater reduction in mechanical"
        "electrical": -18,  # "and electrical costs"
    }
}

# Initialize session state
if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = None
if 'building_area' not in st.session_state:
    st.session_state.building_area = 250000  # 250k sqft hospital
if 'total_budget' not in st.session_state:
    st.session_state.total_budget = 400_000_000  # $400M as mentioned
if 'manual_adjustments' not in st.session_state:
    st.session_state.manual_adjustments = {div: 0 for div in CSI_DIVISIONS.keys()}
if 'mode' not in st.session_state:
    st.session_state.mode = 'manual'  # 'strategy' or 'manual'

# Helper functions
def calculate_costs(strategy_key=None, manual_adjustments=None):
    """Calculate costs with either strategy or manual adjustments"""
    base_costs = {}
    total_base = st.session_state.total_budget
    
    # Calculate base costs from percentages
    for div_id, div_info in CSI_DIVISIONS.items():
        base_costs[div_id] = total_base * (div_info["base_pct"] / 100)
    
    current_costs = base_costs.copy()
    
    if strategy_key and strategy_key in STRATEGIES:
        # Apply strategy effects
        effects = INTERDEPENDENCY_MATRIX[strategy_key]
        for div_id, change_pct in effects.items():
            if change_pct != 0:
                current_costs[div_id] = base_costs[div_id] * (1 + change_pct / 100)
    
    elif manual_adjustments:
        # Apply manual adjustments
        for div_id, adjustment in manual_adjustments.items():
            current_costs[div_id] = base_costs[div_id] * (1 + adjustment / 100)
    
    return base_costs, current_costs

def create_animated_bar_chart(base_costs, current_costs, highlight_division=None):
    """Create bar chart with animation effects"""
    divisions = list(CSI_DIVISIONS.keys())
    division_names = [CSI_DIVISIONS[d]["name"] for d in divisions]
    
    fig = go.Figure()
    
    # Add bars
    base_values = [base_costs[d] / 1e6 for d in divisions]
    current_values = [current_costs[d] / 1e6 for d in divisions]
    
    # Determine colors based on changes
    colors = []
    for d in divisions:
        if highlight_division and d == highlight_division:
            colors.append("#FFD700")  # Gold for currently animating
        elif current_costs[d] > base_costs[d]:
            colors.append("#e74c3c")  # Red for increase
        elif current_costs[d] < base_costs[d]:
            colors.append("#2ecc71")  # Green for decrease
        else:
            colors.append(CSI_DIVISIONS[d]["color"])
    
    fig.add_trace(go.Bar(
        name="Cost",
        x=division_names,
        y=current_values,
        marker_color=colors,
        text=[f"${v:.1f}M" for v in current_values],
        textposition="outside"
    ))
    
    # Layout for presentation
    fig.update_layout(
        title={
            'text': "Hospital Construction Cost by Division",
            'font': {'size': 24}
        },
        xaxis_title="CSI Division",
        yaxis_title="Cost (Millions $)",
        height=600,
        xaxis={'tickangle': -45},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='black'),
        showlegend=False,
        transition={
            'duration': 500,
            'easing': 'cubic-in-out'
        }
    )
    
    return fig

# Main App
st.markdown("### Hospital Construction Cost Modeling Tool")

# Project Configuration - Horizontal layout
with st.container():
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.session_state.total_budget = st.number_input(
            "Total Project Budget ($)",
            min_value=100_000_000,
            max_value=1_000_000_000,
            value=st.session_state.total_budget,
            step=10_000_000,
            format="%d",
            label_visibility="visible"
        )
    
    with col2:
        st.session_state.building_area = st.number_input(
            "Building Area (sq ft)",
            min_value=100000,
            max_value=500000,
            value=st.session_state.building_area,
            step=10000,
            label_visibility="visible"
        )
    
    with col3:
        st.metric(
            "Cost per sq ft", 
            f"${st.session_state.total_budget / st.session_state.building_area:.0f}",
            label_visibility="visible"
        )

st.divider()

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # Mode selection
    mode = st.radio(
        "Select Mode:",
        options=['strategy', 'manual'],
        format_func=lambda x: "🎯 Design Strategies" if x == 'strategy' else "🎚️ Manual Sliders",
        index=1 if st.session_state.mode == 'manual' else 0
    )
    st.session_state.mode = mode
    
    st.divider()
    
    # Mode-specific controls (moved up to be second)
    if st.session_state.mode == 'strategy':
        st.subheader("Design Strategies")
        
        selected_strategy = st.radio(
            "Select a strategy to model:",
            options=["none"] + list(STRATEGIES.keys()),
            format_func=lambda x: "Baseline (No Strategy)" if x == "none" else STRATEGIES[x]["name"]
        )
        st.session_state.selected_strategy = selected_strategy
        
        if selected_strategy != "none":
            st.info(STRATEGIES[selected_strategy]["description"])
    
    else:  # Manual mode
        st.subheader("🎚️ Manual Adjustments")
        st.caption("Adjust each division's budget:")
        
        # Create sliders in sidebar
        for div_id, div_info in CSI_DIVISIONS.items():
            st.session_state.manual_adjustments[div_id] = st.slider(
                f"{div_info['name']}",
                min_value=-30,
                max_value=30,
                value=int(st.session_state.manual_adjustments[div_id]),
                step=1,
                format="%d%%",
                key=f"sidebar_slider_{div_id}"
            )
        
        # Reset button
        if st.button("🔄 Reset All", type="secondary", use_container_width=True):
            for div_id in CSI_DIVISIONS.keys():
                st.session_state.manual_adjustments[div_id] = 0
            st.rerun()
    
    # Data source attribution
    st.divider()
    st.caption("Data Source: Industry averages for healthcare facilities")
    st.caption("Customizable for project-specific data")
    
# Main content tabs
tab1, tab2, tab3 = st.tabs(["Visual Comparison", "Detailed Analysis", "Synergies"])

with tab1:
    st.subheader("Cost Impact Visualization")
    
    # Calculate costs based on mode
    if st.session_state.mode == 'manual':
        base_costs, current_costs = calculate_costs(manual_adjustments=st.session_state.manual_adjustments)
    else:
        if st.session_state.selected_strategy == "none":
            base_costs, current_costs = calculate_costs()
        else:
            base_costs, current_costs = calculate_costs(strategy_key=st.session_state.selected_strategy)
    
    # Summary metrics at the top
    col1, col2, col3 = st.columns(3)
    
    total_base = sum(base_costs.values())
    total_current = sum(current_costs.values())
    total_change = total_current - total_base
    
    with col1:
        st.metric("Baseline Total", f"${total_base:,.0f}")
    with col2:
        st.metric("Adjusted Total", f"${total_current:,.0f}")
    with col3:
        st.metric("Net Change", f"${abs(total_change):,.0f}", f"{-total_change/total_base*100:+.1f}%")
    
    # Chart below metrics
    fig = create_animated_bar_chart(base_costs, current_costs)
    st.plotly_chart(fig, use_container_width=True)
    
with tab2:
    st.subheader("Division-by-Division Analysis")
    
    if st.session_state.mode == 'manual' or st.session_state.selected_strategy != "none":
        # Costs already calculated above
        
        analysis_data = []
        for div_id, div_info in CSI_DIVISIONS.items():
            base = base_costs[div_id]
            current = current_costs[div_id]
            change = current - base
            change_pct = (change / base * 100) if base > 0 else 0
            
            analysis_data.append({
                "Division": div_info["name"],
                "Baseline": f"${base:,.0f}",
                "Optimized": f"${current:,.0f}",
                "Change": f"${change:+,.0f}",
                "Change %": f"{change_pct:+.1f}%"
            })
        
        df = pd.DataFrame(analysis_data)
        
        # Style the dataframe
        def highlight_changes(val):
            if isinstance(val, str) and '$' in val and ('+' in val or '-' in val):
                if '-' in val and val != '$-0':
                    return 'color: green'
                elif '+' in val:
                    return 'color: red'
            return ''
        
        styled_df = df.style.map(highlight_changes, subset=['Change', 'Change %'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("Select a strategy or use manual sliders to see detailed analysis")

with tab3:
    st.subheader("Understanding the Synergies")
    
    st.markdown("""
    ### How Integrated Design Creates Value
    
    Traditional cost-cutting asks everyone to reduce by 10%, resulting in a worse building.
    Integrated design finds synergies between systems:
    
    **Envelope/Mechanical Strategy:**
    - 💰 Invest in better envelope insulation
    - 📉 Reduce HVAC system size and cost
    - ⚡ Lower electrical loads
    - 🏥 Better patient comfort
    
    **Structural Innovation (Mass Timber):**
    - 🌲 Premium structural system
    - 🏗️ Lighter foundations in most conditions
    - ⏱️ Faster construction
    - 🏭 Prefabricated components
    
    **Waste Heat Recovery:**
    - ♻️ Capture and reuse thermal energy
    - 🔧 Additional equipment investment
    - 💡 Significant electrical savings
    - 🌡️ Reduced mechanical loads
    """)
    
    if st.session_state.mode == 'strategy' and st.session_state.selected_strategy != "none":
        st.divider()
        st.markdown(f"### Current Strategy: {STRATEGIES[st.session_state.selected_strategy]['name']}")
        
        effects = INTERDEPENDENCY_MATRIX[st.session_state.selected_strategy]
        increases = [(k, v) for k, v in effects.items() if v > 0]
        decreases = [(k, v) for k, v in effects.items() if v < 0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Investments")
            for div, change in increases:
                st.markdown(f"- {CSI_DIVISIONS[div]['name']}: +{change}%")
        
        with col2:
            st.markdown("#### Savings")
            for div, change in decreases:
                st.markdown(f"- {CSI_DIVISIONS[div]['name']}: {change}%")

# Footer
st.markdown("---")
st.markdown("Built for integrated healthcare design decisions • Supporting sustainable value engineering")
st.markdown("_Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "_")

# Export functionality
with st.expander("Export Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Current Data"):
                # Use the costs already calculated above
                    
                    export_data = []
                    for div_id, div_info in CSI_DIVISIONS.items():
                        export_data.append({
                            "Division": div_info["name"],
                            "Baseline Cost": base_costs[div_id],
                            "Optimized Cost": current_costs[div_id],
                            "Change": current_costs[div_id] - base_costs[div_id],
                            "Change %": ((current_costs[div_id] - base_costs[div_id]) / base_costs[div_id] * 100)
                        })
                    
                    df_export = pd.DataFrame(export_data)
                    csv = df_export.to_csv(index=False)
                    
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"hospital_cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        
        with col2:
            st.info("PowerBI and Grasshopper integration coming soon")