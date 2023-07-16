import json
import os
import re

import pytesseract
from bson import json_util
from flask import Flask, request
from pymongo import MongoClient

#pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

app = Flask(__name__)

# MongoDB configuration
client = MongoClient('mongodb://localhost:27017/')
db = client['cecotec']
collection = db['values']


def process_image(image):
    # text dictionary
    text_lan = ["Peso", "IMC", "% Gordura", "Gordura subcutanea", "Agua do corpo", "Musculo esquelético",
                "Massa Muscular", "massa Ossea", "% Proteina", "TMB", "Idade do Corpo"]
    # Save the image to a temporary location
    image_path = 'temp_image.jpg'
    image.save(image_path)

    # Extract text from the image using OCR
    extracted_text = pytesseract.image_to_string(image_path)

    values = {}
    for line in extracted_text.split("\n"):
        # check if line contains date
        if re.search(r"\d{2}/\d{2}/\d{4}", line):
            values["Date"] = line
            # check date in database
            date = line.split()[1]
            query = {'Date': {'$regex': date}}
            existing_record = collection.find_one(query)
            if existing_record:
                # date already exists in database
                return 'Already uploaded a scale for this date', 400
        for label in text_lan:
            if label in line:
                value = re.search(r"\d+(\.\d+)?", line)
                if value:
                    values[label] = value.group()

    # Insert the values into the database
    collection.insert_one(values)
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

if __name__ == "__main__":
    app.run(debug=True)
