# Spend & Pray — HotVile demo

A classroom storefront and marketing-attribution workspace. Demo v0.4 adds a compact UI, shared reporting filters, and an evidence-based order-review workflow.

## Run locally

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m streamlit run app.py
```

## Workflows

- Customers can filter six sauces by heat, adjust quantities, validate an optional promo code, and place a fictional order with a required name and optional email. No money is collected and no confirmation email is sent. The saved order links the entered name to the unique order ID, recorded cart quantities, and order total.
- Owners can create campaign links and QR codes. Copy links with the copy control in the link's code box. Links generated locally work only on the same computer.
- The dashboard's channels, campaigns, statuses, and optional UTC order-date range apply to all KPIs and charts. Unknown channel and No verified campaign preserve visibility into attribution gaps.
- Planned budgets are full campaign allocations. They are not actual spending, not prorated by selected order dates, and not a profit measure. Zero-budget ROAS is N/A.
- In Order Matching, expand an order, record evidence, and assign a campaign, keep it unattributed, or restore automatic matching. The append-only `data/attribution_reviews.csv` history preserves original tracking records. The latest review takes effect in reports.
- Malformed order dates stay in all-date totals and are disclosed; date-limited reports and trends exclude them. Single-date revenue is shown as a bar, with no invented trend.

## Development

```powershell
.venv/Scripts/python -m unittest discover -s tests
```

`catalog.py` defines products, `dashboard_charts.py` defines revenue visuals, `reporting.py` defines report selection, and `data_store.py` serializes same-process CSV writes. Stable order IDs prevent duplicate writes for retries using the same checkout token. Exact repeated campaign details are rejected.

## Demo boundaries

Owner/customer switching is a demo experience selector, not authentication. CSV data is local to the running instance; locks cover one Python process, not multiple replicas. Keep private data out of a public demo. Production use requires owner authentication, an external transactional database, and a deployment/storage plan. Product sizes, ingredient lists, and allergen claims must come from verified product information and are not invented here.

The old `spend-and-pray-demo.streamlit.app` deployment uses Leya-Varghese's repository. Pushing to `punnamkoteswaravaraprasad-source/spend-and-pray-prototype` does not update that deployment.
