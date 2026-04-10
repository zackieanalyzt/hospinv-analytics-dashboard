# Hospital Inventory Analytics Dashboard

## 📋 Overview

This is a comprehensive AI-powered dashboard for hospital drug and medical supply inventory analytics. It provides real-time monitoring, reporting, and insights into inventory management, procurement, budget analysis, and quality control.

## 🎯 Features

### Dashboards

1. **📊 Dashboard Overview**
   - Key performance indicators (KPIs)
   - Daily consumption trends
   - Movement type distribution
   - Data source freshness monitoring

2. **📦 Inventory Management**
   - Real-time stock levels across warehouses
   - Low stock alerts
   - Expiry date tracking and warnings
   - Dead stock analysis
   - Stock balance by item and location

3. **🛒 Procurement Management**
   - Open purchase orders tracking
   - Pending goods receipt monitoring
   - Top vendor analysis
   - Order value and quantity metrics

4. **💰 Budget Analysis**
   - Monthly budget burn rate
   - Budget allocation vs consumption
   - Category-wise budget breakdown
   - Year-over-year trends
   - Budget health indicators

5. **✅ Quality Control**
   - QC test results and pass rates
   - Quality metrics by test type
   - Recent test results filtering
   - Pass/fail trend analysis

6. **📈 Advanced Analytics**
   - Item consumption analysis
   - Monthly consumption trends
   - Top consumed items
   - Top vendors by order count and value
   - Unit cost calculations

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL analytics database (from ETL pipeline)
- pip or conda

### Installation

1. **Create virtual environment:**
   ```bash
   cd dashboard
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # or
   source venv/bin/activate      # On Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL connection details
   ```

4. **Run the dashboard:**
   ```bash
   streamlit run app.py
   ```

The dashboard will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
dashboard/
├── app.py                    # Main Streamlit application
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── pages/                 # Dashboard pages (multi-page app)
│   ├── 01_Dashboard.py   # Overview dashboard
│   ├── 02_Inventory.py   # Inventory reports
│   ├── 03_Procurement.py # Procurement reports
│   ├── 04_Budget.py      # Budget analysis
│   ├── 05_Quality.py     # Quality control
│   └── 06_Analytics.py   # Advanced analytics
└── utils/                # Utility modules
    ├── db.py            # Database connection manager
    ├── queries.py       # SQL queries for reports
    └── formatting.py    # Data formatting utilities
