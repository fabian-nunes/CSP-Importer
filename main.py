import json
import os
import re
import sqlite3

import pytesseract
from bson import json_util
from flask import Flask, request

#pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

app = Flask(__name__)

def process_image(image):
    # text dictionary
    text_lan = ["Peso", "IMC", "% Gordura", "Gordura subcutanea", "Agua do corpo", "Musculo esquelético",
                "Massa Muscular", "massa Ossea", "% Proteina", "TMB", "Idade do Corpo"]
    text_db = ["weight", "bmi", "fat", "subcutaneous_fat", "body_water", "skeletal_muscle", "muscle_mass", "bone_mass",
               "protein", "bmr", "body_age"]
    # Save the image to a temporary location
    image_path = 'temp_image.jpg'
    image.save(image_path)

    # Extract text from the image using OCR
    extracted_text = pytesseract.image_to_string(image_path)

    values = {}
    bone_mass = 0
    for line in extracted_text.split("\n"):
        # check if line contains date
        with sqlite3.connect('database.db') as sqlite_conn:
            sqlite_cursor = sqlite_conn.cursor()
            if re.search(r"\d{2}/\d{2}/\d{4}", line):
                values["Date"] = line
                # check date in database
                date = line.split()[1]
                sqlite_cursor.execute("SELECT * FROM scale WHERE date = ?", (date,))
                if sqlite_cursor.fetchone():
                    return "Date already exists", 400
            for label in text_lan:
                if label in line:
                    value = re.search(r"\d+(\.\d+)?", line)
                    if value:
                        if text_db[text_lan.index(label)] == "bone_mass":
                            bone_mass = float(value.group())
                        values[text_db[text_lan.index(label)]] = float(value.group())

    # Insert the values into the database
    sqlite_cursor.execute("INSERT INTO scale (date, weight, bmi, fat, subcutaneous_fat, body_water, skeletal_muscle, "
                          "muscle_mass, bone_mass, protein, bmr, body_age) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                          "?)", (date, values["weight"], values["bmi"], values["fat"], values["subcutaneous_fat"],
                                 values["body_water"], values["skeletal_muscle"], values["muscle_mass"],
                                 bone_mass, values["protein"], values["bmr"], values["body_age"]))
    sqlite_conn.commit()
    # Remove the temporary image
    os.remove(image_path)
    return values


@app.route("/scale", methods=["GET", "POST"])
def scale():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No image file in the request', 400

        # Process the image
        values = process_image(request.files['image'])
        # Return success response
        return json.loads(json_util.dumps(values)), 200
    else:
        # Get the values from the database
        values = collection.find()
        # Return the values as JSON
        return json.loads(json_util.dumps(values)), 200

@app.route("/create", methods=["GET"])
def create():
    #Create table
    with sqlite3.connect('database.db') as sqlite_conn:
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS scale
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date text, weight real, bmi real, fat real, subcutaneous_fat real, body_water real, skeletal_muscle real, muscle_mass real, bone_mass real, protein real, bmr real, body_age real)''')
        sqlite_conn.commit()
        return "Table created successfully", 200

if __name__ == "__main__":
    app.run(debug=True)
