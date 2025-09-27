from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from numpy import double
import os
import re
from PyPDF2 import PdfReader
import pandas as pd
from utils import time_to_seconds
import ast
import sqlite3
from flask import render_template


app = Flask(__name__)
CORS(app)
@app.route('/')
def home():
    return render_template('index.html')

DATABASE_URL = os.environ.get("DATABASE_URL")  # Render создаст переменную
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

fina_base_times_scm_male = {
    "50M FREESTYLE": 20.16,
    "50 FREESTYLE": 20.16,
    "100M FREESTYLE": 44.84,
    "100 FREESTYLE": 44.84,
    "200M FREESTYLE": 99.37,
    "200 FREESTYLE": 99.37,
    "400M FREESTYLE": 212.25,
    "400 FREESTYLE": 212.25,
    "800M FREESTYLE": 443.42,
    "800 FREESTYLE": 443.42,
    "1500M FREESTYLE": 846.88,
    "1500 FREESTYLE": 846.88,
    "50M BACKSTROKE": 22.11,
    "50 BACKSTROKE": 22.11,
    "100M BACKSTROKE": 48.33,
    "100 BACKSTROKE": 48.33,
    "200M BACKSTROKE": 105.63,
    "200 BACKSTROKE": 105.63,
    "50M BREASTSTROKE": 24.95,
    "50 BREASTSTROKE": 24.95,
    "100M BREASTSTROKE": 55.28,
    "100 BREASTSTROKE": 55.28,
    "200M BREASTSTROKE": 120.16,
    "200 BREASTSTROKE": 120.16,
    "50M BUTTERFLY": 21.75,
    "50 BUTTERFLY": 21.75,
    "100M BUTTERFLY": 47.78,
    "100 BUTTERFLY": 47.78,
    "200M BUTTERFLY": 106.85,
    "200 BUTTERFLY": 106.85,
    "100M MEDLEY": 49.28,
    "100 MEDLEY": 49.28,
    "200M MEDLEY": 109.63,
    "200 MEDLEY": 109.63,
    "400M MEDLEY": 234.81,
    "400 MEDLEY": 234.81
}

fina_base_times_scm_female = {
    "50M FREESTYLE": 22.93,
    "50 FREESTYLE": 22.93,
    "100M FREESTYLE": 50.25,
    "100 FREESTYLE": 50.25,
    "200M FREESTYLE": 110.31,
    "200 FREESTYLE": 110.31,
    "400M FREESTYLE": 231.30,
    "400 FREESTYLE": 231.30,
    "800M FREESTYLE": 477.42,
    "800 FREESTYLE": 477.42,
    "1500M FREESTYLE": 908.24,
    "1500 FREESTYLE": 908.24,
    "50M BACKSTROKE": 25.25,
    "50 BACKSTROKE": 25.25,
    "100M BACKSTROKE": 54.89,
    "100 BACKSTROKE": 54.89,
    "200M BACKSTROKE": 118.94,
    "200 BACKSTROKE": 118.94,
    "50M BREASTSTROKE": 28.37,
    "50 BREASTSTROKE": 28.37,
    "100M BREASTSTROKE": 62.36,
    "100 BREASTSTROKE": 62.36,
    "200M BREASTSTROKE": 134.57,
    "200 BREASTSTROKE": 134.57,
    "50M BUTTERFLY": 24.38,
    "50 BUTTERFLY": 24.38,
    "100M BUTTERFLY": 54.05,
    "100 BUTTERFLY": 54.05,
    "200M BUTTERFLY": 119.61,
    "200 BUTTERFLY": 119.61,
    "100M MEDLEY": 56.51,
    "100 MEDLEY": 56.51,
    "200M MEDLEY": 121.86,
    "200 MEDLEY": 121.86,
    "400M MEDLEY": 258.94,
    "400 MEDLEY": 258.94
}

