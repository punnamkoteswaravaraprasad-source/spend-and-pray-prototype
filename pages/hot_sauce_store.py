import csv
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from ui import apply_theme, hero, image_data_uri, page_steps, section_label


apply_theme()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
ORDERS_FILE = DATA_DIR / "demo_orders.csv"
CAMPAIGNS_FILE = DATA_DIR / "campaigns.csv"

ORDER_FIELDS = [
    "order_id",
    "order_date",
    "customer_name",
    "customer_email",
    "items",
    "order_total",
    "promo_code",
    "campaign_id",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "match_status",
]

PRODUCTS = [
    {
        "id": 1,
        "name": "Classic Red",
        "price": 8.99,
        "heat": "Medium",
        "emoji": "🌶️",
        "image": "images/classic-red-v2.png",
        "description": "A balanced everyday sauce with red chili, garlic, and a bright vinegar finish.",
    },
    {
        "id": 2,
        "name": "Mango Habanero",
        "price": 10.99,
        "heat": "Hot",
        "emoji": "🥭",
        "image": "images/mango-habanero-v2.png",
        "description": "Sweet mango up front with a bold habanero finish for serious heat lovers.",
    },
    {
        "id": 3,
        "name": "Smoky Chipotle",
        "price": 9.99,
        "heat": "Mild",
        "emoji": "🔥",
        "image": "images/smoky-chipotle-v2.png",
        "description": "Smoked peppers and warm spices create a rich, mellow sauce for tacos and grilling.",
    },
]


