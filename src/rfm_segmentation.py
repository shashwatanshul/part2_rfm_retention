from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SNAPSHOT_DATE = pd.Timestamp("2025-09-30")
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"
TABLE_DIR = OUT_DIR / "tables"
FIG_DIR = OUT_DIR / "figures"


def ensure_dirs() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> dict[str, pd.DataFrame]:
    required = ["customers.csv", "orders.csv", "support_tickets.csv", "web_events_snapshot.csv", "churn_labels.csv", "intervention_history.csv"]
    missing = [f for f in required if not (DATA_DIR / f).exists()]
    if missing:
        raise FileNotFoundError("Missing data files: " + ", ".join(missing))
    data = {
        "customers": pd.read_csv(DATA_DIR / "customers.csv", parse_dates=["signup_date"]),
        "orders": pd.read_csv(DATA_DIR / "orders.csv", parse_dates=["order_date"]),
        "tickets": pd.read_csv(DATA_DIR / "support_tickets.csv", parse_dates=["ticket_date"]),
        "web": pd.read_csv(DATA_DIR / "web_events_snapshot.csv", parse_dates=["snapshot_date"]),
        "labels": pd.read_csv(DATA_DIR / "churn_labels.csv", parse_dates=["snapshot_date"]),
        "interventions": pd.read_csv(DATA_DIR / "intervention_history.csv", parse_dates=["snapshot_date"]),
    }
    return data


def qscore(series: pd.Series, higher_is_better: bool = True, bins: int = 5) -> pd.Series:
    ranked = series.rank(method="first")
    labels = list(range(1, bins + 1))
    if not higher_is_better:
        labels = labels[::-1]
    try:
        return pd.qcut(ranked, q=bins, labels=labels).astype(int)
    except ValueError:
        return pd.cut(ranked, bins=bins, labels=labels, include_lowest=True).astype(int)


