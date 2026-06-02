# Amazon Review Sentiment & Prediction Pipeline

An end-to-end AI-powered pipeline that transforms unstructured Amazon product reviews into structured sentiment analysis and business predictions — built with Python, Claude AI, and vanilla HTML/JavaScript.

---

## What It Does

This project solves a real business problem: companies receive thousands of unstructured customer reviews daily and need to instantly know:

- **Sentiment** — Is the customer positive, neutral, or negative?
- **Score** — How positive/negative on a scale of 1–10?
- **Issue Category** — Quality, Value, Performance, Shipping, etc.
- **Priority** — How urgently does this need attention?
- **Predicted Star Rating** — What rating would this customer give?
- **Escalation Risk** — Will this customer demand a refund or go public?
- **Churn Signal** — Will this customer ever buy again?

---

## Project Files

| File | Description |
|------|-------------|
| `amazon_sentiment_dashboard.html` | Full pipeline dashboard — sentiment analysis + predictions + charts |
| `amazon_predictions.html` | Standalone prediction engine — escalation risk, star rating, churn signal |
| `amazon_sentiment_analysis.csv` | Sample enriched output from 30 Amazon reviews |
| `.env.example` | API key template — copy to `.env` and add your key |

---

## Architecture

```
Unstructured Review Text
        ↓
  Claude AI API (claude-sonnet-4-6)
        ↓
  Structured JSON Output
        ↓
  ┌─────────────────────────────┐
  │  Sentiment Analysis         │
  │  • Sentiment label          │
  │  • Score 1-10               │
  │  • Issue category           │
  │  • Priority level           │
  │  • One-line summary         │
  └─────────────────────────────┘
        ↓
  ┌─────────────────────────────┐
  │  Predictions                │
  │  • Predicted star rating    │
  │  • Escalation risk %        │
  │  • Churn signal %           │
  └─────────────────────────────┘
        ↓
  Dashboard + Exportable CSV
```

---

## How To Use

### 1. Get an Anthropic API Key
- Go to [console.anthropic.com](https://console.anthropic.com)
- Navigate to **API Keys** in the left sidebar
- Create a new key and copy it

### 2. Run the Dashboard
- Download `amazon_sentiment_dashboard.html`
- Open it in any browser (double-click the file)
- Paste your API key in the box at the top
- Type or paste any product review and click **Analyze + Predict**

### 3. Run the Prediction Engine
- Download `amazon_predictions.html`
- Open in browser, paste your API key
- Paste a review and click **Run Predictions**
- See escalation risk, predicted star rating, and churn signal instantly

### 4. Export Results
- Click **Download CSV** in the History tab to export all analyzed reviews

---

## Example Input & Output

**Input review:**
> "I ordered this cable to connect my phone to Android Auto. Good service but sound quality was poor."

**Output:**
```json
{
  "sentiment": "Neutral",
  "sentiment_score": 5,
  "category": "Quality",
  "priority": "Medium",
  "summary": "Customer satisfied with service but disappointed with audio quality.",
  "predicted_stars": 3.0,
  "escalation_risk": "Low",
  "escalation_probability": 15,
  "churn_signal": "Moderate",
  "churn_probability": 45
}
```

---

## Tech Stack

- **Claude AI** (claude-sonnet-4-6) — LLM for analysis and predictions
- **Anthropic API** — Direct browser API calls with structured JSON output
- **HTML / CSS / JavaScript** — Zero-dependency frontend
- **Chart.js** — Interactive charts and visualizations
- **Python + Pandas** — Batch processing pipeline (CSV enrichment)

---

## API Key Security

- Your API key is **never stored** — it lives only in your browser session
- The `.gitignore` ensures `.env` files are never committed to GitHub
- Use `.env.example` as a template if extending this to a Python backend

---

## Future Enhancements

- [ ] Batch upload — process entire CSV files through the dashboard
- [ ] Product failure detection — track sentiment trends per product over time
- [ ] Power BI connector — direct export to Power BI dashboard format
- [ ] Database integration — store results in SQLite or Snowflake
- [ ] Demand forecasting — correlate sentiment trends with sales predictions

---

## Dataset

Sample data sourced from Amazon product reviews (electronics category). The enriched output CSV (`amazon_sentiment_analysis.csv`) contains 30 processed reviews with sentiment scores, categories, and priorities.

---

## Author

Built as a portfolio project demonstrating AI-powered unstructured-to-structured data pipelines.

---

## License

MIT License — free to use, modify, and distribute.
