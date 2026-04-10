"""
Procurement Dashboard - Purchase Orders and Goods Receipt
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Procurement", page_icon="🛒", layout="wide")

st.title("🛒 Procurement Management")

try:
    from utils.db import get_db
    from utils.queries import (
        QUERY_PURCHASE_ORDERS_OPEN,
        QUERY_GOODS_RECEIPT_PENDING,
        QUERY_TOP_VENDORS
    )
    from utils.formatting import format_number, format_date, format_currency
    
    db = get_db()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📋 Purchase Orders",
        "📦 Goods Receipt",
        "🤝 Top Vendors"
    ])
    
    # Tab 1: Purchase Orders
    with tab1:
        st.subheader("Open Purchase Orders")
        
        po_data = db.fetch_dataframe(QUERY_PURCHASE_ORDERS_OPEN)
        
        if not po_data.empty:
            # Status breakdown
            status_counts = po_data['status'].value_counts()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📋 Total Open POs", format_number(len(po_data)))
            
            with col2:
                total_value = po_data['total_amount'].sum()
                st.metric("💰 Total Value", format_currency(total_value))
            
            with col3:
                unique_vendors = po_data['vendor_name'].nunique()
                st.metric("🤝 Unique Vendors", format_number(unique_vendors))
            
            with col4:
                avg_order = total_value / max(len(po_data), 1)
                st.metric("📊 Avg Order Value", format_currency(avg_order))
            
            st.divider()
            
            # Status distribution
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig_status = px.bar(
                    status_counts.reset_index().rename(columns={'index': 'Status', 'status': 'Count'}),
                    x='Status',
                    y='Count',
                    title='PO Status Distribution',
                    color='Count',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                st.subheader("Status Breakdown")
                for status, count in status_counts.items():
                    st.write(f"**{status}**: {format_number(count)}")
            
            st.divider()
            
            # PO Details Table
            st.subheader("Purchase Order Details")
            
            display_data = po_data.copy()
            display_data['po_date'] = display_data['po_date'].astype(str)
            display_data['total_amount'] = display_data['total_amount'].apply(format_currency)
            
            st.dataframe(display_data, use_container_width=True, height=500)
        else:
            st.info("ℹ️ No open purchase orders at this time.")
    
    # Tab 2: Goods Receipt
    with tab2:
        st.subheader("Pending Goods Receipt")
        
        gr_data = db.fetch_dataframe(QUERY_GOODS_RECEIPT_PENDING)
        
        if not gr_data.empty:
            # Status metrics
            status_counts = gr_data['status'].value_counts()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📦 Total Pending", format_number(len(gr_data)))
            
            with col2:
                total_qty = gr_data['total_quantity'].sum()
                st.metric("📊 Total Qty", format_number(total_qty))
            
            with col3:
                unique_vendors = gr_data['vendor_name'].nunique()
                st.metric("🤝 Vendors", format_number(unique_vendors))
            
            with col4:
                avg_qty = total_qty / max(len(gr_data), 1)
                st.metric("📈 Avg Qty/Receipt", format_number(avg_qty, decimals=2))
            
            st.divider()
            
            # Timeline view
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Days pending calculation
                gr_data['days_pending'] = pd.to_datetime(gr_data['receipt_date']).apply(
                    lambda x: (pd.Timestamp.now() - x).days
                )
                
                fig_timeline = px.histogram(
                    gr_data,
                    x='days_pending',
                    nbins=15,
                    title='Distribution of Days Pending Receipt',
                    labels={'days_pending': 'Days Pending', 'count': 'Number of Receipts'},
                    color_discrete_sequence=['#FFA500']
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            with col2:
                st.subheader("Status Breakdown")
                for status, count in status_counts.items():
                    st.write(f"**{status}**: {format_number(count)}")
            
            st.divider()
            
            # Details Table
            st.subheader("Goods Receipt Details")
            
            display_data = gr_data.copy()
            display_data['receipt_date'] = display_data['receipt_date'].astype(str)
            display_data['total_quantity'] = display_data['total_quantity'].apply(format_number)
            
            st.dataframe(display_data, use_container_width=True, height=500)
        else:
            st.success("✅ No pending goods receipts!")
    
    # Tab 3: Top Vendors
    with tab3:
        st.subheader("Top Vendors (Last 6 Months)")
        
        vendor_data = db.fetch_dataframe(QUERY_TOP_VENDORS)
        
        if not vendor_data.empty:
            # Overall metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🤝 Active Vendors", format_number(len(vendor_data)))
            
            with col2:
                total_spent = vendor_data['total_amount'].sum()
                st.metric("💰 Total Spent", format_currency(total_spent))
            
            with col3:
                avg_vendor_value = total_spent / max(len(vendor_data), 1)
                st.metric("📊 Avg Vendor Value", format_currency(avg_vendor_value))
            
            st.divider()
            
            # Charts
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Top vendors by amount
                fig_amount = px.bar(
                    vendor_data.nlargest(10, 'total_amount'),
                    x='total_amount',
                    y='vendor_name',
                    orientation='h',
                    title='Top 10 Vendors by Amount',
                    labels={'vendor_name': 'Vendor', 'total_amount': 'Total Amount'},
                    color='total_amount',
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig_amount, use_container_width=True)
            
            with col2:
                # Top vendors by order count
                fig_count = px.bar(
                    vendor_data.nlargest(10, 'order_count'),
                    x='order_count',
                    y='vendor_name',
                    orientation='h',
                    title='Top 10 Vendors by Order Count',
                    labels={'vendor_name': 'Vendor', 'order_count': 'Number of Orders'},
                    color='order_count',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_count, use_container_width=True)
            
            st.divider()
            
            # Vendor Details
            st.subheader("Vendor Performance Details")
            
            display_data = vendor_data.copy()
            display_data['total_amount'] = display_data['total_amount'].apply(format_currency)
            display_data['avg_order_value'] = display_data['avg_order_value'].apply(format_currency)
            
            st.dataframe(display_data, use_container_width=True)
        else:
            st.info("ℹ️ No vendor data available for the selected period.")

except Exception as e:
    st.error(f"Error loading procurement data: {str(e)}")
    st.info("Please check your database connection and try again.")
