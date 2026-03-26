# Zuzu Food Ordering Chatbot

Zuzu is a restaurant ordering chatbot built with FastAPI, Dialogflow, and MySQL. The project now includes both the backend webhook and a simple frontend landing page with an embedded Dialogflow Messenger chat widget.

## Features

- Conversational food ordering through Dialogflow
- Add items to an active order
- Remove items or reduce quantity from an active order
- Resolve partial menu names such as `lassi`
- Ask for clarification when a menu name matches multiple items
- Calculate totals from menu prices stored in MySQL
- Create orders atomically using stored procedures
- Track order status by `order_id`
- Static frontend page with menu, location, contact details, and chatbot widget

## Project Structure

- [main.py](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/main.py): FastAPI webhook and Dialogflow intent handlers
- [db_helper.py](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/db_helper.py): MySQL connection helpers and order persistence logic
- [stored_procedures.sql](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/stored_procedures.sql): MySQL procedure definitions
- [frontend/home.html](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/frontend/home.html): Static frontend entry page
- [frontend/styles.css](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/frontend/styles.css): Frontend styling
- [frontend/banner.jpg](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/frontend/banner.jpg): Hero banner image
- [frontend/menu1.jpg](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/frontend/menu1.jpg): Menu image 1
- [frontend/menu2.jpg](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/frontend/menu2.jpg): Menu image 2
- [frontend/menu3.jpg](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/frontend/menu3.jpg): Menu image 3
- [zuzu.html](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/zuzu.html): Dialogflow Messenger test page

## Tech Stack

- Python
- FastAPI
- MySQL
- Dialogflow
- HTML/CSS

## Backend Flow

### Add items

The `Order.add-context:ongoing-order` intent:

- reads `number` and `Food-Item`
- resolves the item against the menu
- accumulates quantity if the same item is added again
- stores the active order inside Dialogflow context

Example:

- `1 pizza` then `1 pizza` becomes `2 x Pizza`

### Remove items

The `Order.remove-context:ongoing-order` intent:

- reads `number` and `Food-Item`
- resolves the item against the menu
- subtracts the requested quantity from the active order
- removes the item entirely if the remaining quantity is `0`
- returns an error if the user tries to remove more than they currently have

Example:

- `2 x Pizza, 1 x Mango Lassi`
- `remove 1 pizza`
- result: `1 x Pizza, 1 x Mango Lassi`

### Complete order

The `Order.complete` intent:

- loads the active order from context
- resolves item names again before persistence
- calculates the total from `food_items`
- creates the order in MySQL
- inserts the order items in one transaction
- returns the generated order ID and total price

### Track order

The `Track.order` intent:

- reads the order ID
- looks up the status in `order_tracking`
- sends the result back through Dialogflow context

## Database Notes

The backend expects these main tables:

- `food_items`
- `orders`
- `order_tracking`

`order_tracking.order_id` should be `AUTO_INCREMENT`, so concurrent order creation does not rely on Python-side ID generation.

Stored procedures in [stored_procedures.sql](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/stored_procedures.sql):

- `create_order_entry`
- `insert_order_item`

## Frontend

The frontend lives in [frontend/home.html](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/frontend/home.html). It includes:

- navigation links
- a restaurant banner
- menu image gallery
- location and contact sections
- Dialogflow Messenger embedded directly on the page

The chat widget is configured with the Dialogflow agent ID already present in the HTML.

## Setup

### 1. Install backend dependencies

```bash
pip install fastapi uvicorn mysql-connector-python
```

### 2. Configure MySQL connection

Update [db_helper.py](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/db_helper.py) with your local database credentials.

### 3. Apply stored procedures

Run [stored_procedures.sql](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/stored_procedures.sql) in your MySQL database.

### 4. Start the backend

```bash
uvicorn main:app --reload
```

### 5. Expose the webhook if needed

```bash
ngrok http 8000
```

Then configure Dialogflow webhook fulfillment to:

```text
https://your-public-url/webhook
```

### 6. Run the frontend

Open [frontend/home.html](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/frontend/home.html) in a browser, or serve the folder with a static server.

Example:

```bash
python -m http.server 5500
```

Then open:

```text
http://localhost:5500/frontend/home.html
```

## Dialogflow Intents Used

- `Order.add-context:ongoing-order`
- `Order.remove-context:ongoing-order`
- `Order.complete`
- `Track.order`

## Current Limitations

- Active order state still depends on Dialogflow context
- Database credentials are hardcoded in [db_helper.py](/C:/Users/TUF%20GAMING/Desktop/AI/ZUZU/db_helper.py)
- The frontend is static and not connected to the backend except through Dialogflow Messenger
- No automated tests or load testing are included yet

## Next Improvements

- move DB credentials to environment variables
- add connection pooling
- persist active carts outside Dialogflow context
- add automated tests for add, remove, and complete order flows
- improve frontend styling and responsiveness
- deploy frontend and backend separately for production

## License

Add the license you want before publishing, for example MIT.
