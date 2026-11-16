import unittest
from datetime import date
from dashboard_charts import order_day, revenue_chart


class RevenueChartTests(unittest.TestCase):
    def test_utc_and_invalid_dates(self):
        self.assertEqual(order_day('2026-10-27T23:30:00-02:00'), date(2026, 10, 28))
        self.assertIsNone(order_day('invalid'))

    def test_daily_totals_are_sorted_and_gaps_preserved(self):
        rows = [dict(order_date='2026-10-29', revenue=7),
                dict(order_date='2026-10-27', revenue=10),
                dict(order_date='2026-10-27T16:00:00Z', revenue=20),
                dict(order_date='invalid', revenue=100)]
        fig, note = revenue_chart(rows)
        self.assertEqual(list(fig.data[0].y), [30, 7])
        self.assertEqual(list(fig.data[0].x), [0, 2])
        self.assertIn('1 order(s) excluded', note)
        weekly, note = revenue_chart(rows, weekly=True)
        self.assertEqual(list(weekly.data[0].y), [37])
        self.assertEqual(weekly.data[0].type, 'bar')
        self.assertIn('not a trend', note)

    def test_empty_selection(self):
        fig, note = revenue_chart([])
        self.assertFalse(fig.data)
        self.assertIn('No valid', note)


if __name__ == '__main__':
    unittest.main()
