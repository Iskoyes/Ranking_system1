# backend/app.py
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, re, ast
from pathlib import Path
from PyPDF2 import PdfReader
import pandas as pd
from utils import time_to_seconds
from functools import wraps
import os

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
DOCS_DIR = PROJECT_ROOT / "docs"
DATA_DIR = PROJECT_ROOT / "data"
PDF_PATH = DOCS_DIR / "rudolph.pdf"

# ---------- App ----------
app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR) if TEMPLATES_DIR.exists() else None,
    static_folder=str(STATIC_DIR) if STATIC_DIR.exists() else None
)
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# ---------- DB ----------
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data_2025.db'}")
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
    result = db.Column(db.String(100), nullable=False)
    date_of_competition = db.Column(db.Date, nullable=False)
    pool_length = db.Column(db.Integer, nullable=False)
    fina_points = db.Column(db.Integer, nullable=True)
    rudolph_points = db.Column(db.Integer, nullable=True)

# ---------- Admin credentials ----------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin2025"

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
        new_entry = Swimmers(
            full_name=data["full_name"],
            year_of_birth=int(data["year_of_birth"]),
            gender=data["gender"],
            event=data["event"],
            result=data["result"],
            date_of_competition=datetime.strptime(data["date_of_competition"], "%Y-%m-%d").date(),
            pool_length=int(data["pool_length"]),
        )
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({"message": "Data inserted successfully!"}), 201
    except Exception as e:
        return jsonify({"error": f"Bad payload: {e}"}), 400

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

def extract_rudolph_points_from_pdf(pdf_path: str):
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
        gender_raw = (match.group("gender") or "").lower()
        gender = "M" if gender_raw.startswith("männ") or gender_raw.startswith("mann") else "F"
        results = match.group("data") or ""
        lines = [ln.strip() for ln in results.split("\n") if ln.strip()]
        for line in lines:
            parts = line.split()
            if not parts:
                continue
            points = parts[0]
            if points == "50":
                continue
            freestyle    = [{"distance": d, "time": t} for d, t in zip([50,100,200,400,800,1500], parts[1:7])]
            breaststroke = [{"distance": d, "time": t} for d, t in zip([50,100,200], parts[7:10])]
            butterfly    = [{"distance": d, "time": t} for d, t in zip([50,100,200], parts[10:13])]
            backstroke   = [{"distance": d, "time": t} for d, t in zip([50,100,200], parts[13:16])]
            medley       = [{"distance": d, "time": t} for d, t in zip([200,400], parts[16:18])]
            events = [{"Freestyle": freestyle,"Breaststroke": breaststroke,"Butterfly": butterfly,"Backstroke": backstroke,"Medley": medley}]
            data.append({"age": age_group,"gender": gender,"point": points,"events": events})
    return data

def assign_rudolph_points_to_swimmers():
    csv_path = DATA_DIR / "rudolph_points.csv"
    if not csv_path.exists():
        app.logger.warning("rudolph_points.csv not found; skipping")
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
                        threshold_seconds = time_to_seconds(result.get("time","0"))
                        if threshold_seconds and swimmer_seconds >= threshold_seconds:
                            res = int(point_data["point"])
                            break
            swimmer.rudolph_points = res
        except Exception:
            continue
    db.session.commit()

# ---------- Run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