```

## 🔧 Configuration

### Environment Variables

Edit `.env` file with your settings:

```env
# Database Connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=analytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Hospital Name
HOSPITAL_NAME=Your Hospital Name
```

### config.py Settings

Key configuration options you can modify:

- `CACHE_TTL`: Data cache time-to-live (default: 300 seconds)
- `DEFAULT_DATE_RANGE_DAYS`: Default historical days to display (default: 30)
- `REPORT_CURRENCY`: Currency symbol for reports (default: ฿)
- `HOSPITAL_NAME`: Name displayed in dashboard (from env)

## 📊 Data Sources

The dashboard queries data from the PostgreSQL analytics database populated by the ETL pipeline:

### Schemas Used

- **`core.*`** - Dimension tables (dim_item, dim_vendor, dim_warehouse)
- **`stg.*`** - Staging/fact tables (inventory, purchases, receipts)
- **`mart.*`** - Aggregated/summarized fact tables

### Key Fact Tables

- `fact_stock_balance` - Current inventory levels
- `fact_inventory_movement` - Inventory transactions
- `fact_purchase_order_line` - Purchase orders
- `fact_goods_receipt_line` - Goods receipts
- `sum_consumption_daily` - Daily consumption summaries
- `sum_consumption_monthly` - Monthly consumption summaries
- `sum_budget_burn_monthly` - Budget analysis

## 📈 Key Metrics

### Inventory

- Total items in stock
- Stock levels by warehouse
- Low stock items count
- Items at risk of expiry
- Days to expiry
- Dead stock (no movement >90 days)

### Procurement

- Open purchase orders
- Pending goods receipts
- Top vendors by amount/order count
- Average order values

### Budget

- Budget allocated vs consumed
- Burn rate percentage
- Remaining budget
- Category-wise breakdown

### Quality Control

- Pass rate percentage
- Test results by type
- Pending/approved items

### Consumption

- Daily/monthly trends
- Top consumed items
- Total consumed quantity/value

## 🔍 Features Detail

### Smart Filtering

- Item name/code search
- Warehouse filtering
- Date range selection
- Status filtering
- Minimum quantity thresholds

### Visualizations

- Interactive line charts for trends
- Bar charts for comparisons
- Pie charts for distribution
- Heat maps for status indicators
- Data tables with sorting

### Data Formatting

- Currency formatting with symbols
- Number formatting with separators
- Date/time formatting
- Status color coding
- Trend indicators

### Performance

- Database connection pooling
- Result caching (5-minute TTL)
- Optimized queries
- Lazy loading of data

## 🐛 Troubleshooting

### Database Connection Error

```
Error: could not connect to server
```

**Solution:** Check your `.env` file and ensure PostgreSQL is running.

### Missing Data

If data is not showing in a report:

1. Verify the ETL pipeline has completed successfully
2. Check that the required tables exist in PostgreSQL
3. Verify data freshness using the Dashboard Overview

### Performance Issues

For slow loading:

1. Reduce `DEFAULT_DATE_RANGE_DAYS` in config.py
2. Clear Streamlit cache: `streamlit cache clear`
3. Check database query performance
4. Ensure database has proper indexes

## 📝 Queries

All SQL queries are defined in `utils/queries.py`:

- `QUERY_INVENTORY_LEVEL` - Current stock by item and warehouse
- `QUERY_LOW_STOCK_ITEMS` - Items below reorder point
- `QUERY_EXPIRY_ITEMS` - Items nearing or past expiry
- `QUERY_PURCHASE_ORDERS_OPEN` - Active purchase orders
- `QUERY_BUDGET_BURN_MONTHLY` - Monthly budget tracking
- And many more...

You can modify these queries to customize reports.

## 🎨 Customization

### Add a New Dashboard Page

1. Create file: `pages/07_MyDashboard.py`
2. Use the same structure as existing pages
3. Import utilities: `from utils.db import get_db` and `from utils.queries import QUERY_*`
4. Streamlit automatically discovers the page

### Modify Styling

Edit the CSS in `app.py` under `st.markdown()` to customize colors and layouts.

### Add New Metrics

1. Add SQL query to `utils/queries.py`
2. Query data in your page: `data = db.fetch_dataframe(QUERY_NAME)`
3. Display using Streamlit: `st.metric()`, `st.dataframe()`, etc.

## 🚢 Deployment

### Docker (Recommended)

1. Create `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY dashboard . 
   RUN pip install -r requirements.txt
   EXPOSE 8501
   CMD ["streamlit", "run", "app.py"]
   ```

2. Build and run:
   ```bash
   docker build -t hospital-dashboard .
   docker run -p 8501:8501 --env-file .env hospital-dashboard
   ```

### Streamlit Cloud

1. Push code to GitHub
2. Visit https://streamlit.io/cloud
3. Connect your repository
4. Add secrets in Settings

### Production Server

Deploy using:
- **Gunicorn** + Streamlit
- **Docker** containers
- **Nginx** reverse proxy
- **PM2** process manager

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review query results in database directly
3. Check ETL pipeline logs
4. Verify database connection

## 📄 License

See LICENSE file in project root for licensing information.

## 🔐 Security

### Best Practices

- Never commit `.env` file with credentials
- Use environment variables for sensitive data
- Run behind HTTPS in production
- Implement authentication for dashboard access
- Audit database access logs
- Keep dependencies updated

## 📦 Related Documentation

- ETL Pipeline: See `../PRD_v1.7.md` and related docs
- Database Schema: See `../SCHEMA_SUMMARY.txt`
- Database Structure: See `../invs2019_structure.sql`

## 📅 Version History

- **v1.0** - Initial release with core dashboards
  - Dashboard Overview
  - Inventory Management
  - Procurement
  - Budget Analysis
  - Quality Control
  - Advanced Analytics

---

**Last Updated:** 2026-04-10
**Status:** Production Ready ✅
