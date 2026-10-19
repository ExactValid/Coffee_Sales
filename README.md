# Coffee — Store Manager’s Desk

**Team:** team9

[Open the dashboard](https://coffeesales-ws5pwjhzvkr3wg2juzkxip.streamlit.app/) · [GitHub repository](https://github.com/ExactValid/Coffee_Sales)

The store manager uses **Today’s To-do** to compare the last completed day’s category sales with the next-day forecast, check usable stock, and decide **what to prepare or replenish, and how many sale units to have ready**. Three pages separate the daily action from supporting analysis: **Today’s To-do**, **Sales review**, and **Forecast & data**. Each page serves one selected store and planning date.

**Historical demonstration:** the source ends on **30 June 2023**. The default plan is for **1 July 2023**, using sales known at the close of 30 June. On the interface, **yesterday** means the selected completed sales day and **today** means the following planning day. Thus the default home page compares yesterday’s 30 June sales with a plan for today, 1 July 2023; these labels do not refer to the visitor’s current calendar date. The app does not have a live inventory or point-of-sale connection.

## Step 1 — Dataset and decision-maker

**Dataset:** Coffee Shop Sales, with 149,116 sales records and 11 original columns, approximately 13.33 MB. It covers 1 January–30 June 2023 at three New York City stores. Sources: [Kaggle mirror](https://www.kaggle.com/datasets/ahmedabbas757/coffee-sales) and [original Maven Analytics description](https://mavenanalytics.io/data-playground/coffee-shop-sales). Maven Roasters is a fictitious business; these findings do not establish real-store demand.

One row records a product, quantity, store and timestamp. The plan sums **transaction_qty**, rather than counting rows or dividing revenue by a typical price. The file has no complete receipt or customer identifier, so rows are not treated as customers or complete orders.

The nine recorded categories are Coffee, Tea, Bakery, Drinking Chocolate, Flavours, Coffee beans, Branded, Loose Tea and Packaged Chocolate. A unit means the source's **sale unit within that category**. Categories contain different products, sizes or pack formats. Counts are not added into one total inventory number, and a category quantity does not specify its product mix.

**Decision-maker:** the store manager responsible for category preparation of one store, reviewing the dashboard **after the day's sales are complete and before the next-day ordering or preparation cutoff**. The store selector supports the three-store classroom demonstration; each manager makes the plan for their own store.

## Step 2 — The business decision

**Decision sentence:** If the manager sees that tomorrow's category preparation target exceeds the stock that will still be usable, they will prepare or replenish the difference, after checking the forecast's recent errors and local circumstances.

This project focuses on **how much of each category to have available tomorrow**. The manager enters usable carryover, including only items that will remain fit for sale. For drinks, they enter the serving-equivalent portions supported by ingredients on hand, using their own recipe conversion; this is not a recommendation to make all drinks in advance.

The daily workflow is:

1. Select the store and its last completed sales day; the next day is the planning date.
2. Start on **Today’s To-do**: compare each category’s **Yesterday sold**, **Predicted today**, **Ready target**, **Usable stock**, **Prepare / add**, and next action.
3. Enter usable stock; leave unchecked quantities blank. Confirmed positive additions rise to the top.
4. Open **Sales review** for yesterday’s revenue, recorded sale units and sales records versus the day before, plus the last 28 days of category sales and the planning-day forecast. Open **Forecast & data** for recent forecast errors, method selection and data limits.
5. Return to the To-do page, translate category targets into specific products/recipes/supplier packs, and download the plan. Store, closing date, buffer and entered stock survive page changes within the browser session.

The app keeps these quantities distinct:

- **Expected sales:** the next-day category demand estimate, shown rounded to a whole sale unit.
- **Ready target:** `ceiling(unrounded forecast × (1 + manager buffer))`.
- **Prepare / add:** `max(0, ready target − entered usable stock)`.

An unknown inventory balance produces a **stock-check action and a blank addition**, not an assumed zero. Entering zero explicitly means the manager checked and found none. Stock above the target results in zero additions, never a negative order. Entries are temporary in the browser session and are kept separate for each store/cutoff; download the plan to retain them. Do not enter sensitive operational information into this public coursework demo.

**Why a dashboard?** The manager repeats this decision every day, needs to compare categories, and must change the usable-stock input before seeing the final additions. A static report would not recalculate that decision. Without the tool, our assumed alternative is a manual category sales summary plus a stock check; the dataset does not establish the actual current process or measure time saved.

**Business trade-off:** a larger target may reduce the risk of insufficient preparation, but can increase excess stock and spoilage. The default **10% buffer**, adjustable from 0% to 30%, is a visible manager assumption. It is not an optimized order policy or a measured service level because costs, shelf lives and stockout records are absent.

## Step 3 — Evidence, presentation and deliberate cuts

### Findings that shaped the page

- All three stores have records on the source's 181 dates, permitting daily category histories. A category with no sales on a recorded store-day contributes zero; a missing store-day remains unavailable.
- Coffee and Tea dominate recorded sale units (89,250 and 69,737 across the full source); Bakery contributes 23,214. Category-level preparation makes the differences actionable without assuming identical ingredient needs.
- June revenue exceeds January by 103.8%, while records rise by 104.2%. The plan therefore uses recent category quantities rather than a fixed average across all six months.
- After accounting for calendar counts, all-product daily record counts differ by only about 2.87% between the busiest and quietest weekday. This does not prove every category lacks a weekday pattern; both recent averages and matching-weekday approaches are checked.
- Sparse categories can be difficult to forecast in percentage terms even when the absolute miss is only a few units. The page shows the average miss in **that category's units**, instead of claiming one accuracy score for unlike products.

The executed Coffee EDA is in `Preprocessing.ipynb`. The forecast is separately checked on chronological daily observations rather than selecting a model by looking at tomorrow's outcome.

### What the manager sees, and why

| Element | Definition and purpose |
|---|---|
| Today’s To-do: category plan | Yesterday’s actual sale units, today’s forecast, buffered ready target, usable stock, additions and next action. This is the default page and directly supports preparation. |
| To-do headline metrics | At most three: categories planned, stock checks left, and categories with confirmed positive additions. Unknown inventory is never reported as a confirmed zero shortfall. |
| Sales review | Three separate review metrics—yesterday’s revenue, recorded sale units and sales records—with day-before changes. One supporting chart shows the last 28 recorded days, planning-day forecast and illustrative recent-error range for one category. |
| Forecast & data | Category error table, selected approaches, stock/forecast formulas and limitations. This evidence remains available without extending the daily To-do page. |
| Store and sales-through date | Define whose plan is being made and the information available at that close. |
| Manager's buffer and usable-stock editor | Explicit planning inputs that change ready targets and additions; they do not change the demand forecast. |
| Downloadable plan | Preserves the cutoff, forecast date, store, quantities, errors, selected method and assumptions for review. |

Confirmed additions appear first, followed by outstanding stock checks and categories covered by usable stock. The home page uses a desktop table; narrow screens use category cards showing yesterday’s sales, today’s prediction, the ready target and addition/action without horizontal table scrolling. Supporting sales analysis and forecast/data notes have their own pages rather than sitting below the entire To-do list. A native top navigation menu gives each secondary page its own URL (`/sales` and `/forecast`); only the selected page’s content is rendered. The app remains in `app.py`, with no extra page files or dependencies. Shared filters and separate session stock storage prevent page navigation from discarding manager inputs. See [Streamlit navigation](https://docs.streamlit.io/develop/api-reference/navigation/st.navigation) and [cross-page widget state](https://docs.streamlit.io/develop/concepts/multipage-apps/widgets).

The warm neutral background and restrained green accents keep attention on the quantities. Ready targets have a highlighted column; text labels distinguish stock checks, positive additions and covered categories without relying on color alone. A sortable version of the plan remains available in an expander, while the trend panel separates the recorded sales line from the amber next-day forecast.

### What we deliberately leave out

1. **Revenue as a home-page headline and a daily revenue chart.** Revenue cannot determine preparation units because prices and product mix change it. Yesterday’s revenue is available as secondary context on Sales review, while the To-do page stays focused on category quantities and unresolved stock checks.
2. **Weekday-by-hour heatmap and staffing suggestions.** They address intraday readiness and shift planning, while this manager is setting category quantities for the next day.
3. **Store league tables and a long list of product rankings.** These add comparisons that do not finish the selected store's category plan.

The app also avoids profit, savings, retention, automatic supplier orders and claims about reduced waste. Those outcomes require information or intervention evidence the CSV does not contain. Product-level allocation and ingredient purchasing are future extensions, not hidden capabilities of a category forecast.

### Cleaning and safeguards

- The original CSV is preserved. All 149,116 records are retained.
- No missing values or repeated transaction IDs were found. Required fields, positive integer IDs/quantities, prices, dates, times and product/store mappings are validated; invalid replacements stop with an explanation.
- 1,952 labels have trailing spaces removed in memory. The 398 additional records with identical business fields but different IDs remain because they cannot be established as errors.
- Fifteen products have multiple observed prices, and high-value bean purchases are retained. Neither fact is a reason to remove sale quantities.
- A plan requires **56 consecutive recorded store-days**. A missing day is not filled with zero demand. Category absence on an otherwise recorded day is assumed to be zero recorded sales, which does not prove complete source coverage.
- Forecasts stop at the selected cutoff. Later rows and newly appearing future categories cannot change a historical plan.
- Recorded sales may be constrained by stockouts; the data cannot distinguish unmet demand from genuinely low interest. It has no verified opening schedule, currency field, recipes, stock balances, spoilage, lead times, weather, promotions or holiday annotations.

### Forecast approach and separate review

For each category, the following candidates are defined before reviewing performance:

1. Average quantity over the preceding **7 days**.
2. Average quantity on the preceding **4 matching weekdays** (lags 7, 14, 21 and 28 days).
3. The matching-weekday average multiplied by the preceding 7-day average divided by the previous 7-day average. The multiplier is limited to **0.5–1.5**; when the earlier average is zero, it is set to 1. These limits are fixed safeguards, not tuned on the review window.

At each cutoff, the earlier **14 daily forecast checks** select the lowest-mean-absolute-error candidate for each category. That selection is fixed before evaluating the following **14 days**. Each rolling check forecasts one day using only earlier observations, including earlier review days once they have actually occurred. The selected rule then produces the next-day forecast using all information available at the close. No random train/test split is used for this time-dependent task.

At the default cutoff, selection dates are **3–16 June 2023**, and separate review dates are **17–30 June 2023**. The app reports the category's mean absolute miss over that later window. Fourteen checks are a small, local evaluation; they do not establish future reliability under promotions, holidays or changed demand.

The displayed **planning range** adds the 10th and 90th percentiles of the later window's signed errors (`actual − forecast`) to the point forecast, expands the range to include the point, clips the lower end at zero and rounds outward. It is an illustrative recent-error envelope, **not a calibrated 80% prediction interval or a service-level guarantee**. The separate manager buffer is not derived from this range.

The use of simple benchmarks and chronological rolling evaluation follows the principles in [Forecasting: Principles and Practice, Chapter 5](https://otexts.com/fpp3/toolbox.html). The specific candidates, date windows and stock formulas above are this project's implementation choices.

### Default example — Lower Manhattan, plan for 1 July 2023

Usable stock is initially unknown, so the following are **ready targets**, not finalized additions. With the default 10% buffer:

| Category | Forecast sale units | Ready target | Recent-error planning range | Average miss / day, 17–30 Jun |
|---|---:|---:|---:|---:|
| Coffee | 222.5 | 245 | 180–316 | 48.6 |
| Tea | 195.1 | 215 | 150–251 | 34.1 |
| Bakery | 68.6 | 76 | 49–89 | 13.4 |
| Drinking Chocolate | 45.7 | 51 | 32–58 | 8.0 |
| Flavours | 22.8 | 26 | 1–53 | 18.3 |
| Coffee beans | 4.3 | 5 | 0–9 | 2.6 |
| Branded | 3.1 | 4 | 0–5 | 1.9 |
| Loose Tea | 2.1 | 3 | 0–4 | 2.0 |
| Packaged Chocolate | 1.3 | 2 | 0–3 | 1.1 |

For example, Coffee's unrounded estimate is **222.5**, yielding a ready target of **245**. If the manager enters **80 usable serving equivalents**, the addition becomes **165**. Its recent average miss is **48.6 units/day**, so the 10% buffer is not a promise of sufficient stock. The chart provides context for the manager's judgment rather than making the order automatically.

## Step 4 — Refresh, review and action

**Refresh after close:** in production, append the completed day's store/category sales after daily closing, validate completeness, and rebuild the next-day plan before the relevant ordering/preparation cutoff. This demo reads a frozen CSV; replacing it invalidates the load/forecast cache through the file modification timestamp. It has no automatic data ingestion.

**Review daily:** the store manager checks all category targets after close, enters tomorrow-usable stock, inspects unusual category forecasts and reviews positive additions. A weekly review of forecast misses and actual leftovers would inform future adjustments once those records exist.

**Action rule:** a category with entered usable stock below its ready target is a candidate to prepare/replenish by the calculated difference. Unchecked stock is an unresolved task; stock at or above target needs no addition under this one-day rule. The manager still checks expiry, capacity, local events, supplier timing and recipe/SKU allocation before approving action. The app does not issue a purchase order.

**Why not a live minute-by-minute refresh?** This decision is made after daily close for the next day. Incomplete intraday totals would understate a full day's demand. A stale close can miss recent changes and produce excess preparation or shortages; this dataset cannot quantify the cost or prove that the dashboard prevents either outcome. Long-lead procurement would need a different horizon and inventory policy.

## Run and verify

Use Python **3.14** for the course. Dependencies are declared in `pyproject.toml` and locked in `uv.lock`; `.python-version` selects the local version.

```bash
uv sync --locked --group notebook
uv run streamlit run app.py
uv run python -m unittest discover -s tests -v
```

The application resolves its CSV beside `app.py`. No machine-specific data path, secret, API or external database is required. The two Python modules contain the interface and data/forecast/stock calculations. Both cleaned-data helpers and the existing Coffee EDA remain available.

All **25 tests** pass under Python 3.14. They cover source totals, date/quantity validation, missing store-days, zero category sales on observed days, cutoff leakage, separation of method selection and later review, unknown/zero/excess usable stock, invalid inputs, store/date/category interactions, changing the buffer, a stock edit updating additions, recorded yesterday-sales reconciliation, separate page content, persistence of stock/filters across navigation, and rejecting fractional usable stock without silently truncating it.

## Streamlit deployment and availability

Deploy this public repository using **`app.py`** as the main file. Keep `coffee_data.py`, `Coffee Shop Sales.csv`, `pyproject.toml`, `uv.lock`, `.python-version` and the root `.streamlit/config.toml` with it. In Streamlit Community Cloud's advanced settings, explicitly select **Python 3.14** for the course; the local version file does not replace that setting. See [deployment settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [dependency handling](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

Community Cloud may put an app to sleep after 12 hours without traffic. If the sleep page appears, click **“Yes, get this app back up!”** and wait for the dashboard. This hosting behavior is separate from the historical data cutoff and intended daily data refresh. See [official hibernation guidance](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app#app-hibernation).

## Part 2 and Canvas submission

The separate local `phone-trade-in.ipynb` is complete: 19 executed code cells, 43 saved outputs, 4 figure groups and Q1–Q12 immediately after their supporting code. The phone dataset, notebook outputs and models are unchanged by this dashboard redesign. On the specified 1,000-phone test sample, the best random forest has RMSE **USD 55.19** and R² **0.9078**; its best tested 75% offer buys **568 phones** for simulated gross profit **USD 5,700.76**, before operating costs. Those are Part 2 results, not a model for coffee sales.

For Assignment 4, upload **`phone-trade-in.ipynb`** with its saved outputs to Canvas. The first Markdown cell contains the app and repository links. The phone notebook and CSV remain in the local assignment folder; the Coffee app repository contains this dashboard, its EDA, tests and environment files. The project team is **team9**. Confirm individual account ownership, exact Kaggle download source and the README rationale in your own words before submission.
