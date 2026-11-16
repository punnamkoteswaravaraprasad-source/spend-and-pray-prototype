from collections import defaultdict
from dashboard_charts import order_day, revenue_chart

import plotly.graph_objects as go
import streamlit as st

from attribution_engine import calculate_kpis, process_orders
from ui import (
    BRAND_GOLD,
    BRAND_GREEN,
    BRAND_ORANGE,
    BRAND_RED,
    apply_theme,
    chart_layout,
    hero,
    page_steps,
    section_label,
)


apply_theme()

results, campaigns = process_orders()

hero(
    "Marketing performance at a glance",
    "Compare channels and campaigns, understand attribution coverage, and use available evidence to guide the next budget decision.",
    "Founder Decision Dashboard",
    icon="📊",
)

page_steps([
    ("💰", "Measure", "Review revenue, orders, coverage, and estimated ROAS."),
    ("⚖️", "Compare", "Contrast channels, campaigns, budgets, and results."),
    ("🧭", "Decide", "Use the evidence and tracking gaps to guide spending."),
])

if not results:
    st.info("Place at least one demonstration order to populate the dashboard.")
    st.stop()

kpis = calculate_kpis(results)

total_budget = 0.0
for campaign in campaigns:
    try:
        total_budget += float(campaign.get("budget") or 0)
    except (ValueError, TypeError):
        pass

budget_roas = (
    kpis["matched_revenue"] / total_budget
    if total_budget > 0
    else None
)

channel_summary = defaultdict(lambda: {"orders": 0, "revenue": 0.0})
campaign_summary = defaultdict(lambda: {"orders": 0, "revenue": 0.0})

for row in results:
    if row["status"] != "Matched":
        continue
    channel_summary[row["channel"]]["orders"] += 1
    channel_summary[row["channel"]]["revenue"] += row["revenue"]
    campaign_summary[row["campaign_name"]]["orders"] += 1
    campaign_summary[row["campaign_name"]]["revenue"] += row["revenue"]

campaign_budget = {}
campaign_channel = {}
for campaign in campaigns:
    name = campaign.get("campaign_name") or "Unnamed Campaign"
    campaign_channel[name] = campaign.get("channel") or "Unknown"
    try:
        campaign_budget[name] = float(campaign.get("budget") or 0)
    except (ValueError, TypeError):
        campaign_budget[name] = 0.0

best_channel = "No matched channel"
if channel_summary:
    best_channel = max(
        channel_summary,
        key=lambda channel: channel_summary[channel]["revenue"],
    )


section_label("Primary business KPIs")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"${kpis['total_revenue']:,.2f}")
k2.metric("Total Orders", kpis["total_orders"])
k3.metric("Attribution Coverage", f"{kpis['coverage']:.1f}%")
k4.metric(
    "Budget-Based ROAS",
    f"{budget_roas:.2f}x" if budget_roas is not None else "N/A",
)

with st.expander("How to interpret these KPIs"):
    st.write(
        "**Attribution coverage** is the percentage of orders matched to a saved campaign. "
        "**Budget-based ROAS** divides matched revenue by the campaign budgets entered in the prototype. "
        "It is an estimate and not confirmed channel profit."
    )

section_label("Diagnostic KPIs")
s1, s2, s3, s4 = st.columns(4)
s1.metric("Matched Revenue", f"${kpis['matched_revenue']:,.2f}")
s2.metric("Average Order Value", f"${kpis['average_order_value']:,.2f}")
s3.metric("Best Channel", best_channel)
s4.metric("Needs Review", kpis["needs_review"])


st.markdown("### Compare marketing channels")
available_channels = sorted(channel_summary.keys())
selected_channels = st.multiselect(
    "Channels included in comparison",
    options=available_channels,
    default=available_channels,
)

filtered_channels = [
    channel for channel in available_channels if channel in selected_channels
]

left_chart, right_chart = st.columns(2)

with left_chart:
    revenue_fig = go.Figure(
        go.Bar(
            x=filtered_channels,
            y=[channel_summary[channel]["revenue"] for channel in filtered_channels],
            marker_color=BRAND_RED,
            text=[
                f"${channel_summary[channel]['revenue']:,.0f}"
                for channel in filtered_channels
            ],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{x}<br>Revenue: $%{y:,.2f}<extra></extra>",
        )
    )
    revenue_fig.update_layout(
        **chart_layout("Matched Revenue by Channel", "Revenue ($)")
    )
    revenue_fig.update_xaxes(title_text="Channel")
    st.plotly_chart(revenue_fig, width="stretch", theme=None)

with right_chart:
    orders_fig = go.Figure(
        go.Bar(
            x=filtered_channels,
            y=[channel_summary[channel]["orders"] for channel in filtered_channels],
            marker_color=BRAND_ORANGE,
            text=[channel_summary[channel]["orders"] for channel in filtered_channels],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{x}<br>Orders: %{y}<extra></extra>",
        )
    )
    orders_fig.update_layout(
        **chart_layout("Matched Orders by Channel", "Orders")
    )
    orders_fig.update_xaxes(title_text="Channel")
    st.plotly_chart(orders_fig, width="stretch", theme=None)


