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
- **Backend**: Nodejs
- **Frontend**: HTML, CSS, JAVASCRIPT

## Project Structure
```
nyc-taxi-analytics-platform/
├── data/cleaned_train.csv    # Cleaned data
├── data_cleaning.py         # Data cleaning script
├── database/               # Database module
│   ├── database_schema.sql
│   ├── load_data_to_db.py
│   └── setup_database.sh
├── backend/                
├── frontend/               
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
source venv/bin/activate or venv\Scripts\activate for windows
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
# install Node.js and npm if not already installed
https://nodejs.org/en/download
# Install dependencies
run `npm install` in the project root

Create a .env file in the root directory with the following content:
DB_USER=postgres (or your db user)
DB_PASS=yourpassword
DB_HOST=localhost
DB_NAME=nyc_taxi_analytics
DB_PORT=5432
PORT=8000

run `npm run dev` to start the server (development mode, with hot reload. For production use `npm start`)
(if npm run dev is used, ensure nodemon is installed globally: npm install -g nodemon)
```

## Endpoints

You can check the API documentation at `http://localhost:8000/api/documentation` once the server is running.

### 4. Frontend Dashboard
**NYC Taxi Analytics** is an interactive dashboard that utilizes New York City taxi trip data to provide real-time insights into trip patterns, vendor performance, and city mobility trends, leveraging modern web technologies such as **Chart.js**, **Leaflet**, and **AOS animations**.

# Overview
This web app helps show and analyze NYC taxi data, focusing on:
- The number of times taxis are in demand per hour
- Peak vs Off-Peak activity
- Vendor statistics and list 
- Geospatial trip visualization on a map

Users can explore data interactively with built-in **filters**, **sorting**, and **live charts**.

## Features
**Dynamic Charts**
- Line chart showing trips per hour  
- Doughnut chart comparing peak vs off-peak trips

**Data Filters & Sorting**
- Filter trip data by time of day (Morning, Afternoon, Evening, Night)
- Sort vendors by ID or name  
- Search bar for instant vendor lookup

**Map Visualization**
- Interactive NYC map using **Leaflet.js**

**KPI Summary Cards**
- Real-time counters for peak/off-peak trips and the number of vendors

**Responsive UI**
- Optimized for all devices
- Smooth animations using **AOS (Animate On Scroll)**


##  Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | HTML5, CSS3, JavaScript (ES6) |
| **Charts** | [Chart.js](https://www.chartjs.org/) |
| **Map** | [Leaflet.js](https://leafletjs.com/) |
| **Animations** | [AOS](https://michalsnik.github.io/aos/) |
| **Icons** | Font Awesome |
| **Backend (API)** | Node.js / FastAPI |

##  Project Structure

nyc-taxi-dashboard/
│
├── assets/
│ └── 3D-car.png # 3D car illustration used in hero section
│
├── index.html # Main dashboard structure
├── style.css # Styling and layout
├── chart.js # Chart rendering, filtering, and sorting
├── map.js # Leaflet map setup
├── script.js # General animations / AOS initialization
│
└── README.md # Project documentation

## Setup Instructions

###  Clone the repository
```bash
git clone https://github.com/yourusername/nyc-taxi-dashboard.git
cd nyc-taxi-dashboard
```
as stated on the backend section
npm install
# or
pip install -r requirements.txt

Ensure this line is present in your backend:
<script>
  window.API_BASE = "http://localhost:8000";
</script>

Run the server 
uvicorn main: app --reload

Simply open index.html in your browser

API Endpoints

These are the expected endpoints your backend should provide:

Endpoint: /api/trips/analytics/hourly        	              	             
Description: Hourly trip counts
Example Response: [{"pickup_hour": 8, "trip_count": 15000}, ...]

Endpoint:/api/vendors
Description:Vendor list
Example Response:	[{"vendor_id": 1, "vendor_name": "VeriFone", "description": "Provider"}, ...]


Filters & Sorting Logic

Hour Range Filter:
Updates both charts to show data for selected ranges:

-Morning (05–11)
-Afternoon (12–17)
-Evening (18–23)
-Night (00–04)

Vendor Sorting:
Sorts table alphabetically or by numeric ID.

Live Search:
Instantly filters vendor table rows based on text input.

Map Integration

The Leaflet.js map (in map.js) initializes a zoomable, draggable map centered on NYC:

```
js

const map = L.map('map').setView([40.7128, -74.0060], 11);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

```
You can extend it to:

 -Display trip pickup/dropoff clusters
 -Add real-time markers
 -Visualize heatmaps
 
Animations

AOS is used to animate sections as users scroll:

html
<section data-aos="fade-up">...</section>

Initialize AOS in your script.js:

AOS.init({ duration: 1000, once: true });

Future Improvements

-Date range filter (start–end date pickers)
-Heatmap for pickup density
-Compare multiple vendors
-Export chart data to CSV
-Dark/light mode toggle

Author: The Team


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

[Demo Video](https://www.youtube.com/watch?v=lQ7fq9MTk5Q)


## License
Academic project for ALU Software Engineering

---
