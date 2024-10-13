import os
import create_db

# Define the SQLite database file
DATABASE_FILE = 'food_data.db'

# Define the path to the source CSV files
CSV_PATH = '/Users/sethrose/Documents/Development/python-projects/food-db/database/source_data'

# List of CSV files and their corresponding table names
csv_files = {
    os.path.join(CSV_PATH, 'branded_food.csv'): 'branded_food',
    os.path.join(CSV_PATH, 'food.csv'): 'food',
    os.path.join(CSV_PATH, 'food_attribute.csv'): 'food_attribute',
    os.path.join(CSV_PATH, 'food_nutrient.csv'): 'food_nutrient',
    os.path.join(CSV_PATH, 'nutrient.csv'): 'nutrient',
    os.path.join(CSV_PATH, 'measure_unit.csv'): 'measure_unit'
}

def delete_db_if_exists(db_file):
    """Delete the existing SQLite database if it exists"""
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Deleted existing database: {db_file}")

def main():
    # Delete the existing database
    delete_db_if_exists(DATABASE_FILE)

    # Create a connection to the SQLite database
    conn = create_db.create_connection(DATABASE_FILE)

    if conn is not None:
        # Create tables in the database
        create_db.create_tables(conn)

        # Load CSV files into the database
        for csv_file, table_name in csv_files.items():
            if os.path.exists(csv_file):
                create_db.load_csv_to_db(conn, csv_file, table_name)
            else:
                print(f"File {csv_file} does not exist.")

        # Close the connection
        create_db.close_connection(conn)
    else:
        print("Error! Cannot create the database connection.")

if __name__ == '__main__':
    main()
