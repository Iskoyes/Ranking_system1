from PyPDF2 import PdfReader
import re
import pandas as pd
from pathlib import Path

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
    
if __name__ == "__main__":
    # YEAR OF THE RUDOLPH PDF
    year = 2025
    ##############################################################
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DOCS_DIR = PROJECT_ROOT / "docs"
    data = pd.DataFrame(extract_rudolph_points_from_pdf(DOCS_DIR / f'rudolph-{year}.pdf'))
    csv_path = f'data/rudolph_points_{year}.csv'
    data.to_csv(csv_path, index=False)