from datetime import date
from pathlib import Path
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def visible_plan(app):
    return next(frame.value for frame in app.dataframe if "Prepare / add" in frame.value.columns)


def visit(app, url_path):
    # AppTest.switch_page only supports file-based pages. Resolve the actual
    # registered route to exercise this app's callable pages in the pinned runtime.
    app._page_hash = next(key for key, info in app._registered_pages.items() if info.get("url_pathname") == url_path)
    return app.run()


class DashboardTests(unittest.TestCase):
    def open_app(self):
        return AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    def test_default_todo_has_real_dates_yesterday_and_unknown_stock(self):
        app = self.open_app()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.metric), 3)
        self.assertEqual(next(w for w in app.selectbox if w.label == "Store").value, "Lower Manhattan")
        self.assertEqual(app.date_input[0].value, date(2023, 6, 30))
        self.assertEqual(len(app.get("vega_lite_chart")), 0)
        plan = visible_plan(app)
        self.assertEqual(len(plan), 9)
        self.assertTrue(plan["Prepare / add"].isna().all())
        self.assertTrue(any("Sat 01 Jul 2023" in item.value for item in app.markdown))
        raw = pd.read_csv(ROOT / "Coffee Shop Sales.csv")
        dates = pd.to_datetime(raw.transaction_date, format="%m/%d/%y")
        mask = raw.store_location.eq("Lower Manhattan") & dates.eq(pd.Timestamp("2023-06-30")) & raw.product_category.str.strip().eq("Coffee")
        self.assertEqual(plan.set_index("Category").loc["Coffee", "Yesterday sold"], raw.loc[mask, "transaction_qty"].sum())

    def test_store_and_sales_category_controls_recalculate(self):
        app = self.open_app()
        before = visible_plan(app).set_index("Category")["Predicted today"].copy()
        next(w for w in app.selectbox if w.label == "Store").select("Astoria").run()
        after = visible_plan(app).set_index("Category")["Predicted today"]
        self.assertFalse(before.equals(after))
        visit(app, "sales")
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.get("vega_lite_chart")), 1)
        next(w for w in app.selectbox if w.label == "Inspect a category").select("Tea").run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("**Tea:** expected" in item.value for item in app.markdown))

    def test_buffer_changes_targets_not_forecasts(self):
        app = self.open_app()
        before = visible_plan(app).set_index("Category")
        app.slider[0].set_value(30).run()
        after = visible_plan(app).set_index("Category")
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(before["Predicted today"].equals(after["Predicted today"]))
        self.assertTrue((after["Ready target"] >= before["Ready target"]).all())
        self.assertTrue((after["Ready target"] > before["Ready target"]).any())

    def test_inventory_edit_finishes_one_stock_check(self):
        app = self.open_app()
        app.session_state["stock::Lower Manhattan::2023-06-30"] = {"edited_rows": {0: {"Usable units": 0}}, "added_rows": [], "deleted_rows": []}
        app.run()
        self.assertEqual(len(app.exception), 0)
        plan = visible_plan(app).set_index("Category")
        self.assertEqual(plan.loc["Bakery", "Usable stock"], 0)
        self.assertEqual(plan.loc["Bakery", "Prepare / add"], plan.loc["Bakery", "Ready target"])
        self.assertEqual(app.metric[1].value, "8")
        self.assertEqual(app.metric[2].value, "1")

    def test_historical_cutoff_resets_stock_and_plan_date(self):
        app = self.open_app()
        app.date_input[0].set_value(date(2023, 5, 30)).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Wed 31 May 2023" in item.value for item in app.markdown))
        self.assertTrue(visible_plan(app)["Usable stock"].isna().all())

    def test_routes_show_only_the_selected_workflow(self):
        app = self.open_app()
        paths = {info.get("url_pathname") for info in app._registered_pages.values()}
        self.assertEqual(paths, {"", "sales", "forecast"})
        self.assertFalse(any(w.label == "Inspect a category" for w in app.selectbox))
        visit(app, "sales")
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.metric), 3)
        self.assertFalse(any("Prepare / add" in frame.value.columns for frame in app.dataframe))
        visit(app, "forecast")
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.get("vega_lite_chart")), 0)
        self.assertEqual(len(app.metric), 0)
        self.assertTrue(any("Selected approach" in frame.value.columns for frame in app.dataframe))

    def test_stock_and_filters_survive_page_switching(self):
        app = self.open_app()
        app.session_state["stock::Lower Manhattan::2023-06-30"] = {"edited_rows": {0: {"Usable units": 20}}, "added_rows": [], "deleted_rows": []}
        app.run()
        before = visible_plan(app).set_index("Category").loc["Bakery", "Prepare / add"]
        visit(app, "sales")
        app.slider[0].set_value(20).run()
        visit(app, "forecast")
        visit(app, "")
        self.assertEqual(len(app.exception), 0)
        plan = visible_plan(app).set_index("Category")
        self.assertEqual(plan.loc["Bakery", "Usable stock"], 20)
        self.assertEqual(plan.loc["Bakery", "Prepare / add"], plan.loc["Bakery", "Ready target"] - 20)
        self.assertGreater(plan.loc["Bakery", "Prepare / add"], before)
        self.assertEqual(app.slider[0].value, 20)
        self.assertEqual(app.date_input[0].value, date(2023, 6, 30))

    def test_sales_actuals_match_the_selected_store_and_close(self):
        app = self.open_app()
        visit(app, "sales")
        raw = pd.read_csv(ROOT / "Coffee Shop Sales.csv")
        day = raw.loc[raw.store_location.eq("Lower Manhattan") & pd.to_datetime(raw.transaction_date, format="%m/%d/%y").eq(pd.Timestamp("2023-06-30"))]
        self.assertEqual(app.metric[0].value, f"${(day.transaction_qty * day.unit_price).sum():,.2f}")
        self.assertEqual(app.metric[1].value, f"{day.transaction_qty.sum():,}")
        self.assertEqual(app.metric[2].value, f"{len(day):,}")

    def test_fractional_stock_is_not_silently_truncated(self):
        app = self.open_app()
        app.session_state["stock::Lower Manhattan::2023-06-30"] = {"edited_rows": {0: {"Usable units": 2.5}}, "added_rows": [], "deleted_rows": []}
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("whole number" in error.value for error in app.error))
        self.assertNotIn("Bakery", app.session_state["usable-stock::Lower Manhattan::2023-06-30"])


if __name__ == "__main__":
    unittest.main()
