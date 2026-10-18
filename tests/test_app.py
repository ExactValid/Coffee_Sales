from datetime import date
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def visible_plan(app):
    return next(frame.value for frame in app.dataframe if "Prepare / add" in frame.value.columns)


class DashboardTests(unittest.TestCase):
    def test_default_plan_has_real_dates_and_unknown_stock(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.metric), 3)
        self.assertEqual(next(w for w in app.selectbox if w.label == "Store").value, "Lower Manhattan")
        self.assertEqual(app.date_input[0].value, date(2023, 6, 30))
        self.assertEqual(len(app.get("vega_lite_chart")), 1)
        plan = visible_plan(app)
        self.assertEqual(len(plan), 9)
        self.assertTrue(plan["Prepare / add"].isna().all())
        self.assertTrue(any("Sat 01 Jul 2023" in item.value for item in app.markdown))

    def test_store_and_category_controls_recalculate(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        before = visible_plan(app).set_index("Category")["Expected sales"].copy()
        next(w for w in app.selectbox if w.label == "Store").select("Astoria").run()
        self.assertEqual(len(app.exception), 0)
        after = visible_plan(app).set_index("Category")["Expected sales"]
        self.assertFalse(before.equals(after))
        next(w for w in app.selectbox if w.label == "Inspect a category").select("Tea").run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("**Tea:** expected" in item.value for item in app.markdown))

    def test_buffer_changes_targets_not_forecasts(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        before = visible_plan(app).set_index("Category")
        app.slider[0].set_value(30).run()
        self.assertEqual(len(app.exception), 0)
        after = visible_plan(app).set_index("Category")
        self.assertTrue(before["Expected sales"].equals(after["Expected sales"]))
        self.assertTrue((after["Ready target"] >= before["Ready target"]).all())
        self.assertTrue((after["Ready target"] > before["Ready target"]).any())

    def test_inventory_edit_finishes_one_stock_check(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        key = "stock::Lower Manhattan::2023-06-30"
        app.session_state[key] = {"edited_rows": {0: {"Usable units": 0}}, "added_rows": [], "deleted_rows": []}
        app.run()
        self.assertEqual(len(app.exception), 0)
        plan = visible_plan(app).set_index("Category")
        self.assertEqual(plan.loc["Bakery", "Usable stock"], 0)
        self.assertEqual(plan.loc["Bakery", "Prepare / add"], plan.loc["Bakery", "Ready target"])
        self.assertEqual(app.metric[1].value, "8")
        self.assertEqual(app.metric[2].value, "1")

    def test_historical_cutoff_resets_stock_and_plan_date(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        app.date_input[0].set_value(date(2023, 5, 30)).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Wed 31 May 2023" in item.value for item in app.markdown))
        self.assertTrue(visible_plan(app)["Usable stock"].isna().all())


if __name__ == "__main__":
    unittest.main()
