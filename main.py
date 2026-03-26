from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from db_helper import (
    create_order_with_items,
    find_matching_food_items,
    get_food_item_details,
    get_order_status,
    get_order_total,
)

app = FastAPI()
completed_orders = {}


# -------- EXTRACT SESSION ID -------- #

def extract_session_id(output_contexts):

    if not output_contexts:
        return None

    context_name = output_contexts[0]["name"]
    parts = context_name.split("/")

    if "sessions" in parts:
        return parts[parts.index("sessions") + 1]

    return None


def get_session_order_state(output_contexts, session_id):

    session_orders = {}
    current_order = {}

    for context in output_contexts:
        if context.get("name", "").endswith("/contexts/ongoing-order"):
            context_parameters = context.get("parameters", {})
            session_orders = dict(context_parameters.get("session_orders", {}))
            current_order = dict(session_orders.get(session_id, {})) if session_id else {}
            break

    return session_orders, current_order


def build_order_context(session_id, session_orders, lifespan_count=5):

    return [
        {
            "name": f"projects/zuzu-qlyg/agent/sessions/{session_id}/contexts/ongoing-order",
            "lifespanCount": lifespan_count,
            "parameters": {
                "session_orders": session_orders
            }
        }
    ]


def build_order_summary(current_order):

    if not current_order:
        return "Your order is now empty."

    order_summary = ", ".join(
        f"{quantity} x {item}" for item, quantity in current_order.items()
    )
    return f"You have this order: {order_summary}. Anything else you need?"


# -------- TRACK ORDER FUNCTION -------- #

def track_order(parameters, session_id):

    order_id = parameters.get("number")

    if not order_id:
        return {}

    status = get_order_status(order_id)

    # Send status as parameter back to Dialogflow
    return {
        "outputContexts": [
            {
                "name": f"projects/zuzu-qlyg/agent/sessions/{session_id}/contexts/ongoing-tracking",
                "lifespanCount": 5,
                "parameters": {
                    "order_id": order_id,
                    "order_status": status
                }
            }
        ]
    }
# -------- ADD ORDER FUNCTION -------- #

def add_to_order(parameters, session_id, output_contexts):

    numbers = parameters.get("number", [])
    food_items = parameters.get("Food-Item") or parameters.get("food-item", [])

    if not isinstance(numbers, list):
        numbers = [numbers] if numbers is not None else []

    if not isinstance(food_items, list):
        food_items = [food_items] if food_items is not None else []

    session_orders, current_order = get_session_order_state(output_contexts, session_id)

    if len(numbers) < len(food_items):
        return {
            "fulfillmentText": "Please specify the quantity."
        }

    resolved_items = []

    for item in food_items:
        matches = find_matching_food_items(item)

        if not matches:
            return {
                "fulfillmentText": f"I could not find {item} on the menu."
            }

        if len(matches) > 1:
            options = " or ".join(matches)
            return {
                "fulfillmentText": f"I found multiple matches for {item}. Did you mean {options}?"
            }

        resolved_items.append(matches[0])

    for quantity, item in zip(numbers, resolved_items):
        current_order[item] = current_order.get(item, 0) + int(quantity)

    if session_id:
        session_orders[session_id] = current_order

    return {
        "fulfillmentText": build_order_summary(current_order),
        "outputContexts": build_order_context(session_id, session_orders)
    }


