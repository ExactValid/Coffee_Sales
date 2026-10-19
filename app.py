"""Run with: uv run streamlit run app.py"""

from pathlib import Path
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from coffee_data import category_daily_units, forecast_categories, load_sales, make_stock_plan

TEAM_NAME = "team9"
DATA_PATH = Path(__file__).resolve().parent / "Coffee Shop Sales.csv"
TEAL, AMBER = "#27634F", "#A9662D"

st.set_page_config(page_title=f"{TEAM_NAME} · Manager’s desk", page_icon="☕", layout="wide")
st.markdown("""
<style>
 :root {
   --coffee-ink: var(--text-color, #253A31);
   --coffee-paper: var(--background-color, #F8F6F0);
   --coffee-surface: color-mix(in srgb, var(--coffee-paper) 96%, var(--coffee-ink) 4%);
   --coffee-muted: color-mix(in srgb, var(--coffee-ink) 76%, var(--coffee-paper));
   --coffee-line: color-mix(in srgb, var(--coffee-ink) 16%, var(--coffee-paper));
   --coffee-green: #27634F;
   --coffee-green-soft: color-mix(in srgb, #27634F 9%, var(--coffee-paper));
   --coffee-amber: #915626;
   --coffee-amber-soft: color-mix(in srgb, #A9662D 10%, var(--coffee-paper));
   --coffee-radius: 16px;
 }
 .stMainBlockContainer { max-width: 1210px; padding: 2.3rem 2.2rem 3rem; }
 [data-testid="stHeader"] { background: transparent; }
 [data-testid="stSidebar"] { border-right: 1px solid var(--coffee-line); }
 [data-testid="stSidebar"] h2 { font-size: 1.35rem !important; line-height: 1.3; max-width: 15rem; }
 [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { font-size: .82rem; line-height: 1.65; }
 h1 { font-size: clamp(1.6rem, 2.3vw, 2.25rem) !important; font-weight: 650 !important; letter-spacing: -.045em !important; line-height: 1.2 !important; padding-top: 0 !important; }
 h2 { font-size: 1.3rem !important; letter-spacing: -.025em; }
 h3 { font-size: 1.23rem !important; font-weight: 650 !important; letter-spacing: -.025em; }
 [data-testid="stCaptionContainer"] p { color: var(--coffee-muted); line-height: 1.55; }
 .desk-brand { display: flex; align-items: center; gap: .55rem; color: var(--coffee-muted); font-size: .7rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; margin-bottom: .2rem; }
 .desk-brand svg { width: 24px; height: 24px; color: var(--coffee-green); }
 .section-eyebrow { font-size: .68rem; font-weight: 750; letter-spacing: .13em; text-transform: uppercase; color: var(--coffee-muted); margin-bottom: -.35rem; }
 .context-bar { display: flex; align-items: center; flex-wrap: wrap; gap: .9rem 2rem; padding: .9rem 1.1rem; border: 1px solid var(--coffee-line); border-radius: 10px; margin-top: .2rem; }
 .context-item { display: grid; gap: .18rem; }
 .context-item small { font-size: .68rem; color: var(--coffee-muted); letter-spacing: .06em; text-transform: uppercase; }
 .context-item strong { font-size: .9rem; font-weight: 600; }
 .context-item.plan-date strong { color: var(--coffee-green); }
 .snapshot-badge { margin-left: auto; font-size: .7rem; font-weight: 600; padding: .32rem .6rem; border-radius: 5px; color: var(--coffee-muted); background: var(--coffee-surface); white-space: nowrap; }
 .st-key-overview [data-testid="stHorizontalBlock"] { gap: 1rem; }
 .st-key-overview [data-testid="stMetric"] { border: 1px solid var(--coffee-line); border-radius: 10px; padding: .85rem 1rem; background: var(--coffee-paper); }
 [data-testid="stMetricLabel"] p { color: var(--coffee-muted); font-size: .8rem; }
 .st-key-overview [data-testid="stMetricLabel"] { min-height: 38px; align-items: flex-start; }
 .st-key-overview [data-testid="stMetricLabel"] p { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; min-height: 2.7em; }
 [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 600; letter-spacing: -.04em; font-variant-numeric: tabular-nums; }
 [data-testid="stExpander"] { border-color: var(--coffee-line); border-radius: 10px; }
 [data-testid="stExpander"] summary p { font-size: .9rem; }
 .st-key-stock-entry [data-testid="stExpander"] { background: var(--coffee-surface); }
 .st-key-category-plan { border: 1px solid var(--coffee-line) !important; border-top: 3px solid var(--coffee-green) !important; border-radius: var(--coffee-radius); padding: 1.35rem 1.4rem !important; box-shadow: 0 5px 20px #253A3105; }
 .st-key-sales-trend { border-color: var(--coffee-line) !important; border-radius: var(--coffee-radius); padding: 1.35rem 1.4rem !important; }
 .plan-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: .87rem; margin: .2rem 0 .5rem; color: var(--coffee-ink); }
 .plan-table th, .plan-table td { padding: .65rem .65rem; border-bottom: 1px solid var(--coffee-line); text-align: right; vertical-align: middle; }
 .st-key-category-plan table.plan-table th, .st-key-category-plan table.plan-table td { border-top: 0; border-left: 0; border-right: 0; }
 .plan-table thead th { padding-top: .55rem; padding-bottom: .65rem; font-size: .69rem; font-weight: 650; letter-spacing: .025em; color: var(--coffee-muted); white-space: nowrap; }
 .plan-table th:first-child, .plan-table td:first-child, .plan-table th:last-child, .plan-table td:last-child { text-align: left; }
 .plan-table tbody th { font-weight: 550; min-width: 155px; }
 .plan-table tbody tr:last-child > * { border-bottom: 0; }
 .plan-table .ready { background: var(--coffee-green-soft); color: var(--coffee-ink); }
 .plan-table td.ready { font-size: 1.2rem; font-weight: 700; letter-spacing: -.035em; }
 .plan-table th.ready { color: var(--coffee-ink); border-radius: 8px 8px 0 0; }
 .plan-table tbody tr:last-child .ready { border-radius: 0 0 8px 8px; }
 .plan-table .num { font-variant-numeric: tabular-nums; }
 .plan-table .unknown { color: var(--coffee-muted); }
 .plan-table .addition { font-size: 1.05rem; font-weight: 650; }
 .plan-table .addition.needed { color: var(--coffee-amber); }
 .plan-table .category-cell { display: flex; align-items: center; gap: .55rem; }
 .category-mark { display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; flex: 0 0 26px; border-radius: 7px; background: var(--coffee-surface); color: var(--coffee-muted); font-size: .68rem; font-weight: 650; }
 .status-pill { display: inline-flex; align-items: center; gap: .35rem; padding: .3rem .5rem; border-radius: 5px; background: var(--coffee-surface); color: var(--coffee-muted); font-size: .7rem; font-weight: 550; white-space: nowrap; }
 .status-pill::before { content: ''; width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
 .status-pill.needed { background: var(--coffee-amber-soft); color: var(--coffee-ink); }
 .status-pill.covered { background: var(--coffee-green-soft); color: var(--coffee-ink); }
 .plan-note { display: flex; gap: .6rem; align-items: flex-start; padding: .75rem .9rem; border-radius: 8px; background: var(--coffee-green-soft); font-size: .81rem; line-height: 1.5; color: var(--coffee-ink); }
 .plan-note strong { font-weight: 650; }
 .plan-note svg { flex: 0 0 17px; width: 17px; margin-top: .1rem; }
 .st-key-category-plan [data-testid="stDownloadButton"] button { background: var(--coffee-green); color: #fff; border-color: var(--coffee-green); border-radius: 8px; min-height: 42px; }
 .st-key-category-plan [data-testid="stDownloadButton"] button:hover { background: #1D4F3E; border-color: #1D4F3E; }
 .st-key-category-plan [data-testid="stDownloadButton"] button p { color: #fff; font-weight: 550; font-size: .85rem; }
 .forecast-glance { display: grid; grid-template-columns: repeat(3, 1fr); gap: .8rem; margin: .25rem 0 .4rem; padding: .8rem 1rem; background: var(--coffee-surface); border-radius: 9px; }
 .forecast-glance > div { display: grid; gap: .2rem; }
 .forecast-glance small { font-size: .72rem; color: var(--coffee-muted); }
 .forecast-glance strong { font-size: 1.25rem; font-weight: 650; letter-spacing: -.03em; font-variant-numeric: tabular-nums; }
 .mobile-plan { display: none; }
 .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
 button:focus-visible, input:focus-visible, summary:focus-visible { outline: 2px solid var(--coffee-green) !important; outline-offset: 3px; }
 @media (max-width: 760px) {
   .stMainBlockContainer { padding: 1.3rem 1rem 2rem; }
   .st-key-category-plan, .st-key-sales-trend { padding: 1rem !important; }
   .st-key-category-plan table.plan-table { display: none !important; }
   .mobile-plan { display: grid; }
   .mobile-plan-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .3rem .65rem; align-items: center; padding: .75rem 0; border-bottom: 1px solid var(--coffee-line); }
   .mobile-plan-row:last-child { border-bottom: 0; }
   .mobile-plan-row strong { font-size: .92rem; }
   .mobile-plan-row .target { font-size: 1.3rem; font-weight: 700; letter-spacing: -.04em; text-align: right; }
   .mobile-plan-row .target span { font-size: .67rem; font-weight: 500; letter-spacing: 0; color: var(--coffee-muted); }
   .mobile-plan-row .row-detail { grid-column: 1 / -1; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: .35rem; }
   .mobile-plan-row small { font-size: .76rem; color: var(--coffee-muted); }
 }
 @media (max-width: 640px) {
   h1 { font-size: 1.7rem !important; }
   .context-bar { gap: .8rem 1.2rem; padding: .85rem; }
   .context-item { flex: 1 1 40%; }
   .context-item:first-child { flex-basis: 100%; }
   .snapshot-badge { display: none; }
   .st-key-overview [data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .5rem; }
   .st-key-overview [data-testid="stColumn"] { flex: 1 1 0 !important; min-width: 0 !important; }
   .st-key-overview [data-testid="stMetric"] { padding: .65rem .55rem; min-height: 110px; }
   .st-key-overview [data-testid="stMetricLabel"] p { font-size: .7rem; line-height: 1.35; }
   [data-testid="stMetricValue"] { font-size: 1.5rem; }
   .forecast-glance { padding: .75rem; gap: .45rem; }
   .forecast-glance strong { font-size: 1.1rem; }
   .forecast-glance small { font-size: .69rem; }
 }
 @media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; transition: none !important; } }

 .stMainBlockContainer { padding-top: 2.8rem; }
 [data-testid="stHeader"] { background: var(--coffee-paper); border-bottom: 1px solid var(--coffee-line); }
 .plan-table tbody th { min-width: 125px; }
 .plan-table th, .plan-table td { padding-inline: .5rem; }
 .mobile-counts { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(3, 1fr); gap: .5rem; padding: .3rem 0; }
 .mobile-counts > div { display: grid; gap: .2rem; }
 .mobile-counts b { font-size: 1rem; font-weight: 600; font-variant-numeric: tabular-nums; }
 .st-key-forecast-details { border-color: var(--coffee-line) !important; border-radius: var(--coffee-radius); padding: 1.2rem !important; }
 .st-key-mobile-nav { display: none; }
 @media (max-width: 760px) {
   .stMainBlockContainer { padding-top: 2.3rem; }
   .mobile-plan-row { padding-block: .85rem; }
   .mobile-counts small { font-size: .7rem; }
   .st-key-mobile-nav { display: block; }
   .st-key-mobile-nav [data-testid="stHorizontalBlock"] { flex-wrap: nowrap; gap: .45rem; }
   .st-key-mobile-nav [data-testid="stColumn"] { flex: 1 1 0 !important; min-width: 0 !important; }
   .st-key-mobile-nav [data-testid="stPageLink"] a { width: 100%; min-height: 42px; padding: .5rem .4rem; border: 1px solid var(--coffee-line); border-radius: 8px; justify-content: center; gap: .3rem; }
   .st-key-mobile-nav [data-testid="stPageLink"] a[aria-current="page"] { background: var(--coffee-green-soft); font-weight: 650; }
   .st-key-mobile-nav [data-testid="stPageLink"] p { font-size: .78rem; }
 }

</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def cached_sales(path, modified_ns):
    return load_sales(path)


@st.cache_data(show_spinner=False)
def cached_forecast(path, modified_ns, store_name, cutoff):
    sales = cached_sales(path, modified_ns)
    daily = category_daily_units(sales.frame, store_name, cutoff)
    return forecast_categories(daily, cutoff)


st.markdown('<div class="desk-brand"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 8h13v6a6 6 0 0 1-6 6h-1a6 6 0 0 1-6-6V8Z"/><path d="M17 9h2a3 3 0 0 1 0 6h-2M8 2v3m4-3v3M3 23h16"/></svg> Coffee / Operations desk</div>', unsafe_allow_html=True)
st.title(f"{TEAM_NAME} · Store manager’s desk")
st.caption("For the store manager: check yesterday’s sales and decide today’s category preparation.")
mobile_navigation = st.container(key="mobile-nav")

try:
    modified_ns = DATA_PATH.stat().st_mtime_ns
    sales = cached_sales(str(DATA_PATH), modified_ns)
except (OSError, ValueError, pd.errors.ParserError) as exc:
    st.error("Sales data could not be loaded. Restore the source CSV and review its format.")
    with st.expander("Data issue details"):
        st.code(str(exc))
    st.stop()

df = sales.frame
stores = sorted(df.store_location.unique())
with st.sidebar:
    st.markdown('<div class="section-eyebrow">Your store / your day</div>', unsafe_allow_html=True)
    st.header("Start with the last close.")
    st.caption("The next calendar day becomes today’s preparation plan.")
    selected_store = st.selectbox("Store", stores, index=stores.index("Lower Manhattan") if "Lower Manhattan" in stores else 0, key="selected_store")
    store_dates = df.loc[df.store_location.eq(selected_store), "date"]
    earliest = store_dates.min() + pd.Timedelta(days=55)
    latest = store_dates.max()
    if earliest > latest:
        st.error("This store needs at least 56 days of history before a plan can be reviewed.")
        st.stop()
    cutoff = st.date_input("Last completed sales day", value=latest.date(), min_value=earliest.date(), max_value=latest.date(), format="YYYY-MM-DD", key="sales_cutoff")
    buffer_pct = st.slider("Manager’s safety buffer (%)", min_value=0, max_value=30, value=10, step=5, key="safety_buffer",
                           help="An editable planning assumption, not an optimized service level. Review perishability, storage and local events.")
    st.caption("Quantities are recorded sale units within each category. For drinks, use serving-equivalent ingredients, then convert into your actual recipes and supplier packs.")

if cutoff is None:
    st.info("Choose the last completed sales day.")
    st.stop()
try:
    forecast = cached_forecast(str(DATA_PATH), modified_ns, selected_store, cutoff)
except ValueError as exc:
    st.warning(str(exc))
    st.stop()

st.markdown(f'<div class="context-bar"><div class="context-item"><small>Store</small><strong>{escape(selected_store)}</strong></div><div class="context-item"><small>Yesterday / sales closed</small><strong>{forecast.as_of:%a %d %b %Y}</strong></div><div class="context-item plan-date"><small>Today / preparing for</small><strong>{forecast.target_date:%a %d %b %Y}</strong></div><span class="snapshot-badge">Historical simulation</span></div>', unsafe_allow_html=True)
st.caption("Historical demo: ‘today’ is the planning date after the selected sales cutoff, not the current calendar date.")

# A separate, non-widget key survives when the editor is absent on other pages.
stock_context_key = f"usable-stock::{selected_store}::{cutoff}"
if stock_context_key not in st.session_state:
    st.session_state[stock_context_key] = {}


def current_plan():
    plan = make_stock_plan(forecast.summary, buffer_pct, st.session_state[stock_context_key])
    plan["yesterday_units"] = plan.category.map(forecast.daily.loc[forecast.as_of]).astype(int)
    return plan


def render_todo():
    overview = st.container(key="overview")
    with st.container(key="stock-entry"), st.expander("1. Check usable stock", expanded=False):
        st.write("Enter only stock that will still be usable today. Leave unchecked quantities blank; enter 0 only after checking there is none.")
        st.caption("For drinks, count the servings supported by ingredients on hand. Entries stay available across these pages in this browser session; download the plan to retain them.")
        categories = sorted(forecast.summary.category)
        saved = st.session_state[stock_context_key]
        stock_input = pd.DataFrame({"Category": categories, "Usable units": pd.array([saved.get(category) for category in categories], dtype="Float64")})
        edited = st.data_editor(stock_input, hide_index=True, width="stretch", num_rows="fixed", disabled=["Category"],
                                key=f"stock::{selected_store}::{cutoff}",
                                column_config={"Usable units": st.column_config.NumberColumn("Usable today", min_value=0, step=1, format="%d", help="Sale units or serving equivalents. Blank means unknown.")})
        supplied = {row["Category"]: row["Usable units"] for _, row in edited.iterrows() if not pd.isna(row["Usable units"])}
        try:
            make_stock_plan(forecast.summary, buffer_pct, supplied)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        st.session_state[stock_context_key] = supplied
    try:
        plan = current_plan()
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    pending = int(plan.available_units.isna().sum())
    needs_addition = int(plan.add_units.gt(0).fillna(False).sum())
    cols = overview.columns(3)
    cols[0].metric("Categories planned", len(plan))
    cols[1].metric("Stock checks left", pending, help="Unchecked stock is unknown, rather than zero.")
    cols[2].metric("Categories to add", needs_addition, help="Confirmed positive additions only. Unknown stock may still need replenishment.")

    with st.container(border=True, key="category-plan"):
        st.markdown('<div class="section-eyebrow">2. Prepare today’s categories</div>', unsafe_allow_html=True)
        st.subheader("Today’s To-do")
        st.caption(f"Ready target = today’s forecast + {buffer_pct}% buffer, rounded up. To add = ready target − usable stock, with a minimum of zero.")
        visible = pd.DataFrame({"Category": plan.category, "Yesterday sold": plan.yesterday_units,
                                "Predicted today": plan.forecast_units.round().astype(int), "Ready target": plan.target_units,
                                "Usable stock": plan.available_units, "Prepare / add": plan.add_units, "Next action": plan.action})
        table_rows, mobile_rows = [], []
        for row in plan.itertuples():
            category = escape(row.category)
            known = not pd.isna(row.add_units)
            needed = known and row.add_units > 0
            state = "needed" if needed else ("covered" if known else "pending")
            status = "Prepare / add" if needed else ("Stock covers target" if known else "Check stock")
            available = f"{int(row.available_units):,}" if known else "—"
            addition = f"{int(row.add_units):,}" if known else "—"
            stock_text = f"Usable stock {available}" if known else "Stock not checked"
            pill = f'<span class="status-pill {state}">{status}</span>'
            table_rows.append(
                f'<tr><th scope="row"><span class="category-cell"><span class="category-mark" aria-hidden="true">{category[0]}</span>{category}</span></th>'
                f'<td class="num">{row.yesterday_units:,}</td><td class="num">{row.forecast_units:,.0f}</td><td class="num ready">{row.target_units:,}</td>'
                f'<td class="num {"" if known else "unknown"}">{available}</td><td class="num addition {state}">{addition}</td><td>{pill}</td></tr>')
            mobile_rows.append(
                f'<div class="mobile-plan-row"><strong>{category}</strong><span class="target">{row.target_units:,} <span>ready</span></span>'
                f'<div class="mobile-counts"><div><small>Yesterday sold</small><b>{row.yesterday_units:,}</b></div><div><small>Predicted today</small><b>{row.forecast_units:,.0f}</b></div><div><small>To add</small><b>{addition}</b></div></div>'
                f'<div class="row-detail"><small>{stock_text}</small>{pill}</div></div>')
        st.markdown('<table class="plan-table"><caption class="sr-only">Today’s category preparation: yesterday’s recorded sales, today’s forecast, buffered ready target, usable stock, additions and next action.</caption><thead><tr><th scope="col">Category</th><th scope="col">Yesterday sold</th><th scope="col">Predicted today</th><th class="ready" scope="col">Ready target</th><th scope="col">Usable stock</th><th scope="col">To add</th><th scope="col">Next action</th></tr></thead><tbody>' + ''.join(table_rows) + '</tbody></table><div class="mobile-plan">' + ''.join(mobile_rows) + '</div>', unsafe_allow_html=True)
        if pending:
            note = f"<strong>{pending} stock checks left.</strong> Complete step 1 to calculate the additions. A blank addition is an unresolved task."
        else:
            note = f"<strong>Stock checks complete.</strong> {needs_addition} categories need an addition. Review quantities before preparing or ordering."
        st.markdown(f'<div class="plan-note"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="10" cy="10" r="8"/><path d="M10 9v5m0-8v1"/></svg><span>{note}</span></div>', unsafe_allow_html=True)
        st.caption("Quantities are category sale units. Translate ready targets into specific products, recipes and supplier packs before ordering; drinks are not all prepared in advance.")
        export = plan.drop(columns="selection_mae_units").copy()
        export.insert(0, "store", selected_store)
        export.insert(1, "sales_through", forecast.as_of.date().isoformat())
        export.insert(2, "plan_for", forecast.target_date.date().isoformat())
        st.download_button("3. Download today’s plan", export.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"coffee-plan-{selected_store.lower().replace(' ', '-')}-{forecast.target_date:%Y-%m-%d}.csv", mime="text/csv")
        with st.expander("Open sortable planning table"):
            st.dataframe(visible, hide_index=True, width="stretch", height=365,
                         column_config={"Category": st.column_config.TextColumn(width="medium"),
                                        "Predicted today": st.column_config.NumberColumn(format="%d", help="Rounded display of the next-day forecast."),
                                        "Ready target": st.column_config.NumberColumn(format="%d", help="Ceiling of the unrounded forecast × (1 + buffer)."),
                                        "Usable stock": st.column_config.NumberColumn(format="%d"),
                                        "Prepare / add": st.column_config.NumberColumn(format="%d", help="Unknown stock leaves this unresolved.")})


def render_sales():
    st.markdown('<div class="section-eyebrow">Review / recorded performance</div>', unsafe_allow_html=True)
    st.subheader("Sales review")
    st.caption(f"Yesterday’s actuals ({forecast.as_of:%d %b}) and the recent demand behind today’s plan. All historical views stop at yesterday’s close.")
    store_rows = df.loc[df.store_location.eq(selected_store) & df.date.le(forecast.as_of)]
    yesterday = store_rows.loc[store_rows.date.eq(forecast.as_of)]
    previous = store_rows.loc[store_rows.date.eq(forecast.as_of - pd.Timedelta(days=1))]

    def change(value, before):
        return f"{(value / before - 1) * 100:+.1f}% vs day before" if before else None

    with st.container(key="overview"):
        cols = st.columns(3)
        revenue = int(yesterday.revenue_cents.sum())
        units = int(yesterday.transaction_qty.sum())
        cols[0].metric("Yesterday’s revenue", f"${revenue / 100:,.2f}", change(revenue, int(previous.revenue_cents.sum())))
        cols[1].metric("Recorded sale units", f"{units:,}", change(units, int(previous.transaction_qty.sum())), help="Count of recorded sale units across products, not one interchangeable inventory total.")
        cols[2].metric("Sales records", f"{len(yesterday):,}", change(len(yesterday), len(previous)), help="Source rows, not complete receipts or unique customers.")
    with st.container(border=True, key="sales-trend"):
        st.subheader("Yesterday’s sales in context")
        categories = list(forecast.summary.category)
        focus = st.selectbox("Inspect a category", categories, index=categories.index("Coffee") if "Coffee" in categories else 0, key="focus_category")
        detail = current_plan().loc[lambda frame: frame.category.eq(focus)].iloc[0]
        st.markdown(f'<div class="forecast-glance"><div><small>Yesterday sold</small><strong>{detail.yesterday_units:,} units</strong></div><div><small>Predicted today</small><strong>{detail.forecast_units:,.0f} units</strong></div><div><small>Ready with {buffer_pct}% buffer</small><strong>{detail.target_units:,} units</strong></div></div>', unsafe_allow_html=True)
        history = forecast.daily[[focus]].tail(28).reset_index().rename(columns={"index": "date", focus: "units"})
        history["series"] = "Recorded sales"
        future_line = pd.DataFrame({"date": [forecast.as_of, forecast.target_date], "units": [history.units.iloc[-1], detail.forecast_units], "series": "Forecast"})
        future_point = pd.DataFrame({"date": [forecast.target_date], "units": [detail.forecast_units], "low": [detail.low_units], "high": [detail.high_units], "series": ["Forecast"]})
        colors = alt.Color("series:N", title=None, scale=alt.Scale(domain=["Recorded sales", "Forecast"], range=[TEAL, AMBER]), legend=alt.Legend(orient="top"))
        xy = {"x": alt.X("date:T", title=None, axis=alt.Axis(format="%d %b", tickCount=6, labelAngle=0)),
              "y": alt.Y("units:Q", title="Sale units / day", scale=alt.Scale(zero=True)), "color": colors}
        recorded = alt.Chart(history).mark_line(point=alt.OverlayMarkDef(size=24), strokeWidth=2).encode(**xy, tooltip=[alt.Tooltip("date:T", format="%d %b %Y"), alt.Tooltip("units:Q", format=".0f"), "series:N"])
        connector = alt.Chart(future_line).mark_line(strokeDash=[5, 4], strokeWidth=2).encode(**xy)
        band = alt.Chart(future_point).mark_rule(strokeWidth=5, opacity=0.3).encode(x="date:T", y="low:Q", y2="high:Q", color=colors, tooltip=[alt.Tooltip("low:Q", title="Planning low", format=".0f"), alt.Tooltip("high:Q", title="Planning high", format=".0f")])
        point = alt.Chart(future_point).mark_point(filled=True, size=100).encode(**xy, tooltip=[alt.Tooltip("date:T", format="%d %b %Y"), alt.Tooltip("units:Q", title="Forecast", format=".1f")])
        area = alt.Chart(history).mark_area(color=TEAL, opacity=0.06).encode(x="date:T", y=alt.Y("units:Q", scale=alt.Scale(zero=True)))
        chart = (area + recorded + connector + band + point).properties(height=290, description="28 days of recorded category sales through yesterday’s close, followed by today’s forecast and an illustrative recent-error range.")
        st.altair_chart(chart.configure_view(stroke=None).configure_axis(domain=False, tickSize=0, labelPadding=10, titlePadding=15, gridOpacity=0.12, gridDash=[3, 4], labelFontSize=11, titleFontSize=11).configure_legend(labelFontSize=11, padding=12, symbolStrokeWidth=3), width="stretch", theme="streamlit")
        st.write(f"**{focus}:** expected **{detail.forecast_units:.0f}** sale units today; ready target **{detail.target_units}**. Recent-error planning range: **{detail.low_units}–{detail.high_units}** units.")
        st.caption(f"Average absolute miss over {int(detail.review_days)} recent daily checks: {detail.review_mae_units:.1f} units/day. The range reflects recent misses, not guaranteed coverage.")
    with st.expander("Yesterday’s category breakdown"):
        breakdown = yesterday.groupby("product_category").agg(**{"Sale units": ("transaction_qty", "sum"), "Revenue cents": ("revenue_cents", "sum"), "Sales records": ("transaction_id", "size")}).reset_index().rename(columns={"product_category": "Category"})
        breakdown["Revenue (USD)"] = breakdown.pop("Revenue cents") / 100
        st.dataframe(breakdown.sort_values("Sale units", ascending=False), hide_index=True, width="stretch")


def render_forecast():
    st.markdown('<div class="section-eyebrow">Evidence / assumptions and quality</div>', unsafe_allow_html=True)
    st.subheader("Forecast & data")
    st.caption("Check how much the forecast has missed, how it was chosen, and where manager judgment is still needed.")
    plan = current_plan()
    with st.container(border=True, key="forecast-details"):
        st.subheader("Recent forecast checks")
        details = plan[["category", "forecast_units", "low_units", "high_units", "review_mae_units", "method"]].rename(columns={"category": "Category", "forecast_units": "Predicted today", "low_units": "Planning low", "high_units": "Planning high", "review_mae_units": "Recent average miss", "method": "Selected approach"})
        st.dataframe(details, hide_index=True, width="stretch", column_config={
            "Predicted today": st.column_config.NumberColumn(format="%.1f"),
            "Recent average miss": st.column_config.NumberColumn(format="%.1f"),
            "Planning low": st.column_config.NumberColumn(format="%d"),
            "Planning high": st.column_config.NumberColumn(format="%d"),
        })
        st.caption(f"Method selection: {forecast.selection_start:%d %b}–{forecast.selection_end:%d %b}; separate review: {forecast.review_start:%d %b}–{forecast.review_end:%d %b}. Errors are in category sale units per day.")
    with st.expander("How the forecast and buffer work", expanded=True):
        st.write("Only sales recorded by the selected close are used. For each category, three simple approaches are compared on an earlier 14-day window: a recent 7-day average, an average of the last four matching weekdays, and that weekday average adjusted for recent growth. The chosen approach is checked on the following 14 days without choosing again; each check uses only earlier sales.")
        st.write("Ready target = ceiling(forecast × (1 + buffer)); additions = max(0, ready target − usable stock). The default 10% buffer is an editable manager assumption, not a service level calibrated from stockout costs or spoilage.")
        st.write("The planning range adds the 10th and 90th percentiles of 14 recent signed errors to the prediction, expands to include the point estimate, and rounds outward. It is an illustrative range, not a calibrated 80% interval or a guarantee.")
    with st.expander("Data quality and operational limits", expanded=True):
        st.write(f"{len(df):,} original records retained; {sales.whitespace_fixed:,} labels trimmed; {sales.possible_duplicates:,} possible duplicate business records with different IDs retained for review. {sales.variable_price_products} products have multiple observed prices.")
        st.write("A recorded store-day with no sales in a category contributes zero category sales. An entirely missing store-day stays unavailable; a plan requires 56 consecutive recorded days. Recorded sales may understate demand during stockouts.")
        st.write("There are no inventory balances, recipes, supplier pack sizes, delivery lead times, promotions, weather, holidays or recorded spoilage. Category plans cannot allocate quantities to individual products. Stock entries are temporary session inputs, not connected inventory balances or proof that preparation is complete.")


todo_page = st.Page(render_todo, title="Today’s To-do", icon=":material/checklist:", default=True)
sales_page = st.Page(render_sales, title="Sales review", icon=":material/monitoring:", url_path="sales")
forecast_page = st.Page(render_forecast, title="Forecast & data", icon=":material/insights:", url_path="forecast")
page = st.navigation([todo_page, sales_page, forecast_page], position="top")
with mobile_navigation:
    links = st.columns(3)
    links[0].page_link(todo_page, label="To-do", icon=":material/checklist:")
    links[1].page_link(sales_page, label="Sales", icon=":material/monitoring:")
    links[2].page_link(forecast_page, label="Forecast", icon=":material/insights:")
page.run()

st.divider()
st.caption(f"Data: {df.date.min():%d %b %Y}–{df.date.max():%d %b %Y} · Fictitious NYC coffee business · Intended refresh: after daily close; manager review: before the next service day. Fixed CSV snapshot.")
