from datetime import datetime

import streamlit as st

from attribution_engine import calculate_kpis, process_orders
from ui import apply_theme, hero, page_steps, section_label, status_pill


apply_theme()
results, campaigns = process_orders()
kpis = calculate_kpis(results)

hero(
    "Review how orders were matched",
    "Focus on orders requiring attention while keeping technical tracking signals out of the customer experience.",
    "Attribution Quality",
    icon="🔗",
)

page_steps([
    ("🔎", "Detect", "Check campaign IDs and promo-code signals."),
    ("🧩", "Classify", "Separate matched, unattributed, and review orders."),
    ("✅", "Verify", "Resolve uncertain records before using the results."),
])

if not results:
    st.info("No demonstration orders are available yet.")
    st.stop()

section_label("Attribution summary")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Orders", kpis["total_orders"])
k2.metric("Matched", kpis["matched_orders"])
k3.metric("Unattributed", kpis["unattributed_orders"])
k4.metric("Needs Review", kpis["needs_review"])

d1, d2 = st.columns(2)
d1.metric("Attribution Coverage", f"{kpis['coverage']:.1f}%")
d2.metric("Matched Revenue", f"${kpis['matched_revenue']:,.2f}")

st.markdown("### Orders")
filter_col, count_col = st.columns([3, 1])
with filter_col:
    selected_filter = st.selectbox(
        "Filter by attribution status",
        ["All", "Matched", "Unattributed", "Needs Review"],
    )
with count_col:
    filtered_results = (
        results
        if selected_filter == "All"
        else [row for row in results if row["status"] == selected_filter]
    )
    st.metric("Visible Orders", len(filtered_results))

if not filtered_results:
    st.info("No orders are available in this category.")
else:
    header = st.columns([1.5, 1.35, 2.4, 1.1, 1.7, 1.4])
    header[0].write("**Order**")
    header[1].write("**Date**")
    header[2].write("**Items**")
    header[3].write("**Revenue**")
    header[4].write("**Campaign**")
    header[5].write("**Status**")
    st.divider()

    for order in filtered_results:
        row = st.columns([1.5, 1.35, 2.4, 1.1, 1.7, 1.4])
        row[0].write(order["order_id"])

        raw_date = order.get("order_date") or ""
        try:
            formatted_date = datetime.fromisoformat(
                raw_date.replace("Z", "+00:00")
            ).strftime("%b %d, %Y")
        except ValueError:
            formatted_date = "—"

        row[1].write(formatted_date)
        row[2].write(order.get("items") or "—")
        row[3].write(f"${order['revenue']:,.2f}")
        row[4].write(
            order["campaign_name"]
            if order["status"] == "Matched"
            else "—"
        )
        row[5].markdown(status_pill(order["status"]), unsafe_allow_html=True)
        st.divider()

with st.expander("How order matching works"):
    st.markdown(
        """
        - **Matched:** A campaign ID or valid promo code connects the order to a saved campaign.
        - **Unattributed:** The order contains no campaign ID or promo code.
        - **Needs Review:** A tracking value is present but cannot be verified, or signals conflict.

        Attribution indicates an association between marketing and a purchase. It does not prove that marketing caused the purchase.
        """
    )