def remove_from_order(parameters, session_id, output_contexts):

    numbers = parameters.get("number", [])
    food_items = parameters.get("Food-Item") or parameters.get("food-item", [])

    if not isinstance(numbers, list):
        numbers = [numbers] if numbers is not None else []

    if not isinstance(food_items, list):
        food_items = [food_items] if food_items is not None else []

    session_orders, current_order = get_session_order_state(output_contexts, session_id)

    if not current_order:
        return {
            "fulfillmentText": "I could not find any active order to update."
        }

    if len(numbers) < len(food_items):
        return {
            "fulfillmentText": "Please specify the quantity to remove."
        }

    resolved_items = []

    for item in food_items:
        matches = find_matching_food_items(item)

        if not matches:
            return {
                "fulfillmentText": f"I could not find {item} on the menu."
            }

        if len(matches) > 1:
            options = " or ".join(matches)
            return {
                "fulfillmentText": f"I found multiple matches for {item}. Did you mean {options}?"
            }

        resolved_items.append(matches[0])

    for quantity, item in zip(numbers, resolved_items):
        remove_qty = int(quantity)
        existing_qty = int(current_order.get(item, 0))

        if existing_qty == 0:
            return {
                "fulfillmentText": f"{item} is not in your current order."
            }

        if remove_qty > existing_qty:
            return {
                "fulfillmentText": f"You only have {existing_qty} x {item} in your order."
            }

        remaining_qty = existing_qty - remove_qty

        if remaining_qty > 0:
            current_order[item] = remaining_qty
        else:
            del current_order[item]

    if session_id:
        if current_order:
            session_orders[session_id] = current_order
            output_contexts = build_order_context(session_id, session_orders)
        else:
            session_orders.pop(session_id, None)
            output_contexts = build_order_context(session_id, session_orders, lifespan_count=0)
    else:
        output_contexts = []

    return {
        "fulfillmentText": build_order_summary(current_order),
        "outputContexts": output_contexts
    }


def resolve_order_items(order_map):

    resolved_order = {}

    for item_name, quantity in order_map.items():
        matches = find_matching_food_items(item_name)

        if not matches:
            raise ValueError(f"I could not find {item_name} on the menu.")

        if len(matches) > 1:
            options = " or ".join(matches)
            raise ValueError(f"I found multiple matches for {item_name}. Did you mean {options}?")

        resolved_order[matches[0]] = quantity

    return resolved_order


def complete_order(parameters, output_contexts):

    session_id = extract_session_id(output_contexts)
    session_orders, order_map = get_session_order_state(output_contexts, session_id)

    if not order_map:
        return {
            "fulfillmentText": "I could not find any active order to complete."
        }

    try:
        # Resolve partial names like "lassi" before pricing or persistence.
        order_map = resolve_order_items(order_map)
        total_price = get_order_total(order_map)
    except ValueError as exc:
        return {
            "fulfillmentText": str(exc)
        }

    try:
        # The database now owns order ID allocation and commits the full order atomically.
        order_id = create_order_with_items(order_map)
    except Exception:
        return {
            "fulfillmentText": "I could not place your order right now. Please try again."
        }

    items_with_ids = []

    for item_name, quantity in order_map.items():
        item_details = get_food_item_details(item_name)

        if item_details is None:
            return {
                "fulfillmentText": f"I could not fetch item details for {item_name}."
            }

        line_total = round(int(quantity) * item_details["price"], 2)
        items_with_ids.append({
            "order_id": order_id,
            "item_id": item_details["item_id"],
            "quantity": int(quantity),
            "total_price": line_total
        })

    completed_order = {
        "order_id": order_id,
        "items": items_with_ids,
        "total_price": total_price
    }
    completed_orders[order_id] = completed_order

    if session_id and session_id in session_orders:
        del session_orders[session_id]

    return {
        "fulfillmentText": f"Your order has been placed. Your order ID is {order_id}. Total price is {total_price:.2f}.",
        "outputContexts": build_order_context(session_id, session_orders, lifespan_count=0)
    }


# -------- WEBHOOK -------- #

@app.post("/webhook")
async def webhook(request: Request):

    body = await request.json()

    query_result = body.get("queryResult", {})
    intent = query_result.get("intent", {}).get("displayName")
    parameters = query_result.get("parameters", {})
    output_contexts = query_result.get("outputContexts", [])
    session_id = extract_session_id(output_contexts)

    if intent == "Track.order":
        response = track_order(parameters, session_id)

    elif intent == "Order.add-context:ongoing-order":
        response = add_to_order(parameters, session_id, output_contexts)

    elif intent == "Order.remove-context:ongoing-order":
        response = remove_from_order(parameters, session_id, output_contexts)

    elif intent == "Order.complete":
        response = complete_order(parameters, output_contexts)

    else:
        response = {}

    return JSONResponse(content=response)
