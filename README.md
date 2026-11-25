# BloodCare — Blood Donation Camp Register

A Python + Streamlit implementation of the supplied GreenFuture Hack Project #73 brief.

## Features
- Donor registration with defensive input validation
- Local persistence to `data/donors.json` and `data/donors.csv`
- Search and filters by keyword, blood group and status
- Dashboard KPIs, blood-group charts and executive analytics
- Update/delete donor records
- Bulk CSV import with row-by-row validation errors
- CSV, JSON, Markdown and TXT report downloads
- Dark premium interface

## Run on Windows (VS Code)
1. Install Python 3.10 or newer.
2. Extract the ZIP and open this folder in VS Code.
3. Open Terminal in VS Code and run:

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Your browser opens the app at the local Streamlit address.

## Run on macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Data
- `data/donors.json` and `data/donors.csv` are created automatically after the first save.
- `data/sample_donors.csv` contains fictional sample records for testing.
- Do not use real donor personal information in public demos.
- Medical eligibility must be confirmed by qualified medical personnel; this app is a registration and reporting tool only.
