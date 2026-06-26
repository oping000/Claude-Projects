# =============================================================================
# Amazon Review Intelligence Dashboard & Sentiment Prediction Pipeline
# =============================================================================
# Copyright (c) 2025 oping000 (ODell)
# GitHub: https://github.com/oping000/Claude-Projects
#
# Licensed under Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0)
# You may share and adapt this code for NON-COMMERCIAL purposes only.
# Commercial use requires explicit written permission from the author.
# Full license: https://creativecommons.org/licenses/by-nc/4.0/
# =============================================================================

"""
Amazon Review Sentiment & Prediction Pipeline
==============================================
Batch processes Amazon product reviews through Claude AI and outputs
an enriched CSV with sentiment analysis and business predictions.

Usage:
    python amazon_sentiment_pipeline.py

Requirements:
    pip install anthropic pandas python-dotenv

Setup:
    1. Copy .env.example to .env
    2. Add your Anthropic API key to .env
    3. Place your amazon reviews CSV in the same folder
    4. Run the script
"""

import os
import time
import json
import pandas as pd
import anthropic
from dotenv import load_dotenv

# ── CONFIG ──────────────────────────────────────────────────────────────────
load_dotenv()

INPUT_CSV    = "amazon_sentiment_analysis.csv"   # your input file
OUTPUT_CSV   = "amazon_enriched_output.csv"       # enriched output file
MODEL        = "claude-sonnet-4-6"
MAX_REVIEWS  = 30        # set to None to process all rows
DELAY_SEC    = 0.5       # pause between API calls to avoid rate limits
MAX_TOKENS   = 600

# ── ANTHROPIC CLIENT ─────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ── HELPER: CLEAN TEXT ───────────────────────────────────────────────────────
def clean_text(text: str, max_len: int = 400) -> str:
    """Strip URLs and truncate text for API calls."""
    import re
    text = re.sub(r'https?://\S+', '', str(text))
    return text[:max_len].strip()


# ── CORE: ANALYZE ONE REVIEW ─────────────────────────────────────────────────
def analyze_review(product_name: str, star_rating: float,
                   review_title: str, review_content: str) -> dict:
    """
    Send one review to Claude and return structured JSON with
    sentiment analysis + three business predictions.
    """
    prompt = f"""Analyze this Amazon product review for sentiment AND make three predictions.
Return ONLY valid JSON, no other text.

Product: {clean_text(product_name, 100)}
Star Rating: {star_rating}
Review Title: {clean_text(review_title, 200)}
Review Content: {clean_text(review_content, 400)}

Return exactly this JSON structure:
{{
  "sentiment": "Positive" or "Neutral" or "Negative",
  "sentiment_score": integer 1-10,
  "issue_category": one of ["Quality","Value","Performance","Durability","Shipping","Customer Service","Compatibility","General"],
  "priority": "High" or "Medium" or "Low",
  "summary": "one clean sentence under 20 words",
  "key_issue": "2-4 words",
  "predicted_stars": number 1.0-5.0 with one decimal,
  "rating_confidence": integer 0-100,
  "rating_reasoning": "one sentence explaining predicted stars",
  "escalation_risk": "High" or "Medium" or "Low",
  "escalation_probability": integer 0-100,
  "escalation_reasoning": "one sentence explaining escalation likelihood",
  "churn_signal": "Strong" or "Moderate" or "Weak",
  "churn_probability": integer 0-100,
  "churn_reasoning": "one sentence on whether customer will return"
}}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Extract JSON from response
    import re
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        raise ValueError(f"No JSON found in response: {raw[:200]}")

    return json.loads(match.group())


# ── PRODUCT HEALTH CHECK ─────────────────────────────────────────────────────
def analyze_product_health(product_name: str, reviews: list[str]) -> dict:
    """
    Given a product name and list of reviews (oldest to newest),
    return a health assessment: Stable / Declining / At Risk.
    """
    numbered = "\n".join(f"{i+1}. {r[:200]}" for i, r in enumerate(reviews))

    prompt = f"""You are a product health analyst. Analyze these {len(reviews)} reviews
for the product "{product_name}" and determine if sentiment is stable, declining, or at risk.

Reviews (oldest to newest):
{numbered}

Return ONLY valid JSON:
{{
  "overall_status": "Stable" or "Declining" or "At Risk",
  "status_reasoning": "one sentence explaining the overall health",
  "avg_sentiment_score": number 1-10,
  "trend": "Improving" or "Stable" or "Worsening",
  "top_issue": "main recurring problem in 3-5 words or None if healthy",
  "recommendation": "one actionable sentence for the product team",
  "review_scores": [array of integers 1-10, one per review in order]
}}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    import re
    raw = message.content[0].text.strip()
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        raise ValueError(f"No JSON found in response: {raw[:200]}")

    return json.loads(match.group())