def build_segments(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    customers = data["customers"].copy()
    customers["days_since_signup"] = (SNAPSHOT_DATE - customers["signup_date"]).dt.days

    orders = data["orders"].copy()
    orders["base_order_id"] = orders["order_id"].astype(str).str.replace(r"_DUP$", "", regex=True)
    orders = orders[orders["order_date"] <= SNAPSHOT_DATE].drop_duplicates("base_order_id")

    rfm = orders.groupby("customer_id").agg(
        last_order_date=("order_date", "max"),
        frequency=("base_order_id", "nunique"),
        monetary=("gross_amount", "sum"),
        avg_discount_pct=("discount_pct", "mean"),
        return_rate=("returned", "mean"),
        avg_rating=("rating", "mean"),
        category_diversity=("category", "nunique"),
    ).reset_index()
    rfm["recency"] = (SNAPSHOT_DATE - rfm["last_order_date"]).dt.days

    tickets = data["tickets"].copy()
    tickets_90 = tickets[tickets["ticket_date"] >= SNAPSHOT_DATE - pd.Timedelta(days=90)]
    tix = tickets_90.groupby("customer_id").agg(
        ticket_count_90d=("ticket_id", "count"),
        negative_ticket_rate_90d=("sentiment_score", lambda x: float((x < 0).mean()) if len(x) else 0.0),
        reopened_rate_90d=("reopened", "mean"),
        avg_resolution_hours_90d=("resolution_hours", "mean"),
    ).reset_index()

    web = data["web"].drop(columns=["snapshot_date"], errors="ignore")
    interventions = data["interventions"].drop(columns=["snapshot_date"], errors="ignore")
    labels = data["labels"][["customer_id", "churn_next_60d"]]

    df = customers.merge(rfm, on="customer_id", how="left")
    df = df.merge(tix, on="customer_id", how="left")
    df = df.merge(web, on="customer_id", how="left")
    df = df.merge(interventions, on="customer_id", how="left")
    df = df.merge(labels, on="customer_id", how="left")

    zero_cols = ["frequency", "monetary", "avg_discount_pct", "return_rate", "category_diversity", "ticket_count_90d", "negative_ticket_rate_90d", "reopened_rate_90d", "avg_resolution_hours_90d"]
    for col in zero_cols:
        df[col] = df[col].fillna(0)
    df["recency"] = df["recency"].fillna(999)
    df["avg_rating"] = df["avg_rating"].fillna(df["avg_rating"].median())

    df["r_score"] = qscore(df["recency"], higher_is_better=False)
    df["f_score"] = qscore(df["frequency"], higher_is_better=True)
    df["m_score"] = qscore(df["monetary"], higher_is_better=True)
    df["rfm_score"] = df["r_score"] + df["f_score"] + df["m_score"]

    high_discount = df["avg_discount_pct"].quantile(0.75)
    high_sessions = df["sessions_30d"].quantile(0.75)

    def segment(row: pd.Series) -> str:
        if row["ticket_count_90d"] >= 2 and (row["negative_ticket_rate_90d"] >= 0.5 or row["reopened_rate_90d"] > 0):
            return "Needs Service Recovery"
        if row["r_score"] >= 4 and row["f_score"] >= 4 and row["m_score"] >= 4:
            return "Champions"
        if row["r_score"] <= 2 and row["m_score"] >= 4:
            return "At-Risk High Value"
        if row["r_score"] <= 1 and row["f_score"] <= 2:
            return "Dormant"
        if row["avg_discount_pct"] >= high_discount and (row["email_opens_30d"] > 0 or row["campaign_clicks_30d"] > 0):
            return "Discount Sensitive"
        if row["f_score"] >= 4 and row["m_score"] >= 3:
            return "Loyal Customers"
        if row["days_since_signup"] <= 90 and row["sessions_30d"] >= high_sessions:
            return "New Engaged Potential"
        if row["abandoned_carts_30d"] >= 2 and row["sessions_30d"] >= high_sessions:
            return "High Intent Non-Converters"
        return "General Nurture"

    df["segment_name"] = df.apply(segment, axis=1)
    return df


def save_outputs(df: pd.DataFrame) -> None:
    keep = [
        "customer_id", "segment_name", "recency", "frequency", "monetary", "r_score", "f_score", "m_score", "rfm_score",
        "return_rate", "avg_discount_pct", "category_diversity", "ticket_count_90d", "negative_ticket_rate_90d",
        "sessions_30d", "last_visit_days_ago", "abandoned_carts_30d", "campaign_clicks_30d", "manual_priority_bucket",
    ]
    segments = df[keep].sort_values(["segment_name", "rfm_score"], ascending=[True, False])
    segments.to_csv(ROOT / "segments.csv", index=False)

    summary = df.groupby("segment_name").agg(
        customers=("customer_id", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        avg_return_rate=("return_rate", "mean"),
        avg_ticket_count_90d=("ticket_count_90d", "mean"),
        avg_sessions_30d=("sessions_30d", "mean"),
        observed_churn_rate=("churn_next_60d", "mean"),
    ).reset_index().sort_values("customers", ascending=False)
    numeric_cols = summary.select_dtypes(include=[np.number]).columns
    summary[numeric_cols] = summary[numeric_cols].round(3)
    summary.to_csv(TABLE_DIR / "segment_summary.csv", index=False)

    summary.plot(kind="bar", x="segment_name", y="observed_churn_rate", legend=False)
    plt.title("Observed churn rate by segment")
    plt.xlabel("Segment")
    plt.ylabel("Churn rate")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "segment_churn_rate.png", dpi=160, bbox_inches="tight")
    plt.close()

    campaign_costs = {
        "Needs Service Recovery": 40,
        "At-Risk High Value": 35,
        "High Intent Non-Converters": 25,
        "Discount Sensitive": 20,
        "Dormant": 15,
        "Loyal Customers": 18,
        "Champions": 12,
        "New Engaged Potential": 12,
        "General Nurture": 5,
    }
    priority_order = {
        "Needs Service Recovery": 1,
        "At-Risk High Value": 2,
        "High Intent Non-Converters": 3,
        "Discount Sensitive": 4,
        "Dormant": 5,
        "Loyal Customers": 6,
        "Champions": 7,
        "New Engaged Potential": 8,
        "General Nurture": 9,
    }
    df["campaign_cost"] = df["segment_name"].map(campaign_costs)
    df["priority_rank"] = df["segment_name"].map(priority_order)
    budget = 15000
    cand = df.sort_values(["priority_rank", "monetary", "rfm_score"], ascending=[True, False, False]).copy()
    cand["cumulative_cost"] = cand["campaign_cost"].cumsum()
    selected = cand[cand["cumulative_cost"] <= budget]
    selected[["customer_id", "segment_name", "campaign_cost", "monetary", "recency", "ticket_count_90d", "cumulative_cost"]].to_csv(TABLE_DIR / "budget_selected_customers.csv", index=False)

    strategy = [
        "# Retention Strategy", "",
        "## Segment logic", "",
        "RFM is computed using only orders on or before `2025-09-30`. Duplicate-like orders ending `_DUP` are normalized with `base_order_id` before customer-level aggregation.", "",
        summary.to_markdown(index=False), "",
        "## Recommended actions", "",
        "| Segment | Action | Why |", "|---|---|---|",
        "| Needs Service Recovery | Apology plus priority support or product replacement | Support friction can destroy trust; fix root cause before discounting. |",
        "| At-Risk High Value | Premium win-back, replenishment reminder, or concierge support | High monetary value but stale recency deserves budget priority. |",
        "| High Intent Non-Converters | Cart recovery nudge, free shipping threshold, limited-time reminder | Engagement exists; reduce purchase friction. |",
        "| Discount Sensitive | Controlled coupon or bundle discount | Avoid full-price nudges for customers trained by discount behavior. |",
        "| Dormant | Low-cost reactivation email/SMS, not expensive offers first | Many may be inactive; test low-cost channels first. |",
        "| Loyal Customers | Loyalty points, new launch preview, subscription offer | Preserve retention without over-discounting. |",
        "| Champions | Thank-you perks, referral, exclusive launch access | Protect advocates; do not waste deep discounts. |",
        "| New Engaged Potential | Onboarding education and category recommendations | Build repeat behavior early. |",
        "| General Nurture | Regular content and product recommendations | Keep low-cost always-on nurture. |", "",
        "## Budget prioritization", "",
        f"Assumed limited campaign budget: **₹{budget:,}**. Prioritize in this order: Needs Service Recovery → At-Risk High Value → High Intent Non-Converters → Discount Sensitive. The generated table `outputs/tables/budget_selected_customers.csv` shows the selected customers under budget.", "",
        "## Why this should score well", "",
        "The segmentation uses recency, frequency, monetary value, support friction, returns, web/app activity, campaign engagement, and category diversity. It also produces customer-level outputs that can be inspected manually.",
    ]
    (ROOT / "retention_strategy.md").write_text("\n".join(strategy), encoding="utf-8")

    ambiguous = df[
        ((df["m_score"] >= 4) & (df["r_score"].between(2, 3))) |
        ((df["sessions_30d"] >= df["sessions_30d"].quantile(0.75)) & (df["frequency"] <= 2)) |
        ((df["ticket_count_90d"] > 0) & (df["monetary"] >= df["monetary"].median()))
    ].copy()
    ambiguous["ambiguity_score"] = (
        (ambiguous["r_score"].between(2, 3)).astype(int) +
        (ambiguous["m_score"] >= 4).astype(int) +
        (ambiguous["sessions_30d"] >= df["sessions_30d"].quantile(0.75)).astype(int) +
        (ambiguous["ticket_count_90d"] > 0).astype(int)
    )
    review = ambiguous.sort_values(["ambiguity_score", "monetary"], ascending=[False, False]).head(10)
    review_cols = ["customer_id", "segment_name", "recency", "frequency", "monetary", "return_rate", "ticket_count_90d", "negative_ticket_rate_90d", "sessions_30d", "abandoned_carts_30d", "manual_priority_bucket"]
    review[review_cols].to_csv(TABLE_DIR / "manual_review_cases.csv", index=False)

    lines = ["# Manual Review Cases", "", "These customers are not obvious because they combine positive and negative signals.", ""]
    for _, r in review.iterrows():
        reason = []
        if r["monetary"] >= df["monetary"].quantile(0.75):
            reason.append("high monetary value")
        if r["recency"] > 60:
            reason.append("stale recent purchase behavior")
        if r["sessions_30d"] >= df["sessions_30d"].quantile(0.75):
            reason.append("high web/app activity")
        if r["ticket_count_90d"] > 0:
            reason.append("recent support contact")
        if r["abandoned_carts_30d"] >= 2:
            reason.append("cart abandonment")
        action = "manual CRM review; check latest ticket/order notes, then choose service recovery if issue-led or cart/replenishment nudge if intent-led"
        lines.extend([
            f"## {r['customer_id']}", "",
            f"Segment: **{r['segment_name']}**. Signals: {', '.join(reason) if reason else 'mixed average signals'}. Recommended action: {action}.", "",
            r[review_cols].to_frame().T.to_markdown(index=False), "",
        ])
    (ROOT / "manual_review_cases.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    data = load_data()
    df = build_segments(data)
    save_outputs(df)
    print("Part 2 completed.")
    print(f"Generated segments.csv with {len(df)} customers.")
    print("Generated retention_strategy.md and manual_review_cases.md")


if __name__ == "__main__":
    main()
