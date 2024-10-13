import sqlite3
import pandas as pd
import time

# Function to connect to the SQLite database
def create_connection(db_file):
    """Create a connection to the SQLite database"""
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to SQLite database: {db_file}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to execute a query and display the result
def execute_query(conn, query):
    """Execute a query and return the result as a DataFrame"""
    try:
        start_time = time.time()
        df = pd.read_sql_query(query, conn)
        end_time = time.time()
        print(f"Query executed in {end_time - start_time:.2f} seconds")
        print(df.head())  # Print the first 5 rows of the result
    except Exception as e:
        print(f"Error executing query: {e}")

def main():
    # Connect to the database
    database_file = 'food_data.db'
    conn = create_connection(database_file)

    if conn is not None:
        print("\n--- Enhanced Example Queries ---\n")

        # 1. Join query to get nutrient information for branded foods (with LIMIT)
        query1 = """
        SELECT bf.brand_owner, bf.gtin_upc, n.name AS nutrient_name, fn.amount, n.unit_name
        FROM branded_food bf
        JOIN food_nutrient fn ON bf.fdc_id = fn.fdc_id
        JOIN nutrient n ON fn.nutrient_id = n.id
        WHERE bf.brand_owner LIKE 'CAMPBELL%'
        LIMIT 10;
        """
        print("Query 1: Nutrient information for CAMPBELL branded foods")
        execute_query(conn, query1)

        # 2. Complex filtering to find foods with specific attributes (with LIMIT)
        query2 = """
        SELECT f.description, fa.name AS attribute_name, fa.value AS attribute_value
        FROM food f
        JOIN food_attribute fa ON f.fdc_id = fa.fdc_id
        WHERE f.description LIKE '%Organic%'
        AND fa.name IN ('Organic', 'Nutrient Updated')
        LIMIT 10;
        """
        print("\nQuery 2: Organic foods with specific attributes")
        execute_query(conn, query2)

        # 3. Aggregation query to summarize nutrient data (with LIMIT)
        query3 = """
        SELECT n.name AS nutrient_name, AVG(fn.amount) AS avg_amount, n.unit_name
        FROM food_nutrient fn
        JOIN nutrient n ON fn.nutrient_id = n.id
        GROUP BY n.id
        HAVING AVG(fn.amount) > 10
        ORDER BY avg_amount DESC
        LIMIT 10;
        """
        print("\nQuery 3: Average nutrient amounts across all foods")
        execute_query(conn, query3)

        # 4. Subquery to find foods with above-average protein content (with LIMIT and optimization)
        query4 = """
        WITH avg_protein AS (
            SELECT AVG(amount) as avg_amount
            FROM food_nutrient fn
            JOIN nutrient n ON fn.nutrient_id = n.id
            WHERE n.name = 'Protein'
        )
        SELECT f.description, fn.amount AS protein_amount
        FROM food f
        JOIN food_nutrient fn ON f.fdc_id = fn.fdc_id
        JOIN nutrient n ON fn.nutrient_id = n.id
        CROSS JOIN avg_protein
        WHERE n.name = 'Protein'
        AND fn.amount > avg_protein.avg_amount
        ORDER BY fn.amount DESC
        LIMIT 10;
        """
        print("\nQuery 4: Foods with above-average protein content")
        execute_query(conn, query4)

        # Close the database connection
        conn.close()
        print("SQLite connection is closed.")

if __name__ == '__main__':
    main()
