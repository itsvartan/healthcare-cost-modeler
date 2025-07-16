import os
import base64
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io
from app.config import COST_CATEGORIES

def export_to_csv(model_state, filename=None):
    """Export current cost model data to CSV"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cost_model_export_{timestamp}.csv"
    
    data = []
    total_cost = model_state["total_cost"]
    
    for cat_id, percentage in model_state["allocations"].items():
        cat_name = next(c["name"] for c in COST_CATEGORIES if c["id"] == cat_id)
        base_pct = next(c["base_percentage"] for c in COST_CATEGORIES if c["id"] == cat_id)
        
        data.append({
            "Category": cat_name,
            "Baseline %": base_pct,
            "Adjusted %": percentage,
            "Change %": percentage - base_pct,
            "Baseline $": total_cost * (base_pct / 100),
            "Adjusted $": total_cost * (percentage / 100),
            "Change $": total_cost * ((percentage - base_pct) / 100)
        })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False)

def export_chart_to_image(fig, format="png", width=1200, height=800):
    """Export Plotly figure to image format"""
    img_bytes = fig.to_image(format=format, width=width, height=height)
    return img_bytes

def create_pdf_report(model_state, charts_data):
    """Create comprehensive PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Healthcare Architecture Cost Model Report", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.5*inch))
    
    # Date and project info
    date_text = Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal'])
    project_text = Paragraph(f"Total Project Cost: ${model_state['total_cost']:,.0f}", styles['Heading2'])
    story.append(date_text)
    story.append(project_text)
    story.append(Spacer(1, 0.5*inch))
    
    # Summary table
    data = [["Category", "Baseline %", "Adjusted %", "Change", "Dollar Amount"]]
    
    total_cost = model_state["total_cost"]
    for cat_id, percentage in model_state["allocations"].items():
        cat_name = next(c["name"] for c in COST_CATEGORIES if c["id"] == cat_id)
        base_pct = next(c["base_percentage"] for c in COST_CATEGORIES if c["id"] == cat_id)
        change = percentage - base_pct
        dollar_amt = total_cost * (percentage / 100)
        
        data.append([
            cat_name,
            f"{base_pct:.1f}%",
            f"{percentage:.1f}%",
            f"{change:+.1f}%",
            f"${dollar_amt:,.0f}"
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    
    # Add charts if provided
    if charts_data:
        for chart_title, chart_bytes in charts_data.items():
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(chart_title, styles['Heading2']))
            
            # Convert bytes to image
            img = Image(io.BytesIO(chart_bytes), width=6*inch, height=4*inch)
            story.append(img)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

def create_download_link(data, filename, file_type="text/csv"):
    """Create a download link for exported data"""
    if isinstance(data, bytes):
        b64 = base64.b64encode(data).decode()
    else:
        b64 = base64.b64encode(data.encode()).decode()
    
    return f'<a href="data:{file_type};base64,{b64}" download="{filename}">Download {filename}</a>'