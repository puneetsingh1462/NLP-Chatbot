# Zuzu Food Ordering Chatbot

Zuzu is a FastAPI webhook for a Dialogflow food-ordering chatbot backed by MySQL. It supports adding items to an order, resolving ambiguous menu names, calculating totals, saving completed orders to the database, and tracking order status.

## Features

- Add menu items to an in-progress order from Dialogflow intents
- Resolve partial item names such as `lassi` to `Mango Lassi` when there is only one valid match
- Ask for clarification when a menu name is ambiguous, such as `dosa`
- Calculate order totals from the `food_items` table
- Save completed orders into MySQL using stored procedures
- Save order status in `order_tracking`
- Track order status by `order_id`

## Project Structure

- [main.py](/abs/path/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/main.py): FastAPI webhook and Dialogflow intent handlers
- [db_helper.py](/abs/path/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/db_helper.py): MySQL connection helpers, menu lookup, pricing, and stored procedure calls
- [stored_procedures.sql](/abs/path/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/stored_procedures.sql): MySQL schema/procedure changes used by the application
- [zuzu.html](/abs/path/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/zuzu.html): Dialogflow Messenger test page

## Tech Stack

- Python
- FastAPI
- MySQL
- Dialogflow
- Dialogflow Messenger

## Database Design

The application uses three main tables:

### `food_items`

Stores the menu.

Expected columns:

- `item_id`
- `name`
- `price`

Example menu:

- Pav Bhaji
- Chole Bhature
- Pizza
- Mango Lassi
- Masala Dosa
- Vegetable Biryani
- Vada Pav
- Rava Dosa
- Samosa

### `order_tracking`

Stores one row per order with the order status.

Important change:

- `order_id` is now `AUTO_INCREMENT`

This avoids Python-side `MAX(order_id) + 1` generation and is safer for concurrent requests.

### `orders`

Stores one row per ordered item.

Columns:

- `order_id`
- `item_id`
- `quantity`
- `total_price`

Example row:

```text
order_id = 45
item_id = 1
quantity = 2
total_price = 12.00
```

## Stored Procedures

The project uses stored procedures for writing orders to the database.

### `create_order_entry`

Purpose:

- Inserts a new row into `order_tracking`
- Returns the generated `order_id`

Why it exists:

- Keeps order ID generation inside MySQL
- Reduces race-condition risk for concurrent users

### `insert_order_item`

Purpose:

- Accepts a food item name, quantity, and order ID
- Looks up the `item_id` and price from `food_items`
- Calculates line-level total price
- Inserts one row into `orders`

## Order Flow

### 1. Add items

Dialogflow sends the `Order.add-context:ongoing-order` intent to the webhook.

The application:

- reads `number` and `Food-Item`
- resolves menu names using `find_matching_food_items()`
- auto-selects a single valid match
- asks for clarification if multiple items match
- stores the in-progress order in Dialogflow output context

Examples:

- `1 lassi` -> auto-resolves to `Mango Lassi`
- `1 dosa` -> asks whether the user means `Masala Dosa` or `Rava Dosa`

### 2. Complete order

When Dialogflow sends `Order.complete`, the application:

- loads the order from the `ongoing-order` context
- resolves item names again before persistence
- calculates the total from menu prices
- creates the order in MySQL
- inserts one row per item into `orders`
- returns the generated order ID and total to the user

### 3. Track order

When Dialogflow sends `Track.order`, the application:

- reads the order ID
- looks up the status in `order_tracking`
- sends the status back through output context

## Atomic Order Creation

Order creation is handled in one transaction inside [db_helper.py](/abs/path/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/db_helper.py).

`create_order_with_items()`:

- calls `create_order_entry`
- receives the new `order_id`
- calls `insert_order_item` for each item
- commits only if all inserts succeed
- rolls back the transaction if any insert fails

This is better than separate independent inserts because it prevents partial order writes.

## Setup

### 1. Install Python packages

```bash
pip install fastapi uvicorn mysql-connector-python
```

### 2. Configure MySQL connection

Edit [db_helper.py](/abs/path/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/db_helper.py):

```python
return mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="pandeyji_eatery"
)
```

Update these values for your machine before publishing the project.

### 3. Apply stored procedures

Run the SQL from [stored_procedures.sql](/abs/path/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/stored_procedures.sql) in your MySQL database.

This file:

- modifies `order_tracking.order_id` to `AUTO_INCREMENT`
- creates `create_order_entry`
- creates `insert_order_item`

### 4. Start the API

```bash
uvicorn main:app --reload
```

### 5. Expose the webhook

If Dialogflow needs a public URL, use ngrok or another tunnel:

```bash
ngrok http 8000
```

Then configure the Dialogflow webhook URL to:

```text
https://your-public-url/webhook
```

## Dialogflow Notes

The webhook logic assumes these intents exist:

- `Order.add-context:ongoing-order`
- `Order.complete`
- `Track.order`

Important note:

- If Dialogflow fallback responses are still showing instead of webhook responses, check the static `Responses` section in the matched intent and ensure webhook fulfillment is enabled.

For ambiguous items like `dosa`, the recommended Dialogflow setup is:

- let the webhook receive the raw item text
- avoid hard-mapping `dosa` directly to a single menu item

## Example Completed Order

After order completion, the backend stores a structure like:

```python
{
    "order_id": 45,
    "items": [
        {
            "order_id": 45,
            "item_id": 1,
            "quantity": 1,
            "total_price": 6.0
        }
    ],
    "total_price": 6.0
}
```

And in MySQL `orders`, a row looks like:

```text
45 | 1 | 1 | 6.00
```

## Current Limitations

- `completed_orders` in [main.py](/abs/path/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/main.py) is still in-memory only
- Dialogflow multi-turn ambiguity handling is not fully implemented yet
- credentials are currently hardcoded in [db_helper.py](/abs/path/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/db_helper.py)

## Recommended Next Improvements

- move DB credentials to environment variables
- add proper logging instead of prints
- add request validation and structured error handling
- persist session/order state outside process memory
- add automated tests for menu matching and order completion
- add a single stored procedure that creates the order and inserts all rows entirely inside MySQL if you want the whole workflow to live in the DB layer

## GitHub Preparation Checklist

Before pushing:

- remove or replace hardcoded DB credentials
- add screenshots if you want a better project page
- verify Dialogflow webhook settings
- decide whether to include `ngrok.exe` and the zip file in the repository

## License

Add the license you want before publishing, for example MIT.
