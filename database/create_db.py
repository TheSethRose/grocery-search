import sqlite3
import pandas as pd

# Function to create a connection to the SQLite database
def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints
        print(f"Connected to SQLite database: {db_file}")
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

# Function to clean numeric columns only if they exist
def clean_numeric_columns(df, columns):
    """Converts columns with numeric values, handles errors by setting invalid values to None"""
    for column in columns:
        if column in df.columns:  # Only clean columns that exist in the DataFrame
            df[column] = pd.to_numeric(df[column], errors='coerce')  # Set invalid parsing to NaN
    return df

# Function to create tables with proper schema in SQLite
def create_tables(conn):
    """Create tables with the correct schema and relationships in SQLite"""
    try:
        cursor = conn.cursor()

        # Create the branded_food table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS branded_food (
            fdc_id INTEGER PRIMARY KEY,
            brand_owner TEXT,
            brand_name TEXT,
            subbrand_name TEXT,
            gtin_upc TEXT UNIQUE,
            ingredients TEXT,
            serving_size REAL,
            serving_size_unit TEXT,
            household_serving_fulltext TEXT,
            branded_food_category TEXT,
            data_source TEXT,
            package_weight REAL,
            modified_date TEXT,
            available_date TEXT,
            market_country TEXT,
            discontinued_date TEXT
        );
        ''')

        # Create the food table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS food (
            fdc_id INTEGER PRIMARY KEY,
            data_type TEXT,
            description TEXT,
            food_category_id INTEGER,
            publication_date TEXT,
            market_country TEXT
        );
        ''')

        # Create the food_nutrient table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_nutrient (
            id INTEGER PRIMARY KEY,
            fdc_id INTEGER,
            nutrient_id INTEGER,
            amount REAL,
            FOREIGN KEY(fdc_id) REFERENCES food(fdc_id),
            FOREIGN KEY(nutrient_id) REFERENCES nutrient(id)
        );
        ''')

        # Create the nutrient table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS nutrient (
            id INTEGER PRIMARY KEY,
            name TEXT,
            unit_name TEXT,
            nutrient_nbr INTEGER UNIQUE
        );
        ''')

        # Create the food_attribute table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_attribute (
            id INTEGER PRIMARY KEY,
            fdc_id INTEGER,
            seq_num INTEGER,
            food_attribute_type_id INTEGER,
            name TEXT,
            value TEXT,
            FOREIGN KEY(fdc_id) REFERENCES food(fdc_id)
        );
        ''')

        # Create the measure_unit table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS measure_unit (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        ''')

        # Add indexes to optimize query performance
        cursor.execute('CREATE INDEX idx_food_fdc_id ON food(fdc_id);')
        cursor.execute('CREATE INDEX idx_branded_food_fdc_id ON branded_food(fdc_id);')
        cursor.execute('CREATE INDEX idx_food_nutrient_fdc_id ON food_nutrient(fdc_id);')
        cursor.execute('CREATE INDEX idx_food_nutrient_nutrient_id ON food_nutrient(nutrient_id);')
        cursor.execute('CREATE INDEX idx_nutrient_id ON nutrient(id);')
        cursor.execute('CREATE INDEX idx_food_attribute_fdc_id ON food_attribute(fdc_id);')

        conn.commit()
        print("Tables and indexes created successfully.")

    except Exception as e:
        print(f"Error creating tables: {e}")

# Function to load CSV into SQLite database with additional data checks
def load_csv_to_db(conn, csv_file, table_name):
    """Load a CSV file into a table in the SQLite database"""
    try:
        # Specify dtype where columns have mixed types or large datasets
        dtype_map = {
            'fdc_id': 'Int64',
            'gtin_upc': 'str',
            'discontinued_date': 'str',
            'serving_size': 'str',  # Change to str to handle mixed numeric and text data
            'package_weight': 'str',  # Change to str to handle mixed numeric and text data
            'branded_food_category': 'str',
            'data_source': 'str',
            'amount': 'float'
        }

        # Load the CSV with low_memory=False and dtype where applicable
        df = pd.read_csv(csv_file, dtype=dtype_map, low_memory=False)

        # Clean the numeric columns (convert them to float and set invalid ones to NaN)
        if table_name == 'branded_food':
            df = clean_numeric_columns(df, ['serving_size', 'package_weight'])

        # Convert data types or handle NaN/None conversions if necessary
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Loaded {csv_file} into {table_name} table")
    except Exception as e:
        print(f"Error loading {csv_file}: {e}")

# Function to close the connection
def close_connection(conn):
    """Close the database connection"""
    if conn:
        conn.close()
        print("SQLite connection is closed")
