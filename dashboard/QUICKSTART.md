# 🚀 Quick Start Guide

## Hospital Inventory Analytics Dashboard - Get Started in 5 Minutes

---

## ⚡ Quick Installation

### Windows Users

1. **Open Command Prompt** in the `dashboard` folder
2. **Double-click** `run.bat`
3. **Follow prompts** to configure database

That's it! Dashboard opens automatically at `http://localhost:8501`

### Mac/Linux Users

1. **Open Terminal** in the `dashboard` folder
2. **Run:** `bash run.sh`
3. **Follow prompts** to configure database

Dashboard opens automatically at `http://localhost:8501`

### Manual Setup

```bash
cd dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your database details

# Run
streamlit run app.py
```

---

## 🗄️ Database Configuration

Edit the `.env` file with your PostgreSQL database credentials:

```env
# PostgreSQL Analytics Database
POSTGRES_HOST=localhost          # Your database server
POSTGRES_PORT=5432             # PostgreSQL port
POSTGRES_DB=analytics          # Database name (from ETL)
POSTGRES_USER=postgres         # Database user
POSTGRES_PASSWORD=your_pass    # Database password

# Hospital/Organization
HOSPITAL_NAME=Your Hospital Name
```

**Where to get these values:**
- From your ETL pipeline setup
- PostgreSQL admin or DBA
- Check with your DevOps team

---

## 📊 Dashboard Features

### Main Pages

| Page | what you see | Use for |
|------|-----|---------|
| **📊 Dashboard** | Overview KPIs & trends | Daily monitoring |
| **📦 Inventory** | Stock levels, expiry, dead stock | Inventory management |
| **🛒 Procurement** | Orders, receipts, vendors | Purchase tracking |
| **💰 Budget** | Budget burn, spending trends | Financial analysis |
| **✅ Quality** | QC results, pass rates | Quality assurance |
| **📈 Analytics** | Consumption, top items | Advanced insights |

### Key Features

✅ **Real-time data** from PostgreSQL database  
✅ **Interactive charts** and visualizations  
✅ **Filtering & search** capabilities  
✅ **Automated caching** for performance  
✅ **Mobile responsive** design  
✅ **CSV export** ready data tables  

---

## 🎯 Common Tasks

### View Current Inventory

1. Click **📦 Inventory** in sidebar
2. Check **📊 Stock Levels** tab
3. Search by item or warehouse
4. View quantities and locations

### Check Low Stock Items

1. Go to **📦 Inventory**
2. Open **⚠️ Low Stock** tab
3. See items below reorder point
4. Identify critical items

### Monitor Expiry Dates

1. Navigate to **📦 Inventory**
2. Click **⏰ Expiry Warning** tab
3. Find items expiring soon
4. Sort by urgency

### Analyze Budget Spending

1. Open **💰 Budget**
2. View burn rate chart
3. Check category breakdown
4. Monitor remaining budget

### Check Vendor Performance

1. Go to **🛒 Procurement**
2. Open **🤝 Top Vendors** tab
3. See order counts and values
4. Compare vendor spending

---

## 🔧 Troubleshooting

### Dashboard Won't Start

**Problem:** Error when running `streamlit run app.py`

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Clear Streamlit cache
streamlit cache clear

