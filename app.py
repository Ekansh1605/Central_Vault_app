import os
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import smtplib
from email.mime.text import MIMEText

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = "secret_key"
UPLOAD_FOLDER = "uploaded_files"
NOTES_FILE = "notes.txt"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

notes = []

# Scheduler for reminders
scheduler = BackgroundScheduler()
scheduler.start()

def load_notes():
    """Load notes from a file if it exists."""
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r") as f:
            for line in f:
                note, alarm_time, filename, email = line.strip().split('|')
                notes.append({
                    'text': note,
                    'alarm_time': alarm_time if alarm_time != 'None' else None,
                    'filename': filename if filename != 'None' else None,
                    'email': email if email != 'None' else None
                })

def save_notes():
    """Save notes to a file."""
    with open(NOTES_FILE, "w") as f:
        for note in notes:
            f.write(f"{note['text']}|{note['alarm_time']}|{note['filename']}|{note['email']}\n")

def send_email(subject, body, to_email):
    """Send an email using SMTP"""
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = "eka********"  # Replace with your email
        msg['To'] = to_email

        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login("ekansh*******", "*******")  # Replace with your email and app password
            server.sendmail(msg['From'], [msg['To']], msg.as_string())

        logging.info(f"Email sent to {to_email}")
    except smtplib.SMTPAuthenticationError:
        logging.error("SMTP Authentication Error. Please check your email and app password.")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

def add_reminder(note, alarm_time, email):
    """Schedule a reminder."""
    def reminder():
        logging.info(f"Reminder triggered: {note}")
        
        # Send an email reminder
        send_email("Reminder", f"Reminder: {note}", email)

    scheduler.add_job(reminder, "date", run_date=alarm_time)

@app.route("/")
def home():
    return render_template("index.html", notes=notes)

@app.route("/add_note", methods=["POST"])
def add_note():
    note_text = request.form.get("note")
    alarm_time = request.form.get("alarm_time")
    email = request.form.get("email")  # Updated to use email instead of phone_number
    file = request.files.get("file")

    filename = None
    if file and file.filename:
        filename = file.filename
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

    if note_text:
        alarm_time_obj = None
        if alarm_time:
            alarm_time_obj = datetime.fromisoformat(alarm_time)
            add_reminder(note_text, alarm_time_obj, email)
        notes.append({"text": note_text, "alarm_time": alarm_time, "filename": filename, "email": email})
        save_notes()
        flash("Note added successfully")
    return redirect(url_for("home"))

@app.route("/delete_note/<int:note_index>")
def delete_note(note_index):
    if 0 <= note_index < len(notes):
        note_to_delete = notes.pop(note_index)
        save_notes()
        flash("Note deleted successfully")
        
        # Delete the associated file if it exists
        if note_to_delete.get("filename"):
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], note_to_delete["filename"])
            if os.path.exists(file_path):
                os.remove(file_path)
                flash("Associated file deleted successfully")
    else:
        flash("Invalid note index")
    return redirect(url_for("home"))

if __name__ == "__main__":
    load_notes()
    try:
        app.run(debug=True, use_reloader=False)
    except SystemExit:
        pass
