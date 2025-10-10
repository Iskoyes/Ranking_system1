# backend/app.py
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, re, ast
from pathlib import Path
import pandas as pd
from .utils import time_to_seconds
from functools import wraps
import json

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
DOCS_DIR = PROJECT_ROOT / "docs"
DATA_DIR = BASE_DIR / "data"
PDF_PATH = DOCS_DIR / "rudolph.pdf"
YEAR = 2025
# ---------- App ----------
app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR) if TEMPLATES_DIR.exists() else None,
    static_folder=str(STATIC_DIR) if STATIC_DIR.exists() else None
)
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")
# Session cookie hardening
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
)

# ---------- DB ----------
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / f'data_{YEAR}.db'}")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------- Models ----------
class Swimmers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    year_of_birth = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    event = db.Column(db.String(100), nullable=False)
    result = db.Column(db.Float, nullable=False)  # stored in seconds
    name_of_competition = db.Column(db.String(100), nullable=False)
    date_of_competition = db.Column(db.Date, nullable=False)
    pool_length = db.Column(db.Integer, nullable=False)
    place_taken = db.Column(db.Integer, nullable=False)
    fina_points = db.Column(db.Integer, nullable=True)
    rudolph_points = db.Column(db.Integer, nullable=True)
    __table_args__ = (
        db.CheckConstraint("gender in ('M','F')", name="ck_swimmers_gender"),
        db.CheckConstraint("pool_length in (25,50)", name="ck_swimmers_pool_length"),
    )

# ---------- Admin credentials ----------
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin2025")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ---------- Routes ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        flash("Invalid username or password", "err")
    return render_template("index.html")

@app.route("/logout")
@login_required
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    return render_template("index.html")

@app.route("/api/data", methods=["POST"])
@login_required
def add_data():
    data = request.form or request.json or {}
    try:
        # Normalize/parse inputs
        gender = normalize_gender(data["gender"]) or data["gender"]
        event_name = normalize_event_name(data["event"]) or data["event"]
        result_seconds = time_to_seconds(data["result"])  # supports both seconds and mm:ss,ms
        pool_len = int(data["pool_length"])
        place_taken = int(data["place_taken"])
        name_of_competition = str(data["name_of_competition"])
        event_date = datetime.strptime(data["date_of_competition"], "%Y-%m-%d").date()

        # Compute points
        base_time = get_base_time(event_name, gender, pool_len)
        fina_pts = int(calculate_fina_points(base_time, result_seconds)) if base_time else 0
        rudolph_pts = calculate_rudolph_points(event_name, gender, event_date.year - int(data["year_of_birth"]), result_seconds)

        new_entry = Swimmers(
            full_name=data["full_name"],
            year_of_birth=int(data["year_of_birth"]),
            gender=gender,
            event=event_name,
            result=result_seconds,
            name_of_competition=name_of_competition,
            date_of_competition=event_date,
            pool_length=pool_len,
            place_taken=place_taken,
            fina_points=fina_pts,
            rudolph_points=rudolph_pts
        )
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({"message": "Data inserted successfully!"}), 201
    except Exception as e:
        return jsonify({"error": f"Bad payload: {e}"}), 400

