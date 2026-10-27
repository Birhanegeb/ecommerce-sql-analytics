import argparse
import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import call, patch

import extract_meta_ads


def make_insight(campaign_id="1001"):
    return {
        "account_id": "12345",
        "campaign_id": campaign_id,
        "campaign_name": "Spring campaign",
        "date_start": "2026-01-01",
        "date_stop": "2026-01-01",
        "impressions": "1000",
        "reach": "900",
        "clicks": "50",
        "inline_link_clicks": "40",
        "spend": "25.50",
        "actions": [
            {"action_type": "purchase", "value": "2"},
            {"action_type": "omni_purchase", "value": "3"},
        ],
        "action_values": [
            {"action_type": "omni_purchase", "value": "125.75"},
        ],
    }


class MetaAdsExtractorTests(unittest.TestCase):
    def test_normalizes_campaign_metrics_and_prefers_omni_purchase(self):
        row = extract_meta_ads.normalize_insight(make_insight())

        self.assertEqual(row["impressions"], "1000")
        self.assertEqual(row["spend"], "25.50")
        self.assertEqual(row["purchases"], "3")
        self.assertEqual(row["purchase_conversion_value"], "125.75")

    def test_rejects_missing_required_metric(self):
        insight = make_insight()
        del insight["clicks"]

        with self.assertRaises(extract_meta_ads.MetaAdsAPIError):
            extract_meta_ads.normalize_insight(insight)

    def test_rejects_non_meta_pagination_url(self):
        with self.assertRaises(extract_meta_ads.MetaAdsAPIError):
            extract_meta_ads.validate_next_page(
                "https://attacker.example/v22.0/act_12345/insights?access_token=x",
                "v22.0",
                "12345",
            )

    @patch("extract_meta_ads.request_page", return_value={"data": [], "paging": []})
    def test_rejects_malformed_pagination_data(self, request_page):
        with self.assertRaises(extract_meta_ads.MetaAdsAPIError):
            extract_meta_ads.fetch_insights(
                "12345",
                "secret",
                "v22.0",
                date(2026, 1, 1),
                date(2026, 1, 2),
            )

    @patch("extract_meta_ads.request_page")
    def test_fetches_all_pages(self, request_page):
        next_url = (
            "https://graph.facebook.com/v22.0/act_12345/insights"
            "?after=cursor&access_token=secret"
        )
        request_page.side_effect = [
            {"data": [make_insight()], "paging": {"next": next_url}},
            {"data": [make_insight("1002")]},
        ]

        rows = extract_meta_ads.fetch_insights(
            "12345",
            "secret",
            "v22.0",
            date(2026, 1, 1),
            date(2026, 1, 2),
        )

        self.assertEqual([row["campaign_id"] for row in rows], ["1001", "1002"])
        self.assertEqual(request_page.call_count, 2)
        self.assertEqual(request_page.call_args_list[1], call(next_url, None))

    def test_writes_header_and_rows_to_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "meta_ads_insights.csv"
            extract_meta_ads.write_csv_atomic(
                output_path, [extract_meta_ads.normalize_insight(make_insight())]
            )

            with output_path.open(newline="", encoding="utf-8") as output:
                reader = csv.DictReader(output)
                rows = list(reader)

        self.assertEqual(reader.fieldnames, extract_meta_ads.CSV_FIELDS)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["campaign_id"], "1001")

    def test_requires_strict_iso_dates(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            extract_meta_ads.parse_iso_date("20260101")


if __name__ == "__main__":
    unittest.main()
