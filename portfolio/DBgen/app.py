from flask import Flask, render_template, request, send_file
import csv
import random
import os
from io import StringIO, BytesIO
from faker import Faker
import google.generativeai as genai
import json

app = Flask(__name__, template_folder="templates", static_folder="static")
fake = Faker()

# Configure Gemini Flash
genai.configure(api_key='AIzaSyBsGOw8urROMGEISaAYV8_omMk-a5JoQ3o')  # Replace with your key
model = genai.GenerativeModel('gemini-2.0-flash')


def generate_column_names(topic, n_columns):
    prompt = f"Give me {n_columns} unique column names for a dataset about '{topic}', in comma-separated format. Just output names, no explanation."
    response = model.generate_content(prompt)
    raw_output = response.text.strip()
    return [name.strip() for name in raw_output.split(",")]


def get_column_metadata_from_gemini(column_name):
    prompt = (
        f"You are a helpful data model generator.\n"
        f"Return a SINGLE valid JSON object ONLY (no explanation) describing how to generate data for column '{column_name}'.\n"
        f"Use this format ONLY:\n"
        f'{{"type": "int", "range": [min, max]}} OR\n'
        f'{{"type": "float", "range": [min, max]}} OR\n'
        f'{{"type": "str", "values": ["val1", "val2", "val3"]}} OR\n'
        f'{{"type": "date"}} OR\n'
        f'{{"type": "bool"}}\n'
        f"No comments or formatting. Output just the JSON object."
    )

    response = model.generate_content(prompt)

    try:
        text = response.text.strip()
        if "```" in text:
            text = text.split("```")[-1].strip()
        return json.loads(text)
    except Exception as e:
        print(f"[Gemini Parse Error] for column '{column_name}': {e}")
        return {"type": "str", "values": ["Unknown"]}


def generate_value_from_metadata(metadata):
    dtype = metadata.get("type", "str")

    if dtype == "int":
        r = metadata.get("range", [0, 100])
        return random.randint(r[0], r[1])
    elif dtype == "float":
        r = metadata.get("range", [0.0, 1.0])
        return round(random.uniform(r[0], r[1]), 3)
    elif dtype == "str":
        values = metadata.get("values", [])
        return random.choice(values) if values else fake.word()
    elif dtype == "date":
        return fake.date()
    elif dtype == "bool":
        return random.choice([True, False])
    else:
        return fake.word()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        topic = request.form.get("topic")
        n_columns = int(request.form.get("n_columns", 5))
        n_rows = int(request.form.get("n_rows", 100))
        user_column_names = request.form.get("column_names", "").strip()
        include_custom = request.form.get("include_custom") == "on"

        user_columns = []
        if user_column_names:
            user_columns = [name.strip() for name in user_column_names.split(",")]

        if include_custom:
            n_to_generate = max(n_columns - len(user_columns), 0)
            generated_columns = generate_column_names(topic, n_to_generate)
            column_names = user_columns + generated_columns
        else:
            column_names = user_columns if user_columns else generate_column_names(topic, n_columns)

        column_metadata = {col: get_column_metadata_from_gemini(col) for col in column_names}

        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(column_names)

        for _ in range(n_rows):
            row = [generate_value_from_metadata(column_metadata[col]) for col in column_names]
            writer.writerow(row)

        csv_bytes = BytesIO()
        csv_bytes.write(csv_buffer.getvalue().encode('utf-8'))
        csv_bytes.seek(0)

        return send_file(
            csv_bytes,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"{topic}_dataset.csv"
        )

    return render_template("index.html")


#if __name__ == "__main__":
 #   app.run(debug=True)
