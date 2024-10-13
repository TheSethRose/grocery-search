import requests
import os
from openai import OpenAI
import json
import sqlite3
from dotenv import load_dotenv
import logging
from collections import Counter
from datetime import datetime
from fuzzywuzzy import fuzz
import re
from urllib.parse import urlencode

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set up logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

# Path to the SQLite database
DATABASE_PATH = os.getenv('DATABASE_PATH', './database/food_data.db')
# Backend URL for searching items
BACKEND_URL = os.getenv('BACKEND_URL', 'https://backflipp.wishabi.com/flipp/items/search')

# Debug mode
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

class GroceryPriceFinder:
    def __init__(self, zip_code, grocery_list):
        self.zip_code = zip_code
        self.grocery_list = grocery_list
        self.grocery_items = []
        self.available_stores = set()
        self.store_item_counts = Counter()

        # Create necessary directories
        os.makedirs("responses", exist_ok=True)

    def connect_db(self):
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            logging.info(f"Connected to SQLite database: {DATABASE_PATH}")
            return conn
        except sqlite3.Error as e:
            logging.error(f"Error connecting to SQLite database: {e}")
            return None

    def parse_grocery_list(self):
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Don't change this, it's correct.
            messages=[
                {"role": "system", "content": "You are a helpful assistant that parses grocery lists into structured data with categories."},
                {"role": "user", "content": f"Parse the following grocery list into structured data. For each item, include the name, type, brand, quantity, notes, and category (e.g., dairy, produce, meat, bakery, etc.):\n{self.grocery_list}"}
            ],
            functions=[{
                "name": "clarify_grocery_list",
                "description": "Clarify and structure each item in the grocery list, including category",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "brand": {"type": "string"},
                                    "type": {"type": "string"},
                                    "quantity": {"type": "string"},
                                    "notes": {"type": "string"},
                                    "category": {"type": "string"}
                                },
                                "required": ["name"]
                            }
                        }
                    },
                    "required": ["items"]
                }
            }],
            function_call={"name": "clarify_grocery_list"}
        )

        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "clarify_grocery_list":
            parsed_list = json.loads(function_call.arguments)
            logging.info(f"Parsed {len(parsed_list['items'])} items from grocery list")
            return parsed_list['items']
        else:
            logging.error("Error: Unexpected response format from OpenAI")
            return []

    def expand_item_info(self, item):
        conn = self.connect_db()
        if not conn:
            return item

        cursor = conn.cursor()

        # Only use the database for additional info if a brand is specified
        if item.get('brand'):
            query_branded = """
            SELECT bf.brand_owner, bf.ingredients, bf.serving_size, bf.serving_size_unit, f.description
            FROM branded_food AS bf
            JOIN food AS f ON bf.fdc_id = f.fdc_id
            WHERE LOWER(bf.brand_owner) LIKE '%' || LOWER(?) || '%'
            LIMIT 1;
            """
            cursor.execute(query_branded, (item['brand'],))
            result_branded = cursor.fetchone()

            if result_branded:
                item['brand_owner'] = result_branded[0]
                item['ingredients'] = result_branded[1]
                item['serving_size'] = result_branded[2]
                item['serving_size_unit'] = result_branded[3]
                item['db_description'] = result_branded[4]
                logging.debug(f"Found branded food info for '{item['name']}': {item['db_description']}")
            else:
                logging.debug(f"No additional info found for brand '{item['brand']}'")
        else:
            logging.debug(f"No brand specified for '{item['name']}', skipping database lookup")

        conn.close()
        return item

    def build_query_for_item(self, item):
        query_parts = []

        # Include brand if specified
        if item.get('brand'):
            query_parts.append(item['brand'])

        # Always include the item name
        query_parts.append(item['name'])

        if item.get('type'):
            query_parts.append(item['type'])
        if item.get('quantity'):
            query_parts.append(item['quantity'])
        if item.get('category'):
            query_parts.append(item['category'])

        query = ' '.join(query_parts)
        logging.debug(f"Built query for '{item['name']}': {query}")
        return query.strip()

    def search_item(self, query):
        try:
            params = {'q': query, 'postal_code': self.zip_code}
            url = f"{BACKEND_URL}?{urlencode(params)}"
            logging.info(f"Searching URL: {url}")

            # Log the request
            self.log_api_interaction("REQUEST", url)

            response = requests.get(url)
            response.raise_for_status()

            # Log the raw response
            self.log_api_interaction("RESPONSE", response.text)

            try:
                data = response.json()
                # Save the JSON response for debugging purposes
                #if DEBUG:
                self.save_json_response(query, data)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}")
                logging.error(f"Response content: {response.text}")
                return []

            items = data.get('items', []) + data.get('ecom_items', []) + data.get('related_items', [])
            logging.info(f"Found {len(items)} items for query: {query}")

            # Initialize a set to store all detected stores
            stores = set()

            # Process each item and extract the store name
            for item in items:
                store_name = item.get('merchant') or item.get('merchant_name') or 'Unknown Store'
                store_name = store_name.strip()
                normalized_store_name = store_name.lower()  # Normalize for consistency

                # Add the normalized store name to the set
                stores.add(normalized_store_name)

                # Update the store item counts with the raw (non-normalized) store name
                self.store_item_counts[store_name] += 1

            logging.info(f"Stores found: {', '.join(sorted(stores))}")

            return items
        except requests.RequestException as e:
            logging.error(f"Error searching for item {query}: {e}")
            return []

    def parse_price(self, item):
        if item is None:
            return None
        if 'current_price' in item and item['current_price'] is not None:
            return float(item['current_price'])
        # Try to extract price from 'sale_story' or 'name'
        possible_fields = ['sale_story', 'name', 'description']
        for field in possible_fields:
            text = item.get(field, '')
            if text:
                price_match = re.search(r'\$\s*([0-9]+(\.[0-9]{1,2})?)', text)
                if price_match:
                    return float(price_match.group(1))
        return None

    def parse_unit_size(self, item):
        name = item.get('name', '')
        if not name:
            return {'size': 1, 'unit': 'unit'}
        # Try to extract size and unit from the name
        size_match = re.search(r'([0-9]+(\.[0-9]+)?)\s*(oz|fl oz|g|ml|lb|kg|pack|ct|count|litre|liter|l)', name.lower())
        if size_match:
            size = float(size_match.group(1))
            unit = size_match.group(3)
            return {'size': size, 'unit': unit}
        return {'size': 1, 'unit': 'unit'}

    def normalize_price(self, price, size, unit):
        if price is None or size == 0:
            return None
        conversion_rates = {
            'lb': 16,
            'kg': 35.274,
            'g': 0.035274,
            'l': 33.814,
            'litre': 33.814,
            'liter': 33.814,
            'ml': 0.033814,
            'fl oz': 1,
            'oz': 1,
            'ct': 1,
            'count': 1,
            'pack': 1
        }
        size_in_oz = size * conversion_rates.get(unit, 1)
        return price / size_in_oz if size_in_oz else None

    def item_matches(self, item, original_item):
        if item is None or not isinstance(item, dict):
            return False

        item_name = item.get('name')
        if not isinstance(item_name, str):
            return False

        item_name = item_name.lower()
        original_name = original_item['name'].lower()

        # If a brand is specified, it must match
        if original_item.get('brand'):
            if original_item['brand'].lower() not in item_name:
                return False

        # Use fuzzy matching on item name
        ratio = fuzz.partial_ratio(original_name, item_name)

        return ratio >= 70  # Adjusted the threshold to be more inclusive

    def find_cheapest_item(self, items, original_item, query, revised_query):
        logging.debug(f"Finding cheapest item for: {original_item['name']}")
        cheapest_item = None
        lowest_normalized_price = float('inf')
        stores_searched = set()
        items_matched = 0
        alternatives = set()

        for item in items:
            if item is None:
                logging.debug("Skipping None item")
                continue

            if not isinstance(item, dict):
                logging.debug(f"Skipping non-dict item: {type(item)}")
                continue

            if 'name' not in item or not isinstance(item['name'], str):
                logging.debug(f"Skipping item without valid name: {item}")
                continue

            store_name = item.get('merchant') or item.get('merchant_name', 'Unknown Store')
            stores_searched.add(store_name)

            # Check if the item matches the intended item
            if self.item_matches(item, original_item):
                items_matched += 1
            else:
                alternatives.add(item['name'])  # Add the full name as an alternative
                logging.debug(f"Item does not match: {item.get('name', 'No name')}")
                continue

            price = self.parse_price(item)
            if price is None:
                logging.debug(f"No price found for item: {item.get('name', 'No name')}")
                continue

            size_data = self.parse_unit_size(item)
            normalized_price = self.normalize_price(price, size_data['size'], size_data['unit'])

            # Check if brand matches if specified
            if original_item.get('brand') and original_item['brand'].lower() not in item.get('name', '').lower():
                logging.debug(f"Brand mismatch for item: {item.get('name', 'No name')}")
                continue

            if normalized_price is not None and normalized_price < lowest_normalized_price:
                lowest_normalized_price = normalized_price
                cheapest_item = {
                    'name': item.get('name', original_item['name']),
                    'image': item.get('image_url', 'N/A'),
                    'price': price,
                    'size': f"{size_data['size']} {size_data['unit']}",
                    'normalized_price': normalized_price,
                    'store': store_name,
                    'valid_until': item.get('valid_to', 'N/A'),
                    'original_query': query,
                    'revised_query': revised_query,
                    'stores_searched': list(stores_searched),
                    'items_matched': items_matched,
                    'alternatives': list(alternatives)
                }
                logging.debug(f"New cheapest item found: {cheapest_item['name']} at {cheapest_item['store']}")

        if not cheapest_item:
            logging.warning(f"No valid items found for {original_item['name']}")
            cheapest_item = {
                'name': original_item['name'],
                'image': 'N/A',
                'price': None,
                'size': 'N/A',
                'normalized_price': None,
                'store': 'None',
                'valid_until': 'N/A',
                'original_query': query,
                'revised_query': revised_query,
                'stores_searched': list(stores_searched),
                'items_matched': items_matched,
                'alternatives': list(alternatives)
            }

        return cheapest_item

    def process_grocery_list(self):
        parsed_list = self.parse_grocery_list()
        for item in parsed_list:
            logging.info(f"Processing item: {item['name']}")
            expanded_item = self.expand_item_info(item)
            original_query = item['name']
            revised_query = self.build_query_for_item(expanded_item)
            results = self.search_item(revised_query)
            cheapest_item = self.find_cheapest_item(results, expanded_item, original_query, revised_query)
            self.grocery_items.append(cheapest_item)
            if cheapest_item['store'] not in ['Unknown Store', 'None']:
                self.available_stores.add(cheapest_item['store'])

            if DEBUG:
                logging.debug(f"Cheapest item for {item['name']}: {cheapest_item['store']} - ${cheapest_item['price']}")

    def print_grocery_items(self):
        print("\n" + "=" * 30 + "  SEARCH RESULTS  " + "=" * 30 + "\n")

        for item in self.grocery_items:
            print(f"[Search] {item['original_query'].title()}")
            print(f"    Revised Search: {item['revised_query']}")

            if item['store'] != 'None':
                print(f"    Matched Item: {item['name']}")
                print(f"    Stores Searched: {', '.join(item['stores_searched'])}")
                print(f"    --> Store Selected: {item['store']}")
                print(f"    --> Price: {'$' + format(item['price'], '.2f') if item['price'] else 'N/A'}")
                print(f"    --> Size: {item['size']}")
                print(f"    --> Normalized Price: {'$' + format(item['normalized_price'], '.2f') + ' per oz' if item['normalized_price'] else 'N/A'}")
                if item['valid_until'] != 'N/A':
                    valid_until = datetime.strptime(item['valid_until'][:10], "%Y-%m-%d").strftime("%Y-%m-%d")
                    print(f"    --> Valid Until: {valid_until}")
            else:
                print("    Matched Item: None")
                print(f"    Stores Searched: {', '.join(item['stores_searched']) if item['stores_searched'] else 'None'}")
                print("    --> Message: No valid items found.")

            if item['alternatives']:
                top_5_alternatives = item['alternatives'][:5]
                print(f"    Alternatives: {', '.join(top_5_alternatives)}")

            print("\n" + "-" * 79 + "\n")

        print("=" * 79)

    def save_json_response(self, query, data):
        filename = f"responses/{query.replace(' ', '_')}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Saved JSON response to {filename}")

    def log_api_interaction(self, interaction_type, content):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {interaction_type}:\n{content}\n{'='*50}\n"

        with open("api_interactions.log", "a") as log_file:
            log_file.write(log_entry)

if __name__ == "__main__":
    zip_code = os.getenv("POSTAL_CODE")
    if not zip_code:
        zip_code = input("Enter your postal code or zip code:\n")
    grocery_list = input("Enter your grocery list (you can be as detailed as you like):\n")

    finder = GroceryPriceFinder(zip_code, grocery_list)
    finder.process_grocery_list()
    finder.print_grocery_items()
