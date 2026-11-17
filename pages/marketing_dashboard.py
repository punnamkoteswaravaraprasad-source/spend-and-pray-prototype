from collections import defaultdict
import plotly.graph_objects as go
import streamlit as st
from attribution_engine import calculate_kpis, process_orders
from dashboard_charts import order_day, revenue_chart
from reporting import select_report, amount
from ui import apply_theme, hero, section_label, chart_layout, BRAND_RED, BRAND_ORANGE, BRAND_GOLD, BRAND_GREEN

apply_theme()
all_results, all_campaigns = process_orders()
hero('Marketing performance', 'Compare sales, planned budgets, and tracking quality using one shared selection.', 'Owner dashboard', icon='📊')
if not all_results:
    st.info('Place a demo order to start measuring performance.')
    st.stop()

with st.container(border=True):
    st.markdown('### Report filters')
    channels = sorted({r['channel'] for r in all_results} | {c.get('channel') or 'Unknown' for c in all_campaigns})
    chosen_channels = st.multiselect('Channels', channels, default=channels)
    campaign_map = {c['campaign_id']: c for c in all_campaigns}
    choices = list(campaign_map) + ['__unassigned__']
    chosen_campaigns = st.multiselect('Campaigns', choices, default=choices,
        format_func=lambda key: 'No verified campaign' if key == '__unassigned__' else f"{campaign_map[key]['campaign_name']} · {campaign_map[key].get('channel', 'Unknown')} · {key[-4:]}")
    statuses = ['Matched', 'Unattributed', 'Needs Review']
    chosen_statuses = st.multiselect('Attribution statuses', statuses, default=statuses)
    limit_dates = st.checkbox('Limit order dates', value=False)
    dates = None
    valid_days = sorted({order_day(r.get('order_date')) for r in all_results} - {None})
    if limit_dates and valid_days:
        selected_dates = st.date_input('Order dates (UTC)', (valid_days[0], valid_days[-1]))
        if len(selected_dates) != 2:
            st.info('Choose both a start and end date to run the report.')
            st.stop()
        dates = selected_dates
    elif limit_dates:
        st.warning('No valid order dates are available.')
        st.stop()
    weekly = st.selectbox('Revenue grouping', ['Daily', 'Weekly']) == 'Weekly'
    st.caption('All KPIs and charts use these filters. Unknown channel and No verified campaign include tracking gaps. Planned budgets are full allocations for selected campaigns, not prorated spending during the order-date range.')

results, campaigns = select_report(all_results, all_campaigns, chosen_channels, chosen_campaigns, chosen_statuses, dates)
kpis = calculate_kpis(results)
total_budget = sum(amount(c.get('budget')) for c in campaigns)
section_label('Sales')
a,b,c = st.columns(3)
a.metric('Revenue', f"${kpis['total_revenue']:,.2f}")
b.metric('Orders', kpis['total_orders'])
c.metric('Average order value', f"${kpis['average_order_value']:,.2f}")
section_label('Marketing')
a,b,c = st.columns(3)
a.metric('Matched revenue', f"${kpis['matched_revenue']:,.2f}")
b.metric('Planned campaign budget', f'${total_budget:,.2f}')
c.metric('Budget-based ROAS', f"{kpis['matched_revenue']/total_budget:.2f}x" if total_budget > 0 else 'N/A')
st.caption('ROAS here compares selected order revenue with full planned campaign budgets. Actual ad spend and profit are not recorded. Attribution shows association, not causation.')
section_label('Tracking quality')
a,b,c = st.columns(3)
a.metric('Attribution coverage', f"{kpis['coverage']:.1f}%")
b.metric('Unattributed orders', kpis['unattributed_orders'])
c.metric('Needs review', kpis['needs_review'])
if not results:
    st.info('No orders match this selection. Adjust the report filters; budget allocations may still exist for selected campaigns.')
    st.stop()

sales, comparison, tracking = st.tabs(['Sales patterns', 'Marketing comparisons', 'Tracking quality'])
with sales:
    fig,note = revenue_chart(results, weekly)
    st.plotly_chart(fig, width='stretch', theme=None)
    st.caption(note)
