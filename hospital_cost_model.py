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
    page_title="HDR Architecture | Cost Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Apple-inspired design
st.markdown("""
<style>
    /* Import SF Pro Display font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
        background: linear-gradient(180deg, #FAFAFA 0%, #F5F5F7 100%);
    }
    
    /* Header styling */
    .main-header {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 24px 32px;
        margin-bottom: 32px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
    }
    
    /* Card styling */
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    }
    
    /* Slider styling */
    .stSlider > div > div {
        background: transparent;
    }
    
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #007AFF 0%, #5856D6 100%);
        height: 6px !important;
        border-radius: 3px;
    }
    
    .stSlider > div > div > div > div > div {
        background: white;
        width: 20px !important;
        height: 20px !important;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        margin-top: -7px !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0, 122, 255, 0.4);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.6);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #1D1D1F;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: white;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 12px;
        padding: 16px;
        backdrop-filter: blur(10px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Smooth transitions */
    * {
        transition: color 0.3s ease, background-color 0.3s ease, transform 0.2s ease;
    }
    
    /* HDR brand colors */
    :root {
        --hdr-blue: #0066CC;
        --hdr-dark: #1D1D1F;
        --hdr-gray: #86868B;
        --hdr-light: #F5F5F7;
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
    st.session_state.mode = 'strategy'  # 'strategy' or 'manual'

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

def create_modern_bar_chart(base_costs, current_costs):
    """Create modern Apple-style bar chart"""
    divisions = list(CSI_DIVISIONS.keys())
    division_names = [CSI_DIVISIONS[d]["name"] for d in divisions]
    
    fig = go.Figure()
    
    # Calculate values and changes
    current_values = [current_costs[d] / 1e6 for d in divisions]
    changes = [(current_costs[d] - base_costs[d]) / base_costs[d] * 100 for d in divisions]
    
    # Create gradient colors based on change
    colors = []
    for change in changes:
        if change > 0:
            colors.append('#FF3B30')  # iOS red
        elif change < 0:
            colors.append('#34C759')  # iOS green  
        else:
            colors.append('#007AFF')  # iOS blue
    
    fig.add_trace(go.Bar(
        x=division_names,
        y=current_values,
        marker=dict(
            color=colors,
            line=dict(width=0),
        ),
        text=[f"${v:.1f}M<br>{c:+.1f}%" if c != 0 else f"${v:.1f}M" 
              for v, c in zip(current_values, changes)],
        textposition="outside",
        textfont=dict(size=12)
    ))
    
    # Apple-style layout
    fig.update_layout(
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=12, color='#1D1D1F'),
            gridcolor='rgba(0,0,0,0.05)',
            zerolinecolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            title=dict(
                text="Cost (Millions USD)",
                font=dict(size=14, color='#86868B')
            ),
            tickfont=dict(size=12, color='#86868B'),
            gridcolor='rgba(0,0,0,0.05)',
            zerolinecolor='rgba(0,0,0,0.1)'
        ),
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, r=20, b=100, l=60),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="white",
            font=dict(size=14),
            bordercolor="rgba(0,0,0,0.1)"
        )
    )
    
    return fig

def create_donut_chart(base_costs, current_costs):
    """Create modern donut chart for cost breakdown"""
    divisions = list(CSI_DIVISIONS.keys())
    division_names = [CSI_DIVISIONS[d]["name"] for d in divisions]
    current_values = [current_costs[d] for d in divisions]
    
    # iOS-inspired colors
    colors = ['#007AFF', '#5856D6', '#AF52DE', '#FF2D55', '#FF3B30', 
              '#FF9500', '#FFCC00', '#34C759', '#00C7BE', '#32ADE6',
              '#5AC8FA', '#A0A0A7']
    
    fig = go.Figure(data=[go.Pie(
        labels=division_names,
        values=current_values,
        hole=.7,
        marker=dict(
            colors=colors[:len(divisions)],
            line=dict(color='white', width=2)
        ),
        textinfo='label+percent',
        textposition='outside',
        textfont=dict(size=12)
    )])
    
    # Add center text
    total = sum(current_values) / 1e6
    fig.add_annotation(
        text=f"${total:.0f}M<br>Total",
        x=0.5, y=0.5,
        font=dict(size=24, color="#1D1D1F"),
        showarrow=False
    )
    
    fig.update_layout(
        height=500,
        margin=dict(t=40, r=40, b=40, l=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig

# Main App
# Header with HDR branding
st.markdown("""
<div class="main-header">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
            <h1 style="margin: 0; font-size: 32px; font-weight: 600; color: #1D1D1F;">
                Cost Intelligence Platform
            </h1>
            <p style="margin: 0; margin-top: 8px; font-size: 18px; color: #86868B;">
                HDR Architecture · Hospital Construction Optimization
            </p>
        </div>
        <div style="text-align: right;">
            <p style="margin: 0; font-size: 24px; font-weight: 500; color: #007AFF;">
                ${st.session_state.total_budget/1e6:.0f}M Project
            </p>
            <p style="margin: 0; font-size: 14px; color: #86868B;">
                ${st.session_state.total_budget/st.session_state.building_area:.0f} per sq ft
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
    
# Main content area
col1, col2, col3 = st.columns([1.2, 2, 1])

with col1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("### Project Settings")
    
    total_budget = st.number_input(
        "Total Budget",
        min_value=100_000_000,
        max_value=1_000_000_000,
        value=st.session_state.total_budget,
        step=10_000_000,
        format="%d",
        label_visibility="visible"
    )
    st.session_state.total_budget = total_budget
    
    building_area = st.number_input(
        "Building Area (sq ft)",
        min_value=100000,
        max_value=500000,
        value=st.session_state.building_area,
        step=10000,
        label_visibility="visible"
    )
    st.session_state.building_area = building_area
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Mode selection
    st.markdown("<div class='metric-card' style='margin-top: 20px;'>", unsafe_allow_html=True)
    st.markdown("### Optimization Mode")
    
    mode = st.radio(
        "Select approach:",
        options=['strategy', 'manual'],
        format_func=lambda x: "Smart Strategies" if x == 'strategy' else "Manual Control",
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.mode = mode
    
    if mode == 'strategy':
        st.markdown("#### Select Strategy")
        selected_strategy = st.selectbox(
            "Strategy",
            options=["none"] + list(STRATEGIES.keys()),
            format_func=lambda x: "Baseline" if x == "none" else STRATEGIES[x]["name"],
            label_visibility="collapsed"
        )
        st.session_state.selected_strategy = selected_strategy
        
        if selected_strategy != "none":
            st.info(STRATEGIES[selected_strategy]["description"])
    
    st.markdown("</div>", unsafe_allow_html=True)
    
with col2:
    # Main visualization area
    if st.session_state.mode == 'manual':
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("### Manual Cost Adjustments")
        st.markdown("Fine-tune each division's budget allocation")
        
        # Create sliders for each division
        cols = st.columns(2)
        for i, (div_id, div_info) in enumerate(CSI_DIVISIONS.items()):
            with cols[i % 2]:
                st.session_state.manual_adjustments[div_id] = st.slider(
                    div_info["name"],
                    min_value=-30,
                    max_value=30,
                    value=int(st.session_state.manual_adjustments[div_id]),
                    step=1,
                    format="%d%%",
                    key=f"slider_{div_id}"
                )
        
        # Reset button
        if st.button("Reset All", type="secondary"):
            for div_id in CSI_DIVISIONS.keys():
                st.session_state.manual_adjustments[div_id] = 0
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Calculate with manual adjustments
        base_costs, current_costs = calculate_costs(manual_adjustments=st.session_state.manual_adjustments)
    else:
        # Calculate with strategy
        if st.session_state.selected_strategy and st.session_state.selected_strategy != "none":
            base_costs, current_costs = calculate_costs(strategy_key=st.session_state.selected_strategy)
        else:
            base_costs, current_costs = calculate_costs()
    
    # Visualization tabs
    tab1, tab2, tab3 = st.tabs(["📊 Bar Chart", "🍩 Distribution", "📈 Analysis"])
    
    with tab1:
        fig = create_modern_bar_chart(base_costs, current_costs)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = create_donut_chart(base_costs, current_costs)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Detailed analysis
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
        
        # Apply conditional formatting
        def style_changes(val):
            if isinstance(val, str) and '$' in val and ('+' in val or '-' in val):
                if '-' in val and val != '$-0':
                    return 'color: #34C759'  # iOS green
                elif '+' in val:
                    return 'color: #FF3B30'  # iOS red
            return ''
        
        styled_df = df.style.applymap(style_changes, subset=['Change', 'Change %'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
with col3:
    # Summary metrics
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("### Cost Summary")
    
    total_base = sum(base_costs.values())
    total_current = sum(current_costs.values())
    total_change = total_current - total_base
    
    st.metric("Baseline", f"${total_base/1e6:.1f}M")
    st.metric("Optimized", f"${total_current/1e6:.1f}M")
    st.metric(
        "Net Impact", 
        f"${abs(total_change)/1e6:.1f}M",
        f"{-total_change/total_base*100:.1f}%" if total_change != 0 else "0%",
        delta_color="inverse"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Key insights
    st.markdown("<div class='metric-card' style='margin-top: 20px;'>", unsafe_allow_html=True)
    st.markdown("### Key Insights")
    
    if st.session_state.mode == 'strategy' and st.session_state.selected_strategy != "none":
        effects = INTERDEPENDENCY_MATRIX[st.session_state.selected_strategy]
        increases = [(k, v) for k, v in effects.items() if v > 0]
        decreases = [(k, v) for k, v in effects.items() if v < 0]
        
        if increases:
            st.markdown("**Investments:**")
            for div, change in increases:
                st.markdown(f"• {CSI_DIVISIONS[div]['name']}: +{change}%")
        
        if decreases:
            st.markdown("**Savings:**")
            for div, change in decreases:
                st.markdown(f"• {CSI_DIVISIONS[div]['name']}: {change}%")
    else:
        st.markdown("""
        **HDR's Integrated Design Philosophy:**
        
        • Strategic investments in one system can reduce costs in others
        • Holistic optimization outperforms siloed cost-cutting
        • Sustainability and value engineering work together
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Export section
st.markdown("<div style='margin-top: 40px;'>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown("### Export & Integration")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        # Prepare export data
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
            label="📊 Export CSV",
            data=csv,
            file_name=f"hdr_cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col_b:
        st.button("🔗 Connect PowerBI", use_container_width=True, disabled=True)
        st.caption("Coming soon")
    
    with col_c:
        st.button("🦗 Grasshopper Plugin", use_container_width=True, disabled=True)
        st.caption("Coming soon")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style='text-align: center; margin-top: 60px; padding: 20px; color: #86868B;'>
    <p style='margin: 0;'>HDR Architecture · Cost Intelligence Platform</p>
    <p style='margin: 0; margin-top: 4px; font-size: 12px;'>Supporting integrated healthcare design since 1917</p>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)