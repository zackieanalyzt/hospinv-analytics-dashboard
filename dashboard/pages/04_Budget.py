"""
Budget Analysis Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Budget", page_icon="💰", layout="wide")

st.title("💰 Budget Analysis")

try:
    from utils.db import get_db
    from utils.queries import (
        QUERY_BUDGET_BURN_MONTHLY,
        QUERY_BUDGET_SUMMARY
    )
    from utils.formatting import format_number, format_currency
    
    db = get_db()
    
    # Budget Burn Analysis
    st.subheader("Monthly Budget Burn Rate (Current Year)")
    
    burn_data = db.fetch_dataframe(QUERY_BUDGET_BURN_MONTHLY)
    
    if not burn_data.empty:
        burn_data = burn_data.sort_values('month')
        
        # Calculate current and previous year trends
        current_total_allocated = burn_data['budget_allocated'].sum()
        current_total_consumed = burn_data['budget_consumed'].sum()
        current_total_remaining = burn_data['budget_remaining'].sum()
        
        # KPI Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💵 Total Allocated", format_currency(current_total_allocated))
        
        with col2:
            st.metric("💸 Total Consumed", format_currency(current_total_consumed))
        
        with col3:
            st.metric("💴 Total Remaining", format_currency(current_total_remaining))
        
        with col4:
            burn_pct = (current_total_consumed / max(current_total_allocated, 1)) * 100
            st.metric("📊 Burn Rate", f"{burn_pct:.1f}%", 
                     delta=f"{burn_pct:.1f}%" if burn_pct <= 100 else f"{burn_pct-100:.1f}% Over")
        
        st.divider()
        
        # Budget Burn Trend Chart
        fig_burn = go.Figure()
        
        fig_burn.add_trace(go.Scatter(
            x=burn_data['month'],
            y=burn_data['budget_allocated'],
            name='Allocated',
            mode='lines+markers',
            line=dict(color='blue', width=2)
        ))
        
        fig_burn.add_trace(go.Scatter(
            x=burn_data['month'],
            y=burn_data['budget_consumed'],
            name='Consumed',
            mode='lines+markers',
            line=dict(color='red', width=2)
        ))
        
        fig_burn.add_trace(go.Scatter(
            x=burn_data['month'],
            y=burn_data['budget_remaining'],
            name='Remaining',
            mode='lines+markers',
            line=dict(color='green', width=2)
        ))
        
        fig_burn.update_layout(
            title='Monthly Budget Allocation vs Consumption (Current Year)',
            xaxis_title='Month',
            yaxis_title='Amount (฿)',
            hovermode='x unified',
            height=400,
            template='plotly_light'
        )
        
        st.plotly_chart(fig_burn, use_container_width=True)
        
        st.divider()
        
        # Monthly Burn Percentage
        fig_burn_pct = px.bar(
            burn_data,
            x='month',
            y='burn_percentage',
            title='Monthly Budget Burn Percentage',
            labels={'month': 'Month', 'burn_percentage': 'Burn %'},
            color='burn_percentage',
            color_continuous_scale='RdYlGn_r'
        )
        
        # Add 100% reference line
        fig_burn_pct.add_hline(y=100, line_dash="dash", line_color="red", 
                               annotation_text="Budget Limit")
        
        st.plotly_chart(fig_burn_pct, use_container_width=True)
        
        st.divider()
        
        # Detailed Table
        st.subheader("Monthly Budget Details")
        
        display_data = burn_data.copy()
        display_data['budget_allocated'] = display_data['budget_allocated'].apply(format_currency)
        display_data['budget_consumed'] = display_data['budget_consumed'].apply(format_currency)
        display_data['budget_remaining'] = display_data['budget_remaining'].apply(format_currency)
        display_data['burn_percentage'] = display_data['burn_percentage'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(display_data, use_container_width=True)

    st.divider()
    
    # Budget by Category
    st.subheader("Budget Summary by Category")
    
    summary_data = db.fetch_dataframe(QUERY_BUDGET_SUMMARY)
    
    if not summary_data.empty:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Pie chart: Allocated
            fig_allocated = px.pie(
                summary_data,
                values='allocated',
                names='category',
                title='Budget Allocation by Category'
            )
            st.plotly_chart(fig_allocated, use_container_width=True)
        
        with col2:
            # Pie chart: Consumed
            fig_consumed = px.pie(
                summary_data,
                values='consumed',
                names='category',
                title='Budget Consumption by Category'
            )
            st.plotly_chart(fig_consumed, use_container_width=True)
        
        st.divider()
        
        # Category comparison
        fig_comparison = go.Figure(data=[
            go.Bar(name='Allocated', x=summary_data['category'], y=summary_data['allocated']),
            go.Bar(name='Consumed', x=summary_data['category'], y=summary_data['consumed']),
            go.Bar(name='Remaining', x=summary_data['category'], y=summary_data['remaining'])
        ])
        
        fig_comparison.update_layout(
            title='Budget by Category - Allocated vs Consumed vs Remaining',
            barmode='group',
            xaxis_title='Category',
            yaxis_title='Amount (฿)',
            height=400
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        st.divider()
        
        st.subheader("Category Budget Details")
        
        display_data = summary_data.copy()
        display_data['allocated'] = display_data['allocated'].apply(format_currency)
        display_data['consumed'] = display_data['consumed'].apply(format_currency)
        display_data['remaining'] = display_data['remaining'].apply(format_currency)
        
        # Calculate burn percentage
        display_data['burn_pct'] = summary_data.apply(
            lambda row: f"{(row['consumed']/max(row['allocated'], 1))*100:.1f}%",
            axis=1
        )
        
        st.dataframe(display_data, use_container_width=True)

except Exception as e:
    st.error(f"Error loading budget data: {str(e)}")
    st.info("Please check your database connection and try again.")