fina_base_times_lcm_male = {
    "50M FREESTYLE": 20.91,
    "50 FREESTYLE": 20.91,
    "100M FREESTYLE": 46.86,
    "100 FREESTYLE": 46.86,
    "200M FREESTYLE": 102.00,
    "200 FREESTYLE": 102.00,
    "400M FREESTYLE": 220.07,
    "400 FREESTYLE": 220.07,
    "800M FREESTYLE": 452.12,
    "800 FREESTYLE": 452.12,
    "1500M FREESTYLE": 871.02,
    "1500 FREESTYLE": 871.02,
    "50M BACKSTROKE": 23.55,
    "50 BACKSTROKE": 23.55,
    "100M BACKSTROKE": 51.60,
    "100 BACKSTROKE": 51.60,
    "200M BACKSTROKE": 111.92,
    "200 BACKSTROKE": 111.92,
    "50M BREASTSTROKE": 25.95,
    "50 BREASTSTROKE": 25.95,
    "100M BREASTSTROKE": 56.88,
    "100 BREASTSTROKE": 56.88,
    "200M BREASTSTROKE": 125.48,
    "200 BREASTSTROKE": 125.48,
    "50M BUTTERFLY": 22.27,
    "50 BUTTERFLY": 22.27,
    "100M BUTTERFLY": 49.45,
    "100 BUTTERFLY": 49.45,
    "200M BUTTERFLY": 110.34,
    "200 BUTTERFLY": 110.34,
    "200M MEDLEY": 114.00,
    "200 MEDLEY": 114.00,
    "400M MEDLEY": 242.50,
    "400 MEDLEY": 242.50
}

fina_base_times_lcm_female = {
    "50M FREESTYLE": 23.61,
    "50 FREESTYLE": 23.61,
    "100M FREESTYLE": 51.71,
    "100 FREESTYLE": 51.71,
    "200M FREESTYLE": 112.85,
    "200 FREESTYLE": 112.85,
    "400M FREESTYLE": 235.38,
    "400 FREESTYLE": 235.38,
    "800M FREESTYLE": 484.79,
    "800 FREESTYLE": 484.79,
    "1500M FREESTYLE": 920.48,
    "1500 FREESTYLE": 920.48,
    "50M BACKSTROKE": 26.86,
    "50 BACKSTROKE": 26.86,
    "100M BACKSTROKE": 57.33,
    "100 BACKSTROKE": 57.33,
    "200M BACKSTROKE": 123.14,
    "200 BACKSTROKE": 123.14,
    "50M BREASTSTROKE": 29.16,
    "50 BREASTSTROKE": 29.16,
    "100M BREASTSTROKE": 64.13,
    "100 BREASTSTROKE": 64.13,
    "200M BREASTSTROKE": 137.55,
    "200 BREASTSTROKE": 137.55,
    "50M BUTTERFLY": 24.43,
    "50 BUTTERFLY": 24.43,
    "100M BUTTERFLY": 55.48,
    "100 BUTTERFLY": 55.48,
    "200M BUTTERFLY": 121.81,
    "200 BUTTERFLY": 121.81,
    "200M MEDLEY": 126.12,
    "200 MEDLEY": 126.12,
    "400M MEDLEY": 265.87,
    "400 MEDLEY": 265.87
}

def extract_rudolph_points_from_pdf(pdf_path):
    data = []

    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() for page in reader.pages)

    pattern = re.compile(
        r"Punkttabelle\s+(?P<gender>\w+),\s+Altersklasse\s+(?P<age>\d+|offen)[\s\S]+?" 
        r"Pkt[\s\S]+?(?P<data>(?:\d+\s+[\d:.,\s]+)+)", 
        re.MULTILINE
    )

    for match in pattern.finditer(text):
        age_group = match.group("age")
        if age_group == 'offen':
            age_group = '19'
        elif(int(age_group) > 18):
            age_group = age_group[:-1]
        gender = match.group("gender")
        if gender == "männlich":
            gender = "M"
        else:
            gender = "F"
        results = match.group("data")


        lines = results.strip().split("\n")
        for line in lines:
            events = []
            elements = line.split()
            points = elements[0]
            
            if points == "50":
                continue

            freestyle = [{"distance": dist, "time": time} for dist, time in zip([50, 100, 200, 400, 800, 1500], elements[1:7])]
            breaststroke = [{"distance": dist, "time": time} for dist, time in zip([50, 100, 200], elements[7:10])]
            butterfly = [{"distance": dist, "time": time} for dist, time in zip([50, 100, 200], elements[10:13])]
            backstroke = [{"distance": dist, "time": time} for dist, time in zip([50, 100, 200], elements[13:16])]
            medley = [{"distance": dist, "time": time} for dist, time in zip([200, 400], elements[16:18])]

            events.append({
                "Freestyle": freestyle,
                "Breaststroke": breaststroke,
                "Butterfly": butterfly,
                "Backstroke": backstroke,
                "Medley": medley
            })

            data.append({
                "age": age_group,
                "gender": gender,
                "point": points,
                "events": events
            })

    return data