# ── MAIN PIPELINE ─────────────────────────────────────────────────────────────
def run_pipeline():
    print("=" * 60)
    print("Amazon Review Sentiment & Prediction Pipeline")
    print("=" * 60)

    # Load CSV
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Input file not found: {INPUT_CSV}")
        print("   Make sure your CSV is in the same folder as this script.")
        return

    df = pd.read_csv(INPUT_CSV)
    print(f"✅ Loaded {len(df)} rows from {INPUT_CSV}")

    # Select columns we need
    required_cols = ['product_id', 'product_name', 'product_category',
                     'star_rating', 'review_title', 'review_content']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"❌ Missing columns: {missing}")
        print(f"   Available columns: {df.columns.tolist()}")
        return

    # Take sample if MAX_REVIEWS is set
    sample = df.dropna(subset=['review_content', 'review_title'])
    if MAX_REVIEWS:
        sample = sample.head(MAX_REVIEWS)

    print(f"📋 Processing {len(sample)} reviews with Claude {MODEL}...")
    print("-" * 60)

    results = []
    errors  = 0

    for idx, (_, row) in enumerate(sample.iterrows(), 1):
        try:
            print(f"[{idx:02d}/{len(sample)}] {str(row['product_name'])[:50]}...")

            result = analyze_review(
                product_name   = str(row['product_name']),
                star_rating    = float(row['star_rating']) if pd.notna(row['star_rating']) else 3.0,
                review_title   = str(row['review_title']),
                review_content = str(row['review_content'])
            )

            # Merge original fields + AI output
            results.append({
                'product_id':           row['product_id'],
                'product_name':         str(row['product_name'])[:80],
                'product_category':     str(row['product_category']).split('|')[0],
                'star_rating':          row['star_rating'],
                'sentiment':            result.get('sentiment', ''),
                'sentiment_score':      result.get('sentiment_score', ''),
                'issue_category':       result.get('issue_category', ''),
                'priority':             result.get('priority', ''),
                'key_issue':            result.get('key_issue', ''),
                'summary':              result.get('summary', ''),
                'predicted_stars':      result.get('predicted_stars', ''),
                'rating_confidence':    result.get('rating_confidence', ''),
                'rating_reasoning':     result.get('rating_reasoning', ''),
                'escalation_risk':      result.get('escalation_risk', ''),
                'escalation_probability': result.get('escalation_probability', ''),
                'escalation_reasoning': result.get('escalation_reasoning', ''),
                'churn_signal':         result.get('churn_signal', ''),
                'churn_probability':    result.get('churn_probability', ''),
                'churn_reasoning':      result.get('churn_reasoning', ''),
                'review_title':         clean_text(str(row['review_title']), 120),
                'review_content':       clean_text(str(row['review_content']), 250),
            })

            print(f"         ✓ {result.get('sentiment','?')} | "
                  f"Score: {result.get('sentiment_score','?')}/10 | "
                  f"Escalation: {result.get('escalation_risk','?')} | "
                  f"Predicted: {result.get('predicted_stars','?')}★")

        except Exception as e:
            print(f"         ✗ Error: {e}")
            errors += 1

        time.sleep(DELAY_SEC)

    # Save output
    out_df = pd.DataFrame(results)
    out_df.to_csv(OUTPUT_CSV, index=False)

    # Summary
    print("-" * 60)
    print(f"✅ Done! {len(results)} reviews processed, {errors} errors")
    print(f"📄 Output saved to: {OUTPUT_CSV}")
    print()
    print("📊 Summary:")
    if len(out_df):
        print(f"   Sentiment breakdown:\n{out_df['sentiment'].value_counts().to_string()}")
        print(f"\n   Priority breakdown:\n{out_df['priority'].value_counts().to_string()}")
        print(f"\n   Avg sentiment score: {out_df['sentiment_score'].mean():.1f}/10")
        print(f"   Avg predicted stars: {out_df['predicted_stars'].mean():.1f}/5")
        high_esc = len(out_df[out_df['escalation_risk']=='High'])
        print(f"   High escalation risk: {high_esc} reviews")

    # Optional: run product health check per product
    print()
    run_health = input("Run product health check per product? (y/n): ").strip().lower()
    if run_health == 'y' and len(out_df):
        print("\n🏥 Product Health Analysis:")
        print("-" * 60)
        health_results = []

        for product_name, group in out_df.groupby('product_name'):
            reviews = group['review_content'].dropna().tolist()
            if len(reviews) < 2:
                continue
            try:
                health = analyze_product_health(product_name, reviews)
                icon = '✅' if health['overall_status']=='Stable' else '⚠️' if health['overall_status']=='Declining' else '🚨'
                print(f"{icon} {product_name[:50]}")
                print(f"   Status: {health['overall_status']} | Trend: {health['trend']} | Avg: {health['avg_sentiment_score']}/10")
                print(f"   Top issue: {health['top_issue']}")
                print(f"   Recommendation: {health['recommendation']}")
                print()
                health_results.append({
                    'product_name':    product_name,
                    'health_status':   health['overall_status'],
                    'trend':           health['trend'],
                    'avg_score':       health['avg_sentiment_score'],
                    'top_issue':       health['top_issue'],
                    'recommendation':  health['recommendation'],
                })
                time.sleep(DELAY_SEC)
            except Exception as e:
                print(f"   Error for {product_name[:40]}: {e}")

        if health_results:
            health_df = pd.DataFrame(health_results)
            health_df.to_csv('product_health_report.csv', index=False)
            print(f"📄 Product health report saved to: product_health_report.csv")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ No API key found!")
        print("   1. Copy .env.example to .env")
        print("   2. Add your key: ANTHROPIC_API_KEY=sk-ant-...")
        print("   3. Run the script again")
    else:
        print(f"✅ API key loaded ({api_key[:12]}...)")
        run_pipeline()
