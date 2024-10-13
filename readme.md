# Grocery Price Finder and Food Database Project

This project combines a Grocery Price Finder with a comprehensive Food Database, enabling users to find the best deals on their grocery items while providing robust food information.

## Project Overview

The project consists of two main components: the Food Database and the Grocery Price Finder.

### 1. Food Database

The Food Database is created using data from USDA FoodData Central and includes detailed information on various food items, such as nutrients, attributes, and measurement units.

#### **Food Database Creation Process**

1. **Data Download**
   - Download CSV files from USDA FoodData Central.
   - Place these files in the `database/source_data` directory.

2. **Database Initialization** (`db_builder.py`)
   - Deletes the existing `food_data.db` if present.
   - Calls functions from `create_db.py` to set up the new database.

3. **Table Creation** (`create_db.py`)
   - Creates tables such as `branded_food`, `food`, `food_nutrient`, `nutrient`, `food_attribute`, and `measure_unit`.
   - Establishes relationships and indexes for optimization.

4. **Data Loading** (`create_db.py`)
   - Reads each CSV file using pandas.
   - Cleans and processes data (e.g., handling numeric columns).
   - Loads data into respective tables.

5. **Query Examples** (`query_examples.py`)
   - Provides sample queries to demonstrate database usage, including complex joins, filtering, and aggregations.

#### **Database Schema**

The database contains the following tables:

1. **branded_food**: Information on branded food items, including brand owner, UPC, serving size, ingredients, and market details.
2. **food**: General information about food items, including a description and category ID.
3. **food_attribute**: Attributes such as nutrient updates or ingredient details.
4. **food_nutrient**: Information about nutrients present in each food item, such as nutrient amount.
5. **nutrient**: Nutrients like protein, fat, vitamins, and their units of measurement.
6. **measure_unit**: Measurement units like cups, tablespoons, etc.

Relationships between tables are established via keys such as `fdc_id` and `nutrient_id`. A detailed explanation can be found in `documentation/database_schema.md`.

#### **Setup Instructions**

1. **Download the USDA CSV Files**
   - Visit: <https://fdc.nal.usda.gov/download-datasets.html>
   - Download: `branded_food.csv`, `food.csv`, `food_attribute.csv`, `food_nutrient.csv`, `nutrient.csv`, `measure_unit.csv`.
   - Place files in the `database/source_data` directory.

2. **Create the Database**

   ```bash
   python database/db_builder.py
   ```

   This will create `food_data.db` in the `database` directory.

3. **Run Example Queries**

   ```bash
   python database/query_examples.py
   ```

### 2. Grocery Price Finder

The Grocery Price Finder helps users find the cheapest grocery items by parsing a free-form grocery list, expanding item information, and querying a backend API for prices.

#### **Process Overview**

1. **User Input**
   - The user provides a ZIP code and a grocery list.

2. **List Parsing** (`grocery_list.py`)
   - Uses OpenAI API to parse the free-form list into structured data, extracting item details such as name, brand, type, quantity, and category.

3. **Item Information Expansion**
   - Queries the local food database to expand item information, adding details like ingredients and serving sizes.

4. **Query Building**
   - Constructs search queries for each item using the parsed and expanded information.

5. **Price Search**
   - Sends queries to the backend API (Flipp) with the user's ZIP code.
   - Retrieves matching items from various stores.

6. **Price Analysis**
   - Parses price and unit size for each result, normalizes prices (e.g., price per ounce), and identifies the cheapest option matching the original item.
   - Tracks alternative items for suggestions.

7. **Results Compilation**
   - Compiles information for each grocery item, including the best match, stores searched, number of matches, and alternative items.

8. **Output**
   - Provides formatted results, including matched item details, search queries, stores searched, and alternative items.

### How to Use the Grocery Price Finder

1. **Set Up Environment Variables**
   - Copy `.env.example` to `.env` and fill in your OpenAI API key and other required variables.
   - Update `.env` with your ZIP code if you want to avoid entering it each time you run the Grocery Price Finder.

2. **Run the Grocery Price Finder**

   ```bash
   python grocery_list.py
   ```

   Follow the prompts to enter your ZIP code and grocery list if not set in the `.env` file.

### Features

- Parses free-form grocery lists into structured data.
- Searches multiple local stores for the best deals using the Flipp API.
- Normalizes prices for easy comparison.
- Provides alternative options when exact matches aren't found.
- Leverages a comprehensive food database with nutrient information.

## Future Improvements

- Enhance natural language processing for better grocery list parsing and query building.
- Improve the matching algorithm for handling product variations.
- Integrate additional price comparison APIs.
- Expand the food database with more nutrition and food data sources.

## Contributing

Contributions are welcome! Please feel free to submit pull requests, create issues, or suggest improvements.

## License

This project is open-source and available under the [MIT License](LICENSE).
