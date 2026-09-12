"""Production-oriented ETL, KPI aggregation, churn scoring, and executive alerting.

Usage:
    python scripts/automated_pipeline.py
    python scripts/automated_pipeline.py --input data/raw/retail_raw_stream.csv --notify
"""

from __future__ import annotations

import argparse
import logging
import os
import smtplib
import sys
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

LOGGER = logging.getLogger("apexplanet.pipeline")
REQUIRED_COLUMNS = {
    "Order_Date", "Customer_ID", "Category", "Region", "Units_Sold",
    "Unit_Price", "Discount_Pct", "Shipping_Cost", "Total_Revenue",
    "Net_Profit", "Churn",
}
NUMERIC_COLUMNS = [
    "Units_Sold", "Unit_Price", "Discount_Pct", "Shipping_Cost",
    "Total_Revenue", "Net_Profit", "Churn",
]


@dataclass(frozen=True)
class PipelineConfig:
    input_path: Path
    processed_dir: Path
    notify: bool = False


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def read_and_clean(path: Path) -> pd.DataFrame:
    """Read a raw batch, validate its contract, and return canonical records."""
    if not path.exists():
        raise FileNotFoundError(f"Input batch not found: {path}")
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    frame = frame.drop_duplicates().copy()
    frame["Order_Date"] = pd.to_datetime(frame["Order_Date"], errors="coerce", utc=True).dt.normalize()
    frame = frame.dropna(subset=["Order_Date", "Customer_ID", "Category", "Region"])
    frame["Customer_ID"] = frame["Customer_ID"].astype(str).str.strip().str.upper()
    frame["Category"] = frame["Category"].astype(str).str.strip().str.title()
    frame["Region"] = frame["Region"].astype(str).str.strip().str.title()

    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["Churn"] = frame["Churn"].fillna(0).clip(0, 1).round().astype(int)
    frame["Discount_Pct"] = frame["Discount_Pct"].fillna(0).clip(0, 100)
    frame["Shipping_Cost"] = frame["Shipping_Cost"].fillna(0).clip(lower=0)
    frame["Units_Sold"] = frame["Units_Sold"].fillna(0).clip(lower=0)
    frame = frame.dropna(subset=["Unit_Price", "Total_Revenue", "Net_Profit"])
    frame["Unit_Price"] = frame["Unit_Price"].clip(lower=0)
    frame["Total_Revenue"] = frame["Total_Revenue"].clip(lower=0)
    frame["Net_Profit"] = frame["Net_Profit"].fillna(0)
    frame["Profit_Margin_Pct"] = np.where(
        frame["Total_Revenue"] > 0,
        frame["Net_Profit"] / frame["Total_Revenue"] * 100,
        0,
    ).round(2)
    return frame.sort_values(["Order_Date", "Customer_ID"]).reset_index(drop=True)


def score_churn(frame: pd.DataFrame) -> pd.DataFrame:
    """Infer a transparent 0-100 churn risk score from observed customer behavior."""
    reference_date = frame["Order_Date"].max()
    customer = frame.groupby("Customer_ID", as_index=False).agg(
        Last_Order=("Order_Date", "max"),
        Frequency=("Order_Date", "count"),
        Monetary=("Total_Revenue", "sum"),
        Historical_Churn=("Churn", "max"),
    )
    customer["Recency_Days"] = (reference_date - customer["Last_Order"]).dt.days.clip(lower=0)

    def percentile(series: pd.Series, higher_is_risk: bool = True) -> pd.Series:
        ranks = series.rank(pct=True, method="average").fillna(0.5)
        return ranks if higher_is_risk else 1 - ranks

    customer["Risk"] = (
        0.45 * percentile(customer["Recency_Days"])
        + 0.20 * percentile(customer["Frequency"], higher_is_risk=False)
        + 0.15 * percentile(customer["Monetary"], higher_is_risk=False)
        + 0.20 * customer["Historical_Churn"]
    ) * 100
    customer["Churn_Risk_Score"] = customer["Risk"].clip(0, 100).round(1)
    return frame.merge(customer[["Customer_ID", "Churn_Risk_Score"]], on="Customer_ID", how="left")


