"""Extract daily campaign insights from the Meta Marketing API to CSV."""

import argparse
import csv
import json
import os
import re
import sys
import tempfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import urlopen


CSV_FIELDS = [
    "account_id",
    "campaign_id",
    "campaign_name",
    "date_start",
    "date_stop",
    "impressions",
    "reach",
    "clicks",
    "inline_link_clicks",
    "spend",
    "purchases",
    "purchase_conversion_value",
]
INSIGHTS_FIELDS = ",".join(
    [
        "account_id",
        "campaign_id",
        "campaign_name",
        "date_start",
        "date_stop",
        "impressions",
        "reach",
        "clicks",
        "inline_link_clicks",
        "spend",
        "actions",
        "action_values",
    ]
)
PURCHASE_ACTION_TYPES = (
    "omni_purchase",
    "purchase",
    "offsite_conversion.fb_pixel_purchase",
    "onsite_conversion.purchase",
)
API_TIMEOUT_SECONDS = 60


class MetaAdsAPIError(RuntimeError):
    """Raised when Meta returns an invalid or unsuccessful API response."""


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Set {name} in the environment before running this script.")
    return value


def parse_iso_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a valid YYYY-MM-DD date"
        )
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a valid YYYY-MM-DD date"
        ) from exc


def normalize_account_id(value):
    account_id = value[4:] if value.startswith("act_") else value
    if not account_id.isdigit():
        raise ValueError(
            "META_AD_ACCOUNT_ID must be a numeric ID, optionally prefixed with 'act_'."
        )
    return account_id


def parse_decimal(value, field_name):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise MetaAdsAPIError(f"Meta returned an invalid {field_name} value.") from exc
    if not number.is_finite() or number < 0:
        raise MetaAdsAPIError(f"Meta returned an invalid {field_name} value.")
    return number


def action_value(actions, metric_name):
    if actions is None:
        return Decimal(0)
    if not isinstance(actions, list):
        raise MetaAdsAPIError(f"Meta returned malformed {metric_name} data.")
    values = {}
    for action in actions:
        if not isinstance(action, dict) or "action_type" not in action:
            raise MetaAdsAPIError(f"Meta returned malformed {metric_name} data.")
        if action["action_type"] in PURCHASE_ACTION_TYPES:
            if "value" not in action:
                raise MetaAdsAPIError(f"Meta omitted a purchase {metric_name} value.")
            values[action["action_type"]] = parse_decimal(
                action["value"], metric_name
            )
    for action_type in PURCHASE_ACTION_TYPES:
        if action_type in values:
            return values[action_type]
    return Decimal(0)


def normalize_insight(insight):
    if not isinstance(insight, dict):
        raise MetaAdsAPIError("Meta returned a malformed campaign insight.")
    required_fields = (
        "account_id",
        "campaign_id",
        "campaign_name",
        "date_start",
        "date_stop",
    )
    if any(not insight.get(field) for field in required_fields):
        raise MetaAdsAPIError("Meta returned a campaign insight with missing identifiers.")

    row = {field: str(insight[field]) for field in required_fields}
    for field in ("date_start", "date_stop"):
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[field]):
                raise ValueError
            row[field] = date.fromisoformat(row[field]).isoformat()
        except ValueError as exc:
            raise MetaAdsAPIError(f"Meta returned an invalid {field} date.") from exc
    for field in ("impressions", "reach", "clicks", "inline_link_clicks"):
        value = parse_decimal(insight.get(field), field)
        if value != value.to_integral_value():
            raise MetaAdsAPIError(f"Meta returned a non-integer {field} value.")
        row[field] = str(int(value))
    row["spend"] = format(parse_decimal(insight.get("spend"), "spend"), "f")
    row["purchases"] = format(action_value(insight.get("actions"), "purchase"), "f")
    row["purchase_conversion_value"] = format(
        action_value(insight.get("action_values"), "purchase conversion value"), "f"
    )
    return row


