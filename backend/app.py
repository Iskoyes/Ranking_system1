# backend/app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, re, ast
from pathlib import Path

from PyPDF2 import PdfReader
import pandas as pd

# If your util lives at backend/utils/utils.py (as you showed):
from utils import time_to_seconds

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent          # .../backend
PROJECT_ROOT = BASE_DIR.parent                      # .../ (repo root)
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
DOCS_DIR = PROJECT_ROOT / "docs"
DATA_DIR = PROJECT_ROOT / "data"
PDF_PATH = DOCS_DIR / "rudolph.pdf"

# ---------- App ----------
# Only pass template/static folders if they actually exist (Flask doesn't like None)
if TEMPLATES_DIR.exists() or STATIC_DIR.exists():
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR) if TEMPLATES_DIR.exists() else None,
        static_folder=str(STATIC_DIR) if STATIC_DIR.exists() else None,
    )
else:
    app = Flask(__name__)
CORS(app)

# ---------- DB ----------
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///local.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------- Model ----------
class Swimmers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    year_of_birth = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    event = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(100), nullable=False)
    date_of_competition = db.Column(db.Date, nullable=False)
    pool_length = db.Column(db.Integer, nullable=False)
    fina_points = db.Column(db.Integer, nullable=True)
    rudolph_points = db.Column(db.Integer, nullable=True)

