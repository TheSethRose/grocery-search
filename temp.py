import sqlite3

DATABASE_PATH = './database/food_data.db'  # Update this path if your database is located elsewhere

def connect_db():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        print(f"Connected to SQLite database: {DATABASE_PATH}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite database: {e}")
        return None

def get_table_names(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return [table[0] for table in tables]

def get_column_names(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info('{table_name}');")
    columns = cursor.fetchall()
    return [column[1] for column in columns]

def print_table_schema(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info('{table_name}');")
    schema = cursor.fetchall()
    print(f"\nSchema for table '{table_name}':")
    print("-" * 50)
    for column in schema:
        cid, name, type_, notnull, default_value, pk = column
        pk_text = ' PRIMARY KEY' if pk else ''
        print(f"{name} ({type_}){pk_text}")
    print("-" * 50)

def print_sample_data(conn, table_name, limit=5, search_term=None):
    cursor = conn.cursor()
    column_names = get_column_names(conn, table_name)

    # Determine the appropriate columns to search in
    search_columns = []
    if 'description' in column_names:
        search_columns.append('description')
    if 'short_description' in column_names:
        search_columns.append('short_description')
    if 'brand_owner' in column_names:
        search_columns.append('brand_owner')
    if 'ingredients' in column_names:
        search_columns.append('ingredients')

    # Build the WHERE clause dynamically
    where_clause = " OR ".join([f"{col} LIKE ?" for col in search_columns])
    params = [f'%{search_term}%'] * len(search_columns) + [limit]

    if where_clause:
        query = f"SELECT * FROM '{table_name}' WHERE {where_clause} LIMIT ?;"
    else:
        query = f"SELECT * FROM '{table_name}' LIMIT ?;"
        params = [limit]

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return

    if rows:
        print(f"\nSample data from '{table_name}':")
        print("-" * 50)
        print("\t".join(column_names))
        for row in rows:
            print("\t".join(str(value) if value is not None else 'NULL' for value in row))
        print("-" * 50)
    else:
        print(f"\nNo sample data found in '{table_name}' with search term '{search_term}'.")

def main():
    conn = connect_db()
    if not conn:
        return

    # List of relevant tables to inspect
    relevant_tables = ['branded_food', 'food', 'food_nutrient', 'nutrient', 'food_attribute', 'measure_unit']

    # Get all table names in the database
    all_tables = get_table_names(conn)
    print("Tables in the database:")
    print(", ".join(all_tables))

    for table in relevant_tables:
        if table in all_tables:
            print_table_schema(conn, table)
        else:
            print(f"Table '{table}' does not exist in the database.")

    # Print sample data for items containing 'milk' or 'yogurt'
    search_terms = ['milk', 'eggs', 'bread', 'butter']
    for term in search_terms:
        print(f"\nSample data for search term '{term}':")
        for table in ['branded_food', 'food']:
            if table in all_tables:
                print_sample_data(conn, table, limit=10, search_term=term)
            else:
                print(f"Table '{table}' does not exist in the database.")

    conn.close()

if __name__ == "__main__":
    main()