def validate_next_page(next_url, api_version, account_id):
    if not isinstance(next_url, str):
        raise MetaAdsAPIError("Meta returned a malformed pagination URL.")
    try:
        parsed = urlsplit(next_url)
    except (TypeError, ValueError) as exc:
        raise MetaAdsAPIError("Meta returned a malformed pagination URL.") from exc
    expected_path = f"/{api_version}/act_{account_id}/insights"
    if (
        parsed.scheme != "https"
        or parsed.hostname != "graph.facebook.com"
        or parsed.path != expected_path
    ):
        raise MetaAdsAPIError(
            "Meta returned an unexpected pagination URL; refusing to follow it."
        )
    if "access_token" not in parse_qs(parsed.query):
        raise MetaAdsAPIError("Meta returned a pagination URL without authentication.")
    return next_url


def request_page(url, params=None):
    if params:
        url = f"{url}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=API_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = {}
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        message = error.get("message")
        detail = f": {message}" if message else ""
        raise MetaAdsAPIError(
            f"Meta API request failed with HTTP {exc.code}{detail}"
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise MetaAdsAPIError("Could not reach the Meta Marketing API.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MetaAdsAPIError("Meta returned a response that was not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise MetaAdsAPIError("Meta returned an unexpected API response.")
    if "error" in payload:
        error = payload["error"]
        message = error.get("message") if isinstance(error, dict) else None
        detail = f": {message}" if message else ""
        raise MetaAdsAPIError(f"Meta API request failed{detail}")
    if not isinstance(payload.get("data"), list):
        raise MetaAdsAPIError("Meta response did not contain an insights data list.")
    return payload


def fetch_insights(account_id, access_token, api_version, since, until):
    url = f"https://graph.facebook.com/{api_version}/act_{account_id}/insights"
    params = {
        "access_token": access_token,
        "fields": INSIGHTS_FIELDS,
        "level": "campaign",
        "time_increment": "1",
        "time_range": json.dumps(
            {"since": since.isoformat(), "until": until.isoformat()}
        ),
        "limit": "500",
    }
    rows = []
    while True:
        payload = request_page(url, params)
        rows.extend(normalize_insight(insight) for insight in payload["data"])
        paging = payload.get("paging", {})
        if not isinstance(paging, dict):
            raise MetaAdsAPIError("Meta returned malformed pagination data.")
        next_url = paging.get("next")
        if next_url is None:
            break
        url = validate_next_page(next_url, api_version, account_id)
        params = None
    return rows


def write_csv_atomic(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            newline="",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary_path, 0o644)
        temporary_path.replace(path)
    except OSError:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Export daily campaign insights from the Meta Marketing API."
    )
    parser.add_argument(
        "--since", required=True, type=parse_iso_date, help="Start date (YYYY-MM-DD)."
    )
    parser.add_argument(
        "--until", required=True, type=parse_iso_date, help="End date (YYYY-MM-DD)."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/meta_ads_insights.csv"),
        help="CSV path (default: data/meta_ads_insights.csv).",
    )
    args = parser.parse_args()
    if args.since > args.until:
        parser.error("--since must be on or before --until.")

    try:
        account_id = normalize_account_id(required_env("META_AD_ACCOUNT_ID"))
        access_token = required_env("META_ACCESS_TOKEN")
        api_version = required_env("META_API_VERSION")
        if not re.fullmatch(r"v\d+\.\d+", api_version):
            raise ValueError(
                "META_API_VERSION must match the format v<major>.<minor>, such as v22.0."
            )

        rows = fetch_insights(
            account_id,
            access_token,
            api_version,
            args.since,
            args.until,
        )
        write_csv_atomic(args.output, rows)
    except (MetaAdsAPIError, OSError, ValueError) as exc:
        print(f"Meta Ads extraction failed: {exc}", file=sys.stderr)
        return 1

    print(f"Exported {len(rows)} daily campaign rows to {args.output}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
