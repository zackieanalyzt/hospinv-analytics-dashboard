"""
Quality Control Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Quality Control", page_icon="✅", layout="wide")

st.title("✅ Quality Control Reports")

try:
    from utils.db import get_db
    from utils.queries import (
        QUERY_QUALITY_RESULTS_RECENT,
        QUERY_QUALITY_SUMMARY
    )
    from utils.formatting import format_date, format_datetime, format_number
    
    db = get_db()
    
    # Tabs
    tab1, tab2 = st.tabs(["📊 Summary", "📋 Recent Results"])
    
    # Tab 1: Summary
    with tab1:
        st.subheader("Quality Control Summary (Last 30 Days)")
        
        summary_data = db.fetch_dataframe(QUERY_QUALITY_SUMMARY)
        
        if not summary_data.empty:
            # Status metrics
            passed_count = summary_data[summary_data['result_status'] == 'PASSED']['count'].sum() if 'PASSED' in summary_data['result_status'].values else 0
            failed_count = summary_data[summary_data['result_status'] == 'FAILED']['count'].sum() if 'FAILED' in summary_data['result_status'].values else 0
            total_tests = summary_data['count'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("✅ Passed", format_number(passed_count))
            
            with col2:
                st.metric("❌ Failed", format_number(failed_count))
            
            with col3:
                pass_rate = (passed_count / max(total_tests, 1)) * 100
                st.metric("📊 Pass Rate", f"{pass_rate:.1f}%")
            
            with col4:
                st.metric("📋 Total Tests", format_number(total_tests))
            
            st.divider()
            
            # Status Distribution Charts
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Pie chart
                fig_pie = px.pie(
                    summary_data,
                    values='count',
                    names='result_status',
                    title='QC Results Distribution',
                    color_discrete_map={'PASSED': '#2ecc71', 'FAILED': '#e74c3c', 'PENDING': '#f39c12'}
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Bar chart
                fig_bar = px.bar(
                    summary_data,
                    x='result_status',
                    y='count',
                    title='QC Results by Status',
                    labels={'result_status': 'Status', 'count': 'Count'},
                    color='result_status',
                    color_discrete_map={'PASSED': '#2ecc71', 'FAILED': '#e74c3c', 'PENDING': '#f39c12'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            st.divider()
            
            # Percentage breakdown
            st.subheader("Status Breakdown")
            
            display_data = summary_data.copy()
            display_data['count'] = display_data['count'].apply(format_number)
            display_data['percentage'] = display_data['percentage'].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(display_data, use_container_width=True)
        else:
            st.info("ℹ️ No QC data available for the last 30 days.")
    
    # Tab 2: Recent Results
    with tab2:
        st.subheader("Recent QC Test Results")
        
        recent_data = db.fetch_dataframe(QUERY_QUALITY_RESULTS_RECENT)
        
        if not recent_data.empty:
            # Filter options
            col1, col2, col3 = st.columns([2, 2, 2])
            
            with col1:
                item_filter = st.text_input("🔍 Filter by Item", "")
            
            with col2:
                status_filter = st.selectbox(
                    "Status Filter",
                    ["All"] + recent_data['result_status'].unique().tolist()
                )
            
            with col3:
                test_type_filter = st.selectbox(
                    "Test Type Filter",
                    ["All"] + recent_data['test_type'].unique().tolist()
                )
            
            # Apply filters
            filtered_data = recent_data.copy()
            
            if item_filter:
                filtered_data = filtered_data[
                    filtered_data['item_name'].str.contains(item_filter, case=False, na=False)
                ]
            
            if status_filter != "All":
                filtered_data = filtered_data[filtered_data['result_status'] == status_filter]
            
            if test_type_filter != "All":
                filtered_data = filtered_data[filtered_data['test_type'] == test_type_filter]
            
            # Count by status
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📋 Filtered Results", format_number(len(filtered_data)))
            
            with col2:
                passed = len(filtered_data[filtered_data['result_status'] == 'PASSED'])
                st.metric("✅ Passed", format_number(passed))
            
            with col3:
                failed = len(filtered_data[filtered_data['result_status'] == 'FAILED'])
                st.metric("❌ Failed", format_number(failed))
            
            st.divider()
            
            # Results table
            display_data = filtered_data.copy()
            display_data['test_date'] = pd.to_datetime(display_data['test_date']).astype(str)
            
            # Color code status
            def highlight_status(val):
                if val == 'PASSED':
                    return 'background-color: #d4edda'
                elif val == 'FAILED':
                    return 'background-color: #f8d7da'
                else:
                    return 'background-color: #fff3cd'
            
            st.dataframe(display_data, use_container_width=True, height=500)
            
            st.divider()
            
            # Statistics
            st.subheader("QC Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("By Test Type")
                test_type_counts = filtered_data['test_type'].value_counts()
                for test_type, count in test_type_counts.items():
                    st.write(f"**{test_type}**: {format_number(count)}")
            
            with col2:
                st.subheader("By Status")
                status_counts = filtered_data['result_status'].value_counts()
                for status, count in status_counts.items():
                    st.write(f"**{status}**: {format_number(count)}")
            
            with col3:
                st.subheader("By Warehouse")
                warehouse_counts = filtered_data['warehouse_name'].value_counts()
                for wh, count in warehouse_counts.items():
                    st.write(f"**{wh}**: {format_number(count)}")
        else:
            st.info("ℹ️ No recent QC results available.")

except Exception as e:
    st.error(f"Error loading QC data: {str(e)}")
    st.info("Please check your database connection and try again.")
