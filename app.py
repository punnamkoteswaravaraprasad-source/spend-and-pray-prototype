import csv
from pathlib import Path

import streamlit as st

from ui import apply_theme, hero, info_card, page_steps, section_label


st.set_page_config(
    page_title="Spend & Pray",
    page_icon="🌶️",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

DATA_DIR = Path(__file__).resolve().parent / "data"
ORDERS_FILE = DATA_DIR / "demo_orders.csv"
CAMPAIGNS_FILE = DATA_DIR / "campaigns.csv"


def load_csv(path):
    if not path.exists():
        return []
    with open(path, "r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "campaign_tracking" not in st.session_state:
    st.session_state.campaign_tracking = {}

params = st.query_params
campaign_keys = [
    "campaign_id",
    "utm_source",
    "utm_medium",
    "utm_campaign",
]

has_campaign_link = any(key in params for key in campaign_keys)

if has_campaign_link:
    incoming_tracking = {
        key: params.get(key, "")
        for key in campaign_keys
        if key in params
    }
    campaign_signature = tuple(
        incoming_tracking.get(key, "") for key in campaign_keys
    )

    if st.session_state.get("last_campaign_signature") != campaign_signature:
        st.session_state.user_role = "Customer"
        st.session_state.last_campaign_signature = campaign_signature

    st.session_state.campaign_tracking = incoming_tracking


def select_role(role):
    st.session_state.user_role = role
    st.rerun()


def change_role():
    st.session_state.user_role = None
    st.session_state.campaign_tracking = {}
    st.session_state.last_campaign_signature = None
    st.query_params.clear()
    st.rerun()


def business_owner_home():
    orders = load_csv(ORDERS_FILE)
    campaigns = load_csv(CAMPAIGNS_FILE)

    total_revenue = 0.0
    for order in orders:
        try:
            total_revenue += float(order.get("order_total") or 0)
        except (TypeError, ValueError):
            pass

    tracked_orders = sum(
        1 for order in orders
        if (order.get("campaign_id") or "").strip()
        or (order.get("promo_code") or "").strip()
    )
    coverage = tracked_orders / len(orders) * 100 if orders else 0

    hero(
        "Turn marketing activity into evidence",
        "Create trackable campaigns, connect customer orders, and compare performance before making the next budget decision.",
        "Business Owner Workspace",
        icon="📈",
    )

    page_steps([
        ("📣", "Track", "Create campaigns with reusable tracking assets."),
        ("🔗", "Connect", "Match customer orders to available signals."),
        ("📊", "Improve", "Compare performance before changing the budget."),
    ])

    section_label("Current snapshot")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Campaigns", len(campaigns))
    k2.metric("Demo Orders", len(orders))
    k3.metric("Total Revenue", f"${total_revenue:,.2f}")
    k4.metric("Tracking Coverage", f"{coverage:.1f}%")

    st.markdown("### How the prototype works")
    step1, step2, step3, step4, step5 = st.columns(5)
    with step1:
        info_card("📣", "1. Create", "Choose a channel, dates, and budget.")
    with step2:
        info_card("🔗", "2. Share", "Use the generated link, QR code, or promo code.")
    with step3:
        info_card("🛒", "3. Purchase", "A customer completes a demonstration order.")
    with step4:
        info_card("🧩", "4. Match", "The system evaluates available tracking signals.")
    with step5:
        info_card("📊", "5. Compare", "The founder reviews channels, campaigns, and gaps.")

    st.markdown("### Owner tools")
    left, middle, right = st.columns(3)
    with left:
        with st.container(border=True):
            st.subheader("📣 Create Campaign")
            st.write("Generate a campaign ID, trackable link, promo code, and QR code.")
            st.page_link(
                "pages/create_campaign.py",
                label="Open Campaign Builder",
                icon="📣",
                width="stretch",
            )
    with middle:
        with st.container(border=True):
            st.subheader("🔗 Order Matching")
            st.write("Review matched, unattributed, and conflicting orders.")
            st.page_link(
                "pages/order_matching.py",
                label="Review Attribution",
                icon="🔗",
                width="stretch",
            )
    with right:
        with st.container(border=True):
            st.subheader("📊 Marketing Dashboard")
            st.write("Compare revenue, orders, budgets, ROAS, and coverage.")
            st.page_link(
                "pages/marketing_dashboard.py",
                label="Open Dashboard",
                icon="📊",
                width="stretch",
            )

    if orders and coverage < 70:
        st.warning(
            "Tracking coverage is below 70%. Review unattributed orders before changing the marketing budget."
        )
    elif orders:
        st.success(
            "Most demonstration orders contain a usable tracking signal. Review channel comparisons in the dashboard."
        )
    else:
        st.info(
            "Start by creating a campaign, then open its tracking link and place a demonstration order."
        )

    st.caption(
        "Academic prototype • Demonstration transactions only • Associations do not prove causation"
    )


if st.session_state.user_role is None:
    hero(
        "Know what brings customers to your store",
        "Spend & Pray is a marketing attribution prototype for HotVile Hot Sauce Co. Select the experience you want to explore.",
        "HotVile Hot Sauce Co.",
        icon="🌶️",
    )

    owner_col, customer_col = st.columns(2, gap="large")

    with owner_col:
        with st.container(border=True, key="owner_role_card"):
            st.markdown(
                """
                <div class="role-visual">
                    <span class="role-icon">📈</span>
                    <div>
                        <p class="role-kicker">Plan • Track • Compare</p>
                        <h2 class="role-title">Business Owner</h2>
                    </div>
                </div>
                <p class="role-description">Create trackable campaigns, connect orders to available signals, and compare marketing performance before deciding where to spend next.</p>
                <div>
                    <span class="feature-chip">📣 Campaign builder</span>
                    <span class="feature-chip">🔗 Order matching</span>
                    <span class="feature-chip">📊 KPI dashboard</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Continue as Business Owner",
                type="primary",
                width="stretch",
            ):
                select_role("Business Owner")

    with customer_col:
        with st.container(border=True, key="customer_role_card"):
            st.markdown(
                """
                <div class="role-visual">
                    <span class="role-icon">🛍️</span>
                    <div>
                        <p class="role-kicker">Browse • Choose • Purchase</p>
                        <h2 class="role-title">Customer</h2>
                    </div>
                </div>
                <p class="role-description">Explore handcrafted sauces, filter by heat level, build a cart, and place a fictional order through a tracked customer journey.</p>
                <div>
                    <span class="feature-chip">🌶️ Product gallery</span>
                    <span class="feature-chip">🛒 Interactive cart</span>
                    <span class="feature-chip">🎟️ Promo codes</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Continue as Customer",
                width="stretch",
            ):
                select_role("Customer")

    with st.expander("✨ See how Spend & Pray turns marketing activity into evidence"):
        step_a, step_b, step_c = st.columns(3)
        with step_a:
            info_card("📣", "1. Launch", "The owner creates a campaign with a tracking link, QR code, or promo code.")
        with step_b:
            info_card("🛒", "2. Capture", "A customer visits the store and completes a demonstration purchase.")
        with step_c:
            info_card("📊", "3. Learn", "The dashboard compares available signals while clearly showing tracking gaps.")

    st.caption("Academic prototype • No account, real payment, or personal authentication is required.")

else:
    role = st.session_state.user_role

    with st.sidebar:
        st.markdown("### 🌶️ Spend & Pray")
        st.caption(f"Current experience: {role}")
        if st.button("Switch Experience", width="stretch"):
            change_role()

    if role == "Business Owner":
        pages = {
            "Business Owner": [
                st.Page(
                    business_owner_home,
                    title="Owner Overview",
                    icon="🏠",
                    default=True,
                ),
                st.Page(
                    "pages/create_campaign.py",
                    title="Create Campaign",
                    icon="📣",
                ),
                st.Page(
                    "pages/order_matching.py",
                    title="Order Matching",
                    icon="🔗",
                ),
                st.Page(
                    "pages/marketing_dashboard.py",
                    title="Marketing Dashboard",
                    icon="📊",
                ),
            ]
        }
    else:
        pages = {
            "Customer": [
                st.Page(
                    "pages/hot_sauce_store.py",
                    title="HotVile Store",
                    icon="🌶️",
                    url_path="hot_sauce_store",
                    default=True,
                )
            ]
        }

    navigation = st.navigation(pages)
    navigation.run()