st.markdown("### Compare spending and results")
campaign_names = sorted(
    set(campaign_budget.keys()) | set(campaign_summary.keys())
)

budget_revenue_fig = go.Figure()
budget_revenue_fig.add_trace(
    go.Bar(
        name="Campaign Budget",
        x=campaign_names,
        y=[campaign_budget.get(name, 0) for name in campaign_names],
        marker_color=BRAND_GOLD,
    )
)
budget_revenue_fig.add_trace(
    go.Bar(
        name="Matched Revenue",
        x=campaign_names,
        y=[campaign_summary[name]["revenue"] for name in campaign_names],
        marker_color=BRAND_RED,
    )
)
budget_revenue_fig.update_layout(
    barmode="group",
    **chart_layout("Campaign Budget vs Matched Revenue", "Amount ($)", 410),
)
budget_revenue_fig.update_xaxes(title_text="Campaign")
st.plotly_chart(budget_revenue_fig, width="stretch", theme=None)

campaign_roas = []
for name in campaign_names:
    budget = campaign_budget.get(name, 0)
    revenue = campaign_summary[name]["revenue"]
    campaign_roas.append(revenue / budget if budget > 0 else 0)

roas_fig = go.Figure(
    go.Bar(
        x=campaign_names,
        y=campaign_roas,
        marker_color=[
            BRAND_GREEN if value >= 1 else BRAND_ORANGE
            for value in campaign_roas
        ],
        text=[f"{value:.2f}x" for value in campaign_roas],
        textposition="outside",
            cliponaxis=False,
        hovertemplate="%{x}<br>Estimated ROAS: %{y:.2f}x<extra></extra>",
    )
)
roas_fig.add_hline(
    y=1,
    line_dash="dash",
    line_color="#6f5b50",
    annotation_text="1.0x reference",
)
roas_fig.update_layout(
    **chart_layout("Estimated ROAS by Campaign", "Revenue per Budget Dollar")
)
roas_fig.update_xaxes(title_text="Campaign")
st.plotly_chart(roas_fig, width="stretch", theme=None)


st.markdown("### Tracking Quality and Sales Patterns")
st.caption("These filters apply to both charts below. Other dashboard comparisons retain their own selection.")
statuses = ["Matched", "Unattributed", "Needs Review"]
selected_statuses = st.multiselect("Attribution statuses", statuses, default=statuses)
valid_days = sorted({order_day(row.get("order_date")) for row in results} - {None})
date_range = st.date_input("Order date range (UTC)", value=(valid_days[0], valid_days[-1])) if valid_days else ()
weekly = st.selectbox("Revenue grouping", ["Daily", "Weekly"]) == "Weekly"
filtered = [row for row in results if row["status"] in selected_statuses]
if len(date_range) == 2:
    filtered = [row for row in filtered if order_day(row.get("order_date")) is not None
                and date_range[0] <= order_day(row.get("order_date")) <= date_range[1]]
elif valid_days:
    st.info("Choose both a start and end date to apply the date filter.")
invalid_dates = sum(order_day(row.get("order_date")) is None for row in results)
if invalid_dates:
    st.caption(f"{invalid_dates} order(s) have missing or invalid dates and cannot be included in a date range.")

# Full-width charts remain readable on tablets and narrow screens.
st.markdown("#### Tracking Quality")
if filtered:
    counts = [sum(row["status"] == status for row in filtered) for status in statuses]
    status_fig = go.Figure(go.Bar(
        x=counts, y=statuses, orientation="h", marker_color=[BRAND_GREEN, "#687587", BRAND_GOLD],
        text=counts, textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x} orders<extra></extra>",
    ))
    status_fig.update_layout(**chart_layout("Attribution Status", height=410))
    status_fig.update_layout(margin=dict(l=120, r=50, t=90, b=75), showlegend=False)
    status_fig.update_xaxes(title_text="Orders", rangemode="tozero", dtick=1,
                           range=[0, max(counts) * 1.25 or 1])
    status_fig.update_yaxes(title_text="Status", automargin=True, type="category")
    st.plotly_chart(status_fig, width="stretch", theme=None, config={"responsive": True})
else:
    st.info("No orders match the selected filters.")

st.markdown("#### Sales Patterns")
trend_fig, trend_note = revenue_chart(filtered, weekly)
if filtered:
    st.plotly_chart(trend_fig, width="stretch", theme=None, config={"responsive": True})
st.caption(trend_note)


if kpis["coverage"] < 70:
    st.markdown(
        f"""
        <div class="insight-box">
            <strong>Decision note:</strong> Attribution coverage is {kpis['coverage']:.1f}%.
            Review unattributed orders before shifting budget because the current channel comparison does not represent every purchase.
        </div>
        """,
        unsafe_allow_html=True,
    )
elif best_channel != "No matched channel":
    st.markdown(
        f"""
        <div class="insight-box">
            <strong>Decision note:</strong> {best_channel} currently has the highest matched revenue.
            Treat this as an association and validate it with additional orders before making a large budget change.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(
    "Budget-based ROAS uses entered campaign budgets and matched demonstration revenue. It does not represent confirmed profit or causal impact."
)
