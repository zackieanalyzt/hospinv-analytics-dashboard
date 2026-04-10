"""
Dashboard Overview Page - Main Metrics and KPIs
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard Overview")

try:
    from utils.db import get_db
    from utils.queries import (
        QUERY_INVENTORY_MOVEMENT_SUMMARY,
        QUERY_CONSUMPTION_DAILY,
        QUERY_DATA_FRESHNESS
    )
    from utils.formatting import format_number, format_currency
    
    db = get_db()
    
    # Key Metrics Row
    st.subheader("Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Movement Summary
        movement_data = db.fetch_dataframe(QUERY_INVENTORY_MOVEMENT_SUMMARY)
        
        if not movement_data.empty:
            total_qty = movement_data['total_quantity'].sum()
            total_value = movement_data['total_value'].sum()
            transaction_count = movement_data['transaction_count'].sum()
            
            with col1:
                st.metric("📦 Total Transactions (30d)", format_number(transaction_count))
            
            with col2:
                st.metric("📊 Total Quantity Moved (30d)", format_number(total_qty))
            
            with col3:
                st.metric("💰 Total Value (30d)", format_currency(total_value))
            
            with col4:
                st.metric("🎯 Avg Transaction Value", format_currency(total_value / max(transaction_count, 1)))
    
    except Exception as e:
        st.warning(f"Could not load movement summary: {str(e)}")
    
    st.divider()
    
    # Consumption Trend
    st.subheader("Daily Consumption Trend (Last 30 Days)")
    
    try:
        consumption_data = db.fetch_dataframe(QUERY_CONSUMPTION_DAILY)
        
        if not consumption_data.empty:
            consumption_data['date'] = pd.to_datetime(consumption_data['date'])
            consumption_data = consumption_data.sort_values('date')
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=consumption_data['date'],
                y=consumption_data['total_quantity'],
                name='Quantity',
                mode='lines+markers',
                line=dict(color='#667eea', width=2),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title="Daily Consumption - Quantity Trend",
                xaxis_title="Date",
                yaxis_title="Quantity",
                hovermode='x unified',
                height=400,
                template="plotly_light"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Could not load consumption trend: {str(e)}")
    
    st.divider()
    
    # Movement Type Distribution
    st.subheader("Movement Type Distribution (Last 30 Days)")
    
    try:
        movement_data = db.fetch_dataframe(QUERY_INVENTORY_MOVEMENT_SUMMARY)
        
        if not movement_data.empty:
            fig = px.pie(
                movement_data,
                values='transaction_count',
                names='movement_type',
                title='Transactions by Movement Type',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Summary Table")
                
                display_data = movement_data.copy()
                display_data['transaction_count'] = display_data['transaction_count'].apply(format_number)
                display_data['total_quantity'] = display_data['total_quantity'].apply(format_number)
                display_data['total_value'] = display_data['total_value'].apply(format_currency)
                
                st.dataframe(display_data, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Could not load movement distribution: {str(e)}")
    
    st.divider()
    
    # Data Freshness
    st.subheader("Data Source Freshness")
    
    try:
        freshness_data = db.fetch_dataframe(QUERY_DATA_FRESHNESS)
        
        if not freshness_data.empty:
            freshness_data_display = freshness_data.copy()
            freshness_data_display['last_updated'] = freshness_data_display['last_updated'].astype(str)
            freshness_data_display['hours_since_update'] = freshness_data_display['hours_since_update'].apply(
                lambda x: f"{x:.1f} hrs" if pd.notna(x) else "N/A"
            )
            
            # Color code based on freshness
            def color_freshness(hours):
                if pd.isna(hours):
                    return "background-color: gray"
                if hours < 24:
                    return "background-color: lightgreen"
                elif hours < 48:
                    return "background-color: lightyellow"
                else:
                    return "background-color: lightcoral"
            
            st.dataframe(
                freshness_data_display[['table_name', 'last_updated', 'hours_since_update']],
                use_container_width=True
            )
    
    except Exception as e:
        st.info(f"Data freshness tracking not available: {str(e)}")

except Exception as e:
    st.error(f"Error loading dashboard: {str(e)}")
    st.info("Please check your database connection and try again.")
