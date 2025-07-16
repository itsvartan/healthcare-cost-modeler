import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import base64
from io import BytesIO

# Page config
st.set_page_config(
    page_title="Healthcare Cost Modeler",
    page_icon="🏥",
    layout="wide"
)

# Initialize session state
if 'allocations' not in st.session_state:
    st.session_state.allocations = {
        "envelope": 15.0,
        "superstructure": 20.0,
        "foundation": 10.0,
        "plumbing": 8.0,
        "mechanical": 18.0,
        "electrical": 12.0,
        "equipment": 7.0,
        "fees": 10.0
    }

# Constants
CATEGORIES = {
    "envelope": {"name": "Enclosure (Envelope)", "base": 15.0, "color": "#2E86AB"},
    "superstructure": {"name": "Superstructure", "base": 20.0, "color": "#A23B72"},
    "foundation": {"name": "Foundation", "base": 10.0, "color": "#F18F01"},
    "plumbing": {"name": "Plumbing", "base": 8.0, "color": "#C73E1D"},
    "mechanical": {"name": "Mechanical", "base": 18.0, "color": "#6A994E"},
    "electrical": {"name": "Electrical", "base": 12.0, "color": "#BC4B51"},
    "equipment": {"name": "Equipment", "base": 7.0, "color": "#5B8C85"},
    "fees": {"name": "Contractor & A/E Fees", "base": 10.0, "color": "#8B5A3C"}
}

TRADE_RULES = {
    "envelope": {"mechanical": -0.8, "electrical": -0.3},
    "superstructure": {"foundation": -0.6},
    "plumbing": {"electrical": -0.6, "mechanical": -0.4}
}

# Title
st.title("🏥 Healthcare Architecture Cost Modeling Tool")
st.markdown("Adjust cost allocations to see trade-offs across building systems")

# Sidebar
with st.sidebar:
    st.header("Project Settings")
    total_cost = st.number_input(
        "Total Project Cost ($)",
        min_value=1000000,
        max_value=500000000,
        value=50000000,
        step=1000000,
        format="%d"
    )
    
    if st.button("Reset to Baseline", type="secondary"):
        for cat_id in st.session_state.allocations:
            st.session_state.allocations[cat_id] = CATEGORIES[cat_id]["base"]
        st.rerun()

# Main layout
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Cost Category Adjustments")
    
    # Store original values
    original_values = st.session_state.allocations.copy()
    
    # Create sliders
    for cat_id, cat_info in CATEGORIES.items():
        value = st.slider(
            cat_info["name"],
            min_value=0.0,
            max_value=30.0,
            value=st.session_state.allocations[cat_id],
            step=0.5,
            key=f"slider_{cat_id}"
        )
        
        # If value changed, apply trade-off rules
        if value != original_values[cat_id]:
            # Reset all to base first
            for cid in st.session_state.allocations:
                st.session_state.allocations[cid] = CATEGORIES[cid]["base"]
            
            # Apply the change
            st.session_state.allocations[cat_id] = value
            delta = value - CATEGORIES[cat_id]["base"]
            
            # Apply trade-off rules
            if cat_id in TRADE_RULES and delta != 0:
                for affected, multiplier in TRADE_RULES[cat_id].items():
                    adjustment = delta * multiplier / 10
                    st.session_state.allocations[affected] += adjustment
            
            st.rerun()
        
        # Show delta
        delta = st.session_state.allocations[cat_id] - CATEGORIES[cat_id]["base"]
        if abs(delta) > 0.1:
            dollar_delta = total_cost * (delta / 100)
            st.caption(f"{delta:+.1f}% (${dollar_delta:+,.0f})")

with col2:
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Comparison View", "Breakdown", "Trade-offs"])
    
    with tab1:
        # Comparison chart
        categories = [CATEGORIES[cid]["name"] for cid in CATEGORIES]
        baseline = [CATEGORIES[cid]["base"] for cid in CATEGORIES]
        current = [st.session_state.allocations[cid] for cid in CATEGORIES]
        
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
            marker_color=[CATEGORIES[cid]["color"] for cid in CATEGORIES],
            text=[f"{v:.1f}%" for v in current],
            textposition="outside"
        ))
        fig.update_layout(
            title="Cost Allocation Comparison",
            barmode="group",
            height=500,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Treemap
        data = []
        for cid, info in CATEGORIES.items():
            pct = st.session_state.allocations[cid]
            amount = total_cost * (pct / 100)
            data.append({
                "Category": info["name"],
                "Amount": amount,
                "Percentage": pct
            })
        
        df = pd.DataFrame(data)
        
        fig = go.Figure(go.Treemap(
            labels=df["Category"],
            values=df["Amount"],
            parents=[""] * len(df),
            text=[f"{cat}<br>${amt:,.0f}<br>{pct:.1f}%" 
                  for cat, amt, pct in zip(df["Category"], df["Amount"], df["Percentage"])],
            marker=dict(
                colorscale="RdYlBu_r",
                cmid=15,
                cmin=0,
                cmax=30,
                colorbar=dict(title="Percentage")
            )
        ))
        fig.update_layout(
            title=f"Project Cost Breakdown (Total: ${total_cost:,.0f})",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Trade-off waterfall
        deltas = []
        for cid in CATEGORIES:
            delta = st.session_state.allocations[cid] - CATEGORIES[cid]["base"]
            if abs(delta) > 0.1:
                deltas.append({
                    "Category": CATEGORIES[cid]["name"],
                    "Change": total_cost * (delta / 100),
                    "Percentage": delta
                })
        
        if deltas:
            df_deltas = pd.DataFrame(deltas)
            
            fig = go.Figure(go.Waterfall(
                x=df_deltas["Category"],
                y=df_deltas["Change"],
                text=[f"{p:+.1f}%<br>${c:+,.0f}" for p, c in zip(df_deltas["Percentage"], df_deltas["Change"])],
                textposition="outside",
                increasing={"marker": {"color": "green"}},
                decreasing={"marker": {"color": "red"}}
            ))
            fig.update_layout(
                title="Cost Trade-off Analysis",
                height=500,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Adjust sliders to see trade-offs")

# Export section
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    # CSV Export
    csv_data = []
    for cid, info in CATEGORIES.items():
        csv_data.append({
            "Category": info["name"],
            "Baseline %": info["base"],
            "Adjusted %": st.session_state.allocations[cid],
            "Change %": st.session_state.allocations[cid] - info["base"],
            "Baseline $": total_cost * (info["base"] / 100),
            "Adjusted $": total_cost * (st.session_state.allocations[cid] / 100)
        })
    
    df_export = pd.DataFrame(csv_data)
    csv = df_export.to_csv(index=False)
    
    st.download_button(
        label="📊 Download CSV",
        data=csv,
        file_name=f"cost_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

with col2:
    st.button("🖼️ Export Charts", disabled=True, help="Use browser screenshot for now")

with col3:
    st.button("📄 Generate PDF", disabled=True, help="Coming soon")

# Footer
st.markdown("---")
st.markdown("Built for healthcare architecture cost analysis • Trade-off rules are customizable")