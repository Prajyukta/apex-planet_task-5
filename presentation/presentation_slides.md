# Apexplanet Capstone Deck | 10-Slide Layout

> Source layout for `presentation_slides.pptx`. Export this outline into PowerPoint or Canva after replacing placeholders with approved visuals.

## 1. Title
- Apexplanet Retail Intelligence: Final Reporting and Pipeline Deployment
- Subtitle: Task 5 Capstone | Presenter | Date
- Visual: executive dashboard hero image

## 2. Problem
- Manual reporting delays action and creates inconsistent KPI definitions.
- Business questions: What changed? Where is margin leaking? Which customers need intervention?
- Success measure: trusted daily decision pack by 06:00 UTC.

## 3. Data
- 11 source fields across transaction, customer, product, geography, commercial, and churn domains.
- Data contract: required columns, UTC date standard, numeric bounds, deduplication rule.
- Visual: source-to-model lineage diagram.

## 4. EDA
- Revenue, profit margin, AOV, active customers, and units sold.
- Top 5 discoveries: regional contribution, category mix, discount-margin relationship, repeat behavior, risk concentration.
- Visual: KPI strip plus annotated trend and category chart.

## 5. Dashboard
- Executive overview, regional drill-through, customer risk, and tooltip microchart pages.
- Visual: replace `dashboards/assets/*.png` placeholders with approved screenshots.
- Interaction: date, region, and category filters.

## 6. ML and Statistics
- ANOVA, t-tests, and confidence intervals for performance comparisons.
- ARIMA baseline: 92% accuracy claim requires validation on the approved holdout.
- K-Means RFM segments and transparent churn-risk score.

## 7. Recommendations
- Immediate: retain high-value/high-risk customers and investigate margin outliers.
- Mid-term: category playbooks, shipping optimization, and experiment measurement.
- Long-term: feature store, monitored propensity model, and forecast-led planning.

## 8. Challenges
- Batch quality variation, sparse customer history, metric governance, and dashboard refresh ownership.
- Controls: schema validation, anomaly handling, versioned artifacts, secrets management, and logs.

## 9. Future Scope
- Replace CSV handoff with warehouse tables and incremental loads.
- Add drift, freshness, and anomaly alerts.
- Add causal uplift testing and monitored model registry.

## 10. Thank You
- Key takeaway: a reproducible daily analytics operating loop.
- Links: repository, dashboard cloud URL, unlisted demo URL.
- Contact: presenter email.