with comparison:
    summary = defaultdict(lambda: {'revenue':0.0, 'orders':0, 'budget':0.0})
    for row in results:
        if row['status']=='Matched':
            summary[row['channel']]['revenue'] += row['revenue']
            summary[row['channel']]['orders'] += 1
    for campaign in campaigns:
        summary[campaign.get('channel') or 'Unknown']['budget'] += amount(campaign.get('budget'))
    names = sorted(summary)
    if not names:
        st.info('No verified channel data for this selection.')
    else:
        # Full-width chart avoids squeezing labels into three tiny plots.
        fig = go.Figure()
        for name,key,color in [('Matched revenue','revenue',BRAND_RED),('Planned budget','budget',BRAND_GOLD)]:
            fig.add_trace(go.Bar(name=name, x=names, y=[summary[n][key] for n in names], marker_color=color,
                                 hovertemplate='%{x}<br>$%{y:,.2f}<extra>%{fullData.name}</extra>'))
        fig.update_layout(**chart_layout('Revenue and Planned Budget by Channel','Amount ($)',470), barmode='group')
        fig.update_xaxes(title_text='Channel')
        st.plotly_chart(fig,width='stretch',theme=None)
        st.dataframe([{'Channel':n,'Matched orders':summary[n]['orders'],'Matched revenue ($)':summary[n]['revenue'],'Planned budget ($)':summary[n]['budget']} for n in names],hide_index=True,width='stretch')
    campaign_revenue = defaultdict(float)
    for row in results:
        if row['status']=='Matched':
            campaign_revenue[row['campaign_id']] += row['revenue']
    st.markdown('#### Campaign performance')
    table=[]
    for campaign in campaigns:
        budget=amount(campaign.get('budget')); revenue=campaign_revenue[campaign['campaign_id']]
        table.append({'Campaign':campaign['campaign_name'], 'Channel':campaign.get('channel','Unknown'), 'Revenue ($)':round(revenue,2), 'Planned budget ($)':budget, 'Budget-based ROAS': f'{revenue/budget:.2f}x' if budget>0 else 'N/A'})
    if table:
        st.dataframe(table,hide_index=True,width='stretch')
        labels=[f"{c['campaign_name']} · {c['campaign_id'][-4:]}" for c in campaigns]
        fig=go.Figure()
        fig.add_trace(go.Bar(name='Matched revenue',x=labels,y=[campaign_revenue[c['campaign_id']] for c in campaigns],marker_color=BRAND_RED))
        fig.add_trace(go.Bar(name='Planned budget',x=labels,y=[amount(c.get('budget')) for c in campaigns],marker_color=BRAND_GOLD))
        fig.update_layout(**chart_layout('Campaign Revenue and Planned Budget','Amount ($)',470),barmode='group')
        fig.update_xaxes(title_text='Campaign')
        st.plotly_chart(fig,width='stretch',theme=None)
with tracking:
    counts=[sum(r['status']==s for r in results) for s in statuses]
    fig=go.Figure(go.Bar(x=counts,y=statuses,orientation='h',marker_color=[BRAND_GREEN,'#687587',BRAND_GOLD],text=counts,textposition='outside',cliponaxis=False))
    fig.update_layout(**chart_layout('Attribution Status',height=410),showlegend=False)
    fig.update_layout(margin=dict(l=125,r=45,t=80,b=75))
    fig.update_xaxes(title_text='Orders',dtick=1,range=[0,max(counts)*1.25 or 1])
    fig.update_yaxes(type='category',automargin=True)
    st.plotly_chart(fig,width='stretch',theme=None)
    st.link_button('Review and resolve order attribution', 'order_matching', icon='🔎')
    invalid=sum(order_day(r.get('order_date')) is None for r in results)
    if invalid:
        st.warning(f'{invalid} order(s) have missing or invalid dates. They remain in unfiltered KPIs but cannot appear in a date-limited report or revenue trend.')