def build_daily_kpis(frame: pd.DataFrame) -> pd.DataFrame:
    daily = frame.groupby("Order_Date", as_index=False).agg(
        Revenue=("Total_Revenue", "sum"),
        Profit=("Net_Profit", "sum"),
        AOV=("Total_Revenue", "mean"),
        Active_Customers=("Customer_ID", "nunique"),
        Orders=("Customer_ID", "size"),
        Units_Sold=("Units_Sold", "sum"),
    )
    daily["Profit_Margin_Pct"] = np.where(
        daily["Revenue"] > 0, daily["Profit"] / daily["Revenue"] * 100, 0
    ).round(2)
    daily["High_Risk_Customers"] = frame.assign(
        High_Risk=frame["Churn_Risk_Score"] >= 60
    ).groupby("Order_Date")["High_Risk"].sum().reindex(daily["Order_Date"]).fillna(0).astype(int).to_numpy()
    daily = daily.sort_values("Order_Date")
    daily["Revenue_7D_Rolling"] = daily["Revenue"].rolling(7, min_periods=1).sum().round(2)
    daily["Profit_7D_Rolling"] = daily["Profit"].rolling(7, min_periods=1).sum().round(2)
    daily["Revenue_Weekly_Rolling"] = daily["Revenue"].rolling(7, min_periods=1).mean().round(2)
    return daily


def write_outputs(frame: pd.DataFrame, daily: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_dir / "master_cleaned_data.csv", index=False, date_format="%Y-%m-%d")
    daily.to_csv(output_dir / "daily_kpi_summary.csv", index=False, date_format="%Y-%m-%d")


def render_executive_email(daily: pd.DataFrame, status: str = "SUCCESS") -> str:
    latest = daily.iloc[-1]
    return f"""<html><body><h2>Apexplanet Daily Analytics: {status}</h2>
<p>Run date: <strong>{latest['Order_Date'].date()}</strong></p>
<table border='1' cellpadding='6' cellspacing='0'>
<tr><th>Revenue</th><th>Profit Margin</th><th>AOV</th><th>Active Customers</th><th>High-Risk Customers</th></tr>
<tr><td>INR {latest['Revenue']:,.2f}</td><td>{latest['Profit_Margin_Pct']:.2f}%</td>
<td>INR {latest['AOV']:,.2f}</td><td>{int(latest['Active_Customers'])}</td>
<td>{int(latest['High_Risk_Customers'])}</td></tr></table>
<p>Weekly rolling revenue: INR {latest['Revenue_7D_Rolling']:,.2f}.</p></body></html>"""


def send_email(html: str, subject: str = "Apexplanet Daily Analytics Run") -> None:
    """Send an alert using SMTP_* environment variables; never hard-code credentials."""
    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("EXECUTIVE_EMAIL_TO")
    if not all([host, username, password, recipient]):
        LOGGER.warning("Email skipped: SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and EXECUTIVE_EMAIL_TO are required")
        return
    message = EmailMessage()
    message["From"] = os.getenv("EXECUTIVE_EMAIL_FROM", username)
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content("Your email client does not support HTML.")
    message.add_alternative(html, subtype="html")
    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=30) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(message)


def run(config: PipelineConfig) -> pd.DataFrame:
    frame = score_churn(read_and_clean(config.input_path))
    daily = build_daily_kpis(frame)
    write_outputs(frame, daily, config.processed_dir)
    if config.notify:
        send_email(render_executive_email(daily))
    LOGGER.info("Pipeline complete: %s records, %s daily KPI rows", len(frame), len(daily))
    return daily


def parse_args(args: Iterable[str] | None = None) -> PipelineConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--input", type=Path, default=root / "data/raw/retail_raw_stream.csv")
    parser.add_argument("--processed-dir", type=Path, default=root / "data/processed")
    parser.add_argument("--notify", action="store_true", help="Send the executive email when SMTP variables are configured")
    values = parser.parse_args(args)
    return PipelineConfig(values.input, values.processed_dir, values.notify)


if __name__ == "__main__":
    configure_logging()
    try:
        run(parse_args())
    except Exception:
        LOGGER.exception("Pipeline failed")
        sys.exit(1)
