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

### How to run the server
```bash
# Install dependencies
run `npm install` in the project root

Create a .env file in the root directory with the following content:
DB_USER=postgres (or your db user)
DB_PASS=yourpassword
DB_HOST=localhost
DB_NAME=nyc_taxi_analytics
DB_PORT=5432
PORT=8000

cd backend
python server.py
```

## Endpoints

You can check the API documentation at `http://localhost:8000/api/documentation` once the server is running.

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