def load_campaigns():
    if not CAMPAIGNS_FILE.exists():
        return []
    with open(CAMPAIGNS_FILE, "r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def validate_promo_code(code):
    normalized = code.strip().upper()
    if not normalized:
        return True
    return any(
        normalized == (campaign.get("promo_code") or "").strip().upper()
        for campaign in load_campaigns()
    )


def save_order(customer_name, customer_email, promo_code, total):
    tracking = st.session_state.get("campaign_tracking", {})
    order_id = "ORD-" + uuid.uuid4().hex[:8].upper()

    cart_items = []
    for product in PRODUCTS:
        quantity = st.session_state.cart.get(product["id"], 0)
        if quantity > 0:
            cart_items.append(f"{product['name']} x{quantity}")

    order = {
        "order_id": order_id,
        "order_date": datetime.now(timezone.utc).isoformat(),
        "customer_name": customer_name.strip(),
        "customer_email": customer_email.strip(),
        "items": "; ".join(cart_items),
        "order_total": round(total, 2),
        "promo_code": promo_code.strip().upper(),
        "campaign_id": tracking.get("campaign_id", ""),
        "utm_source": tracking.get("utm_source", ""),
        "utm_medium": tracking.get("utm_medium", ""),
        "utm_campaign": tracking.get("utm_campaign", ""),
        "match_status": "Pending",
    }

    file_exists = ORDERS_FILE.exists()
    with open(ORDERS_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=ORDER_FIELDS)
        if not file_exists or ORDERS_FILE.stat().st_size == 0:
            writer.writeheader()
        writer.writerow(order)

    return order


params = st.query_params
if "campaign_tracking" not in st.session_state:
    st.session_state.campaign_tracking = {}

for key in ["campaign_id", "utm_source", "utm_medium", "utm_campaign"]:
    if key in params:
        st.session_state.campaign_tracking[key] = params[key]

if "cart" not in st.session_state:
    st.session_state.cart = {}


hero(
    "Fire, flavor, and a sauce for every table",
    "Explore small-batch HotVile sauces, choose your heat, and place a fictional demonstration order.",
    "HotVile Hot Sauce Co.",
    icon="🛍️",
)

page_steps([
    ("🌶️", "Explore", "Filter sauces and compare flavor and heat."),
    ("🛒", "Build", "Add products and adjust quantities in the cart."),
    ("🎟️", "Complete", "Use an optional promo code and place a demo order."),
])

if st.session_state.get("last_order"):
    order = st.session_state.last_order
    with st.container(border=True):
        st.success("Your demonstration order was placed successfully.")
        r1, r2, r3 = st.columns(3)
        r1.metric("Order", order["order_id"])
        r2.metric("Items", len(order["items"].split("; ")))
        r3.metric("Total", f"${order['order_total']:,.2f}")
        st.caption("No real payment was collected. This order supports the attribution demonstration.")
        if st.button("Start a New Order"):
            st.session_state.last_order = None
            st.rerun()


section_label("Shop sauces")
filter_col, cart_col = st.columns([3, 1])
with filter_col:
    heat_filter = st.segmented_control(
        "Filter by heat level",
        options=["All", "Mild", "Medium", "Hot"],
        default="All",
    )
with cart_col:
    total_units = sum(st.session_state.cart.values())
    st.metric("Cart Items", total_units)

visible_products = [
    product
    for product in PRODUCTS
    if heat_filter in (None, "All") or product["heat"] == heat_filter
]

product_columns = st.columns(len(visible_products))
for column, product in zip(product_columns, visible_products):
    heat_class = f"heat-{product['heat'].lower()}"
    product_image = image_data_uri(product["image"])
    with column:
        st.markdown(
            f"""
            <div class="product-card">
                <div class="product-photo-wrap">
                    <img class="product-photo" src="{product_image}" alt="{product['name']} hot sauce bottle">
                </div>
                <span class="heat-pill {heat_class}">{product['heat']} heat</span>
                <h3>{product['name']}</h3>
                <p>{product['description']}</p>
                <h2>${product['price']:.2f}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Add to Cart",
            key=f"add_{product['id']}",
            type="primary",
            width="stretch",
        ):
            product_id = product["id"]
            st.session_state.cart[product_id] = (
                st.session_state.cart.get(product_id, 0) + 1
            )
            st.rerun()


st.markdown("### 🛒 Your cart")

if not st.session_state.cart:
    with st.container(border=True):
        st.info("Your cart is empty. Add a sauce to begin your demonstration order.")
else:
    total = 0.0
    for product in PRODUCTS:
        quantity = st.session_state.cart.get(product["id"], 0)
        if quantity <= 0:
            continue

        subtotal = quantity * product["price"]
        total += subtotal
        name_col, minus_col, quantity_col, plus_col, price_col, remove_col = st.columns(
            [3, 0.6, 0.7, 0.6, 1.2, 1]
        )
        name_col.write(f"**{product['emoji']} {product['name']}**")
        if minus_col.button("−", key=f"minus_{product['id']}"):
            new_quantity = quantity - 1
            if new_quantity <= 0:
                st.session_state.cart.pop(product["id"], None)
            else:
                st.session_state.cart[product["id"]] = new_quantity
            st.rerun()
        quantity_col.markdown(f"### {quantity}")
        if plus_col.button("+", key=f"plus_{product['id']}"):
            st.session_state.cart[product["id"]] = quantity + 1
            st.rerun()
        price_col.write(f"**${subtotal:,.2f}**")
        if remove_col.button("Remove", key=f"remove_{product['id']}"):
            st.session_state.cart.pop(product["id"], None)
            st.rerun()

    st.divider()
    total_col, clear_col = st.columns([3, 1])
    total_col.markdown(f"## Order total: ${total:,.2f}")
    if clear_col.button("Clear Cart", width="stretch"):
        st.session_state.cart = {}
        st.rerun()

    st.markdown("### Checkout")
    st.caption("Only the information required for this classroom demonstration is requested.")

    with st.form("checkout_form"):
        customer_name = st.text_input("Name", placeholder="Demo Customer")
        customer_email = st.text_input("Email", placeholder="demo@example.com")
        promo_code = st.text_input(
            "Promo Code (optional)",
            placeholder="Enter a campaign promo code",
        )
        place_order = st.form_submit_button(
            "Place Demonstration Order",
            type="primary",
            width="stretch",
        )

        if place_order:
            if not customer_name.strip() or not customer_email.strip():
                st.error("Enter a name and email to continue.")
            elif "@" not in customer_email:
                st.error("Enter a valid demonstration email address.")
            elif not validate_promo_code(promo_code):
                st.error("That promo code was not recognized. Check the code or leave it blank.")
            else:
                order = save_order(
                    customer_name,
                    customer_email,
                    promo_code,
                    total,
                )
                st.session_state.last_order = order
                st.session_state.cart = {}
                st.rerun()

st.caption("Academic prototype • Demonstration orders only • No payment is collected")