# ---------- Constants ----------
# -- SHORT COURSE (25m) --
fina_base_times_scm_male = {
    "50M FREESTYLE": 20.16, "50 FREESTYLE": 20.16,
    "100M FREESTYLE": 44.84, "100 FREESTYLE": 44.84,
    "200M FREESTYLE": 99.37, "200 FREESTYLE": 99.37,
    "400M FREESTYLE": 212.25, "400 FREESTYLE": 212.25,
    "800M FREESTYLE": 443.42, "800 FREESTYLE": 443.42,
    "1500M FREESTYLE": 846.88, "1500 FREESTYLE": 846.88,
    "50M BACKSTROKE": 22.11, "50 BACKSTROKE": 22.11,
    "100M BACKSTROKE": 48.33, "100 BACKSTROKE": 48.33,
    "200M BACKSTROKE": 105.63, "200 BACKSTROKE": 105.63,
    "50M BREASTSTROKE": 24.95, "50 BREASTSTROKE": 24.95,
    "100M BREASTSTROKE": 55.28, "100 BREASTSTROKE": 55.28,
    "200M BREASTSTROKE": 120.16, "200 BREASTSTROKE": 120.16,
    "50M BUTTERFLY": 21.75, "50 BUTTERFLY": 21.75,
    "100M BUTTERFLY": 47.78, "100 BUTTERFLY": 47.78,
    "200M BUTTERFLY": 106.85, "200 BUTTERFLY": 106.85,
    "100M MEDLEY": 49.28, "100 MEDLEY": 49.28,
    "200M MEDLEY": 109.63, "200 MEDLEY": 109.63,
    "400M MEDLEY": 234.81, "400 MEDLEY": 234.81
}
fina_base_times_scm_female = {
    "50M FREESTYLE": 22.93, "50 FREESTYLE": 22.93,
    "100M FREESTYLE": 50.25, "100 FREESTYLE": 50.25,
    "200M FREESTYLE": 110.31, "200 FREESTYLE": 110.31,
    "400M FREESTYLE": 231.30, "400 FREESTYLE": 231.30,
    "800M FREESTYLE": 477.42, "800 FREESTYLE": 477.42,
    "1500M FREESTYLE": 908.24, "1500 FREESTYLE": 908.24,
    "50M BACKSTROKE": 25.25, "50 BACKSTROKE": 25.25,
    "100M BACKSTROKE": 54.89, "100 BACKSTROKE": 54.89,
    "200M BACKSTROKE": 118.94, "200 BACKSTROKE": 118.94,
    "50M BREASTSTROKE": 28.37, "50 BREASTSTROKE": 28.37,
    "100M BREASTSTROKE": 62.36, "100 BREASTSTROKE": 62.36,
    "200M BREASTSTROKE": 134.57, "200 BREASTSTROKE": 134.57,
    "50M BUTTERFLY": 24.38, "50 BUTTERFLY": 24.38,
    "100M BUTTERFLY": 54.05, "100 BUTTERFLY": 54.05,
    "200M BUTTERFLY": 119.61, "200 BUTTERFLY": 119.61,
    "100M MEDLEY": 56.51, "100 MEDLEY": 56.51,
    "200M MEDLEY": 121.86, "200 MEDLEY": 121.86,
    "400M MEDLEY": 258.94, "400 MEDLEY": 258.94
}
# -- LONG COURSE (50m) --
fina_base_times_lcm_male = {
    "50M FREESTYLE": 20.91, "50 FREESTYLE": 20.91,
    "100M FREESTYLE": 46.86, "100 FREESTYLE": 46.86,
    "200M FREESTYLE": 102.00, "200 FREESTYLE": 102.00,
    "400M FREESTYLE": 220.07, "400 FREESTYLE": 220.07,
    "800M FREESTYLE": 452.12, "800 FREESTYLE": 452.12,
    "1500M FREESTYLE": 871.02, "1500 FREESTYLE": 871.02,
    "50M BACKSTROKE": 23.55, "50 BACKSTROKE": 23.55,
    "100M BACKSTROKE": 51.60, "100 BACKSTROKE": 51.60,
    "200M BACKSTROKE": 111.92, "200 BACKSTROKE": 111.92,
    "50M BREASTSTROKE": 25.95, "50 BREASTSTROKE": 25.95,
    "100M BREASTSTROKE": 56.88, "100 BREASTSTROKE": 56.88,
    "200M BREASTSTROKE": 125.48, "200 BREASTSTROKE": 125.48,
    "50M BUTTERFLY": 22.27, "50 BUTTERFLY": 22.27,
    "100M BUTTERFLY": 49.45, "100 BUTTERFLY": 49.45,
    "200M BUTTERFLY": 110.34, "200 BUTTERFLY": 110.34,
    "200M MEDLEY": 114.00, "200 MEDLEY": 114.00,
    "400M MEDLEY": 242.50, "400 MEDLEY": 242.50
}
fina_base_times_lcm_female = {
    "50M FREESTYLE": 23.61, "50 FREESTYLE": 23.61,
    "100M FREESTYLE": 51.71, "100 FREESTYLE": 51.71,
    "200M FREESTYLE": 112.85, "200 FREESTYLE": 112.85,
    "400M FREESTYLE": 235.38, "400 FREESTYLE": 235.38,
    "800M FREESTYLE": 484.79, "800 FREESTYLE": 484.79,
    "1500M FREESTYLE": 920.48, "1500 FREESTYLE": 920.48,
    "50M BACKSTROKE": 26.86, "50 BACKSTROKE": 26.86,
    "100M BACKSTROKE": 57.33, "100 BACKSTROKE": 57.33,
    "200M BACKSTROKE": 123.14, "200 BACKSTROKE": 123.14,
    "50M BREASTSTROKE": 29.16, "50 BREASTSTROKE": 29.16,
    "100M BREASTSTROKE": 64.13, "100 BREASTSTROKE": 64.13,
    "200M BREASTSTROKE": 137.55, "200 BREASTSTROKE": 137.55,
    "50M BUTTERFLY": 24.43, "50 BUTTERFLY": 24.43,
    "100M BUTTERFLY": 55.48, "100 BUTTERFLY": 55.48,
    "200M BUTTERFLY": 121.81, "200 BUTTERFLY": 121.81,
    "200M MEDLEY": 126.12, "200 MEDLEY": 126.12,
    "400M MEDLEY": 265.87, "400 MEDLEY": 265.87
}

# ---------- Helpers ----------
def calculate_fina_points(base_time, swimmer_time):
    """Return FINA points; swimmer_time can be seconds or 'MM:SS(.ms)'."""
    try:
        total_swimmer_time = float(swimmer_time)
    except Exception:
        total_swimmer_time = time_to_seconds(swimmer_time)

    if base_time and total_swimmer_time > 0:
        return round(1000 * (base_time / total_swimmer_time) ** 3, 2)
    return 0

