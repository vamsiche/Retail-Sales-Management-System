# Sales Management System

A full-stack web application for managing and analyzing sales transactions with multi-select filters, built with FastAPI and NeonDB (PostgreSQL).

## Features

- **Multi-Select Filters**: Apply multiple filters simultaneously
  - Customer Region
  - Gender
  - Age Range
  - Product Category
  - Tags
  - Payment Method
  - Date Range
- **Real-time Statistics**: Total units sold, total amount, total discount
- **Dynamic Search**: Search by customer name or phone number
- **Sorting Options**: Sort by name, date, or amount
- **Responsive UI**: Clean, modern interface matching the Figma design

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: NeonDB (PostgreSQL)
- **Frontend**: HTML, Tailwind CSS, Vanilla JavaScript
- **ORM**: SQLAlchemy

## Prerequisites

- Python 3.8+
- NeonDB account (free tier)
- CSV file with sales data

## Setup Instructions

### 1. Clone or Download the Project

```bash
cd bamsi
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure NeonDB

1. Go to [NeonDB Console](https://console.neon.tech/)
2. Create a new project (free tier)
3. Copy your connection string
4. Create a `.env` file in the project root:

```bash
# Create .env file from template
cp .env.example .env
```

5. Edit `.env` and add your NeonDB connection string:

```env
DATABASE_URL=postgresql://username:password@ep-xxxx-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### 5. Load Data into Database

Place your CSV file in the project directory and run:

```bash
python init_db.py your_sales_data.csv
```

The script will:
- Create the database tables
- Process and normalize the CSV data
- Load all records into NeonDB
- Verify the data

### 6. Run the Application

```bash
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access the Application

Open your browser and navigate to:
```
http://localhost:8000
```

## CSV File Format

Your CSV file should contain the following columns (column names are flexible, the script will normalize them):

- Transaction ID
- Date
- Customer ID
- Customer Name
- Phone Number
- Gender
- Age
- Customer Region
- Product Category
- Quantity
- Total Amount (or Price)
- Payment Method
- Tags (optional, comma-separated)
- Discount (optional)

## API Endpoints

### Get Filter Options
```
GET /api/filters/options
```
Returns all available filter values for dropdowns.

### Get Transactions
```
GET /api/transactions?customer_regions=North&genders=Male&limit=100
```
Returns filtered transactions with pagination.

Query Parameters:
- `customer_regions` (array)
- `genders` (array)
- `age_ranges` (array)
- `product_categories` (array)
- `tags` (array)
- `payment_methods` (array)
- `start_date` (date)
- `end_date` (date)
- `search` (string)
- `sort_by` (string)
- `sort_order` (asc/desc)
- `limit` (int)
- `offset` (int)

### Get Statistics
```
GET /api/statistics?customer_regions=North
```
Returns aggregated statistics based on applied filters.

## Database Schema

### sales_transactions table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| transaction_id | String | Unique transaction identifier |
| date | Date | Transaction date |
| customer_id | String | Customer identifier |
| customer_name | String | Customer name |
| phone_number | String | Contact number |
| gender | String | Customer gender |
| age | Integer | Customer age |
| customer_region | String | Geographic region |
| product_category | String | Product type |
| quantity | Integer | Units sold |
| price_per_unit | Float | Unit price |
| total_amount | Float | Total transaction amount |
| discount | Float | Discount applied |
| payment_method | String | Payment type |
| tags | Array[String] | Associated tags |

## NeonDB Free Tier Limits

- **Storage**: 0.5 GB
- **Active time**: 100 hours/month
- **Compute**: Shared CPU, 256 MB RAM

The application is optimized to work within these limits. The database automatically scales down when inactive.

## Multi-Select Filter Behavior

- Multiple options can be selected within a single filter (OR logic)
- Multiple different filters can be applied together (AND logic)
- Example: Tags=[Premium, VIP] AND Category=[Electronics] returns transactions that have either Premium OR VIP tag AND are in Electronics category

## Troubleshooting

### Database Connection Error
- Verify your DATABASE_URL in `.env`
- Check NeonDB console for project status
- Ensure your IP is not blocked by firewall

### CSV Loading Issues
- Check CSV encoding (should be UTF-8)
- Verify column names match expected format
- Ensure date format is parseable (YYYY-MM-DD recommended)

### No Data Displayed
- Confirm data was loaded: Check init_db.py output
- Verify API is running: Visit http://localhost:8000/health
- Check browser console for errors

## Development

To run in development mode with auto-reload:

```bash
uvicorn app:app --reload --port 8000
```

## Production Deployment

For production deployment:

1. Set proper environment variables
2. Use production WSGI server (Gunicorn)
3. Enable HTTPS
4. Configure proper CORS settings
5. Set up monitoring and logging

## License

This project is for educational/assessment purposes.

## Support

For issues or questions, please check:
- NeonDB Documentation: https://neon.tech/docs
- FastAPI Documentation: https://fastapi.tiangolo.com
- SQLAlchemy Documentation: https://docs.sqlalchemy.org
