"""Checks for the event labels and index invariants used in the demo."""

import unittest

from src.portfolio import calculate_weights
from src.risk_engine import classify_event
from src.social_filter import focused_on


STOCKS = [
    {"ticker": "AAPL", "company": "Apple", "base_weight": "0.5"},
    {"ticker": "JPM", "company": "JPMorgan Chase", "base_weight": "0.5"},
]


class EventRulesTest(unittest.TestCase):
    def test_earnings_date_is_not_a_result(self):
        self.assertEqual(classify_event("Microsoft announces quarterly earnings release date")[0],
                         "Other/Unclear")

    def test_campaign_is_not_a_product(self):
        self.assertEqual(classify_event("Meta to launch regional education campaign")[0],
                         "Other/Unclear")

    def test_new_device_is_product_launch(self):
        self.assertEqual(classify_event("Amazon announces an all-new family of tablets")[0],
                         "Product Launch")

    def test_regulatory_event(self):
        self.assertEqual(classify_event("FTC appeals Meta monopolization ruling")[0],
                         "Regulatory")


class PortfolioTest(unittest.TestCase):
    def test_opposite_signs_transfer_without_changing_total(self):
        signals = [
            {"ticker": "AAPL", "event_type": "Product Launch", "sentiment_score": 0.5},
            {"ticker": "JPM", "event_type": "Regulatory", "sentiment_score": -0.5},
        ]
        rows = calculate_weights(STOCKS, signals)
        self.assertAlmostEqual(rows[0]["new_weight"], 0.55)
        self.assertAlmostEqual(rows[1]["new_weight"], 0.45)
        self.assertAlmostEqual(sum(row["new_weight"] for row in rows), 1.0)

    def test_unknown_event_and_one_sided_signal_do_not_move_weights(self):
        signals = [
            {"ticker": "AAPL", "event_type": "Other/Unclear", "sentiment_score": -0.5},
            {"ticker": "JPM", "event_type": "Corporate Action", "sentiment_score": 0.5},
        ]
        rows = calculate_weights(STOCKS, signals)
        self.assertEqual([row["new_weight"] for row in rows], [0.5, 0.5])


class SocialAttributionTest(unittest.TestCase):
    def test_accepts_single_cashtag_with_company_name(self):
        self.assertTrue(focused_on("AAPL", "Apple cuts iPhone orders $AAPL"))

    def test_rejects_multi_ticker_roundup(self):
        self.assertFalse(focused_on("AAPL", "Meta faces probe $META $AAPL"))

    def test_rejects_cashtag_without_company_name(self):
        self.assertFalse(focused_on("MSFT", "OpenAI reports revenue growth $MSFT"))


if __name__ == "__main__":
    unittest.main()
