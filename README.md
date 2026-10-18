# Coffee Store Planning — Assignment 4

[Open the Streamlit dashboard](https://coffeesales-ws5pwjhzvkr3wg2juzkxip.streamlit.app/) · [GitHub repository](https://github.com/ExactValid/Coffee_Sales)

This dashboard helps the manager of one coffee store decide when to prepare more drinks and review shift coverage. It keeps the decision visible through **three headline metrics, two charts and two filters**. The sections below explain the dataset, the business decision, the content choices and the planned refresh process required by the course.

The published application consists of `app.py`, `coffee_data.py` and `Coffee Shop Sales.csv`. The complete local assignment also contains the Coffee EDA, phone-pricing notebook, tests and locked environment files; those additional files are not currently published here. Part 2 is submitted separately through Canvas.

## Step 1: Dataset and decision-maker

**Dataset:** Coffee Shop Sales. [Kaggle mirror](https://www.kaggle.com/datasets/ahmedabbas757/coffee-sales); [original Maven Analytics description](https://mavenanalytics.io/data-playground/coffee-shop-sales).

Maven describes transaction records for Maven Roasters, a **fictitious coffee business with three New York City locations**. Treat it as simulated business data rather than verified observations from real stores. The local file has 149,116 rows, 11 original columns and a size of about 13.33 MB. It covers 1 January through 30 June 2023, with sales on all 181 dates at each of three stores. No sampling or aggregation of the source file was necessary to meet the approximately 25 MB course guideline.

One row identifies one product sold at a store and timestamp, with its quantity and unit price. Although the identifier is called `transaction_id`, there is no receipt or customer identifier. Therefore, row counts are called **sales records**, not customers or receipt-level orders. A mean row amount is not called average order value.

**One decision-maker:** the manager of one store. The selector lets the classroom demonstration show any of the three stores; each real manager would open their assigned store by default.

## Step 2: Why this dashboard exists

**Who and how often?** The store manager checks it before opening for preparation and reviews it each week before planning the next week's shifts and preparation tasks.

**Decision sentence:** If the manager sees sustained growth in freshly prepared drink demand during an hour of the day, they will move preparation and ingredient checks ahead of that hour and review how existing staff are allocated around the peak. Demand is a workload proxy, not a calculation of required headcount.

**What happens without it?** Our business assumption is that the manager exports raw sales and manually summarizes hours, or relies on experience. This can consume preparation time or miss a changing peak. The dataset cannot establish the current process or quantify time saved, labor savings, queues or lost sales, so those are not presented as measured benefits.

**Why a dashboard?** The same person repeatedly asks the same questions and needs to switch dates and inspect the relevant time slots. A one-off report becomes stale; a weekly email cannot provide the same filtering. A production alert could supplement the dashboard for a particular exception, but does not replace the manager's weekly review.

## Step 3: EDA, choices and ordering

The local `Preprocessing.ipynb` contains the executed Pandas/Matplotlib EDA with tables and figures; that notebook is not currently published in this repository. It includes shape, types, missing values, duplicates, distributions, mapping checks, date coverage, price variation and time/product relationships.

### Findings that shaped the design

- June sales revenue is 103.8% above January, while sales records are up 104.2% and mean row value changes by only about -0.17%. Volume growth deserves attention.
- February total revenue is down 6.77% month over month, but daily average revenue is up 3.21%. Unequal month lengths can mislead.
- 08:00–10:59 accounts for about 36.2% of all-product sales records. Fresh-drink demand curves differ between stores, so the dashboard focuses on one store at a time.
- After adjusting for calendar counts, the busiest and quietest weekdays differ by only about 2.87% in daily sales records. Weekday totals should not be exaggerated.
- Coffee and Tea contribute about 66.7% of revenue. However, income contribution and preparation workload answer different questions.
- Highest versus lowest store revenue differs by only about 2.81%. A store leaderboard would distract from more useful operational variation.

### What we show

| Element | Definition | Why it is present |
|---|---|---|
| Sales revenue | Sum of quantity × actual unit price, in USD assumed from the NYC context | Overall recorded business activity; not profit |
| Freshly prepared drinks | Units in Coffee, Tea and Drinking Chocolate | Preparation workload proxy, excluding beans, merchandise and syrups |
| Sales records | Number of source rows | Another view of sales activity; not customer or complete order count |
| Daily revenue trend | Daily selected revenue; preceding equal-length period aligned by day | Show whether a change persists across dates |
| Weekday × hour heatmap | Drink units divided by observed dates of each weekday | Locate the hours needing preparation attention |
| Store and date filters | One store and one date range | The minimum controls needed for the decision |

The default window is the latest 28 complete dates in this snapshot: **3–30 June 2023**, compared with **6 May–2 June 2023**. Both contain four occurrences of every weekday. Arbitrary date ranges are allowed, with a caption when weekday mixes differ. Metrics omit change percentages when either period lacks full store-date coverage, or when the baseline is zero. Dates without any store records are unavailable and not automatically treated as zero sales. The historical snapshot does not indicate what is happening today.

The heatmap divides by observed **calendar dates**, including dates with no drink sales at an hour, not by dates with purchases of that drink. Weekdays absent from the filter, and hours outside that store's full-source observed hour range, are grey and unavailable. A zero within observed hours remains a zero. Neither the observed hour range nor an absent store-date is independent evidence of opening hours or closure.

### What we deliberately cut

1. **Top-ten product rankings.** Useful for a separate assortment analysis, but they do not directly locate preparation times and would add a third supporting chart.
2. **Weekday share pie charts.** They hide changes over time and unadjusted totals depend on weekday counts. The heatmap better answers the chosen operational question.

We also avoid customer retention, average order value, profit, inventory alerts and staffing-efficiency metrics because the required identifiers or denominators are absent.

### Page order

The top identifies the team, decision-maker, store and period, then shows the three metrics in `st.columns` with `st.metric`. The daily trend explains the change first; the heatmap then locates preparation slots. Supporting chart data and data-quality notes are collapsed at the bottom. The snapshot period and planned refresh frequency remain visible. This order prioritizes a quick scan before detail; there are exactly two charts.

### Cleaning and misleading data

- No missing values or repeated transaction IDs were found. The app validates required columns, positive integer quantities/IDs, prices, explicit `MM/DD/YY` dates, times and identifier mappings; invalid source replacements produce a clear error instead of silently dropping rows.
- 1,952 trailing spaces in Scottish Cream Scone were removed. Original records remain in the CSV; cleaning occurs in memory.
- 398 additional rows have identical business fields but different IDs. They are kept and disclosed because the dataset cannot prove an error.
- 15 products have multiple prices. Revenue uses each row's actual price, not a fixed product price. Variation is not automatically labeled a promotion.
- Large coffee-bean purchases are retained. The maximum row amount of $360 equals 8 × $45; an IQR flag alone is insufficient to delete it.
- Money is calculated in integer cents before display. USD is an explicit context assumption; the CSV contains no currency or time-zone field.
- Six months cannot establish annual seasonality, causality, service quality or optimal staffing. Source completeness within each observed date is not proven merely because all dates appear.

## Step 4: Refresh, review and action

**Refresh:** in production, load the completed day's point-of-sale records nightly after closing, ready before the next opening. Preparation and weekly assignments do not require a live refresh every minute. This demonstration reads a frozen CSV and does not pretend to update automatically. Replacing the CSV invalidates the in-memory load cache via the file modification timestamp; that cache is not a production data pipeline.

**Review:** brief daily review before opening; a fuller review during weekly planning. Refresh frequency and review frequency serve different purposes.

**Track and act:** compare an hour's average freshly prepared drink units over the latest complete four weeks with the preceding four weeks. As an initial business discussion threshold, growth greater than 20% on two consecutive weekly reviews would prompt a check of preparation and staff allocation. This threshold is uncalibrated, not a statistical significance test or an optimal policy. It is documented rather than implemented as an automatic alert, because the CSV has no continuing history of weekly review decisions.

**Cost of stale data:** a week-old view can miss increased demand or a shifted peak and leave preparation mismatched to demand. Queue times and financial losses cannot be estimated from this dataset. Inventory on hand and service-level monitoring would require additional sources.

## Part 2 — Phone trade-in analysis (Canvas notebook)

The separately submitted `phone-trade-in.ipynb` contains the full workflow and every numbered answer immediately after its supporting code. All **19 code cells** were executed in order under Python 3.14.3, yielding **43 saved outputs**, including **4 figure groups**, with no code errors. The supplied CSV was unchanged.

The specified split gives 4,000 training phones and 1,000 locked test phones (`test_size=0.2`, `random_state=409`). All original predictors except `phone_id` and `resale_price` are retained. Median imputation and scaling for numerical features, and mode imputation and one-hot encoding for categorical features, are fitted inside each pipeline and cross-validation fold. All parameter choices use five-fold training-only CV; the final test predictions and accuracy scores are calculated once and reused for interpretation and profit scenarios.

| Method | Test RMSE (USD) | Test MAE (USD) | Test R² |
| --- | --- | --- | --- |
| Baseline | 181.81 | 137.53 | -0.000009 |
| Linear regression | 98.01 | 71.35 | 0.709397 |
| SGD | 97.91 | 71.61 | 0.709970 |
| Random forest | 55.19 | 33.21 | 0.907832 |

The searches select SGD `eta0=0.01`, `max_iter=10000`, `tol=1e-5`, and a random forest with **150 trees and depth 10**. At the best of the seven tested forest offer rates, **75%**, the simulation buys **568 out of 1,000 quoted phones** for **USD 5,700.76 total gross profit**. Linear regression has R² of 0.7094 but loses USD 6,876.72 at a 75% offer, mainly in the 3–4-year age groups. The notebook explains why prediction accuracy and trading profit differ.

Profits exclude repair, inspection, shipping, returns and other operating costs. The data and seller-acceptance rule are simulated. Selecting the offer rate on these same test scenarios is required by the assignment; it is not an independent evaluation of the selected policy. A real deployment would need separate validation. Read and understand Q1–Q12 before submission, and review the Part 1 README rationale in your own words as required by the course.

The phone notebook and its supplied CSV are held in the local assignment folder for Canvas submission; they are not currently included in this Coffee dashboard repository.

## Run the published dashboard locally

Use Python **3.14** for this coursework. With `uv` installed, download this repository and run the following from the folder containing `app.py`:

```bash
uv run --python 3.14 --with streamlit==1.63.0 --with pandas==3.0.5 --with altair==6.2.2 streamlit run app.py
```

Keep `coffee_data.py` and `Coffee Shop Sales.csv` beside `app.py`. The CSV path is resolved relative to the application file, so moving the folder does not require editing a machine-specific path. The dashboard needs no secrets, external database or API.

The complete local assignment also has `pyproject.toml`, `uv.lock`, `.python-version`, `.streamlit/config.toml`, the notebooks and tests. When those supporting files are available in the same project folder, its locked environment can instead be restored with:

```bash
uv sync --locked --group notebook
uv run streamlit run app.py
```

The local dashboard/data test suite passed all 10 tests. It covers calendar-normalized demand, unavailable weekdays and hours, exact-cent totals, complete-period comparisons, input validation and Streamlit filter behavior. Those tests are maintained in the local assignment folder rather than this published repository.

## Deployment and availability

The app is deployed from this repository with **`app.py`** as the entry point. To recreate the full course deployment, also publish the dependency and environment files from the local assignment folder, then explicitly select **Python 3.14** in Streamlit Community Cloud's advanced deployment settings. A local `.python-version` file does not replace the Cloud setting. See [deployment settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [dependency handling](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

If deployment reports `No module named 'coffee_data'`, check that `coffee_data.py` was committed beside `app.py`; it is a local module. The CSV must also be present. The app's metric and chart colors follow the active Streamlit theme.

**If the app is sleeping:** Community Cloud hibernates apps after 12 hours without traffic. Click **“Yes, get this app back up!”** and wait for the dashboard to load. Any visitor with viewing access can wake it. This hosting behavior is separate from the data refresh policy: the dashboard remains a historical January–June 2023 snapshot. See [Streamlit's official hibernation explanation](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app#app-hibernation).

## Assignment submission

Upload **`phone-trade-in.ipynb`** to Canvas with its saved outputs. Its first Markdown cell contains the deployed app URL and GitHub repository URL. The repository and Streamlit deployment must be under the student's own accounts, and the README design rationale must be reviewed and expressed in the student's own words, as required by the assignment.

Before submission, confirm the team name displayed by the app (`Coffee Operations Team` is the current working name), the exact Kaggle mirror used for the download, public access to the app, and both links in the notebook. All Part 2 code outputs and numbered answers have already been saved in the local notebook.
