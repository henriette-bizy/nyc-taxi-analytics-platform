# NYC Taxi Analytics Platform

Full-stack analytics application for exploring NYC taxi trip data with data cleaning, database design, and visualization capabilities.

## Team Members
- **Henriette Biziyaremye** - Data Cleaning & Preprocessing
- **Aderline Gashugi** - Database Design & Implementation
- **David Shumbusho** - Backend API Development
- **Darcy Teta Mbanza** - Frontend Dashboard Development

## Tech Stack
- **Data Processing**: Python, Pandas, NumPy
- **Database**: PostgreSQL
- **Backend**: [TBD]
- **Frontend**: [TBD]

## Project Structure
```
nyc-taxi-analytics-platform/
├── data/cleaned_train.csv    # Cleaned data
├── data_cleaning.py         # Data cleaning script
├── database/               # Database module
│   ├── database_schema.sql
│   ├── load_data_to_db.py
│   └── setup_database.sh
├── backend/                # [Coming soon]
├── frontend/               # [Coming soon]
└── README.md
```

## Quick Start

### 1. Data Cleaning

**Install dependencies:**
```bash
pip install pandas numpy
```

**Download dataset:**
- Get `train.csv` from [Kaggle NYC Taxi Dataset](https://www.kaggle.com/competitions/nyc-taxi-trip-duration/data)
- Place in project root

**Run cleaning:**
```bash
python data_cleaning.py
```

**Output:** `data/cleaned_train.csv`

### 2. Database Setup

**Install PostgreSQL and Python dependencies:**
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Install Python packages
cd database
python3 -m venv venv
source venv/bin/activate
pip install psycopg2-binary pandas numpy tqdm
```

**Create database and load data:**
```bash
# Create database schema
./setup.database.sh

# Load cleaned data into the db
python load_data_to_db.py --csv ../data/cleaned_train.csv --user (your db user) --password (db password)
```

**Verify:**
```bash
psql nyc_taxi_analytics -c "SELECT COUNT(*) FROM trip_facts;"
```

### 3. Backend API

# NYC Taxi Analytics - Backend API (Minimal docs)

Base URL: `http://localhost:8000/`(or your configured port)
Auth: HTTP Basic Auth (username/password). Set credentials via env vars.

### How to run the server
```bash
Create a .env file in the root directory with the following content:
DB_HOST=localhost
DB_PORT=5432 
DB_NAME=nyc_taxi_analytics
DB_USER=postgres
DB_PASSWORD=your_password_here
API_USER=your_api_username
API_PASS=your_api_password
PORT=8000

cd backend
python server.py
```

## Endpoints

### GET /
Description: API root and endpoints list.
Response:
200 OK
{
  "success": true,
  "message": "NYC Taxi Analytics API",
  "endpoints": [...]
}

### GET /vendors
List vendors.
Params: none
Sample response:
200 OK
{
  "success": true,
  "count": 2,
  "data": [
    {"vendor_id":1, "vendor_name":"Creative Mobile Technologies", "description":"..."}
  ]
}

### GET /locations
List locations.
Query params (optional):
- `zone_name` — exact zone name filter
- `bbox` — bounding box `minlon,minlat,maxlon,maxlat`
Examples:
- `/locations?zone_name=East Village`
- `/locations?bbox=-74.02,40.70,-73.95,40.75`

### GET /time_dimensions
List time dimension records (limited).

### GET /trips
List trips with filters and pagination.
Query params:
- `start_date` (ISO e.g., 2021-01-01)
- `end_date` (ISO)
- `min_distance_km` (float)
- `max_distance_km` (float)
- `pickup_zone_id` (int)
- `dropoff_zone_id` (int)
- `sort_by` one of: pickup_datetime, trip_duration, trip_distance_km, trip_speed_kmh
- `page` (int) default 1
- `page_size` (int) default 50
Response:
{
  "success": true,
  "page": 1,
  "page_size": 50,
  "total": 12345,
  "count": 50,
  "data": [{trip objects...}]
}

### GET /trips/{trip_id}
Get trip details by `trip_id`.

### GET /analytics/hourly
Return view `hourly_trip_stats`.
Optional query params:
- `hour` (0-23)
- `is_weekend` (true/false)

### GET /analytics/daily
Return `daily_trip_stats`.
Optional:
- `start_date`, `end_date` (YYYY-MM-DD)

### GET /analytics/location_stats
Return `location_trip_stats`.

### GET /analytics/top_zones
Top pickup zones by number of pickups.
Query params:
- `limit` (default 10)
This endpoint demonstrates a custom algorithm to produce top-k results.

## Authentication
All endpoints require Basic Auth. Example:
`Authorization: Basic base64(username:password)`

## Examples (curl)

NB: 1. Replace `admin:password123` with your credentials.
    2. Adjust `localhost:8000` if using a different port.

List trips (page 1):
curl -u admin:password123 “http://localhost:8000/trips?page=1&page_size=25&start_date=2021-01-01&end_date=2021-01-31”

Get top 5 pickup zones:
curl -u admin:password123 “http://localhost:8000/analytics/top_zones?limit=5”

Get hourly stats for hour 8:
curl -u admin:password123 “http://localhost:8000/analytics/hourly?hour=8”

### 4. Frontend Dashboard
*[Coming soon]*

## Dataset Overview

**Original Records:** ~1.4M NYC taxi trips  
**Cleaned Records:** ~1.4M (after removing invalid data)  
**Date Range:** 2016  
**Features:** 21 columns including derived metrics (distance, speed, efficiency)

## Data Cleaning Pipeline

1. Remove missing values and duplicates
2. Validate timestamps (dropoff > pickup)
3. Clean coordinates (NYC boundaries: 40.5-41.0°N, -74.3 to -73.7°W)
4. Filter trip duration (1 min - 24 hours)
5. Validate passenger count (1-6)
6. Remove speed outliers (1-120 km/h)
7. Generate derived features (distance, speed, efficiency, time_of_day, is_weekend)

## Database Schema

**Star schema** with 4 tables:
- `trip_facts` - Main trip records (fact table)
- `time_dimensions` - Temporal attributes
- `locations` - Geographic coordinates
- `vendors` - Taxi service providers

**Key Features:**
- 15+ indexes for query optimization
- Foreign key constraints for data integrity
- Pre-built views for common analytics

## Video Walkthrough
*[Link to be added]*

## License
Academic project for ALU Software Engineering

---
