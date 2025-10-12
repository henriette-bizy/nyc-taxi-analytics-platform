import pandas as pd
import numpy as np
from datetime import datetime
import os
import json

class NYCTaxiDataCleaner:
    """
    Comprehensive data cleaning pipeline for NYC Taxi Trip Dataset
    """
    
    def __init__(self, input_path, output_dir='data'):
        self.input_path = input_path
        self.output_dir = output_dir
        self.df = None
        self.cleaning_log = {
            'total_records': 0,
            'removed_records': {},
            'suspicious_records': [],
            'statistics': {}
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f'{output_dir}/logs', exist_ok=True)
        
    def load_data(self):
        """Load the raw CSV data"""
        print("Loading data...")
        self.df = pd.read_csv(self.input_path)
        self.cleaning_log['total_records'] = len(self.df)
        print(f"Loaded {len(self.df)} records")
        print(f"Columns: {list(self.df.columns)}")
        return self
    
    def handle_missing_values(self):
        """Identify and handle missing values"""
        print("\n=== Handling Missing Values ===")
        missing_counts = self.df.isnull().sum()
        print("Missing values per column:")
        print(missing_counts[missing_counts > 0])
        
        # Log missing values
        self.cleaning_log['removed_records']['missing_values'] = int(missing_counts.sum())
        
        # Remove rows with any missing values
        initial_count = len(self.df)
        self.df = self.df.dropna()
        removed = initial_count - len(self.df)
        print(f"Removed {removed} records with missing values")
        
        return self
    
    def handle_duplicates(self):
        """Remove duplicate records"""
        print("\n=== Handling Duplicates ===")
        initial_count = len(self.df)
        
        # Check for duplicate IDs
        duplicate_ids = self.df['id'].duplicated().sum()
        print(f"Found {duplicate_ids} duplicate IDs")
        
        # Remove duplicates based on ID
        self.df = self.df.drop_duplicates(subset=['id'], keep='first')
        
        removed = initial_count - len(self.df)
        self.cleaning_log['removed_records']['duplicates'] = removed
        print(f"Removed {removed} duplicate records")
        
        return self
    
    def clean_timestamps(self):
        """Parse and validate timestamps"""
        print("\n=== Cleaning Timestamps ===")
        
        # Convert to datetime
        self.df['pickup_datetime'] = pd.to_datetime(self.df['pickup_datetime'])
        self.df['dropoff_datetime'] = pd.to_datetime(self.df['dropoff_datetime'])
        
        # Remove records where dropoff is before pickup
        invalid_time = self.df['dropoff_datetime'] <= self.df['pickup_datetime']
        invalid_count = invalid_time.sum()
        
        if invalid_count > 0:
            print(f"Found {invalid_count} records with invalid time sequence")
            self.cleaning_log['suspicious_records'].extend(
                self.df[invalid_time]['id'].tolist()[:100]  # Log first 100
            )
            self.df = self.df[~invalid_time]
        
        # Extract time features
        self.df['pickup_hour'] = self.df['pickup_datetime'].dt.hour
        self.df['pickup_day'] = self.df['pickup_datetime'].dt.day
        self.df['pickup_month'] = self.df['pickup_datetime'].dt.month
        self.df['pickup_weekday'] = self.df['pickup_datetime'].dt.dayofweek
        self.df['pickup_year'] = self.df['pickup_datetime'].dt.year
        
        print(f"Timestamp range: {self.df['pickup_datetime'].min()} to {self.df['pickup_datetime'].max()}")
        
        return self
    
    def clean_coordinates(self):
        """Validate and clean geographic coordinates"""
        print("\n=== Cleaning Coordinates ===")
        
        # NYC bounding box (approximate)
        # Latitude: 40.5 to 41.0
        # Longitude: -74.3 to -73.7
        valid_lat_min, valid_lat_max = 40.5, 41.0
        valid_lon_min, valid_lon_max = -74.3, -73.7
        
        initial_count = len(self.df)
        
        # Filter invalid coordinates
        valid_pickup = (
            (self.df['pickup_latitude'] >= valid_lat_min) &
            (self.df['pickup_latitude'] <= valid_lat_max) &
            (self.df['pickup_longitude'] >= valid_lon_min) &
            (self.df['pickup_longitude'] <= valid_lon_max)
        )
        
        valid_dropoff = (
            (self.df['dropoff_latitude'] >= valid_lat_min) &
            (self.df['dropoff_latitude'] <= valid_lat_max) &
            (self.df['dropoff_longitude'] >= valid_lon_min) &
            (self.df['dropoff_longitude'] <= valid_lon_max)
        )
        
        invalid_coords = ~(valid_pickup & valid_dropoff)
        invalid_count = invalid_coords.sum()
        
        if invalid_count > 0:
            print(f"Found {invalid_count} records with coordinates outside NYC")
            self.df = self.df[~invalid_coords]
        
        # Remove records with zero coordinates
        zero_coords = (
            (self.df['pickup_latitude'] == 0) |
            (self.df['pickup_longitude'] == 0) |
            (self.df['dropoff_latitude'] == 0) |
            (self.df['dropoff_longitude'] == 0)
        )
        zero_count = zero_coords.sum()
        
        if zero_count > 0:
            print(f"Found {zero_count} records with zero coordinates")
            self.df = self.df[~zero_coords]
        
        removed = initial_count - len(self.df)
        self.cleaning_log['removed_records']['invalid_coordinates'] = removed
        print(f"Removed {removed} records with invalid coordinates")
        
        return self
    
    def clean_trip_duration(self):
        """Clean and validate trip duration"""
        print("\n=== Cleaning Trip Duration ===")
        
        initial_count = len(self.df)
        
        # Remove trips with duration <= 0 or extremely long (> 24 hours)
        max_duration = 24 * 3600  # 24 hours in seconds
        min_duration = 60  # 1 minute
        
        invalid_duration = (
            (self.df['trip_duration'] <= min_duration) |
            (self.df['trip_duration'] > max_duration)
        )
        
        invalid_count = invalid_duration.sum()
        print(f"Found {invalid_count} records with invalid duration (< 1 min or > 24 hours)")
        
        self.df = self.df[~invalid_duration]
        
        # Statistical outlier removal using IQR method
        Q1 = self.df['trip_duration'].quantile(0.25)
        Q3 = self.df['trip_duration'].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 3 * IQR
        upper_bound = Q3 + 3 * IQR
        
        outliers = (
            (self.df['trip_duration'] < lower_bound) |
            (self.df['trip_duration'] > upper_bound)
        )
        
        outlier_count = outliers.sum()
        print(f"Found {outlier_count} statistical outliers in trip duration")
        self.df = self.df[~outliers]
        
        removed = initial_count - len(self.df)
        self.cleaning_log['removed_records']['invalid_duration'] = removed
        print(f"Removed {removed} records with invalid duration")
        
        return self
    
    def clean_passenger_count(self):
        """Validate passenger count"""
        print("\n=== Cleaning Passenger Count ===")
        
        initial_count = len(self.df)
        
        # NYC taxis typically accommodate 1-6 passengers
        invalid_passengers = (
            (self.df['passenger_count'] < 1) |
            (self.df['passenger_count'] > 6)
        )
        
        invalid_count = invalid_passengers.sum()
        print(f"Found {invalid_count} records with invalid passenger count")
        
        self.df = self.df[~invalid_passengers]
        
        removed = initial_count - len(self.df)
        self.cleaning_log['removed_records']['invalid_passengers'] = removed
        print(f"Removed {removed} records with invalid passenger count")
        
        return self
    
    def calculate_derived_features(self):
        """Calculate derived features from the cleaned data"""
        print("\n=== Calculating Derived Features ===")
        
        # 1. Trip Speed (km/h)
        # Calculate distance using Haversine formula
        self.df['trip_distance_km'] = self._haversine_distance(
            self.df['pickup_latitude'], self.df['pickup_longitude'],
            self.df['dropoff_latitude'], self.df['dropoff_longitude']
        )
        
        # Speed = distance / time (in hours)
        self.df['trip_speed_kmh'] = (
            self.df['trip_distance_km'] / 
            (self.df['trip_duration'] / 3600)
        )
        
        # Remove unrealistic speeds (> 120 km/h or < 1 km/h for completed trips)
        valid_speed = (
            (self.df['trip_speed_kmh'] >= 1) &
            (self.df['trip_speed_kmh'] <= 120)
        )
        removed_speed = (~valid_speed).sum()
        print(f"Removed {removed_speed} records with unrealistic speed")
        self.df = self.df[valid_speed]
        
        # 2. Trip Efficiency Score (distance per minute)
        self.df['trip_efficiency'] = (
            self.df['trip_distance_km'] / 
            (self.df['trip_duration'] / 60)
        )
        
        # 3. Time of Day Category
        def categorize_time(hour):
            if 6 <= hour < 12:
                return 'morning'
            elif 12 <= hour < 18:
                return 'afternoon'
            elif 18 <= hour < 22:
                return 'evening'
            else:
                return 'night'
        
        self.df['time_of_day'] = self.df['pickup_hour'].apply(categorize_time)
        
        # 4. Is Weekend
        self.df['is_weekend'] = self.df['pickup_weekday'].isin([5, 6]).astype(int)
        
        print(f"Added derived features: trip_distance_km, trip_speed_kmh, trip_efficiency, time_of_day, is_weekend")
        
        return self
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        Returns distance in kilometers
        """
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def generate_statistics(self):
        """Generate cleaning statistics"""
        print("\n=== Generating Statistics ===")
        
        self.cleaning_log['statistics'] = {
            'final_record_count': len(self.df),
            'records_removed': self.cleaning_log['total_records'] - len(self.df),
            'removal_percentage': round(
                ((self.cleaning_log['total_records'] - len(self.df)) / 
                 self.cleaning_log['total_records']) * 100, 2
            ),
            'trip_duration': {
                'mean': float(self.df['trip_duration'].mean()),
                'median': float(self.df['trip_duration'].median()),
                'std': float(self.df['trip_duration'].std())
            },
            'trip_distance': {
                'mean': float(self.df['trip_distance_km'].mean()),
                'median': float(self.df['trip_distance_km'].median()),
                'std': float(self.df['trip_distance_km'].std())
            },
            'trip_speed': {
                'mean': float(self.df['trip_speed_kmh'].mean()),
                'median': float(self.df['trip_speed_kmh'].median()),
                'std': float(self.df['trip_speed_kmh'].std())
            }
        }
        
        print(f"Final dataset: {len(self.df)} records")
        print(f"Removed: {self.cleaning_log['statistics']['records_removed']} records ({self.cleaning_log['statistics']['removal_percentage']}%)")
        
        return self
    
    def save_cleaned_data(self):
        """Save cleaned data and logs"""
        print("\n=== Saving Cleaned Data ===")
        
        # Save cleaned CSV
        output_path = f"{self.output_dir}/cleaned_train.csv"
        self.df.to_csv(output_path, index=False)
        print(f"Saved cleaned data to: {output_path}")
        
        # Save cleaning log
        log_path = f"{self.output_dir}/logs/cleaning_log.json"
        with open(log_path, 'w') as f:
            json.dump(self.cleaning_log, f, indent=2)
        print(f"Saved cleaning log to: {log_path}")
        
        # Save summary report
        report_path = f"{self.output_dir}/logs/cleaning_report.txt"
        with open(report_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("NYC TAXI DATA CLEANING REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Input file: {self.input_path}\n")
            f.write(f"Processing date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("CLEANING SUMMARY\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total records processed: {self.cleaning_log['total_records']}\n")
            f.write(f"Final records: {self.cleaning_log['statistics']['final_record_count']}\n")
            f.write(f"Records removed: {self.cleaning_log['statistics']['records_removed']}\n")
            f.write(f"Removal percentage: {self.cleaning_log['statistics']['removal_percentage']}%\n\n")
            
            f.write("RECORDS REMOVED BY CATEGORY\n")
            f.write("-" * 60 + "\n")
            for category, count in self.cleaning_log['removed_records'].items():
                f.write(f"{category}: {count}\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        print(f"Saved summary report to: {report_path}")
        
        return self
    
    def run_pipeline(self):
        """Execute the complete cleaning pipeline"""
        print("\n" + "=" * 60)
        print("NYC TAXI DATA CLEANING PIPELINE")
        print("=" * 60)
        
        (self
         .load_data()
         .handle_missing_values()
         .handle_duplicates()
         .clean_timestamps()
         .clean_coordinates()
         .clean_trip_duration()
         .clean_passenger_count()
         .calculate_derived_features()
         .generate_statistics()
         .save_cleaned_data())
        
        print("\n" + "=" * 60)
        print("CLEANING PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        return self.df


# Main execution
if __name__ == "__main__":
    # Initialize cleaner
    cleaner = NYCTaxiDataCleaner(
        input_path='train.csv',
        output_dir='data'
    )
    
    # Run the pipeline
    cleaned_df = cleaner.run_pipeline()
    
    # Display sample of cleaned data
    print("\nSample of cleaned data:")
    print(cleaned_df.head())
    print(f"\nCleaned dataset shape: {cleaned_df.shape}")
    print(f"Columns: {list(cleaned_df.columns)}")