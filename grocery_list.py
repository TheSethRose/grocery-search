import requests
import os
import openai
import json
import sqlite3
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=log_level)

# Path to the SQLite database
DATABASE_PATH = os.getenv('DATABASE_PATH', './database/food_data.db')
# Backend URL for searching items
BACKEND_URL = os.getenv('BACKEND_URL', 'https://backflipp.wishabi.com/flipp/items/search')

# Set OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Debug mode
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

class GroceryPriceFinder:
    def __init__(self, zip_code, grocery_list):
        self.zip_code = zip_code
        self.grocery_list = grocery_list
        self.grocery_items = []  # List to store the processed grocery items
        self.available_stores = set()  # Set to store the unique available stores

    def connect_db(self):
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            logging.info(f"Connected to SQLite database: {DATABASE_PATH}")
            return conn
        except sqlite3.Error as e:
            logging.error(f"Error connecting to SQLite database: {e}")
        return None

    def parse_grocery_list(self):
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # This is valid, don't change it.
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that parses grocery lists into structured data. "
                        "For each item, provide: \n"
                        "1. name: The main item name\n"
                        "2. brand: Brand name if specified, otherwise null\n"
                        "3. type: Any specific type or variety\n"
                        "4. quantity: Any quantity information\n"
                        "5. notes: Any additional notes or preferences"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Parse the following grocery list into structured data:\n{self.grocery_list}\nReturn the data as a JSON array of objects."
                }
            ],
            functions=[
                {
                    "name": "clarify_grocery_list",
                    "description": "Clarify and structure each item in the grocery list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "The main name of the grocery item"},
                                        "brand": {"type": "string", "description": "The brand of the item, if specified"},
                                        "type": {"type": "string", "description": "The type or variation of the item"},
                                        "quantity": {"type": "string", "description": "The quantity or size of the item"},
                                        "notes": {"type": "string", "description": "Any additional notes or preferences"}
                                    },
                                    "required": ["name"]
                                }
                            }
                        },
                        "required": ["items"]
                    }
                }
            ],
            function_call={"name": "clarify_grocery_list"}
        )

        # Extract the function call result
        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "clarify_grocery_list":
            parsed_list = json.loads(function_call.arguments)
            return parsed_list['items']
        else:
            print("Error: Unexpected response format from OpenAI")
            return []

    def expand_item_info(self, item):
        conn = self.connect_db()
        if not conn:
            return item

        cursor = conn.cursor()
        query = """
        SELECT brand_owner, ingredients, serving_size, serving_size_unit
        FROM branded_food
        WHERE description LIKE ?
        LIMIT 1;
        """
        cursor.execute(query, (f"%{item['name']}%",))
        result = cursor.fetchone()
        conn.close()

        if result:
            item['db_brand'] = result[0]
            item['ingredients'] = result[1]
            item['serving_size'] = f"{result[2]} {result[3]}"

        return item

    def build_query_for_item(self, item):
        query = item['name']
        if item['type']:
            query += f" {item['type']}"
        if item['brand']:
            query = f"{item['brand']} {query}"
        if item['quantity']:
            query += f" {item['quantity']}"
        return query.strip()

    def search_item(self, query):
        try:
            url = f"{BACKEND_URL}?q={requests.utils.quote(query)}&postal_code={self.zip_code}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if not data or (not data.get('items') and not data.get('ecom_items')):
                return []
            return data.get('items', []) + data.get('ecom_items', [])
        except Exception as e:
            print(f"Error searching for item {query}: {e}")
            return []

    def parse_price(self, item):
        if item.get('current_price'):
            return item['current_price']
        price_match = item.get('name', '').split('$')
        if len(price_match) > 1:
            return float(price_match[1].split()[0])
        return None

    def parse_unit_size(self, item):
        size_match = item.get('name', '').split()
        if len(size_match) > 1:
            return {'size': float(size_match[0]), 'unit': size_match[1].lower()}
        return {'size': 1, 'unit': 'unit'}

    def normalize_price(self, price, size, unit):
        if price is None:
            return None
        conversion_rates = {
            'lb': 16, 'kg': 35.274, 'g': 0.035274, 'l': 33.814, 'ml': 0.033814
        }
        return price / (size * conversion_rates.get(unit, 1))

    def find_cheapest_item(self, items, original_item):
        cheapest_item = None
        lowest_normalized_price = float('inf')

        for item in items:
            price = self.parse_price(item)
            size_data = self.parse_unit_size(item)
            normalized_price = self.normalize_price(price, size_data['size'], size_data['unit'])

            if original_item['brand'] and item.get('merchant') != original_item['brand']:
                continue

            if normalized_price is not None and normalized_price < lowest_normalized_price:
                lowest_normalized_price = normalized_price
                cheapest_item = {
                    'name': item.get('name', original_item['name']),
                    'image': item.get('image_url', 'N/A'),
                    'price': price,
                    'size': f"{size_data['size']} {size_data['unit']}",
                    'normalized_price': normalized_price,
                    'store': item.get('merchant', 'Unknown Store'),
                    'valid_until': item.get('valid_to', 'N/A')
                }

        if not cheapest_item:
            cheapest_item = {
                'name': original_item['name'],
                'image': 'N/A',
                'price': None,
                'size': 'N/A',
                'normalized_price': None,
                'store': 'Not found',
                'valid_until': 'N/A'
            }

        return cheapest_item

    def process_grocery_list(self):
        parsed_list = self.parse_grocery_list()
        for item in parsed_list:
            expanded_item = self.expand_item_info(item)
            query = self.build_query_for_item(expanded_item)
            results = self.search_item(query)
            cheapest_item = self.find_cheapest_item(results, expanded_item)
            self.grocery_items.append(cheapest_item)
            if cheapest_item['store'] != 'Unknown Store' and cheapest_item['store'] != 'Not found':
                self.available_stores.add(cheapest_item['store'])

            if DEBUG:
                logging.debug(f"Processed item: {item['name']}")
                logging.debug(f"Query: {query}")
                logging.debug(f"Results found: {len(results)}")
                logging.debug(f"Cheapest item: {cheapest_item}")

    def print_grocery_items(self):
        for item in self.grocery_items:
            print(f"Store: {item['store']}")
            print(f"Item: {item['name']}")
            print(f"Price: {'$' + format(item['price'], '.2f') if item['price'] else 'N/A'}")
            print(f"Size: {item['size']}")
            print(f"Normalized Price: {'$' + format(item['normalized_price'], '.4f') + ' per oz' if item['normalized_price'] else 'N/A'}")
            print(f"Valid Until: {item['valid_until']}")
            print(f"Image: {item['image']}")
            print("-" * 40)

if __name__ == "__main__":
    zip_code = os.getenv("POSTAL_CODE")
    grocery_list = input("Enter your grocery list (you can be as detailed as you like):\n")

    finder = GroceryPriceFinder(zip_code, grocery_list)
    finder.process_grocery_list()
    finder.print_grocery_items()
