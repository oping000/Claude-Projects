"""
CSV Analyzer
------------
Reads a company list CSV, generates a printed summary,
and produces two output files:
  1. company_list_cleaned.csv  — cleaned, trimmed version of the original
  2. company_list_summary.csv  — aggregated stats by industry and state

Usage:
  python analyze_inc5000.py
"""

import pandas as pd
import os

# ── CONFIG ─────────────────────────────────────────────────────────────────────
INPUT_FILE  = r'C:\Users\oping\OneDrive\Documents\Python\Company List.csv'
OUTPUT_CLEANED = r'C:\Users\oping\OneDrive\Documents\Python\company_list_cleaned.csv'
OUTPUT_SUMMARY = r'C:\Users\oping\OneDrive\Documents\Python\company_list_summary.csv'
# ───────────────────────────────────────────────────────────────────────────────


def load_data(filepath):
    """Load the CSV and keep only the useful columns."""
    df = pd.read_csv(filepath)
    keep = ["rank", "company", "city", "state_l", "state_s",
            "metro", "industry", "workers", "revenue", "growth", "yrs_on_list", "url"]
    df = df[[c for c in keep if c in df.columns]]
    return df


def clean_data(df):
    """Basic cleaning: strip whitespace, drop rows missing core fields."""
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())
    df = df.dropna(subset=["rank", "company"])
    df = df.drop_duplicates(subset=["rank"])
    df = df.sort_values("rank").reset_index(drop=True)
    return df


def print_summary(df):
    """Print a human-readable summary to the console."""
    print("=" * 60)
    print("         INC 5000 — 2014 COMPANY LIST SUMMARY")
    print("=" * 60)

    print(f"\n📋 Total companies:       {len(df):,}")
    print(f"🏭 Unique industries:     {df['industry'].nunique()}")
    print(f"🗺️  States represented:    {df['state_l'].nunique()}")

    print(f"\n📈 Growth Rate (%):")
    print(f"   Highest:  {df['growth'].max():,.1f}%  → {df.loc[df['growth'].idxmax(), 'company']}")
    print(f"   Average:  {df['growth'].mean():,.1f}%")
    print(f"   Median:   {df['growth'].median():,.1f}%")

    print(f"\n💰 Revenue ($M):")
    print(f"   Highest:  ${df['revenue'].max():,}M  → {df.loc[df['revenue'].idxmax(), 'company']}")
    print(f"   Average:  ${df['revenue'].mean():,.1f}M")

    print(f"\n👥 Employees:")
    print(f"   Most:     {df['workers'].max():,}  → {df.loc[df['workers'].idxmax(), 'company']}")
    print(f"   Average:  {df['workers'].mean():,.0f}")

    print("\n🏆 Top 5 Industries by # of Companies:")
    top_industries = df["industry"].value_counts().head(5)
    for industry, count in top_industries.items():
        print(f"   {industry:<35} {count:>4} companies")

    print("\n🗺️  Top 5 States by # of Companies:")
    top_states = df["state_l"].value_counts().head(5)
    for state, count in top_states.items():
        print(f"   {state:<35} {count:>4} companies")

    print("\n🔁 Years on List:")
    yrs = df["yrs_on_list"].value_counts().sort_index()
    for yr, count in yrs.items():
        print(f"   {yr} year(s): {count:,} companies")

    print("=" * 60)


def build_summary_df(df):
    """Build an aggregated summary CSV grouped by industry."""
    summary = df.groupby("industry").agg(
        num_companies=("company", "count"),
        avg_growth_pct=("growth", "mean"),
        median_growth_pct=("growth", "median"),
        avg_revenue_m=("revenue", "mean"),
        total_revenue_m=("revenue", "sum"),
        avg_employees=("workers", "mean"),
        top_ranked_company=("rank", lambda x: df.loc[x.idxmin(), "company"]),
        top_rank=("rank", "min"),
    ).reset_index()

    summary = summary.sort_values("num_companies", ascending=False)

    # Round numeric columns for readability
    summary["avg_growth_pct"] = summary["avg_growth_pct"].round(1)
    summary["median_growth_pct"] = summary["median_growth_pct"].round(1)
    summary["avg_revenue_m"] = summary["avg_revenue_m"].round(1)
    summary["total_revenue_m"] = summary["total_revenue_m"].round(1)
    summary["avg_employees"] = summary["avg_employees"].round(0).astype(int)

    return summary


def main():
    print(f"\n📂 Reading: {INPUT_FILE}\n")

    # Load & clean
    df = load_data(INPUT_FILE)
    df = clean_data(df)

    # Print summary to console
    print_summary(df)

    # Save cleaned CSV
    df.to_csv(OUTPUT_CLEANED, index=False)
    print(f"\n✅ Cleaned CSV saved:  {OUTPUT_CLEANED}")

    # Save summary CSV
    summary_df = build_summary_df(df)
    summary_df.to_csv(OUTPUT_SUMMARY, index=False)
    print(f"✅ Summary CSV saved:  {OUTPUT_SUMMARY}")
    print("\nDone! 🎉\n")


if __name__ == "__main__":
    main()
