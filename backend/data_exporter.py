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
