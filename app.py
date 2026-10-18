"""Run with: uv run streamlit run app.py"""

from pathlib import Path
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from coffee_data import category_daily_units, forecast_categories, load_sales, make_stock_plan

TEAM_NAME = "Coffee Operations Team"  # Replace with the actual course team name.
DATA_PATH = Path(__file__).resolve().parent / "Coffee Shop Sales.csv"
TEAL, AMBER = "#247266", "#B67732"

st.set_page_config(page_title="Coffee · Next-day prep", page_icon="☕", layout="wide")
st.markdown("""
<style>
 :root { --coffee-accent: #247266; --coffee-radius: 12px; --coffee-space: 1rem; }
 .stMainBlockContainer { max-width: 1180px; padding-top: 1.5rem; }
 h1 { font-size: 1.9rem !important; line-height: 1.2 !important; }
 h2 { font-size: 1.3rem !important; } h3 { font-size: 1.05rem !important; }
 [data-testid="stMetricValue"] { font-size: 1.55rem; font-variant-numeric: tabular-nums; }
 [data-testid="stMetric"] { padding-block: .2rem; }
 .mobile-plan { display: none; }
 button:focus-visible, input:focus-visible { outline: 2px solid var(--coffee-accent); outline-offset: 3px; }
 @media (max-width: 640px) {
   .stMainBlockContainer { padding: 1rem .9rem 2rem; }
   h1 { font-size: 1.5rem !important; }
   [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) { gap: .5rem; }
   [data-testid="stMetricValue"] { font-size: 1.2rem; }
   .st-key-category-plan [data-testid="stDataFrame"] { display: none; }
   .mobile-plan { display: block; }
   .mobile-plan-row { display: grid; grid-template-columns: 1fr auto; gap: .2rem .7rem; padding: .8rem 0; border-bottom: 1px solid #90978e55; }
   .mobile-plan-row .target { font-size: 1.25rem; font-weight: 700; text-align: right; }
   .mobile-plan-row small { font-size: .85rem; }
 }
 @media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; } }
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


st.title(f"{TEAM_NAME} · Next-day prep")
st.caption("For the replenishment manager closing the day: review tomorrow’s category demand, check usable stock, and set preparation quantities.")
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
    st.header("Close today. Plan tomorrow.")
    selected_store = st.selectbox("Store", stores, index=stores.index("Lower Manhattan") if "Lower Manhattan" in stores else 0)
    store_dates = df.loc[df.store_location.eq(selected_store), "date"]
    earliest = store_dates.min() + pd.Timedelta(days=55)
    latest = store_dates.max()
    if earliest > latest:
        st.error("This store needs at least 56 days of history before a plan can be reviewed.")
        st.stop()
    cutoff = st.date_input("Sales recorded through", value=latest.date(), min_value=earliest.date(), max_value=latest.date(), format="YYYY-MM-DD")
    buffer_pct = st.slider("Manager’s safety buffer (%)", min_value=0, max_value=30, value=10, step=5,
                           help="A planning assumption, not an optimized service level. Review perishability, storage and local events before adding a buffer.")
    st.caption("All quantities use recorded sale units within each category. Drinks need serving-equivalent ingredients; these are not kilograms, supplier packs, or instructions to make every drink in advance.")

if cutoff is None:
    st.info("Choose the date through which sales have been recorded.")
    st.stop()

try:
    forecast = cached_forecast(str(DATA_PATH), modified_ns, selected_store, cutoff)
except ValueError as exc:
    st.warning(str(exc))
    st.stop()

st.markdown(f"**{selected_store}** · Sales through **{forecast.as_of:%a %d %b %Y}** · Plan for **{forecast.target_date:%a %d %b %Y}**")
st.caption("Historical demo: ‘tomorrow’ means the day after your selected 2023 cutoff. This is not a live forecast for today’s calendar date.")

with st.expander("Enter usable stock to calculate what to add", expanded=False):
    st.write("Leave unknown stock blank. Enter 0 only after checking there is none. Count only stock that will remain usable tomorrow; exclude expired items and expected waste.")
    st.caption("For drinks, enter the portions supported by ingredients already on hand, using your own recipe conversion. Entries are temporary in this browser session; download the plan to retain them.")
    stock_input = pd.DataFrame({"Category": sorted(forecast.summary.category), "Usable units": pd.Series([None] * len(forecast.summary), dtype="Float64")})
    edited_stock = st.data_editor(stock_input, hide_index=True, width="stretch", num_rows="fixed",
                                 disabled=["Category"], key=f"stock::{selected_store}::{cutoff}",
                                 column_config={"Usable units": st.column_config.NumberColumn("Usable tomorrow", min_value=0, step=1, format="%d", help="Sale units or serving equivalents. Blank means unknown.")})
stock = dict(zip(edited_stock.Category, edited_stock["Usable units"]))
try:
    plan = make_stock_plan(forecast.summary, buffer_pct, stock)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

pending = int(plan.available_units.isna().sum())
needs_addition = int(plan.add_units.gt(0).fillna(False).sum())
cols = st.columns(3)
cols[0].metric("Categories in tomorrow’s plan", len(plan))
cols[1].metric("Usable-stock checks left", pending, help="Unknown inventory is not counted as zero. Finish these checks before approving additions.")
cols[2].metric("Confirmed categories to add", needs_addition, help="Only categories with entered usable stock and a positive shortfall. Other categories can still need a stock check.")

with st.container(border=True, key="category-plan"):
    st.subheader("What should be ready tomorrow?")
    st.write(f"Start with each category’s demand estimate. The ready target adds your **{buffer_pct}% buffer**; the final addition subtracts usable stock.")
    visible = pd.DataFrame({
        "Category": plan.category,
        "Expected sales": plan.forecast_units.round().astype(int),
        "Ready target": plan.target_units,
        "Usable stock": plan.available_units,
        "Prepare / add": plan.add_units,
        "Next action": plan.action,
    })
    st.dataframe(visible, hide_index=True, width="stretch", height=365,
                 column_config={
                     "Category": st.column_config.TextColumn(width="medium"),
                     "Expected sales": st.column_config.NumberColumn(format="%d", help="Next-day forecast, displayed to the nearest unit."),
                     "Ready target": st.column_config.NumberColumn(format="%d", help="Unrounded forecast × (1 + buffer), rounded up."),
                     "Usable stock": st.column_config.NumberColumn(format="%d"),
                     "Prepare / add": st.column_config.NumberColumn(format="%d", help="max(0, ready target − entered usable stock). Blank requires a stock check."),
                 })
    mobile_rows = []
    for row in plan.itertuples():
        action = "Check usable stock" if pd.isna(row.add_units) else f"Prepare / add {row.add_units}"
        available_text = "Stock unknown" if pd.isna(row.available_units) else f"Usable stock {row.available_units}"
        mobile_rows.append(f'<div class="mobile-plan-row"><strong>{escape(row.category)}</strong><span class="target">{row.target_units} ready</span><small>Forecast {row.forecast_units:.0f} · {available_text}</small><small>{action}</small></div>')
    st.markdown('<div class="mobile-plan">' + ''.join(mobile_rows) + '</div>', unsafe_allow_html=True)
    st.caption("— means usable stock has not been entered. A ready target is a sales-unit planning target; translate it into specific products and ingredient quantities before ordering.")
    if pending:
        st.info(f"Check usable stock for {pending} categories to finish the additions. Targets and forecasts are available now.")
    else:
        st.success(f"All stock checks entered. {needs_addition} categories have a positive addition; review the plan before ordering.")
    export = plan.drop(columns="selection_mae_units").copy()
    export.insert(0, "store", selected_store)
    export.insert(1, "sales_through", forecast.as_of.date().isoformat())
    export.insert(2, "plan_for", forecast.target_date.date().isoformat())
    st.download_button("Download tomorrow’s category plan", export.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"coffee-plan-{selected_store.lower().replace(' ', '-')}-{forecast.target_date:%Y-%m-%d}.csv", mime="text/csv")

st.subheader("Recent sales, with tomorrow in view")
categories = list(forecast.summary.category)
focus = st.selectbox("Inspect a category", categories, index=categories.index("Coffee") if "Coffee" in categories else 0)
detail = plan.loc[plan.category.eq(focus)].iloc[0]
history = forecast.daily[[focus]].tail(28).reset_index().rename(columns={"index": "date", focus: "units"})
history["series"] = "Recorded sales"
future_line = pd.DataFrame({"date": [forecast.as_of, forecast.target_date],
                            "units": [history.units.iloc[-1], detail.forecast_units], "series": "Forecast"})
future_point = pd.DataFrame({"date": [forecast.target_date], "units": [detail.forecast_units],
                             "low": [detail.low_units], "high": [detail.high_units], "series": ["Forecast"]})
colors = alt.Color("series:N", title=None, scale=alt.Scale(domain=["Recorded sales", "Forecast"], range=[TEAL, AMBER]), legend=alt.Legend(orient="top"))
xy = {"x": alt.X("date:T", title=None, axis=alt.Axis(format="%d %b", tickCount=6, labelAngle=0)),
      "y": alt.Y("units:Q", title="Sale units / day", scale=alt.Scale(zero=True)), "color": colors}
recorded = alt.Chart(history).mark_line(point=alt.OverlayMarkDef(size=24), strokeWidth=2).encode(
    **xy, tooltip=[alt.Tooltip("date:T", format="%d %b %Y"), alt.Tooltip("units:Q", format=".0f"), "series:N"])
connector = alt.Chart(future_line).mark_line(strokeDash=[5, 4], strokeWidth=2).encode(**xy)
band = alt.Chart(future_point).mark_rule(strokeWidth=5, opacity=0.3).encode(
    x="date:T", y="low:Q", y2="high:Q", color=colors,
    tooltip=[alt.Tooltip("low:Q", title="Planning low", format=".0f"), alt.Tooltip("high:Q", title="Planning high", format=".0f")])
point = alt.Chart(future_point).mark_point(filled=True, size=100).encode(
    **xy, tooltip=[alt.Tooltip("date:T", format="%d %b %Y"), alt.Tooltip("units:Q", title="Forecast", format=".1f"),
                   alt.Tooltip("low:Q", title="Planning low"), alt.Tooltip("high:Q", title="Planning high")])
chart = (recorded + connector + band + point).properties(height=270,
    description="28 days of category sales through the selected cutoff, followed by the next-day forecast and an illustrative recent-error range.")
st.altair_chart(chart.configure_view(stroke=None).configure_axis(domain=False, labelFontSize=11, titleFontSize=11), width="stretch", theme="streamlit")
st.write(f"**{focus}:** expected **{detail.forecast_units:.0f}** sale units; ready target **{detail.target_units}** with your buffer. The recent-error planning range is **{detail.low_units}–{detail.high_units}** units.")
st.caption(f"Across the last {int(detail.review_days)} rolling next-day checks ({forecast.review_start:%d %b}–{forecast.review_end:%d %b}), this category’s average absolute forecast miss was {detail.review_mae_units:.1f} units/day. The range reflects recent misses, not guaranteed coverage or a measured service level.")

with st.expander("Forecast details and assumptions"):
    st.write("The forecast uses only sales recorded by the selected cutoff. For each category, three simple approaches are compared on an earlier 14-day window; the chosen approach is then checked on the following 14 days without choosing again. Each daily check uses only earlier sales.")
    st.caption(f"Method selection: {forecast.selection_start:%d %b}–{forecast.selection_end:%d %b}; separate review: {forecast.review_start:%d %b}–{forecast.review_end:%d %b}. Selected methods may differ between categories.")
    details = plan[["category", "forecast_units", "low_units", "high_units", "review_mae_units", "method"]].rename(columns={
        "category": "Category", "forecast_units": "Forecast", "low_units": "Planning low", "high_units": "Planning high", "review_mae_units": "Recent average miss", "method": "Selected approach"})
    st.dataframe(details, hide_index=True, width="stretch")
    st.write("Ready target = ceiling(forecast × (1 + buffer)); additions = max(0, ready target − usable stock). The default 10% buffer is an editable manager assumption. It is not calibrated from stockout costs or spoilage.")
    st.write("The planning range uses the 10th and 90th percentiles of the 14 recent signed forecast errors, expanded to include the point estimate and rounded outward. Fourteen checks are too few to promise a calibrated interval.")

with st.expander("Data quality and limits"):
    st.write(f"{len(df):,} original sales records retained; {sales.whitespace_fixed:,} labels trimmed; {sales.possible_duplicates:,} possible duplicate business records with different IDs retained for review. {sales.variable_price_products} products have multiple observed prices.")
    st.write("A date with store records but no sales in a category contributes zero category sales. A missing store-date stays unavailable; a plan requires 56 consecutive recorded days. Recorded sales can understate demand during stockouts.")
    st.write("There are no inventory balances, recipes, supplier pack sizes, delivery lead times, promotions, weather, holidays or recorded spoilage. Category plans cannot allocate quantities to individual products. No forecast accuracy, waste reduction or stockout improvement is guaranteed.")

st.divider()
st.caption(f"Source: {df.date.min():%d %b %Y}–{df.date.max():%d %b %Y} · Fictitious NYC coffee business · Intended refresh: after daily close; manager review: before the next-day order/prep cutoff. This demo reads a fixed CSV.")