@app.route("/api/swimmers", methods=["GET"])
@login_required
def list_swimmers():
    try:
        limit = int(request.args.get("limit", 20))
        swimmers = (
            Swimmers.query.order_by(Swimmers.id.desc()).limit(limit).all()
        )
        def to_dict(s: Swimmers):
            return {
                "id": s.id,
                "full_name": s.full_name,
                "year_of_birth": s.year_of_birth,
                "gender": s.gender,
                "event": s.event,
                "result": s.result,
                "name_of_competition": s.name_of_competition,
                "date_of_competition": s.date_of_competition.isoformat(),
                "pool_length": s.pool_length,
                "place_taken": s.place_taken,
                "fina_points": s.fina_points or 0,
                "rudolph_points": s.rudolph_points or 0,
            }
        return jsonify([to_dict(s) for s in swimmers])
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/swimmers/<int:swimmer_id>", methods=["PUT"])
@login_required
def update_swimmer(swimmer_id: int):
    payload = request.json or {}
    s = Swimmers.query.get_or_404(swimmer_id)
    try:
        if "full_name" in payload:
            s.full_name = payload["full_name"]
        if "year_of_birth" in payload:
            s.year_of_birth = int(payload["year_of_birth"])
        if "gender" in payload:
            s.gender = normalize_gender(payload["gender"]) or payload["gender"]
        if "event" in payload:
            s.event = normalize_event_name(payload["event"]) or payload["event"]
        if "result" in payload:
            s.result = float(time_to_seconds(payload["result"]))
        if "name_of_competition" in payload:
            s.name_of_competition = payload["name_of_competition"]
        if "date_of_competition" in payload:
            s.date_of_competition = datetime.strptime(payload["date_of_competition"], "%Y-%m-%d").date()
        if "pool_length" in payload:
            s.pool_length = int(payload["pool_length"])
        if "place_taken" in payload:
            s.place_taken = int(payload["place_taken"])
        # Recompute points if any relevant fields changed
        base_time = get_base_time(s.event, s.gender, s.pool_length)
        s.fina_points = int(calculate_fina_points(base_time, s.result)) if base_time else 0
        age = s.date_of_competition.year - s.year_of_birth
        s.rudolph_points = calculate_rudolph_points(s.event, s.gender, age, s.result)
        db.session.commit()
        return jsonify({"message": "Updated"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route("/api/swimmers/<int:swimmer_id>", methods=["DELETE"])
@login_required
def delete_swimmer(swimmer_id: int):
    s = Swimmers.query.get_or_404(swimmer_id)
    try:
        db.session.delete(s)
        db.session.commit()
        return jsonify({"message": "Deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route("/api/export", methods=["GET"])
@login_required
def export_excel():
    try:
        swimmers = Swimmers.query.all()
        if not swimmers:
            return jsonify({"error": "No data to export"}), 400
        rows = []
        for s in swimmers:
            rows.append({
                "ФИО": s.full_name,
                "Год рождения": s.year_of_birth,
                "Пол": 'Ж' if s.gender == 'F' else 'M',
                "Дистанция": s.event,
                "Время": s.result,
                "Название соревнования": s.name_of_competition,
                "Дата проведения соревнований": s.date_of_competition,
                "Тип бассейна": s.pool_length,
                "Занятое место": s.place_taken,
                "FINA Points": s.fina_points or 0,
                "Rudolph Points": s.rudolph_points or 0,
            })
        df = pd.DataFrame(rows)
        # Map events to RU labels
        df['Дистанция'] = df['Дистанция'].astype(str).str.replace('M ', 'm ', regex=False)
        mapping = {
            '50m Freestyle':'50м кроль','100m Freestyle':'100м кроль','200m Freestyle':'200м кроль','400m Freestyle':'400м кроль','800m Freestyle':'800м кроль','1500m Freestyle':'1500м кроль',
            '50m Breaststroke':'50м брасс','100m Breaststroke':'100м брасс','200m Breaststroke':'200м брасс',
            '50m Butterfly':'50м батт','100m Butterfly':'100м батт','200m Butterfly':'200м батт',
            '50m Backstroke':'50м на спине','100m Backstroke':'100м на спине','200m Backstroke':'200м на спине',
            '200m Medley':'200м комплекс','400m Medley':'400м комплекс'
        }
        df['Дистанция'] = df['Дистанция'].replace(mapping)
        # Format date
        df['Дата проведения соревнований'] = pd.to_datetime(df['Дата проведения соревнований'], errors='coerce').dt.strftime('%d/%m/%Y')
        # Ensure ints
        df['FINA Points'] = pd.to_numeric(df['FINA Points'], errors='coerce').fillna(0).astype(int)
        df['Rudolph Points'] = pd.to_numeric(df['Rudolph Points'], errors='coerce').fillna(0).astype(int)
        # Write file
        excel_dir = PROJECT_ROOT / 'output' / f'Swimming Ranking {YEAR}'
        excel_dir.mkdir(parents=True, exist_ok=True)
        excel_path = excel_dir / 'Swimmers_Data.xlsx'
        df.to_excel(str(excel_path), index=False)
        return send_file(str(excel_path), as_attachment=True, download_name='Swimmers_Data.xlsx')
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/healthz")
def healthz():
    return {"ok": True}, 200

# ---------- Startup ----------
with app.app_context():
    db.create_all()

# ---------- Helpers ----------
def calculate_fina_points(base_time, swimmer_time):
    try:
        total_swimmer_time = float(swimmer_time)
    except Exception:
        total_swimmer_time = time_to_seconds(swimmer_time)
    if base_time and total_swimmer_time > 0:
        return round(1000 * (base_time / total_swimmer_time) ** 3, 2)
    return 0

def normalize_event_name(event: str) -> str:
    return (event or "").strip().title()

def normalize_gender(gender: str) -> str:
    if not gender:
        return ""
    g = gender.strip().upper()
    if g in {"M", "MALE"}:
        return "M"
    if g in {"F", "FEMALE", "Ж"}:
        return "F"
    return ""

# ---------- FINA base times ----------
_BASE_TIMES = None

def _load_base_times():
    global _BASE_TIMES
    if _BASE_TIMES is None:
        json_path = BASE_DIR / "base_times.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as fh:
                _BASE_TIMES = json.load(fh)
        else:
            _BASE_TIMES = {}

def get_base_time(event_name: str, gender: str, pool_length: int):
    _load_base_times()
    if not _BASE_TIMES:
        return None
    key_pool = "scm" if pool_length == 25 else "lcm"
    key_gender = "male" if gender == "M" else "female"
    table_key = f"fina_base_times_{key_pool}_{key_gender}"
    table = _BASE_TIMES.get(table_key, {})
    # The JSON includes both "50M Freestyle" and "50 Freestyle"; try both cases
    return table.get(event_name) or table.get(event_name.replace("M ", " "))

def assign_rudolph_points_to_swimmers():
    csv_path = DATA_DIR / f"rudolph_points_{YEAR}.csv"
    if not csv_path.exists():
        app.logger.warning(f"rudolph_points_{YEAR}.csv not found; skipping")
        return
    rudolph_points_df = pd.read_csv(csv_path)
    for swimmer in Swimmers.query.all():
        try:
            age = swimmer.date_of_competition.year - swimmer.year_of_birth
            if age > 18:
                age = 19
            parts = (swimmer.event or "").split()
            if len(parts) < 2:
                continue
            distance = parts[0].lower()
            stroke = parts[1].title()
            filtered = rudolph_points_df.loc[(rudolph_points_df["age"]==age) & (rudolph_points_df["gender"]==swimmer.gender)]
            res = 0
            for _, point_data in filtered.iterrows():
                try:
                    results_dict = ast.literal_eval(point_data["events"])
                except Exception:
                    continue
                bucket = results_dict[0] if results_dict else {}
                if stroke not in bucket:
                    continue
                for result in bucket[stroke]:
                    if f"{result.get('distance')}m" == distance:
                        try:
                            swimmer_seconds = float(swimmer.result)
                        except Exception:
                            swimmer_seconds = time_to_seconds(swimmer.result)
                        threshold_seconds = time_to_seconds(result.get("time", "0"))
                        # Faster times (lower seconds) should meet or beat the threshold
                        if threshold_seconds and swimmer_seconds >= threshold_seconds:
                            res = int(point_data["point"])
                            break
            swimmer.rudolph_points = res
        except Exception:
            continue
    db.session.commit()

# In-memory Rudolph points for faster per-insert lookup
_RUDOLPH_POINTS_DF = None

def _load_rudolph_points_df():
    global _RUDOLPH_POINTS_DF
    if _RUDOLPH_POINTS_DF is None:
        csv_path = DATA_DIR / f"rudolph_points_{YEAR}.csv"
        if csv_path.exists():
            _RUDOLPH_POINTS_DF = pd.read_csv(csv_path)
        else:
            _RUDOLPH_POINTS_DF = None

def calculate_rudolph_points(event_name: str, gender: str, age: int, swimmer_seconds: float) -> int:
    _load_rudolph_points_df()
    if _RUDOLPH_POINTS_DF is None:
        return 0
    if age > 18:
        age = 19
    parts = (event_name or "").split()
    if len(parts) < 2:
        return 0
    distance = parts[0].lower()  # e.g., "50m"
    stroke = parts[1].title()
    filtered = _RUDOLPH_POINTS_DF.loc[( _RUDOLPH_POINTS_DF["age"] == age) & (_RUDOLPH_POINTS_DF["gender"] == gender)]
    best = 0
    for _, point_data in filtered.iterrows():
        try:
            results_dict = ast.literal_eval(point_data["events"])  # TODO: switch to JSON if possible
        except Exception:
            continue
        bucket = results_dict[0] if results_dict else {}
        if stroke not in bucket:
            continue
        for result in bucket[stroke]:
            if f"{result.get('distance')}m" == distance:
                threshold_seconds = time_to_seconds(result.get("time", "0"))
                if threshold_seconds and swimmer_seconds <= threshold_seconds:
                    best = max(best, int(point_data["point"]))
    return best

# ---------- Run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
