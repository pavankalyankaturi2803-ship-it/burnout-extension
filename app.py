print("App Started")
from flask import Flask, render_template, request
import pandas as pd
import os
import smtplib
from datetime import date
from sklearn.linear_model import LogisticRegression
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import screen_tracker
from fatigue_camera import detect_fatigue
import activity_monitor

app = Flask(__name__)
threading.Thread(target=screen_tracker.start_tracking, daemon=True).start()

# ---------- LOAD & TRAIN MODEL ----------
df = pd.read_csv("training_data.csv")

X = df[["WorkingHours", "SleepHours"]]
y = df["Burnout"]

model = LogisticRegression()
model.fit(X, y)
site_usage = {}

def check_overuse(site, time):

    if site not in site_usage:
        site_usage[site] = 0

    site_usage[site] += time

    if site == "youtube.com" and site_usage[site] > 3600:
        return "YouTube overuse detected"

    if site == "instagram.com" and site_usage[site] > 1800:
        return "Instagram limit exceeded"

    return None

# ---------- FUNCTIONS ----------

def predict_burnout(work, sleep):

    person = pd.DataFrame([[work, sleep]], columns=X.columns)

    return round(model.predict_proba(person)[0][1] * 100, 2)
def get_stress_and_suggestions(work, sleep):

    if work >= 10 and sleep <= 5:

        return "High", [
            "Reduce working hours",
            "Sleep at least 7 hours",
            "Avoid overtime",
            "Take mental breaks"
        ]

    elif work >= 8:

        return "Medium", [
            "Maintain work-life balance",
            "Avoid late nights"
        ]

    else:

        return "Low", [
            "You are following a healthy routine"
        ]


def update_history_and_get_trend(current_risk):

    os.makedirs("data", exist_ok=True)

    history_file = "data/burnout_history.xlsx"

    if os.path.exists(history_file):

        old = pd.read_excel(history_file)

        previous_risk = old.iloc[-1]["BurnoutRisk"]

        if current_risk > previous_risk:

            trend = "Burnout Increased ⬆️"

        elif current_risk < previous_risk:

            trend = "Burnout Decreased ⬇️"

        else:

            trend = "No Change"

        new_entry = pd.DataFrame(
            [[date.today(), current_risk, trend]],
            columns=["Date", "BurnoutRisk", "Trend"]
        )

        updated = pd.concat([old, new_entry], ignore_index=True)

    else:

        trend = "Initial Measurement"

        updated = pd.DataFrame(
            [[date.today(), current_risk, trend]],
            columns=["Date", "BurnoutRisk", "Trend"]
        )

    updated.to_excel(history_file, index=False)

    return trend


# ---------- EMAIL FUNCTIONS ----------

def send_email(receiver, stress, risk, trend, suggestions):

    sender_email = "pavankalyankaturi3@gmail.com"
    app_password = "fsrw umkt dsqb fcuc"

    msg = MIMEMultipart()

    msg["From"] = sender_email
    msg["To"] = receiver
    msg["Subject"] = "Burnout Report"

    text = f"""
Stress Level: {stress}
Burnout Risk: {risk}%
Trend: {trend}

Suggestions:
- """ + "\n- ".join(suggestions)

    msg.attach(MIMEText(text, "plain"))

    try:

        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.starttls()

        server.login(sender_email, app_password)

        server.sendmail(sender_email, receiver, msg.as_string())

        server.quit()

        return True

    except Exception as e:

        print(e)

        return False


def send_mail(receiver, fatigue):

    sender = "pavankalyankaturi3@gmail.com"
    password = "fsrw umkt dsqb fcuc"

    if fatigue:
        message = """Subject: Fatigue Alert

Fatigue detected!

Recommendations:
- Take a 10 minute break
- Drink water
- Rest your eyes
- Avoid continuous screen usage
"""

    else:
        message = """Subject: Fatigue Scan Result

Good news!

No fatigue detected.
Keep maintaining a healthy routine.
"""

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, receiver, message)
    server.quit()
def final_risk_level(risk, fatigue, screen_time):

    if risk > 70 or fatigue or screen_time > 6:
        return "HIGH RISK"

    elif risk > 40 or screen_time > 4:
        return "MEDIUM RISK"

    else:
        return "LOW RISK"


# ---------- ROUTES ----------
@app.route('/', methods=['GET', 'POST'])

def home():

    return render_template("index.html")

from flask import jsonify

screen_data = []

@app.route("/screen-data", methods=["POST"])
def screen_data_api():

    data = request.get_json()

    site = data["site"]
    time_spent = data["time"]

    screen_data.append({
        "site": site,
        "time": time_spent
    })

    print("Received:", site, time_spent)

    # CHECK OVERUSE
    warning = check_overuse(site, time_spent)

    if warning:
        print("⚠", warning)

    return {"status": "ok"}
def check_overuse(site, time):

    if site == "youtube.com" and time > 3600:
        return "YouTube overuse detected"

    if site == "instagram.com" and time > 1800:
        return "Instagram limit exceeded"

    return None
from flask import jsonify

blocked_sites = {
    "youtube.com": 20,
    "instagram.com": 15
}

@app.route("/blocked")
def blocked():
    return jsonify(blocked_sites)
@app.route("/analyze", methods=["POST"])
def analyze():

    email = request.form["email"]
    work = int(request.form["work"])
    sleep = int(request.form["sleep"])

    risk = predict_burnout(work, sleep)

    stress, suggestions = get_stress_and_suggestions(work, sleep)

    trend = update_history_and_get_trend(risk)

    screen_time = screen_tracker.get_screen_time()

    fatigue = False

    status = final_risk_level(risk, fatigue, screen_time)

    send_email(email, stress, risk, trend, suggestions)

    return render_template(
        "result.html",
        stress=stress,
        risk=risk,
        trend=trend,
        suggestions=suggestions,
        status=status,
        screen_time=screen_time
    )
@app.route("/scan", methods=["POST"])
def scan():

    user_email = request.form["email"]

    print("Scan started for", user_email)

    fatigue = detect_fatigue()

    send_mail(user_email, fatigue)

    if fatigue:
        return "Fatigue detected. Email sent."

    return "No fatigue detected. Email sent."
@app.route("/detect", methods=["POST"])
def detect():

    file = request.files["image"]

    import numpy as np
    import cv2

    img = cv2.imdecode(
        np.frombuffer(file.read(), np.uint8),
        cv2.IMREAD_COLOR
    )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    eyes = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_eye.xml"
    )

    faces = face.detectMultiScale(gray,1.3,5)

    fatigue = False

    for (x,y,w,h) in faces:

        roi = gray[y:y+h, x:x+w]

        eye_detect = eyes.detectMultiScale(roi)

        if len(eye_detect) == 0:
            fatigue = True

    if fatigue:
        return "Fatigue detected! Please take a break."

    return "No fatigue detected"
activity_monitor.start_monitor()
idle = activity_monitor.get_idle_time()
if idle > 300:
    print("User inactive")
# ---------- MAIN ----------

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    app.run(debug=True)
