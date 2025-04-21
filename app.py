from flask import Flask, request, jsonify
from flask_cors import CORS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")
    company = data.get("company")

    print("DATA RECEIVED:", name, email, message, company)

    # Honeypot check
    if company:
        print("\ud83d\uded1 Bot submission blocked.")
        return jsonify({"status": "error", "message": "Bot detected."}), 400

    if not all([name, email, message]):
        return jsonify({"status": "error", "message": "All fields are required."}), 400

    email_pattern = r"[^@]+@[^@]+\.[^@]+"
    if not re.match(email_pattern, email):
        return jsonify({"status": "error", "message": "Invalid email format."}), 400

    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))

        # Email to owner
        message_to_owner = Mail(
            from_email=os.environ.get("VEL_SENDGRID_FROM"),
            to_emails=os.environ.get("VEL_SENDGRID_TO"),
            subject=f"New Velocis Inquiry from {name}",
            plain_text_content=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
        )

        # Email to client
        message_to_client = Mail(
            from_email=os.environ.get("VEL_SENDGRID_FROM"),
            to_emails=email,
            subject="Thanks for reaching out to Velocis!",
            plain_text_content=f"Hi {name},\n\nThanks for contacting Velocis! We've received your message and will be in touch very soon.\n\n– The Velocis Team",
        )

        sg.send(message_to_owner)
        sg.send(message_to_client)

        return jsonify({"status": "success", "message": "Thanks! We'll be in touch soon."})

    except Exception as e:
        print("SendGrid error:", str(e))
        return jsonify({"status": "error", "message": "Submission failed. Try again later."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
