"""
Inventory Management Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Inventory", page_icon="📦", layout="wide")

st.title("📦 Inventory Management")

try:
    from utils.db import get_db
    from utils.queries import (
        QUERY_INVENTORY_LEVEL,
        QUERY_LOW_STOCK_ITEMS,
        QUERY_EXPIRY_ITEMS,
        QUERY_DEAD_STOCK,
        QUERY_EXPIRY_SUMMARY
    )
    from utils.formatting import (
        format_number, format_date, format_currency,
        days_until, format_dataframe_display
    )
    
    db = get_db()
    
    # Tabs for different inventory views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Stock Levels",
        "⚠️ Low Stock",
        "⏰ Expiry Warning",
        "💀 Dead Stock",
        "📈 Expiry Summary"
    ])
    
    # Tab 1: Stock Levels
    with tab1:
        st.subheader("Current Stock Levels")
        
        inventory_data = db.fetch_dataframe(QUERY_INVENTORY_LEVEL)
        
        if not inventory_data.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                unique_items = inventory_data['item_code'].nunique()
                st.metric("🏷️ Total Items", format_number(unique_items))
            
            with col2:
                unique_warehouses = inventory_data['warehouse'].nunique()
                st.metric("🏢 Warehouses", format_number(unique_warehouses))
            
            with col3:
                total_qty = inventory_data['quantity'].sum()
                st.metric("📦 Total Quantity", format_number(total_qty))
            
            with col4:
                st.metric("📅 Last Updated", 
                         inventory_data['last_updated'].max().strftime("%d/%m/%Y %H:%M") 
                         if not inventory_data.empty else "N/A")
            
            st.divider()
            
            # Search and filter
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                item_filter = st.text_input("🔍 Filter by Item Code/Name", "")
            with col2:
                warehouse_filter = st.selectbox(
                    "🏢 Filter by Warehouse",
                    ["All"] + inventory_data['warehouse'].unique().tolist()
                )
            with col3:
                min_qty = st.number_input("Min Quantity", 0, value=0)
            
            # Apply filters
            filtered_data = inventory_data.copy()
            
            if item_filter:
                filtered_data = filtered_data[
                    (filtered_data['item_code'].str.contains(item_filter, case=False, na=False)) |
                    (filtered_data['item_name'].str.contains(item_filter, case=False, na=False))
                ]
            
            if warehouse_filter != "All":
                filtered_data = filtered_data[filtered_data['warehouse'] == warehouse_filter]
            
            filtered_data = filtered_data[filtered_data['quantity'] >= min_qty]
            
            # Display table
            display_data = filtered_data.copy()
            display_data['quantity'] = display_data['quantity'].apply(format_number)
            display_data['last_updated'] = display_data['last_updated'].astype(str)
            
            st.dataframe(display_data, use_container_width=True, height=500)
            
            # Chart: Top items by quantity
            st.divider()
            st.subheader("Top 15 Items by Stock Quantity")
            
            top_items = inventory_data.groupby('item_code')['quantity'].sum().nlargest(15).reset_index()
            
            fig = px.bar(
                top_items,
                x='quantity',
                y='item_code',
                orientation='h',
                title='Top 15 Items by Stock Quantity',
                labels={'item_code': 'Item', 'quantity': 'Quantity'},
                color='quantity',
                color_continuous_scale='Viridis'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Tab 2: Low Stock Items
    with tab2:
        st.subheader("Low Stock Alert")
        
        low_stock_data = db.fetch_dataframe(QUERY_LOW_STOCK_ITEMS)
        
        if not low_stock_data.empty:
            # Risk level metrics
            critical = len(low_stock_data[low_stock_data['stock_qty'] <= 0])
            warning = len(low_stock_data[(low_stock_data['stock_qty'] > 0) & 
                                         (low_stock_data['stock_qty'] <= low_stock_data['reorder_point'] * 0.5)])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🔴 Critical (Out of Stock)", format_number(critical))
            
            with col2:
                st.metric("🟡 Warning", format_number(warning))
            
            with col3:
                st.metric("📋 Total Low Stock Items", format_number(len(low_stock_data)))
            
            st.divider()
            
            # Display table with color coding
            display_data = low_stock_data.copy()
            display_data['stock_qty'] = display_data['stock_qty'].apply(format_number)
            display_data['reorder_point'] = display_data['reorder_point'].apply(format_number)
            display_data['last_checked'] = display_data['last_checked'].astype(str)
            
            st.dataframe(display_data, use_container_width=True, height=500)
            
            # Chart: Low stock by warehouse
            st.divider()
            st.subheader("Low Stock Items by Warehouse")
            
            low_stock_by_wh = low_stock_data.groupby('warehouse').size().reset_index(name='count')
            
            fig = px.bar(
                low_stock_by_wh,
                x='warehouse',
                y='count',
                title='Low Stock Items by Warehouse',
                labels={'warehouse': 'Warehouse', 'count': 'Number of Items'},
                color='count',
                color_continuous_scale='Reds'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No low stock items detected!")
    
    # Tab 3: Expiry Warning
    with tab3:
        st.subheader("Items Nearing Expiry")
        
        expiry_data = db.fetch_dataframe(QUERY_EXPIRY_ITEMS)
        
        if not expiry_data.empty:
            # Risk levels
            expired = len(expiry_data[expiry_data['days_to_expiry'] <= 0])
            critical_soon = len(expiry_data[(expiry_data['days_to_expiry'] > 0) & 
                                            (expiry_data['days_to_expiry'] <= 30)])
            warning = len(expiry_data[(expiry_data['days_to_expiry'] > 30) & 
                                      (expiry_data['days_to_expiry'] <= 90)])
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🔴 Already Expired", format_number(expired))
            
            with col2:
                st.metric("🔴 Expiring <30d", format_number(critical_soon))
            
            with col3:
                st.metric("🟡 30-90 Days", format_number(warning))
            
            with col4:
                st.metric("📋 Total Items", format_number(len(expiry_data)))
            
            st.divider()
            
            # Display table
            display_data = expiry_data.copy()
            display_data['expiry_date'] = display_data['expiry_date'].astype(str)
            display_data['stock_qty'] = display_data['stock_qty'].apply(format_number)
            display_data['days_to_expiry'] = display_data['days_to_expiry'].apply(lambda x: f"{x} days")
            
            st.dataframe(display_data, use_container_width=True, height=500)
            
            # Chart: Expiry distribution
            st.divider()
            
            fig = px.histogram(
                expiry_data,
                x='days_to_expiry',
                nbins=20,
                title='Distribution of Days to Expiry',
                labels={'days_to_expiry': 'Days to Expiry', 'count': 'Number of Lots'},
                color_discrete_sequence=['#ff6b6b']
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No items nearing expiry!")
    
    # Tab 4: Dead Stock
    with tab4:
        st.subheader("Dead Stock Analysis")
        
        dead_stock_data = db.fetch_dataframe(QUERY_DEAD_STOCK)
        
        if not dead_stock_data.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💀 Dead Stock Items", format_number(len(dead_stock_data)))
            
            with col2:
                total_dead_qty = dead_stock_data['stock_qty'].sum()
                st.metric("📦 Total Dead Stock Qty", format_number(total_dead_qty))
            
            with col3:
                avg_inactive = dead_stock_data['days_inactive'].mean()
                st.metric("⏳ Avg Days Inactive", format_number(avg_inactive))
            
            st.divider()
            
            # Display table
            display_data = dead_stock_data.copy()
            display_data['stock_qty'] = display_data['stock_qty'].apply(format_number)
            display_data['last_movement'] = display_data['last_movement'].astype(str)
            display_data['days_inactive'] = display_data['days_inactive'].apply(format_number)
            
            st.dataframe(display_data, use_container_width=True, height=500)
            
            # Chart: Inactivity period distribution
            st.divider()
            
            fig = px.histogram(
                dead_stock_data,
                x='days_inactive',
                nbins=20,
                title='Distribution of Days Since Last Movement',
                labels={'days_inactive': 'Days Inactive', 'count': 'Number of Items'},
                color_discrete_sequence=['#8b0000']
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No dead stock detected!")
    
    # Tab 5: Expiry Summary
    with tab5:
        st.subheader("Expiry Timeline Summary")
        
        expiry_summary = db.fetch_dataframe(QUERY_EXPIRY_SUMMARY)
        
        if not expiry_summary.empty:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Pie chart
                fig_pie = px.pie(
                    expiry_summary,
                    values='total_quantity',
                    names='expiry_range',
                    title='Stock by Expiry Range'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Bar chart
                fig_bar = px.bar(
                    expiry_summary,
                    x='expiry_range',
                    y='item_count',
                    title='Number of Lots by Expiry Range',
                    labels={'expiry_range': 'Expiry Range', 'item_count': 'Number of Lots'},
                    color='item_count',
                    color_continuous_scale='RdYlGn_r'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            st.divider()
            st.subheader("Expiry Summary Table")
            
            display_data = expiry_summary.copy()
            display_data['item_count'] = display_data['item_count'].apply(format_number)
            display_data['total_quantity'] = display_data['total_quantity'].apply(format_number)
            
            st.dataframe(display_data, use_container_width=True)

except Exception as e:
    st.error(f"Error loading inventory data: {str(e)}")
    st.info("Please check your database connection and try again.")