def normalize_event_name(event: str) -> str:
    return (event or "").strip().upper()

def normalize_gender(gender: str) -> str:
    if not gender:
        return ""
    g = gender.strip().upper()
    if g in {"M", "MALE"}:
        return "M"
    if g in {"F", "FEMALE", "Ж"}:
        return "F"
    return ""

def extract_rudolph_points_from_pdf(pdf_path: str):
    """Parse the Rudolph PDF into a structured list.

    NOTE: PDF parsing is brittle; keep regex defensive and expect blanks.
    """
    data = []

    reader = PdfReader(pdf_path)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)

    pattern = re.compile(
        r"Punkttabelle\s+(?P<gender>\w+),\s+Altersklasse\s+(?P<age>\d+|offen)[\s\S]+?"
        r"Pkt[\s\S]+?(?P<data>(?:\d+\s+[\d:.,\s]+)+)",
        re.MULTILINE
    )

    for match in pattern.finditer(text):
        age_group = match.group("age")
        if age_group == "offen":
            age_group = "19"
        elif age_group and age_group.isdigit() and int(age_group) > 18:
            # Convert "19+"-ish buckets if present in source
            age_group = age_group[:-1]

        gender_raw = (match.group("gender") or "").lower()
        gender = "M" if gender_raw.startswith("männ") or gender_raw.startswith("mann") else "F"

        results = match.group("data") or ""
        lines = [ln.strip() for ln in results.split("\n") if ln.strip()]

        for line in lines:
            parts = line.split()
            if not parts:
                continue
            points = parts[0]
            if points == "50":  # skip header-like rows
                continue

            # Defensive zips in case a row is short
            freestyle    = [{"distance": d, "time": t} for d, t in zip([50, 100, 200, 400, 800, 1500], parts[1:7])]
            breaststroke = [{"distance": d, "time": t} for d, t in zip([50, 100, 200], parts[7:10])]
            butterfly    = [{"distance": d, "time": t} for d, t in zip([50, 100, 200], parts[10:13])]
            backstroke   = [{"distance": d, "time": t} for d, t in zip([50, 100, 200], parts[13:16])]
            medley       = [{"distance": d, "time": t} for d, t in zip([200, 400], parts[16:18])]

            events = [{
                "Freestyle": freestyle,
                "Breaststroke": breaststroke,
                "Butterfly": butterfly,
                "Backstroke": backstroke,
                "Medley": medley
            }]

            data.append({
                "age": age_group,
                "gender": gender,
                "point": points,
                "events": events
            })
    return data

def assign_rudolph_points_to_swimmers():
    csv_path = DATA_DIR / "rudolph_points.csv"
    if not csv_path.exists():
        app.logger.warning("rudolph_points.csv not found at %s; skipping assignment", csv_path)
        return

    rudolph_points_df = pd.read_csv(csv_path)

    for swimmer in Swimmers.query.all():
        try:
            year_of_competition = swimmer.date_of_competition.year
        except Exception:
            # If date is missing/bad, skip
            continue

        age = year_of_competition - int(swimmer.year_of_birth)
        if age > 18:
            age = 19

        # split "50m Backstroke" -> ["50m", "Backstroke"]
        parts = (swimmer.event or "").split()
        if len(parts) < 2:
            continue
        distance = parts[0].lower()  # e.g., "50m"
        stroke = parts[1].title()    # "Backstroke"

        filtered = rudolph_points_df.loc[
            (rudolph_points_df["age"] == age) & (rudolph_points_df["gender"] == swimmer.gender)
        ]

        res = 0
        for _, point_data in filtered.iterrows():
            try:
                results_dict = ast.literal_eval(point_data["events"])
            except Exception:
                results_dict = None
            if not results_dict:
                continue

            # Expecting a list-of-dict like [{"Freestyle": [...], ...}]
            bucket = results_dict[0] if isinstance(results_dict, list) and results_dict else {}
            if stroke not in bucket:
                continue

            for result in bucket[stroke]:
                # result['distance'] is int (e.g., 50), compare to '50m'
                if f"{result.get('distance')}m" == distance:
                    try:
                        swimmer_seconds = float(swimmer.result)
                    except Exception:
                        swimmer_seconds = time_to_seconds(swimmer.result)

                    try:
                        threshold_seconds = time_to_seconds(result.get("time", "0"))
                    except Exception:
                        threshold_seconds = 0

                    if threshold_seconds and swimmer_seconds >= threshold_seconds:
                        res = int(point_data["point"])
                        break

        swimmer.rudolph_points = res

    db.session.commit()

