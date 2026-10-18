"""Conservative cleaning and calendar-aware aggregates for the dashboard."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "transaction_id", "transaction_date", "transaction_time", "transaction_qty",
    "store_id", "store_location", "product_id", "unit_price", "product_category",
    "product_type", "product_detail",
]
TEXT_COLUMNS = ["store_location", "product_category", "product_type", "product_detail"]
DRINK_CATEGORIES = ["Coffee", "Tea", "Drinking Chocolate"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass(frozen=True)
class SalesData:
    frame: pd.DataFrame
    whitespace_fixed: int
    possible_duplicates: int
    variable_price_products: int


@dataclass(frozen=True)
class Period:
    start: pd.Timestamp
    end: pd.Timestamp
    previous_start: pd.Timestamp
    previous_end: pd.Timestamp
    days: int


def load_sales(path: str | Path) -> SalesData:
    """Keep every valid source row; refuse ambiguous or invalid core data."""
    raw = pd.read_csv(path, encoding="utf-8-sig")
    missing = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    df = raw[REQUIRED_COLUMNS].copy()
    if df.empty:
        raise ValueError("Source data contains no sales records.")
    if df.isna().any().any():
        raise ValueError("Source data contains missing values. Review them before publishing.")
    possible_duplicates = int(df.duplicated(df.columns.drop("transaction_id").tolist()).sum())
    whitespace_fixed = 0
    for column in TEXT_COLUMNS:
        cleaned = df[column].astype("string").str.strip()
        whitespace_fixed += int(df[column].ne(cleaned).sum())
        if cleaned.eq("").any():
            raise ValueError(f"Blank labels in {column}.")
        df[column] = cleaned
    for column in ["transaction_id", "transaction_qty", "store_id", "product_id"]:
        values = pd.to_numeric(df[column], errors="coerce")
        if values.isna().any() or values.mod(1).ne(0).any() or values.le(0).any():
            raise ValueError(f"{column} must contain positive whole numbers.")
        df[column] = values.astype("int64")
    if df.transaction_id.duplicated().any():
        raise ValueError("Duplicate transaction IDs require review; no records were removed.")
    prices = pd.to_numeric(df.unit_price, errors="coerce")
    if prices.isna().any() or prices.le(0).any() or prices.isin([float('inf'), float('-inf')]).any():
        raise ValueError("Unit prices must be positive numbers.")
    if prices.mul(100).sub(prices.mul(100).round()).abs().gt(1e-6).any():
        raise ValueError("Unit prices with more than two decimal places require review.")
    df["unit_price"] = prices
    df["date"] = pd.to_datetime(df.transaction_date, format="%m/%d/%y", errors="coerce")
    parsed_time = pd.to_datetime(df.transaction_time, format="%H:%M:%S", errors="coerce")
    if df.date.isna().any() or parsed_time.isna().any():
        raise ValueError("Invalid dates or times. Expected MM/DD/YY and HH:MM:SS.")
    for key, label in [("store_id", "store_location"), ("store_location", "store_id"),
                       ("product_id", "product_detail"), ("product_id", "product_type"),
                       ("product_id", "product_category")]:
        if df.groupby(key)[label].nunique().gt(1).any():
            raise ValueError(f"Inconsistent mapping between {key} and {label}.")
    df["hour"] = parsed_time.dt.hour
    df["weekday_num"] = df.date.dt.dayofweek
    df["unit_price_cents"] = prices.mul(100).round().astype("int64")
    df["revenue_cents"] = df.transaction_qty * df.unit_price_cents
    df["is_drink"] = df.product_category.isin(DRINK_CATEGORIES)
    variable_prices = int(df.groupby("product_id").unit_price_cents.nunique().gt(1).sum())
    return SalesData(df, whitespace_fixed, possible_duplicates, variable_prices)


def make_period(start: date | pd.Timestamp, end: date | pd.Timestamp) -> Period:
    start, end = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    if start > end:
        raise ValueError("Start date must be on or before end date.")
    days = (end - start).days + 1
    previous_end = start - pd.Timedelta(days=1)
    return Period(start, end, previous_end - pd.Timedelta(days=days - 1), previous_end, days)


def select_period(store: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return store.loc[store.date.between(start, end)].copy()


def has_full_coverage(store: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> bool:
    expected = pd.date_range(start, end)
    observed = pd.DatetimeIndex(store.loc[store.date.between(start, end), "date"].unique())
    return len(expected.difference(observed)) == 0


def totals(rows: pd.DataFrame) -> dict[str, int]:
    return {"revenue_cents": int(rows.revenue_cents.sum()),
            "drinks": int(rows.loc[rows.is_drink, "transaction_qty"].sum()),
            "records": len(rows)}


def percent_change(current: int | float, previous: int | float) -> float | None:
    return None if previous <= 0 else (current / previous - 1) * 100


def daily_series(store: pd.DataFrame, period: Period, include_previous: bool) -> pd.DataFrame:
    """Missing store-days remain unavailable, never silently filled with sales zero."""
    blocks = []
    for start, end, label in [(period.start, period.end, "Selected period"),
                              (period.previous_start, period.previous_end, "Previous period")]:
        if label == "Previous period" and not include_previous:
            continue
        rows = select_period(store, start, end)
        daily = rows.groupby("date").revenue_cents.sum().reindex(pd.date_range(start, end))
        block = pd.DataFrame({"source_date": daily.index, "revenue_usd": daily.values / 100})
        block["plot_date"] = pd.date_range(period.start, period.end)
        block["period"] = label
        blocks.append(block)
    return pd.concat(blocks, ignore_index=True)


def hourly_demand(store: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    """Use observed calendar dates as the denominator, including zero-drink dates."""
    observed_dates = selected[["date", "weekday_num"]].drop_duplicates()
    denominators = observed_dates.groupby("weekday_num").size().reindex(range(7), fill_value=0)
    drinks = selected.loc[selected.is_drink]
    hours = range(6, 21)
    grid = pd.MultiIndex.from_product([range(7), hours], names=["weekday_num", "hour"])
    units = drinks.groupby(["weekday_num", "hour"]).transaction_qty.sum().reindex(grid, fill_value=0)
    heatmap = units.rename("drink_units").reset_index()
    heatmap["observed_days"] = heatmap.weekday_num.map(denominators)
    heatmap["avg_drinks"] = heatmap.drink_units.div(heatmap.observed_days.replace(0, float("nan")))
    # The source has no opening-hours schedule: do not invent demand outside observed hours.
    min_hour, max_hour = int(store.hour.min()), int(store.hour.max())
    heatmap.loc[~heatmap.hour.between(min_hour, max_hour), "avg_drinks"] = float("nan")
    heatmap["weekday"] = heatmap.weekday_num.map(dict(enumerate(WEEKDAYS)))
    heatmap["hour_label"] = heatmap.hour.map(lambda hour: f"{hour:02}:00")
    heatmap["availability"] = heatmap.avg_drinks.map(lambda x: "Unavailable" if pd.isna(x) else "Observed")
    return heatmap

# Next-day category planning. Legacy aggregation helpers above are retained for EDA.
from math import ceil, floor, isfinite


FORECAST_METHODS = ("Recent 7-day average", "Last 4 matching weekdays", "Weekday average + recent trend")
MIN_PLANNING_DAYS = 56


@dataclass(frozen=True)
class CategoryForecast:
    as_of: pd.Timestamp
    target_date: pd.Timestamp
    daily: pd.DataFrame
    summary: pd.DataFrame
    validation: pd.DataFrame
    selection_start: pd.Timestamp
    selection_end: pd.Timestamp
    review_start: pd.Timestamp
    review_end: pd.Timestamp


def category_daily_units(rows: pd.DataFrame, store_name: str, as_of) -> pd.DataFrame:
    """One row per calendar day through cutoff; an unobserved store-day stays unknown."""
    cutoff = pd.Timestamp(as_of).normalize()
    past = rows.loc[rows.store_location.eq(store_name) & rows.date.le(cutoff)]
    if past.empty:
        raise ValueError("No recorded sales are available for this store and cutoff.")
    dates = pd.date_range(past.date.min(), cutoff, name="date")
    categories = sorted(past.product_category.unique())
    daily = past.groupby(["date", "product_category"]).transaction_qty.sum().unstack(fill_value=0)
    daily = daily.reindex(index=dates, columns=categories).astype(float)
    return daily


def forecast_categories(daily: pd.DataFrame, as_of) -> CategoryForecast:
    """Select on the earlier 14 rolling origins; report the next 14 without reselection."""
    cutoff = pd.Timestamp(as_of).normalize()
    history = daily.loc[daily.index <= cutoff].copy()
    if history.empty or history.index[-1] != cutoff:
        raise ValueError("The chosen sales-through date must have recorded store data.")
    if not history.index.is_unique or not history.index.is_monotonic_increasing:
        raise ValueError("Daily sales must have unique dates in chronological order.")
    expected_dates = pd.date_range(cutoff - pd.Timedelta(days=55), cutoff)
    recent = history.reindex(expected_dates)
    if len(history) < MIN_PLANNING_DAYS or recent.isna().any().any():
        raise ValueError("Planning needs 56 consecutive recorded store-days. Missing days are not zero demand; choose another date or review the source.")
    if (recent < 0).any().any() or not recent.map(isfinite).all().all():
        raise ValueError("Daily sale quantities must be finite and nonnegative.")
    target = cutoff + pd.Timedelta(days=1)
    extended = recent.reindex(pd.date_range(expected_dates[0], target))
    recent7 = extended.shift(1).rolling(7, min_periods=7).mean()
    prior7 = extended.shift(8).rolling(7, min_periods=7).mean()
    weekday = sum(extended.shift(lag) for lag in (7, 14, 21, 28)) / 4
    ratio = recent7.div(prior7.where(prior7 > 0)).fillna(1).clip(lower=0.5, upper=1.5)
    candidates = dict(zip(FORECAST_METHODS, (recent7, weekday, weekday * ratio)))
    selection = pd.date_range(cutoff - pd.Timedelta(days=27), cutoff - pd.Timedelta(days=14))
    review = pd.date_range(cutoff - pd.Timedelta(days=13), cutoff)
    summaries, validation_rows = [], []
    for category in recent.columns:
        selection_mae = {
            method: (values.loc[selection, category] - recent.loc[selection, category]).abs().mean()
            for method, values in candidates.items()
        }
        chosen = min(FORECAST_METHODS, key=selection_mae.get)
        predicted = candidates[chosen].loc[review, category]
        actual = recent.loc[review, category]
        residual = actual - predicted
        point = max(0.0, float(candidates[chosen].loc[target, category]))
        # The envelope includes the point forecast; it is not a calibrated coverage claim.
        lower = max(0, floor(min(point, point + float(residual.quantile(0.10)))))
        upper = ceil(max(point, point + float(residual.quantile(0.90))))
        denominator = float(actual.sum())
        summaries.append({
            "category": category, "forecast_units": point,
            "low_units": lower, "high_units": upper, "method": chosen,
            "selection_mae_units": float(selection_mae[chosen]),
            "review_mae_units": float(residual.abs().mean()),
            "review_wape": float(residual.abs().sum() / denominator) if denominator > 0 else None,
            "review_days": len(review), "recent7_units": float(recent[category].tail(7).mean()),
        })
        for day in review:
            validation_rows.append({"date": day, "category": category,
                                    "actual_units": float(actual.loc[day]),
                                    "forecast_units": float(predicted.loc[day]), "method": chosen})
    summary = pd.DataFrame(summaries).sort_values("forecast_units", ascending=False).reset_index(drop=True)
    return CategoryForecast(cutoff, target, recent, summary, pd.DataFrame(validation_rows),
                            selection[0], selection[-1], review[0], review[-1])


def make_stock_plan(forecasts: pd.DataFrame, buffer_pct: float, stock: dict | None = None) -> pd.DataFrame:
    """Unknown usable stock never becomes an assumed zero; known stock is sale-unit equivalents."""
    if not isfinite(float(buffer_pct)) or not 0 <= float(buffer_pct) <= 30:
        raise ValueError("Choose a safety buffer between 0% and 30%.")
    supplied = stock or {}
    plan = forecasts.copy()
    targets, available, additions, statuses = [], [], [], []
    for row in plan.itertuples():
        prediction = float(row.forecast_units)
        if not isfinite(prediction) or prediction < 0:
            raise ValueError("Forecast quantities must be finite and nonnegative.")
        target = ceil(prediction * (1 + float(buffer_pct) / 100))
        raw = supplied.get(row.category)
        if raw is None or pd.isna(raw):
            known, addition, status = None, None, "Check usable stock"
        else:
            value = float(raw)
            if not isfinite(value) or value < 0 or value % 1:
                raise ValueError("Available stock must be a nonnegative whole number, or left blank.")
            known = int(value)
            addition = max(0, target - known)
            status = "Prepare / replenish" if addition else "Covered by usable stock"
        targets.append(target)
        available.append(known)
        additions.append(addition)
        statuses.append(status)
    plan["target_units"] = pd.array(targets, dtype="Int64")
    plan["available_units"] = pd.array(available, dtype="Int64")
    plan["add_units"] = pd.array(additions, dtype="Int64")
    plan["action"] = statuses
    plan["buffer_pct"] = float(buffer_pct)
    plan["priority"] = plan.action.map({"Prepare / replenish": 0, "Check usable stock": 1, "Covered by usable stock": 2})
    return plan.sort_values(["priority", "add_units", "target_units"], ascending=[True, False, False], na_position="last").drop(columns="priority").reset_index(drop=True)
