# NYC Taxi Analytics Platform


## Overview
This module handles the cleaning and preprocessing of the NYC Taxi Trip Duration dataset. It implements a comprehensive pipeline that handles missing values, duplicates, outliers, and invalid records while generating meaningful derived features.

## Project Structure
```
/data
  /logs
    - cleaning_log.json          # Detailed cleaning log
    - cleaning_report.txt        # Human-readable summary
  - cleaned_train.csv            # Cleaned dataset output
/data_cleaning.py                # Main cleaning script
```

## Prerequisites
- Python 3.8+
- pandas
- numpy

## Installation

1. Install required packages:
```bash
pip install pandas numpy
```
## Dataset Setup

1. Download the NYC Taxi Trip dataset from [Kaggle](https://www.kaggle.com/competitions/nyc-taxi-trip-duration/data?select=train.zip)
2. Extract `train.csv` 
3. Place your `train.csv` file in the project root directory

## Usage

Run the cleaning script:
```bash
python data_cleaning.py
```

The script will:
1. Load the raw `train.csv` data
2. Execute the complete cleaning pipeline
3. Save cleaned data to `data/cleaned_train.csv`
4. Generate logs in `data/logs/`

## Data Cleaning Steps

### 1. Missing Values
- Identifies all missing values across columns
- Removes records with any missing critical fields
- Logs count of removed records

### 2. Duplicate Removal
- Identifies duplicate trip IDs
- Keeps first occurrence, removes subsequent duplicates
- Logs duplicate count

### 3. Timestamp Validation
- Converts strings to datetime objects
- Removes records where dropoff time ≤ pickup time
- Extracts temporal features: hour, day, month, weekday, year

### 4. Geographic Coordinate Cleaning
- Validates coordinates within NYC boundaries (40.5-41.0°N, -74.3 to -73.7°W)
- Removes records with zero coordinates
- Removes coordinates outside valid range

### 5. Trip Duration Cleaning
- Removes trips < 1 minute or > 24 hours
- Applies IQR-based outlier detection (3× IQR threshold)
- Removes statistical outliers

### 6. Passenger Count Validation
- Validates passenger count between 1-6 (NYC taxi standard)
- Removes invalid counts

## Derived Features

The cleaning pipeline generates these derived features:

### 1. **Trip Distance (km)**
- Calculated using Haversine formula
- Measures great circle distance between pickup and dropoff coordinates
- Accounts for Earth's curvature

### 2. **Trip Speed (km/h)**
- Formula: `distance / (duration/3600)`
- Validates realistic speeds (1-120 km/h)
- Removes records with unrealistic speeds

### 3. **Trip Efficiency**
- Formula: `distance / (duration/60)`
- Measures kilometers traveled per minute
- Useful for identifying traffic patterns

### 4. **Time of Day Category**
- Morning: 6:00 AM - 11:59 AM
- Afternoon: 12:00 PM - 5:59 PM
- Evening: 6:00 PM - 9:59 PM
- Night: 10:00 PM - 5:59 AM

### 5. **Is Weekend**
- Binary flag (0/1)
- 1 = Saturday or Sunday, 0 = Weekday

## Output Files

### cleaned_train.csv
Contains all original columns plus derived features:
- Original: id, vendor_id, pickup_datetime, dropoff_datetime, passenger_count, pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude, store_and_fwd_flag, trip_duration
- Temporal: pickup_hour, pickup_day, pickup_month, pickup_weekday, pickup_year
- Derived: trip_distance_km, trip_speed_kmh, trip_efficiency, time_of_day, is_weekend

### cleaning_log.json
JSON file containing:
- Total records processed
- Records removed by category
- Suspicious record IDs (sample)
- Statistical summaries

### cleaning_report.txt
Human-readable text report with:
- Processing metadata
- Cleaning summary
- Breakdown of removed records

## Data Quality Metrics

After cleaning, the dataset maintains:
- ✓ No missing values
- ✓ No duplicates
- ✓ Valid timestamps (dropoff > pickup)
- ✓ Coordinates within NYC boundaries
- ✓ Realistic trip durations (1 min - 24 hours)
- ✓ Valid passenger counts (1-6)
- ✓ Realistic speeds (1-120 km/h)

## Justification for Cleaning Decisions

### Geographic Bounds
NYC roughly spans 40.5°N to 41.0°N latitude and -74.3°W to -73.7°W longitude. Trips outside this range are likely data errors or trips to neighboring areas (airports) that would skew analysis.

### Duration Thresholds
- Minimum 1 minute: Accounts for short trips; anything less is likely a cancellation or error
- Maximum 24 hours: Extremely long trips suggest data errors or unusual circumstances
- IQR outliers: Catches statistically unusual trips while preserving valid edge cases

### Speed Limits
- Minimum 1 km/h: Ensures the vehicle was actually moving
- Maximum 120 km/h: Accounts for highway speeds; higher speeds suggest GPS errors or data anomalies

## Transparency and Logging

All cleaning decisions are logged for transparency:
- Exact counts of removed records by category
- Sample IDs of suspicious records
- Statistical summaries before and after cleaning

This ensures reproducibility and allows for audit of cleaning decisions.

## Next Steps

After data cleaning, the cleaned dataset can be:
1. Loaded into the database (handled by database module)
2. Used for analysis and visualization
3. Served via the backend API

## Contributors

1. Henriette Biziyaremye
2. Aderline Gashugi
3. David Shumbusho
4. Darcy Teta Mbabazi


