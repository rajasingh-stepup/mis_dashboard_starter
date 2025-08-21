# MIS Dashboard & Report Starter (Streamlit + Python)

This starter lets you upload MIS files (Excel/CSV), select sheets/columns, clean/transform, and render a **live dashboard** with KPIs, charts and tables. It also generates a **PowerPoint deck** with key visuals for weekly/monthly reporting.

## Quickstart (Local)
```bash
# 1) Create venv (optional)
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) Run the app
streamlit run app.py
```

## Deploy
See the end of this README for deployment options: Streamlit Community Cloud, Render, Railway, Hugging Face Spaces, or Docker.

## Data assumptions
- Your MIS is typically a monthly/weekly export (Excel/CSV). Common columns:
  - `date`, `week`, `month`, `segment`, `region`
  - `channel`, `product`, `orders`, `gmv`, `revenue`, `cost`, `units`, `customers`
- The app supports **column mapping**, so your actual column names can differ.

## Pages
- **Home**: upload/mapping, filters, KPIs, charts, detailed table
- **Report (PPT)**: one-click export of current filtered KPIs/charts to a PowerPoint file
- **Data Dictionary**: view/define column mappings & save as JSON for reuse

## Files
- `app.py` – main dashboard, file upload, filters, charts
- `pages/1_Report_PPT.py` – export a PPT report
- `pages/2_Data_Dictionary.py` – define/save column mappings
- `assets/sample_mis.csv` – sample data
- `requirements.txt` – Python dependencies

## Notes
- This is intentionally modular—add new charts/metrics by editing `build_charts()` in `app.py`.
- Large Excel files: prefer CSV for speed; or host on a DB (Postgres/MySQL/BigQuery) and swap `load_data()`.

## Deployment recipes
### Streamlit Community Cloud
1. Push this folder to GitHub.
2. Go to https://share.streamlit.io, connect repo, select `app.py`, and deploy.
3. Set `PYTHON_VERSION` to 3.11+ if prompted.

### Render (free tier possible)
1. Push to GitHub.
2. Create new **Web Service** → Runtime **Python**.
3. Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

### Railway / Fly.io / Hugging Face Spaces
- Similar steps; for HF Spaces choose **Streamlit** template and upload repo.

### Docker (optional)
Use the `Dockerfile` below:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Support
- Add calculations or bespoke visuals in `build_kpis()` and `build_charts()`.
- For data quality checks, extend `validate_data()` in `app.py`.