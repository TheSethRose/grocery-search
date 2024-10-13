# Food Database Project

This project is designed to create and manage a SQLite database using several CSV files that contain data about branded foods, nutrients, food attributes, and more. The data is provided by the USDA and needs to be downloaded separately.

## Project Structure

The project includes the following key files:

- `database/create_db.py`: This script contains functions to set up the SQLite database, create the necessary tables, and load data from the CSV files into the database.
- `database/db_builder.py`: This script orchestrates the database creation process by calling functions in `create_db.py`. It deletes any existing database, creates new tables, and populates them with data.
- `database/query_examples.py`: This script contains example SQL queries for each table in the database, showing how to query the data effectively.
- `grocery_list.py`: This script uses the database to process a grocery list, find the best deals, and provide pricing information.
- `README.md`: Documentation for the project (this file).

## Prerequisites

Ensure you have the following installed:

- Python 3.x
- SQLite (optional, as Python includes SQLite by default)
- Required Python libraries. You can install them using:

  ```bash
  pip install -r requirements.txt
  ```

## How to Run

### Step 1: Download the Source Data

1. Visit the USDA FoodData Central download page: <https://fdc.nal.usda.gov/download-datasets.html>
2. Download the following CSV files (inside "Full Download of All Data Types"):
   - `branded_food.csv`
   - `food.csv`
   - `food_attribute.csv`
   - `food_nutrient.csv`
   - `nutrient.csv`
   - `measure_unit.csv`
3. Place these files in the `database/source_data` directory in your project folder.

### Step 2: Create the Database

To create and populate the database:

```bash
python database/db_builder.py
```

This will:

1. Delete any existing `food_data.db` database file.
2. Create new tables in `./database/food_data.db`.
3. Load the data from the CSV files into the database.

### Step 3: Running Query Examples

To run query examples that demonstrate how to query the database:

```bash
python database/query_examples.py
```

This script will execute example queries on each table and print the results to the console.

### Step 4: Using the Grocery List Processor

To use the grocery list processor:

```bash
python grocery_list.py
```

Follow the prompts to enter your grocery list and get pricing information.

## Database Schema

The database contains the following tables:

1. branded_food: Contains data about branded food items, including brand owner, UPC, serving size, ingredients, and market details.
2. food: Contains general information about food items, including a description and category ID.
3. food_attribute: Stores various attributes of food items, such as nutrient updates or ingredient details.
4. food_nutrient: Stores information about nutrients present in each food item, such as the nutrient amount.
5. nutrient: Represents various nutrients like protein, fat, vitamins, and their units of measurement.
6. measure_unit: Stores measurement units like cups, tablespoons, etc.

You can see a detailed explanation of the schema and relationships in [documentation/database_schema.md](documentation/database_schema.md) and [documentation/dataDictionary.pdf](documentation/dataDictionary.pdf).

## Querying the Database

Once the database is set up, you can query it using SQL. Here are a few example queries:

- Find branded foods from "CAMPBELL":

  ```sql
  SELECT brand_owner, gtin_upc, ingredients, serving_size, market_country
  FROM branded_food
  WHERE brand_owner LIKE '%CAMPBELL%'
  LIMIT 5;
  ```

- Get nutrient information for a specific food:

  ```sql
  SELECT fdc_id, nutrient_id, amount
  FROM food_nutrient
  WHERE fdc_id = 1105904;
  ```

- List nutrients with KCAL as their unit:

  ```sql
  SELECT id, name, unit_name
  FROM nutrient
  WHERE unit_name = 'KCAL';
  ```

For more example queries, refer to `database/query_examples.py`.

## Contributing

Feel free to contribute by submitting pull requests, creating issues, or suggesting improvements!

## License

This project is open-source and available under the [MIT License](LICENSE).