def calculate_fina_points(base_time, swimmer_time):
    total_swimmer_time = double(swimmer_time)  


    if base_time and total_swimmer_time > 0:
        return round(1000 * (base_time / total_swimmer_time) ** 3, 2)
    return 0

def normalize_event_name(event):
    return event.strip().upper()  
    
def normalize_gender(gender):
    if not gender:  
        return ''
    gender = gender.strip().upper()
    if gender in ['M', 'MALE',]:
        return 'M'
    elif gender in ['F', 'FEMALE', 'Ж']:
        return 'F'
    return ''  


def assign_rudolph_points_to_swimmers():
    rudolph_points_df = pd.read_csv('data/rudolph_points.csv')
    
    for swimmer in Swimmers.query.all():
        year_of_competition = swimmer.date_of_competition.year
        age = year_of_competition - int(swimmer.year_of_birth)
        if age > 18:
            age = 19

        # Split event into distance + stroke
        parts = swimmer.event.split(' ')  # e.g., "50M Backstroke" -> ["50M", "Backstroke"]
        distance = parts[0]  # "50M"
        stroke = parts[1].capitalize()  # ensure "Backstroke" format

        # Filter by age and gender
        filtered = rudolph_points_df.loc[
            (rudolph_points_df['age']==age) & (rudolph_points_df['gender']==swimmer.gender)
        ]
        res = 0

        for index, point_data in filtered.iterrows():
            results_dict = ast.literal_eval(point_data['events'])
            
            # Normalize stroke name to match the dict key
            stroke_dict_key = stroke.title()  # e.g., "Backstroke", "Butterfly", etc.
            
            if stroke_dict_key not in results_dict[0]:
                continue  # skip if stroke not in dict

            for result in results_dict[0][stroke_dict_key]:
                if str(result['distance'])+'m' == distance:
                    if double(swimmer.result) >= time_to_seconds(result['time']):
                        res = point_data['point']
                        break

        swimmer.rudolph_points = res
        db.session.commit()


with app.app_context():
    db.create_all()

    data = extract_rudolph_points_from_pdf('../docs/rudolph.pdf')
    data = pd.DataFrame(data)
    csv_path = 'data/rudolph_points.csv'
    data.to_csv(csv_path, index=False)   

    swimmers = Swimmers.query.all()

    for swimmer in swimmers:
        id = swimmer.id
        gender = normalize_gender(swimmer.gender)
        event = normalize_event_name(swimmer.event)
        result = swimmer.result
        pool_length = getattr(swimmer, 'pool_length', None)  
    
        valid_genders = {'M', 'F'}
        valid_pool_lengths = {25, 50}
    
        if gender not in valid_genders:
            print(f"Swimmer ID {id}: Invalid gender '{gender}'. Skipping...")
            continue

        if pool_length not in valid_pool_lengths:
            print(f"Swimmer ID {id}: Invalid pool length '{pool_length}'. Skipping...")
            continue

        base_times_lookup = {
            ('M', 25): fina_base_times_scm_male,
            ('F', 25): fina_base_times_scm_female,
            ('M', 50): fina_base_times_lcm_male,
            ('F', 50): fina_base_times_lcm_female,
    }

        base_time = base_times_lookup.get((gender, pool_length), {}).get(event)

        if base_time is None:
            print(f"Swimmer ID {id}: Event '{event}' not found in base times for pool length {pool_length}. Skipping...")
            continue

        try:
            fina_points = calculate_fina_points(base_time, result)
            swimmer.fina_points = fina_points  
        except Exception as e:
            print(f"Swimmer ID {id}: Error calculating FINA points: {e}")
            continue

        db.session.commit()
    
    assign_rudolph_points_to_swimmers()

@app.route('/api/data', methods=['POST'])
def add_data():
    data = request.form  # <--- changed from request.json

    full_name = data['full_name']
    year_of_birth = int(data['year_of_birth'])
    gender = data['gender']
    event = data['event']
    result = data['result']
    date_of_competition = datetime.strptime(data['date_of_competition'], '%Y-%m-%d').date()
    pool_length = int(data['pool_length'])

    new_entry = Swimmers(
        full_name=full_name,
        year_of_birth=year_of_birth,
        gender=gender,
        event=event,
        result=result,
        date_of_competition=date_of_competition,
        pool_length=pool_length
    )

    db.session.add(new_entry)
    db.session.commit()

    return jsonify({'message': 'Data inserted successfully!'}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)



