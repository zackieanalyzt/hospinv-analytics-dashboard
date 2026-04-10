"""
Advanced Analytics Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

st.title("📈 Advanced Analytics")

try:
    from utils.db import get_db
    from utils.queries import (
        QUERY_CONSUMPTION_BY_ITEM,
        QUERY_CONSUMPTION_MONTHLY,
        QUERY_TOP_VENDORS
    )
    from utils.formatting import format_number, format_currency
    
    db = get_db()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Consumption Analysis",
        "📈 Monthly Trends",
        "🏆 Top Items & Vendors"
    ])
    
    # Tab 1: Consumption by Item
    with tab1:
        st.subheader("Item Consumption Analysis (Last 30 Days)")
        
        consumption_data = db.fetch_dataframe(QUERY_CONSUMPTION_BY_ITEM)
        
        if not consumption_data.empty:
            # Metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📦 Items Consumed", format_number(len(consumption_data)))
            
            with col2:
                total_consumed = consumption_data['total_consumed'].sum()
                st.metric("📊 Total Quantity", format_number(total_consumed))
            
            with col3:
                total_cost = consumption_data['total_cost'].sum()
                st.metric("💰 Total Cost", format_currency(total_cost))
            
            st.divider()
            
            # Top consumed items chart
            st.subheader("Top 20 Most Consumed Items")
            
            top_items = consumption_data.nlargest(20, 'total_consumed')
            
            fig = px.barh(
                top_items,
                x='total_consumed',
                y='item_code',
                title='Top 20 Items by Consumption Quantity',
                labels={'item_code': 'Item Code', 'total_consumed': 'Quantity Consumed'},
                color='total_consumed',
                color_continuous_scale='Blues'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Top items by cost
            st.subheader("Top 20 Items by Cost")
            
            top_cost_items = consumption_data.nlargest(20, 'total_cost')
            
            fig_cost = px.barh(
                top_cost_items,
                x='total_cost',
                y='item_code',
                title='Top 20 Items by Consumption Cost',
                labels={'item_code': 'Item Code', 'total_cost': 'Total Cost'},
                color='total_cost',
                color_continuous_scale='Reds'
            )
            
            st.plotly_chart(fig_cost, use_container_width=True)
            
            st.divider()
            
            # Detailed table
            st.subheader("Consumption Details")
            
            display_data = consumption_data.copy()
            display_data['total_consumed'] = display_data['total_consumed'].apply(format_number)
            display_data['total_cost'] = display_data['total_cost'].apply(format_currency)
            
            # Add unit cost calculation
            display_data['unit_cost'] = consumption_data.apply(
                lambda row: format_currency(row['total_cost'] / max(row['total_consumed'], 1)),
                axis=1
            )
            
            st.dataframe(display_data, use_container_width=True, height=500)
        else:
            st.info("ℹ️ No consumption data available for the last 30 days.")
    
    # Tab 2: Monthly Trends
    with tab2:
        st.subheader("Monthly Consumption Trends")
        
        monthly_data = db.fetch_dataframe(QUERY_CONSUMPTION_MONTHLY)
        
        if not monthly_data.empty:
            monthly_data = monthly_data.sort_values(['YEAR', 'MONTH'])
            
            # Create date label
            monthly_data['date_label'] = monthly_data.apply(
                lambda row: f"{int(row['MONTH'])}/{int(row['YEAR'])}",
                axis=1
            )
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=monthly_data['date_label'],
                y=monthly_data['total_quantity'],
                name='Quantity',
                mode='lines+markers',
                line=dict(color='#3498db', width=2),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title='Monthly Consumption Quantity Trend',
                xaxis_title='Month/Year',
                yaxis_title='Quantity',
                hovermode='x unified',
                height=400,
                template='plotly_light'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Value trend
            fig_value = go.Figure()
            
            fig_value.add_trace(go.Scatter(
                x=monthly_data['date_label'],
                y=monthly_data['total_value'],
                name='Value',
                mode='lines+markers',
                line=dict(color='#e74c3c', width=2),
                marker=dict(size=8)
            ))
            
            fig_value.update_layout(
                title='Monthly Consumption Value Trend',
                xaxis_title='Month/Year',
                yaxis_title='Value (฿)',
                hovermode='x unified',
                height=400,
                template='plotly_light'
            )
            
            st.plotly_chart(fig_value, use_container_width=True)
            
            st.divider()
            
            # Monthly data table
            st.subheader("Monthly Consumption Details")
            
            display_data = monthly_data.copy()
            display_data['YEAR'] = display_data['YEAR'].apply(lambda x: int(x))
            display_data['MONTH'] = display_data['MONTH'].apply(lambda x: int(x))
            display_data['total_quantity'] = display_data['total_quantity'].apply(format_number)
            display_data['total_value'] = display_data['total_value'].apply(format_currency)
            
            st.dataframe(
                display_data[['YEAR', 'MONTH', 'total_quantity', 'total_value']],
                use_container_width=True
            )
        else:
            st.info("ℹ️ No monthly consumption data available.")
    
    # Tab 3: Top Items & Vendors
    with tab3:
        st.subheader("Top Performers Analysis")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📦 Top Consumed Items")
            
            consumption_data = db.fetch_dataframe(QUERY_CONSUMPTION_BY_ITEM)
            
            if not consumption_data.empty:
                top_consumption = consumption_data.nlargest(10, 'total_consumed')[
                    ['item_code', 'item_name', 'total_consumed', 'total_cost']
                ]
                
                display_data = top_consumption.copy()
                display_data['total_consumed'] = display_data['total_consumed'].apply(format_number)
                display_data['total_cost'] = display_data['total_cost'].apply(format_currency)
                
                st.dataframe(display_data, use_container_width=True)
        
        with col2:
            st.subheader("🤝 Top Vendors")
            
            vendor_data = db.fetch_dataframe(QUERY_TOP_VENDORS)
            
            if not vendor_data.empty:
                top_vendors = vendor_data.nlargest(10, 'total_amount')[
                    ['vendor_name', 'order_count', 'total_amount', 'avg_order_value']
                ]
                
                display_data = top_vendors.copy()
                display_data['total_amount'] = display_data['total_amount'].apply(format_currency)
                display_data['avg_order_value'] = display_data['avg_order_value'].apply(format_currency)
                
                st.dataframe(display_data, use_container_width=True)

except Exception as e:
    st.error(f"Error loading analytics data: {str(e)}")
    st.info("Please check your database connection and try again.")
