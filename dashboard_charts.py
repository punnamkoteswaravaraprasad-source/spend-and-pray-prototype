"""Chart builders shared by the dashboard and its verification checks."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import plotly.graph_objects as go

from ui import BRAND_RED, chart_layout


def order_day(value):
    """Use UTC dates consistently; historical naive timestamps are treated as UTC."""
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc)
        return parsed.date()
    except (ValueError, TypeError):
        return None


def revenue_chart(rows, weekly=False):
    totals = defaultdict(float)
    invalid = 0
    for row in rows:
        day = order_day(row.get("order_date"))
        if day is None:
            invalid += 1
            continue
        if weekly:
            day -= timedelta(days=day.weekday())
        totals[day] += row["revenue"]
    days = sorted(totals)
    fig = go.Figure()
    # Explicit category dates prevent Plotly's single-date millisecond tick range.
    x = [day.isoformat() for day in days]
    common = dict(x=x, y=[totals[d] for d in days],
                  hovertemplate="%{x}<br>Revenue: $%{y:,.2f}<extra></extra>")
    if len(days) == 1:
        fig.add_trace(go.Bar(**common, marker_color=BRAND_RED,
                             text=[f"${totals[days[0]]:,.2f}"], textposition="outside",
                             cliponaxis=False))
    elif days:
        fig.add_trace(go.Scatter(**common, mode="lines+markers",
                                 line=dict(color=BRAND_RED, width=3), marker_size=9))
    fig.update_layout(**chart_layout("Revenue Over Time", "Revenue ($)", 430))
    # Numeric day offsets keep gaps between observed dates proportional without
    # adding fictional zero-revenue dates. Tick text never includes time values.
    if len(days) > 1:
        offsets = [(d - days[0]).days for d in days]
        fig.data[0].x = offsets
        fig.data[0].customdata = x
        fig.data[0].hovertemplate = "%{customdata}<br>Revenue: $%{y:,.2f}<extra></extra>"
        indices = sorted(set(round(i * (len(days) - 1) / min(3, len(days) - 1)) for i in range(min(4, len(days)))))
        fig.update_xaxes(type="linear", tickmode="array", tickvals=[offsets[i] for i in indices],
                         ticktext=[days[i].strftime("%b %d<br>%Y") for i in indices])
    else:
        fig.update_xaxes(type="category", tickmode="array", tickvals=x,
                         ticktext=[d.strftime("%b %d<br>%Y") for d in days])
    fig.update_xaxes(title_text="Date", title_standoff=20)
    fig.update_yaxes(type="linear", tickprefix="$", tickformat=",.2f", rangemode="tozero")
    if len(days) == 1 and totals[days[0]] >= 0:
        fig.update_yaxes(range=[0, totals[days[0]] * 1.25 or 1])
    period = "week" if weekly else "date"
    note = (f"Only one {period} is available for this selection; the bar shows its total revenue, not a trend."
            if len(days) == 1 else f"Actual {'weekly (Monday start)' if weekly else 'daily'} totals, grouped by UTC date. Only observed dates are connected.")
    if not days:
        note = "No valid order dates are available for this selection."
    if invalid:
        note += f" {invalid} order(s) excluded because their dates are missing or invalid."
    return fig, note
