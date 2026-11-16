import csv
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
ORDERS_FILE = DATA_DIR / "demo_orders.csv"
CAMPAIGNS_FILE = DATA_DIR / "campaigns.csv"


def load_csv(file_path):
    if not file_path.exists():
        return []
    with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def match_order(order, campaigns):
    campaign_id = (order.get("campaign_id") or "").strip()
    promo_code = (order.get("promo_code") or "").strip().upper()

    id_match = None
    promo_match = None

    for campaign in campaigns:
        saved_id = (campaign.get("campaign_id") or "").strip()
        saved_promo = (campaign.get("promo_code") or "").strip().upper()

        if campaign_id and campaign_id == saved_id:
            id_match = campaign
        if promo_code and saved_promo and promo_code == saved_promo:
            promo_match = campaign

    if id_match and promo_match:
        if id_match["campaign_id"] != promo_match["campaign_id"]:
            return "Needs Review", None

    if id_match:
        return "Matched", id_match
    if promo_match:
        return "Matched", promo_match
    if campaign_id or promo_code:
        return "Needs Review", None
    return "Unattributed", None


def process_orders():
    orders = load_csv(ORDERS_FILE)
    campaigns = load_csv(CAMPAIGNS_FILE)
    results = []

    for order in orders:
        status, campaign = match_order(order, campaigns)
        try:
            revenue = float(order.get("order_total") or 0)
        except (ValueError, TypeError):
            revenue = 0.0

        results.append(
            {
                "order_id": order.get("order_id", ""),
                "order_date": order.get("order_date", ""),
                "items": order.get("items", ""),
                "revenue": revenue,
                "status": status,
                "campaign_id": (
                    campaign.get("campaign_id", "")
                    if campaign
                    else order.get("campaign_id", "")
                ),
                "campaign_name": (
                    campaign.get("campaign_name", "")
                    if campaign
                    else "Not verified"
                ),
                "channel": (
                    campaign.get("channel", "")
                    if campaign
                    else "Unknown"
                ),
            }
        )

    return results, campaigns


def calculate_kpis(results):
    total_orders = len(results)
    matched_orders = sum(1 for row in results if row["status"] == "Matched")
    unattributed_orders = sum(
        1 for row in results if row["status"] == "Unattributed"
    )
    needs_review = sum(
        1 for row in results if row["status"] == "Needs Review"
    )
    total_revenue = sum(row["revenue"] for row in results)
    matched_revenue = sum(
        row["revenue"] for row in results if row["status"] == "Matched"
    )
    coverage = matched_orders / total_orders * 100 if total_orders else 0
    average_order_value = total_revenue / total_orders if total_orders else 0

    return {
        "total_orders": total_orders,
        "matched_orders": matched_orders,
        "unattributed_orders": unattributed_orders,
        "needs_review": needs_review,
        "total_revenue": total_revenue,
        "matched_revenue": matched_revenue,
        "coverage": coverage,
        "average_order_value": average_order_value,
    }