import pandas as pd
from app import db, Swimmers, app  # Importing the app and db instance from app.py

def seconds_to_time(result_in_seconds):
    try:
        result_in_seconds = float(result_in_seconds)
    except ValueError:
        raise ValueError(f"Invalid input for time conversion: {result_in_seconds}")
    minutes = int(result_in_seconds // 60)
    seconds = int(result_in_seconds % 60)
    milliseconds = int((result_in_seconds % 1) * 100)

    formatted_time = f"{minutes:02}:{seconds:02},{milliseconds:02}"
    return formatted_time

def export_to_excel():

    with app.app_context():

        swimmers = Swimmers.query.all()

        if not swimmers:
            print("No data found in the database.")
            return

        swimmers_data = []
        for swimmer in swimmers:
            swimmers_data.append({
                "ФИО": swimmer.full_name,
                "Год рождения": swimmer.year_of_birth,
                "Пол": swimmer.gender,
                "Дистанция": swimmer.event,
                "Время": swimmer.result,
                "Дата проведения соревнований": swimmer.date_of_competition,
                "Тип бассейна": swimmer.pool_length,
                "FINA Points": swimmer.fina_points,
                "Rudolph Points": swimmer.rudolph_points
            })

        df = pd.DataFrame(swimmers_data)
        df['Пол'] = df['Пол'].replace('F', 'Ж')
        df['Дистанция'] = df['Дистанция'].replace('50m Freestyle', '50м кроль')
        df['Дистанция'] = df['Дистанция'].replace('100m Freestyle', '100м кроль')
        df['Дистанция'] = df['Дистанция'].replace('200m Freestyle', '200м кроль')
        df['Дистанция'] = df['Дистанция'].replace('400m Freestyle', '400м кроль')
        df['Дистанция'] = df['Дистанция'].replace('800m Freestyle', '800м кроль')
        df['Дистанция'] = df['Дистанция'].replace('1500m Freestyle', '1500м кроль')
        df['Дистанция'] = df['Дистанция'].replace('50m Breaststroke', '50м брасс')
        df['Дистанция'] = df['Дистанция'].replace('100m Breaststroke', '100м брасс')
        df['Дистанция'] = df['Дистанция'].replace('200m Breaststroke', '200м брасс')
        df['Дистанция'] = df['Дистанция'].replace('50m Butterfly', '50м батт')
        df['Дистанция'] = df['Дистанция'].replace('100m Butterfly', '100м батт')
        df['Дистанция'] = df['Дистанция'].replace('200m Butterfly', '200м батт')
        df['Дистанция'] = df['Дистанция'].replace('50m Backstroke', '50м на спине')
        df['Дистанция'] = df['Дистанция'].replace('100m Backstroke', '100м на спине')
        df['Дистанция'] = df['Дистанция'].replace('200m Backstroke', '200м на спине')
        df['Дистанция'] = df['Дистанция'].replace('200m Medley', '200м комплекс')
        df['Дистанция'] = df['Дистанция'].replace('400m Medley', '400м комплекс')
        df['Время'] = df['Время'].apply(seconds_to_time)
        df['Дата проведения соревнований'] = pd.to_datetime(df['Дата проведения соревнований'], errors='coerce')
        df['Дата проведения соревнований'] = df['Дата проведения соревнований'].dt.strftime('%d/%m/%Y')
        df['FINA Points'] = df['FINA Points'].apply(int)

        excel_file = 'Swimming Ranking 2025/Swimmers_Data.xlsx'
        df.to_excel(excel_file, index=False)

        print(f"Database successfully exported to {excel_file}")

if __name__ == '__main__':

    export_to_excel()


def time_to_seconds(time_str):
    # Split the time string into minutes, seconds, and milliseconds
    minutes, rest = time_str.split(':')
    seconds, milliseconds = rest.split(',')

    # Convert minutes, seconds, and milliseconds to integers
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)

    # Calculate the total time in seconds
    total_seconds = minutes * 60 + seconds + milliseconds / 1000

    return total_seconds 