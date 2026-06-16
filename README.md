# Part 2 — RFM Segmentation & Retention Strategy

## Goal
Create customer segments using RFM plus behavioral/support signals, recommend actions, and prepare manual review cases.

## Project Structure

```text
part2_rfm_retention/
├── data/                    # Raw capstone datasets & data dictionary
├── outputs/
│   ├── figures/             # Visualizations (e.g. segment churn rates)
│   └── tables/              # Segment summaries and targeted customer lists
├── src/
│   └── rfm_segmentation.py  # Main script for RFM modeling and segmentation
├── manual_review_cases.md   # Profiles of specific customers flagged for human review
├── rfm_segmentation.ipynb   # Notebook running the RFM segmentation
├── retention_strategy.md    # Retention tactics, budgets, and action plans
├── segments.csv             # Output CSV file containing segmented customers
├── README.md                # Project documentation and developer info
└── requirements.txt         # Python dependencies
```

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

## Developer Information

- **Developer:** Shashwat SIngh
- **Student Code:** IITP_AIML_2506887
- **Email:** shashwatanshul@gmail.com

