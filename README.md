# Part 2 — RFM Segmentation & Retention Strategy

## Goal
Create customer segments using RFM plus behavioral/support signals, recommend actions, and prepare manual review cases.

## How to run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/rfm_segmentation.py
```

Optional notebook execution:

```bash
jupyter nbconvert --to notebook --execute rfm_segmentation.ipynb --inplace
```

## Required outputs generated

- `rfm_segmentation.ipynb`
- `segments.csv`
- `retention_strategy.md`
- `manual_review_cases.md`
- supporting tables in `outputs/tables/`
