#!/bin/bash

DB_NAME="nyc_taxi_analytics"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"

echo "=============================================="
echo "NYC Taxi Analytics - Database Setup"
echo "=============================================="
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "ERROR: PostgreSQL is not installed or not in PATH"
    exit 1
fi

echo "PostgreSQL found. Proceeding with setup..."
echo ""

# Check if database exists
DB_EXISTS=$(psql -U $DB_USER -h $DB_HOST -p $DB_PORT -lqt | cut -d \| -f 1 | grep -w $DB_NAME)

if [ -z "$DB_EXISTS" ]; then
    echo "Creating database: $DB_NAME"
    createdb -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME
    
    if [ $? -eq 0 ]; then
        echo "✓ Database created successfully"
    else
        echo "✗ Failed to create database"
        exit 1
    fi
else
    echo "Database $DB_NAME already exists"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        dropdb -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME
        createdb -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME
        echo "✓ Database recreated successfully"
    else
        echo "Keeping existing database"
    fi
fi

echo ""
echo "Running database schema..."
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -f database_schema.sql

if [ $? -eq 0 ]; then
    echo "✓ Schema created successfully"
else
    echo "✗ Failed to create schema"
    exit 1
fi

echo ""
echo "=============================================="
echo "Database setup complete!"
echo "=============================================="
echo ""
echo "Database Details:"
echo "  Name: $DB_NAME"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo ""
echo "Next Steps:"
echo "  1. Ensure your cleaned CSV file is ready (e.g., data/cleaned_train.csv)"
echo "  3. Load data: python load_data_to_db.py --csv data/cleaned_train.csv"
echo ""