"""
Hospital Inventory Analytics Dashboard - Main Application
Streamlit multi-page dashboard for hospital drug & medical supply analytics
"""
import streamlit as st
import sys
from pathlib import Path

# Add dashboard to path
dashboard_path = Path(__file__).parent
sys.path.insert(0, str(dashboard_path))

from utils.db import get_db
from config import HOSPITAL_NAME, PAGE_ICON, LAYOUT

# Configure Streamlit page
st.set_page_config(
    page_title=f"{HOSPITAL_NAME} - Analytics Dashboard",
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    /* Custom styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #ff9800;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #4caf50;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #f44336;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Sidebar
    with st.sidebar:
        st.title(f"{PAGE_ICON} {HOSPITAL_NAME}")
        st.divider()
        
        # Test database connection
        with st.spinner("Testing database connection..."):
            db = get_db()
            is_connected, msg = db.test_connection()
        
        if is_connected:
            st.success("✅ Database Connected")
        else:
            st.error(f"❌ Database Error: {msg}")
            st.stop()
        
        st.divider()
        st.write("### Navigation")
        st.info("""
        Select a dashboard from the left sidebar to view reports and analytics.
        Data is automatically refreshed every 5 minutes.
        """)
        
        st.divider()
        st.write("### About")
        st.caption("""
        Hospital Drug & Medical Supply Analytics Dashboard
        Version: 1.0
        """)

    # Main content
    st.title(f"{PAGE_ICON} {HOSPITAL_NAME}")
    st.write("---")
    
    # Welcome message
    st.write("""
    ## Welcome to the Analytics Dashboard
    
    This dashboard provides comprehensive analytics and reporting for hospital inventory management,
    including:
    
    - **Inventory Dashboard** - Real-time stock levels and locations
    - **Procurement** - Purchase orders and goods receipt tracking
    - **Budget Analysis** - Budget consumption and burn rate
    - **Quality Control** - QC test results and trending
    - **Analytics** - Advanced analytics and trends
    - **Reports** - Detailed reports and exports
    
    ### Quick Stats
    """)
    
    try:
        # Get dashboard summary
        db = get_db()
        
        from utils.queries import QUERY_DASHBOARD_SUMMARY
        from utils.formatting import format_number
        
        result = db.execute_query(QUERY_DASHBOARD_SUMMARY)
        if result:
            summary = result[0]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="📦 Total Items",
                    value=format_number(summary['total_items']),
                    delta=None
                )
            
            with col2:
                st.metric(
                    label="🏢 Warehouses",
                    value=format_number(summary['total_warehouses']),
                    delta=None
                )
            
            with col3:
                st.metric(
                    label="🤝 Vendors",
                    value=format_number(summary['total_vendors']),
                    delta=None
                )
            
            with col4:
                st.metric(
                    label="📊 Total Stock Qty",
                    value=format_number(summary['total_stock_qty']),
                    delta=None
                )
    
    except Exception as e:
        st.error(f"Error loading dashboard summary: {str(e)}")
    
    st.divider()
    
    st.write("""
    ### Getting Started
    
    Navigate using the menu on the left to explore different dashboards and reports.
    Each section provides detailed analytics, visualizations, and actionable insights.
    
    Use the filters and date pickers to customize your view and generate specific reports.
    """)

if __name__ == "__main__":
    main()
