from flask import Flask, request, jsonify
from flask_cors import CORS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from email.message import EmailMessage
import os
import re
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
CORS(app)

# Environment variables for security
EMAIL_ADDRESS = os.environ.get("VELOCIS_EMAIL")
EMAIL_PASSWORD = os.environ.get("VELOCIS_PASSWORD")
RECEIVE_TO = os.environ.get("VELOCIS_RECEIVER") or EMAIL_ADDRESS

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")
    email_pattern = r"[^@]+@[^@]+\\.[^@]+"
    company = data.get("company")

    # Honeypot check
    if company:
        print("🛑 Bot submission blocked.")
        return jsonify({"status": "error", "message": "Bot detected."}), 400

    if not all([name, email, message]):
        return jsonify({"status": "error", "message": "All fields are required."}), 400
    if not re.match(email_pattern, email):
        return jsonify({"status": "error", "message": "Invalid email format."}), 400


    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))

        # Email to owner
        message_to_owner = Mail(
            from_email=os.environ.get("VEL_SENDGRID_FROM"),
            to_emails=os.environ.get("VEL_SENDGRID_TO"),
            subject=f"New Velocis Inquiry from {name}",
            plain_text_content=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        )

        # Email to client
        message_to_client = Mail(
            from_email=os.environ.get("VEL_SENDGRID_FROM"),
            to_emails=email,
            subject="Thanks for reaching out to Velocis!",
            plain_text_content=f"Hi {name},\n\nThanks for contacting Velocis! We've received your message and will be in touch very soon.\n\n– The Velocis Team"
        )

        sg.send(message_to_owner)
        sg.send(message_to_client)

        return jsonify({"status": "success", "message": "Thanks! We'll be in touch soon."})

    except Exception as e:
        print("SendGrid error:", str(e))
        return jsonify({"status": "error", "message": "Submission failed. Try again later."}), 500

if __name__ == "__main__":
    app.run(debug=True)