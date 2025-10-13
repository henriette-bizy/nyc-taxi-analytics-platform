import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import sys
from tqdm import tqdm
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_load.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Handles loading cleaned taxi data into PostgreSQL database"""
    
    def __init__(self, host, database, user, password, port=5432):
        """Initialize database connection parameters"""
        self.conn_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port
        }
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.cursor = self.conn.cursor()
            logger.info("Successfully connected to PostgreSQL database")
            return True
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def load_csv(self, csv_path):
        """Load cleaned CSV file into pandas DataFrame"""
        try:
            logger.info(f"Loading CSV file: {csv_path}")
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} records from CSV")
            logger.info(f"Columns: {list(df.columns)}")
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return None
    
    def populate_time_dimensions(self, df):
        """Populate time_dimensions table with unique datetime entries"""
        logger.info("Populating time_dimensions table...")
        
        try:
            # Convert pickup_datetime to datetime if it's not already
            df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'])
            
            # Get unique datetime entries with all temporal features
            time_data = df[['pickup_datetime', 'pickup_hour', 'pickup_day', 
                          'pickup_month', 'pickup_weekday', 'pickup_year', 
                          'time_of_day', 'is_weekend']].drop_duplicates()
            
            # Convert to list of tuples for batch insert
            time_records = [
                (
                    row['pickup_datetime'],
                    int(row['pickup_hour']),
                    int(row['pickup_day']),
                    int(row['pickup_month']),
                    int(row['pickup_weekday']),
                    int(row['pickup_year']),
                    row['time_of_day'],
                    bool(int(row['is_weekend']))
                )
                for _, row in time_data.iterrows()
            ]
            
            # Batch insert
            insert_query = """
                INSERT INTO time_dimensions 
                (pickup_datetime, pickup_hour, pickup_day, pickup_month, 
                 pickup_weekday, pickup_year, time_of_day, is_weekend)
                VALUES %s
                ON CONFLICT (pickup_datetime) DO NOTHING
            """
            
            execute_values(self.cursor, insert_query, time_records, page_size=1000)
            self.conn.commit()
            
            logger.info(f"Inserted {len(time_records)} unique time dimension records")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to populate time_dimensions: {e}")
            return False
    
    def populate_locations(self, df):
        """Populate locations table with unique pickup and dropoff locations"""
        logger.info("Populating locations table...")
        
        try:
            # Get unique pickup locations
            pickup_locs = df[['pickup_latitude', 'pickup_longitude']].drop_duplicates()
            pickup_locs.columns = ['latitude', 'longitude']
            pickup_locs['location_type'] = 'pickup'
            
            # Get unique dropoff locations
            dropoff_locs = df[['dropoff_latitude', 'dropoff_longitude']].drop_duplicates()
            dropoff_locs.columns = ['latitude', 'longitude']
            dropoff_locs['location_type'] = 'dropoff'
            
            # Combine and remove duplicates
            all_locations = pd.concat([pickup_locs, dropoff_locs])
            all_locations = all_locations.drop_duplicates(subset=['latitude', 'longitude'])
            
            # Mark locations that appear in both pickup and dropoff
            pickup_set = set(map(tuple, pickup_locs[['latitude', 'longitude']].values))
            dropoff_set = set(map(tuple, dropoff_locs[['latitude', 'longitude']].values))
            both_set = pickup_set & dropoff_set
            
            all_locations['location_type'] = all_locations.apply(
                lambda row: 'both' if (row['latitude'], row['longitude']) in both_set 
                else row['location_type'], axis=1
            )
            
            # Convert to list of tuples
            location_records = [
                (float(row['latitude']), float(row['longitude']), row['location_type'])
                for _, row in all_locations.iterrows()
            ]
            
            # Batch insert
            insert_query = """
                INSERT INTO locations (latitude, longitude, location_type)
                VALUES %s
                ON CONFLICT (latitude, longitude) DO NOTHING
            """
            
            execute_values(self.cursor, insert_query, location_records, page_size=1000)
            self.conn.commit()
            
            logger.info(f"Inserted {len(location_records)} unique location records")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to populate locations: {e}")
            return False
    
    def get_location_id_map(self):
        """Create a mapping of (lat, lon) -> location_id for fast lookups"""
        logger.info("Creating location ID mapping...")
        
        self.cursor.execute("SELECT location_id, latitude, longitude FROM locations")
        location_map = {
    (round(float(row[1]), 6), round(float(row[2]), 6)): row[0] 
    for row in self.cursor.fetchall()
}        
        logger.info(f"Created location map with {len(location_map)} entries")
        return location_map
    
    def get_time_id_map(self):
        """Create a mapping of pickup_datetime -> time_id for fast lookups"""
        logger.info("Creating time ID mapping...")
        
        self.cursor.execute("SELECT time_id, pickup_datetime FROM time_dimensions")
        time_map = {row[1]: row[0] for row in self.cursor.fetchall()}
        
        logger.info(f"Created time map with {len(time_map)} entries")
        return time_map
    
    def populate_trip_facts(self, df, location_map, time_map, batch_size=1000):
        """Populate trip_facts table with main trip data"""
        logger.info("Populating trip_facts table...")
        
        try:
            df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'])
            df['dropoff_datetime'] = pd.to_datetime(df['dropoff_datetime'])
            
            total_records = len(df)
            inserted_records = 0
            rejected_records = 0
            
            # Process in batches
            for start_idx in tqdm(range(0, total_records, batch_size), desc="Loading trips"):
                end_idx = min(start_idx + batch_size, total_records)
                batch_df = df.iloc[start_idx:end_idx]
                
                trip_records = []
                
                for _, row in batch_df.iterrows():
                    try:
                        # Get location IDs
                        pickup_loc_id = location_map.get(
                            (round(float(row['pickup_latitude']), 6), round(float(row['pickup_longitude']), 6))
                        )
                        dropoff_loc_id = location_map.get(
                            (round(float(row['dropoff_latitude']), 6), round(float(row['dropoff_longitude']), 6))
                        )
                        
                        # Get time ID
                        time_id = time_map.get(pd.Timestamp(row['pickup_datetime']))
                        
                        if pickup_loc_id and dropoff_loc_id and time_id:
                            trip_records.append((
                                str(row['id']),
                                int(row['vendor_id']),
                                pickup_loc_id,
                                dropoff_loc_id,
                                time_id,
                                row['pickup_datetime'],
                                row['dropoff_datetime'],
                                int(row['trip_duration']),
                                float(row['trip_distance_km']),
                                float(row['trip_speed_kmh']),
                                float(row['trip_efficiency']),
                                int(row['passenger_count']),
                                str(row['store_and_fwd_flag']).upper()
                            ))
                        else:
                            rejected_records += 1
                            
                    except Exception as e:
                        rejected_records += 1
                        logger.warning(f"Skipped record {row.get('id', 'unknown')}: {e}")
                
                # Batch insert
                if trip_records:
                    insert_query = """
                        INSERT INTO trip_facts 
                        (trip_id, vendor_id, pickup_location_id, dropoff_location_id, time_id,
                         pickup_datetime, dropoff_datetime, trip_duration, trip_distance_km,
                         trip_speed_kmh, trip_efficiency, passenger_count, store_and_fwd_flag)
                        VALUES %s
                        ON CONFLICT (trip_id) DO NOTHING
                    """
                    
                    execute_values(self.cursor, insert_query, trip_records, page_size=1000)
                    self.conn.commit()
                    inserted_records += len(trip_records)
            
            logger.info(f"Successfully inserted {inserted_records} trip records")
            logger.info(f"Rejected {rejected_records} records due to missing references")
            
            # Log to data_quality_log table
            self.cursor.execute("""
                INSERT INTO data_quality_log 
                (total_records_processed, records_inserted, records_rejected, 
                 rejection_reason, load_status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                total_records,
                inserted_records,
                rejected_records,
                'Missing location or time references',
                'SUCCESS' if rejected_records == 0 else 'PARTIAL'
            ))
            self.conn.commit()
            
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to populate trip_facts: {e}")
            return False
    
    def verify_data_integrity(self):
        """Verify data was loaded correctly"""
        logger.info("\n=== Data Integrity Check ===")
        
        queries = {
            'Total Trips': 'SELECT COUNT(*) FROM trip_facts',
            'Total Locations': 'SELECT COUNT(*) FROM locations',
            'Total Time Dimensions': 'SELECT COUNT(*) FROM time_dimensions',
            'Average Trip Distance (km)': 'SELECT ROUND(AVG(trip_distance_km)::NUMERIC, 2) FROM trip_facts',
            'Average Trip Duration (sec)': 'SELECT ROUND(AVG(trip_duration)::NUMERIC, 2) FROM trip_facts',
            'Average Speed (km/h)': 'SELECT ROUND(AVG(trip_speed_kmh)::NUMERIC, 2) FROM trip_facts',
            'Date Range': 'SELECT MIN(pickup_datetime), MAX(pickup_datetime) FROM trip_facts'
        }
        
        for description, query in queries.items():
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            logger.info(f"{description}: {result[0] if len(result) == 1 else result}")
        
        logger.info("=== Data Integrity Check Complete ===\n")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Load cleaned NYC taxi data into PostgreSQL')
    parser.add_argument('--csv', required=True, help='Path to cleaned CSV file')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--db', default='nyc_taxi_analytics', help='Database name')
    parser.add_argument('--user', default='postgres', help='Database user')
    parser.add_argument('--password', default='postgres', help='Database password')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for inserts')
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("NYC Taxi Analytics Platform - Database Loader")
    logger.info("=" * 70)
    
    # Initialize database loader
    loader = DatabaseLoader(args.host, args.db, args.user, args.password, args.port)
    
    # Connect to database
    if not loader.connect():
        logger.error("Failed to connect to database. Exiting.")
        sys.exit(1)
    
    # Load CSV data
    df = loader.load_csv(args.csv)
    if df is None:
        logger.error("Failed to load CSV file. Exiting.")
        loader.close()
        sys.exit(1)
    
    # Populate tables in correct order (dimensions first, then facts)
    success = True
    
    # 1. Time dimensions
    if not loader.populate_time_dimensions(df):
        success = False
    
    # 2. Locations
    if not loader.populate_locations(df):
        success = False
    
    # 3. Create lookup maps
    location_map = loader.get_location_id_map()
    time_map = loader.get_time_id_map()
    
    # 4. Trip facts
    if not loader.populate_trip_facts(df, location_map, time_map, args.batch_size):
        success = False
    
    # Verify data integrity
    loader.verify_data_integrity()
    
    # Close connection
    loader.close()
    
    if success:
        logger.info("\n✓ Data loading completed successfully!")
    else:
        logger.error("\n✗ Data loading completed with errors. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()