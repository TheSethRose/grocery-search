# Grocery Price Finder Process

This document outlines the step-by-step process used by the Grocery Price Finder application to standardize grocery items and find the best deals.

## 1. User Input

1. The user provides a ZIP code (or it's loaded from the environment variables).
2. The user enters a comma-separated list of grocery items.

## 2. ZIP Code Validation

1. The application validates the ZIP code using the Zippopotam.us API.
2. If the ZIP code is invalid, the user is prompted to enter a valid one.

## 3. Grocery List Preprocessing

For each item in the grocery list:

1. The application attempts to standardize the item using the local SQLite database (`food_data.db`).
2. If the item is found in the database:
   - It retrieves the standardized information (brand, quantity, etc.).
3. If the item is not found in the database:
   - It uses the OpenAI API to standardize the item.
4. The standardized item information is stored for further processing.

## 4. Price Search

For each standardized item:

1. The application builds a search query using the standardized information.
2. It sends a request to the Flipp API (BACKEND_URL) with the query and ZIP code.
3. The API returns a list of matching items from various stores' weekly ads.

## 5. Price Analysis

For each item returned by the Flipp API:

1. The application parses the price and unit size.
2. It normalizes the price to a per-unit cost (e.g., price per ounce).
3. It identifies the cheapest option among the results.

## 6. Results Compilation

1. The application compiles the cheapest option for each grocery item.
2. It keeps track of the available stores that offer these items.

## 7. Output

The application prints out the results, including:

- The store name
- The item name
- The price
- The size/quantity
- The normalized price (price per unit)
- The validity period of the offer
- An image URL (if available)

## Note on Current Limitations

- The process currently relies on finding exact matches in the Flipp API, which may lead to "Not found" results for many items.
- The standardization process might over-specify items (e.g., including brand names from the database), potentially limiting matches in the Flipp API.

## Potential Improvements

- Implement a more flexible matching algorithm for the Flipp API search.
- Adjust the standardization process to provide more generic search terms.
- Consider using a different or additional API for price comparisons.