# Try running again
streamlit run app.py
```

### Can't Connect to Database

**Problem:** "could not connect to server"

**Solution:**
1. Verify PostgreSQL is running
2. Check `.env` credentials
3. Test connection manually:
   ```bash
   psql -h <host> -U <user> -d <database>
   ```
4. Check firewall/network access

### No Data Showing

**Problem:** Tables are empty or no results

**Solution:**
1. Verify ETL pipeline has run
2. Check databases exist:
   ```bash
   psql -U postgres -l
   ```
3. Look at Dashboard > Data Freshness
4. Check ETL logs

### Performance Issues

**Problem:** Dashboard is slow

**Solution:**
1. Reduce date range in filters
2. Clear Streamlit cache:
   ```bash
   streamlit cache clear
   ```
3. Restart the application
4. Check database performance

### Port Already in Use

**Problem:** "Error: Address already in use"

**Solution:**
```bash
# Run on different port
streamlit run app.py --server.port 8502
```

---

## 📈 Understanding the Dashboards

### Dashboard Overview
- **Total Items**: Count of unique products
- **Warehouses**: Count of storage locations
- **Vendors**: Count of suppliers
- **Total Stock Qty**: Total inventory quantity
- **Movement Trends**: Last 30 days activity
- **Data Freshness**: How recent is the data

### Inventory Dashboard
- **Stock Levels**: Current quantity by item/warehouse
- **Low Stock**: Items below reorder point (⚠️ Alert!)
- **Expiry Warning**: Items expiring soon (🔴 Critical!)
- **Dead Stock**: Items not moved in 90+ days
- **Expiry Summary**: Distribution by expiry range

### Procurement Dashboard
- **Open POs**: Active purchase orders
- **Pending Receipts**: Outstanding goods receipts
- **Top Vendors**: Best performing vendors
- **Order Metrics**: Value and quantity trends

### Budget Dashboard
- **Burn Rate**: % of budget spent
- **Remaining Budget**: Available funds
- **Monthly Trends**: Budget consumption pattern
- **Category Breakdown**: Spending by category

### Quality Dashboard
- **Pass Rate**: % tests passed
- **Test Results**: Individual QC records
- **Status Distribution**: Passed vs Failed vs Pending
- **Warehouse Stats**: QC by location

### Analytics Dashboard
- **Consumption Analysis**: What's being used most
- **Monthly Trends**: Spending patterns over time
- **Top Items**: Most consumed products
- **Top Vendors**: Best suppliers by value

---

## 📚 Documentation

- **README.md** - Complete guide and features
- **DEPLOYMENT_GUIDE.md** - Production deployment
- **.env.example** - Configuration template
- **requirements.txt** - Python dependencies

---

## 🆘 Getting Help

### Check These First
1. ✅ Database is configured correctly in `.env`
2. ✅ PostgreSQL is running and accessible
3. ✅ ETL pipeline has completed
4. ✅ All dependencies installed: `pip install -r requirements.txt`

### Common Solutions
- **Restart**: Stop and restart the application
- **Refresh**: Press F5 or Ctrl+R in browser
- **Cache Clear**: `streamlit cache clear`
- **Log Check**: Look for error messages in terminal

### Contact Support
- Check database connection
- Review ETL pipeline status
- Verify data in PostgreSQL directly
- Check application logs

---

## 🎓 Learning Resources

### Understand Your Data

Visit **📊 Dashboard > Data Freshness** to see:
- When each data source was last updated
- Hours since last refresh
- Data availability status

### Explore Data

Use filters on any dashboard:
- 🔍 Item/Code search
- 📍 Warehouse/Location filter
- 📅 Date range selection
- 📊 Status filtering

### Export Data

Click the ⬇️ icon on any data table to download as CSV for Excel analysis.

---

## 💡 Tips & Tricks

- **Bookmark important views** for quick access
- **Use filters** to focus on specific items/areas
- **Check Dashboard daily** for alerts (low stock, expiry)
- **Export data** for reporting to management
- **Compare periods** using date filters
- **Monitor trends** to forecast needs

---

## 🚀 Next Steps

1. ✅ **Start the dashboard** using `run.bat` or `run.sh`
2. ✅ **Explore each page** to understand your data
3. ✅ **Set up alerts** for low stock items
4. ✅ **Schedule regular checks** (daily inventory review)
5. ✅ **Share with team** via URL: `http://<your-server>:8501`

---

## 📞 Quick Reference

| Task | Location | Steps |
|------|----------|-------|
| **Check stock** | Inventory > Stock Levels | Search item > View warehouse |
| **See low stock** | Inventory > Low Stock | Review alert items |
| **Check expiry** | Inventory > Expiry Warning | Sort by days remaining |
| **View orders** | Procurement > Purchase Orders | See open POs |
| **Check budget** | Budget | Review burn rate % |
| **QC results** | Quality Control | Filter by status |
| **Top items** | Analytics > Consumption | Sort by quantity |

---

## 🎉 You're Ready!

Your Hospital Inventory Analytics Dashboard is ready to use!

**Start now:**
- Windows: Double-click `run.bat`
- Mac/Linux: Run `bash run.sh`

**Then:**
1. Open browser to `http://localhost:8501`
2. Explore each dashboard page
3. Use filters to find what you need
4. Export data as needed
5. Share with team members

---

**Happy analyzing! 📊✨**

For more details, see **README.md** or **DEPLOYMENT_GUIDE.md**