# ---------- Routes ----------
@app.route("/healthz")
def healthz():
    return {"ok": True}, 200

@app.route("/")
def home():
    # Serve index.html if present; else a simple JSON ok
    if TEMPLATES_DIR.exists() and (TEMPLATES_DIR / "index.html").exists():
        return render_template("index.html")
    return jsonify({"status": "ok"})

@app.route("/api/data", methods=["POST"])
def add_data():
    data = request.form or (request.json or {})
    try:
        new_entry = Swimmers(
            full_name=data["full_name"],
            year_of_birth=int(data["year_of_birth"]),
            gender=data["gender"],
            event=data["event"],
            result=data["result"],
            date_of_competition=datetime.strptime(data["date_of_competition"], "%Y-%m-%d").date(),
            pool_length=int(data["pool_length"]),
        )
    except Exception as e:
        return jsonify({"error": f"Bad payload: {e}"}), 400

    db.session.add(new_entry)
    db.session.commit()
    return jsonify({"message": "Data inserted successfully!"}), 201

@app.route("/rudolph-data")
def rudolph_data():
    if not PDF_PATH.exists():
        return {"error": f"PDF not found at {PDF_PATH}"}, 404
    try:
        data = extract_rudolph_points_from_pdf(str(PDF_PATH))
    except Exception as e:
        app.logger.exception("Failed to parse PDF")
        return {"error": f"Failed to parse PDF: {e}"}, 500
    return jsonify(data)

@app.route("/rudolph/generate-csv")
def generate_rudolph_csv():
    """Generate CSV from the PDF on demand."""
    if not PDF_PATH.exists():
        return {"error": f"PDF not found at {PDF_PATH}"}, 404
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        rows = extract_rudolph_points_from_pdf(str(PDF_PATH))
        df = pd.DataFrame(rows)
        csv_path = DATA_DIR / "rudolph_points.csv"
        df.to_csv(csv_path, index=False)
        return {"message": "CSV generated", "rows": len(df)}, 200
    except Exception as e:
        app.logger.exception("Failed to generate CSV")
        return {"error": f"Failed to generate CSV: {e}"}, 500

@app.route("/recalc-points")
def recalc_points():
    """Recalculate points for all swimmers (requires CSV to exist)."""
    try:
        assign_rudolph_points_to_swimmers()
        return {"message": "Recalculated"}, 200
    except Exception as e:
        app.logger.exception("Failed to recalc points")
        return {"error": f"Failed to recalc points: {e}"}, 500

# ---------- Startup (safe) ----------
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        # Don't crash import-time on managed DB hiccups; log instead.
        app.logger.warning("DB init warning: %s", e)

    # Optional bootstrap toggles
    if os.getenv("PRELOAD_RUDOLPH_CSV") == "1":
        try:
            if PDF_PATH.exists():
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                rows = extract_rudolph_points_from_pdf(str(PDF_PATH))
                pd.DataFrame(rows).to_csv(DATA_DIR / "rudolph_points.csv", index=False)
        except Exception as e:
            app.logger.warning("PRELOAD_RUDOLPH_CSV failed: %s", e)

    if os.getenv("ASSIGN_RUDOLPH_ON_BOOT") == "1":
        try:
            assign_rudolph_points_to_swimmers()
        except Exception as e:
            app.logger.warning("ASSIGN_RUDOLPH_ON_BOOT failed: %s", e)

if __name__ == "__main__":
    # For local dev only; Render will run via Gunicorn: gunicorn backend.app:app
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
