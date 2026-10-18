from pathlib import Path
import tempfile
import unittest
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coffee_data import (
    has_full_coverage, hourly_demand, load_sales, make_period,
    percent_change, select_period, totals,
)


class FullDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sales = load_sales(ROOT / "Coffee Shop Sales.csv")
        cls.df = cls.sales.frame

    def test_source_reconciles_to_known_totals(self):
        self.assertEqual(len(self.df), 149116)
        self.assertEqual(int(self.df.transaction_qty.sum()), 214470)
        self.assertEqual(totals(self.df)["revenue_cents"], 69881233)
        self.assertEqual(self.sales.whitespace_fixed, 1952)
        self.assertEqual(self.sales.possible_duplicates, 398)
        self.assertEqual(self.sales.variable_price_products, 15)

    def test_default_window_matches_weekdays_and_has_comparison(self):
        period = make_period("2023-06-03", "2023-06-30")
        self.assertEqual(period.days, 28)
        self.assertEqual(period.previous_start, pd.Timestamp("2023-05-06"))
        self.assertEqual(period.previous_end, pd.Timestamp("2023-06-02"))
        store = self.df.loc[self.df.store_location.eq("Lower Manhattan")]
        self.assertTrue(has_full_coverage(store, period.start, period.end))
        self.assertTrue(has_full_coverage(store, period.previous_start, period.previous_end))
        self.assertFalse(has_full_coverage(store, pd.Timestamp("2022-12-31"), pd.Timestamp("2023-01-01")))

    def test_missing_store_day_is_unavailable_not_sales_zero(self):
        from coffee_data import daily_series
        store = self.df.loc[self.df.store_location.eq("Lower Manhattan")]
        store = store.loc[store.date.ne(pd.Timestamp("2023-06-15"))]
        period = make_period("2023-06-03", "2023-06-30")
        self.assertFalse(has_full_coverage(store, period.start, period.end))
        daily = daily_series(store, period, False)
        self.assertTrue(pd.isna(daily.loc[daily.source_date.eq(pd.Timestamp("2023-06-15")), "revenue_usd"].iloc[0]))

    def test_unobserved_hours_and_absent_weekdays_remain_unavailable(self):
        store = self.df.loc[self.df.store_location.eq("Astoria")]
        selected = select_period(store, pd.Timestamp("2023-06-30"), pd.Timestamp("2023-06-30"))
        heatmap = hourly_demand(store, selected)
        self.assertTrue(heatmap.loc[heatmap.weekday_num.ne(4), "avg_drinks"].isna().all())
        self.assertTrue(heatmap.loc[heatmap.hour.eq(6), "avg_drinks"].isna().all())
        self.assertTrue(heatmap.loc[heatmap.hour.eq(20), "avg_drinks"].isna().all())

    def test_demand_denominator_includes_observed_dates_without_drinks(self):
        # Two observed Mondays. Only one has drinks; the other has a bakery record.
        rows = pd.DataFrame({
            "date": pd.to_datetime(["2023-06-05", "2023-06-12"]),
            "weekday_num": [0, 0], "hour": [10, 10],
            "is_drink": [True, False], "transaction_qty": [8, 1],
        })
        heatmap = hourly_demand(rows, rows)
        cell = heatmap.loc[heatmap.weekday_num.eq(0) & heatmap.hour.eq(10)].iloc[0]
        self.assertEqual(cell.observed_days, 2)
        self.assertEqual(cell.avg_drinks, 4.0)

    def test_zero_baseline_and_reversed_dates(self):
        self.assertIsNone(percent_change(12, 0))
        self.assertAlmostEqual(percent_change(120, 100), 20)
        with self.assertRaises(ValueError):
            make_period("2023-06-30", "2023-06-01")

    def test_invalid_source_requires_review(self):
        row = self.df.iloc[[0]][[
            "transaction_id", "transaction_date", "transaction_time", "transaction_qty",
            "store_id", "store_location", "product_id", "unit_price", "product_category",
            "product_type", "product_detail",
        ]].copy()
        task_temp = ROOT / ".test_tmp"
        task_temp.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=task_temp) as directory:
            path = Path(directory) / "invalid.csv"
            row.loc[:, "transaction_qty"] = 0
            row.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "positive whole numbers"):
                load_sales(path)
            row.loc[:, "transaction_qty"] = 1
            pd.concat([row, row]).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "Duplicate transaction IDs"):
                load_sales(path)

from coffee_data import category_daily_units, forecast_categories, make_stock_plan


class CategoryPlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = load_sales(ROOT / "Coffee Shop Sales.csv").frame
        cls.daily = category_daily_units(cls.frame, "Lower Manhattan", "2023-06-30")
        cls.forecast = forecast_categories(cls.daily, "2023-06-30")

    def test_daily_categories_reconcile_to_original_units(self):
        self.assertEqual(int(self.daily.to_numpy().sum()), int(self.frame.loc[self.frame.store_location.eq("Lower Manhattan"), "transaction_qty"].sum()))
        self.assertEqual(self.daily.shape, (181, 9))

    def test_future_rows_and_new_categories_do_not_change_a_past_forecast(self):
        cutoff = pd.Timestamp("2023-05-30")
        before = category_daily_units(self.frame, "Lower Manhattan", cutoff)
        changed = self.frame.copy()
        future = changed.date.gt(cutoff)
        changed.loc[future, "transaction_qty"] = 1000000
        changed.loc[future, "product_category"] = "Future-only category"
        after = category_daily_units(changed, "Lower Manhattan", cutoff)
        pd.testing.assert_frame_equal(before, after)
        pd.testing.assert_frame_equal(forecast_categories(before, cutoff).summary, forecast_categories(after, cutoff).summary)

    def test_missing_store_days_are_not_category_zero(self):
        changed = self.frame.loc[self.frame.date.ne(pd.Timestamp("2023-06-15"))]
        daily = category_daily_units(changed, "Lower Manhattan", "2023-06-30")
        self.assertTrue(daily.loc["2023-06-15"].isna().all())
        with self.assertRaisesRegex(ValueError, "56 consecutive"):
            forecast_categories(daily, "2023-06-30")

    def test_zero_category_sales_on_an_observed_store_day(self):
        sample = pd.DataFrame({"date": pd.to_datetime(["2023-06-01", "2023-06-01", "2023-06-02"]),
                               "store_location": ["A"] * 3, "product_category": ["Coffee", "Tea", "Tea"],
                               "transaction_qty": [10, 3, 7]})
        daily = category_daily_units(sample, "A", "2023-06-02")
        self.assertEqual(daily.loc["2023-06-02", "Coffee"], 0)
        self.assertEqual(daily.loc["2023-06-02", "Tea"], 7)

    def test_review_outcomes_do_not_reselect_the_method(self):
        changed = self.daily.copy()
        changed.loc[self.forecast.review_start:, :] *= 3
        other = forecast_categories(changed, "2023-06-30")
        original_methods = self.forecast.summary.set_index("category").method.sort_index()
        pd.testing.assert_series_equal(original_methods, other.summary.set_index("category").method.sort_index())
        self.assertLess(self.forecast.selection_end, self.forecast.review_start)
        self.assertEqual(len(self.forecast.validation), 14 * 9)

    def test_a_review_day_prediction_cannot_use_its_own_actual(self):
        day = self.forecast.review_start
        changed = self.daily.copy()
        changed.loc[day:, :] += 10000
        other = forecast_categories(changed, "2023-06-30")
        before = self.forecast.validation.loc[self.forecast.validation.date.eq(day)].set_index("category").forecast_units.sort_index()
        after = other.validation.loc[other.validation.date.eq(day)].set_index("category").forecast_units.sort_index()
        pd.testing.assert_series_equal(before, after)

    def test_unknown_zero_and_excess_stock_have_different_actions(self):
        sample = pd.DataFrame({"category": ["Unknown", "Empty", "Covered"], "forecast_units": [10.1, 10.1, 10.1]})
        plan = make_stock_plan(sample, 10, {"Empty": 0, "Covered": 20}).set_index("category")
        self.assertTrue(pd.isna(plan.loc["Unknown", "add_units"]))
        self.assertEqual(plan.loc["Unknown", "action"], "Check usable stock")
        self.assertEqual(plan.loc["Empty", "target_units"], 12)
        self.assertEqual(plan.loc["Empty", "add_units"], 12)
        self.assertEqual(plan.loc["Covered", "add_units"], 0)

    def test_stock_and_buffer_validation_and_short_history(self):
        for value in (-1, .5, float("inf")):
            with self.assertRaises(ValueError):
                make_stock_plan(self.forecast.summary, 10, {"Coffee": value})
        for value in (-1, 31, float("nan")):
            with self.assertRaises(ValueError):
                make_stock_plan(self.forecast.summary, value)
        with self.assertRaisesRegex(ValueError, "56 consecutive"):
            forecast_categories(self.daily.tail(30), "2023-06-30")

    def test_planning_range_and_all_stores_are_supported(self):
        for store in self.frame.store_location.unique():
            forecast = forecast_categories(category_daily_units(self.frame, store, "2023-06-30"), "2023-06-30")
            self.assertEqual(forecast.target_date, pd.Timestamp("2023-07-01"))
            summary = forecast.summary
            self.assertTrue((summary.low_units >= 0).all())
            self.assertTrue((summary.low_units <= summary.forecast_units).all())
            self.assertTrue((summary.high_units >= summary.forecast_units).all())


if __name__ == "__main__":
    unittest.main()
