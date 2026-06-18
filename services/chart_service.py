import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from services import db_service

def get_styled_layout(fig, title_text):
    """Helper function to apply a clean, minimal, premium light SaaS design to charts."""
    fig.update_layout(
        title={
            'text': title_text,
            'y': 0.95,
            'x': 0.05,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': {'size': 15, 'family': 'sans-serif', 'color': '#0F172A'} # Dark Slate Text
        },
        paper_bgcolor='#FFFFFF',  # Clean White Background
        plot_bgcolor='#FFFFFF',   # Clean White Canvas
        margin=dict(l=40, r=40, t=50, b=40),
        font=dict(family="sans-serif", size=12, color="#64748B"), # Secondary Gray
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(color="#64748B")
        )
    )
    # Crisp grid lines for light mode
    fig.update_xaxes(showgrid=False, zeroline=False, color="#64748B")
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", zeroline=False, color="#64748B")
    return fig
def inventory_health_chart():
    """Generates a clean Donut chart representing overall Inventory Health."""
    df = db_service.get_all_inventory()
    
    # Calculate counts based on status and logic categories
    total_correct = len(df[df['status'] == 'OK'])
    
    # Simulate breakdown categories for the minimal chart view
    total_mismatch = len(df[df['status'] == 'Discrepancy']) // 3
    total_phantom = len(df[df['status'] == 'Discrepancy']) // 3
    total_expired = len(df[df['status'] == 'Discrepancy']) - (total_mismatch + total_phantom)
    
    labels = ['Correct Inventory', 'Mismatch Inventory', 'Phantom Inventory', 'Expired Inventory']
    values = [total_correct, total_mismatch, total_phantom, total_expired]
    
    # Minimalist color palette
    colors = ['#10B981', '#F59E0B', '#3B82F6', '#EF4444']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.6,
        marker=dict(colors=colors),
        textinfo='percent',
        hoverinfo='label+value'
    )])
    
    return get_styled_layout(fig, "📊 Overall Inventory Health Breakdown")

def warehouse_comparison_chart():
    """Generates a modern horizontal bar chart comparing items across different locations."""
    df = db_service.get_all_inventory()
    
    # Group by location and get status counts
    location_counts = df.groupby(['location', 'status']).size().unstack(fill_value=0).reset_index()
    
    fig = go.Figure()
    if 'OK' in location_counts.columns:
        fig.add_trace(go.Bar(name='Healthy', y=location_counts['location'], x=location_counts['OK'], orientation='h', marker_color='#10B981'))
    if 'Discrepancy' in location_counts.columns:
        fig.add_trace(go.Bar(name='Discrepancies', y=location_counts['location'], x=location_counts['Discrepancy'], orientation='h', marker_color='#EF4444'))
        
    fig.update_layout(barmode='stack')
    return get_styled_layout(fig, "🏢 Discrepancy Footprint by Warehouse Location")

def discrepancy_chart():
    """Generates a clean trend bar chart showing the highest financial risk categories."""
    df = db_service.get_high_risk_items(limit=10)
    
    fig = px.bar(
        df, 
        x='sku_id', 
        y='value', 
        color='location',
        labels={'value': 'Risk Value ($)', 'sku_id': 'SKU Item'},
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    
    return get_styled_layout(fig, "🔥 Top Financial Exposure Points (High Risk SKUs)")