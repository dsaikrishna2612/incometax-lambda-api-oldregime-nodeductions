import json
import boto3
import base64
from io import BytesIO
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

ses_client = boto3.client("ses")

def generate_pdf(name, age, email, mobile, income, tax):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica", 12)
    p.drawString(100, 750, "Income Tax Report")
    p.drawString(100, 720, f"Name: {name}")
    p.drawString(100, 700, f"Age: {age}")
    p.drawString(100, 680, f"Email: {email}")
    p.drawString(100, 660, f"Mobile: {mobile}")
    p.drawString(100, 640, f"Annual Income: ₹{income}")
    p.drawString(100, 620, f"Calculated Tax: ₹{tax}")
    p.save()
    buffer.seek(0)
    return buffer.read()

def send_email_with_pdf(to_email, pdf_bytes, filename="TaxReport.pdf"):
    sender = "azure2612sai@gmail.com"  # Replace with your SES verified email
    subject = "Your Income Tax Calculation Report"
    body_text = "Hello,\n\nPlease find attached your tax calculation report.\n\nRegards,\nTax App"

    # Build MIME message
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    # Add text part
    msg.attach(MIMEText(body_text, "plain"))

    # Attach PDF
    part = MIMEApplication(pdf_bytes)
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)

    # Send via SES
    response = ses_client.send_raw_email(
        Source=sender,
        Destinations=[to_email],
        RawMessage={"Data": msg.as_string()}
    )
    return response

def lambda_handler(event, context):
    path = event.get("rawPath", "/")
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    # Frontend Route (same as before)...
    if path == "/" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": "<h2>Frontend Form Here...</h2>"  # Keep your previous HTML
        }

    # Backend Route
    elif path == "/calculate" and method == "POST":
        body = json.loads(event["body"])
        name = body.get("name")
        age = int(body.get("age", 0))
        email = body.get("email")
        mobile = body.get("mobile")
        income = float(body.get("income", 0))

        # Tax Calculation
        tax = 0
        if income <= 250000:
            tax = 0
        elif income <= 500000:
            tax = (income - 250000) * 0.05
        elif income <= 1000000:
            tax = (250000 * 0.05) + (income - 500000) * 0.20
        else:
            tax = (250000 * 0.05) + (500000 * 0.20) + (income - 1000000) * 0.30

        # Generate PDF
        pdf_bytes = generate_pdf(name, age, email, mobile, income, round(tax, 2))

        # Send Email
        send_email_with_pdf(email, pdf_bytes)

        response = {
            "message": f"Hello {name}, your calculated tax is ₹{round(tax, 2)}. Report sent to {email}"
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response)
        }

    else:
        return {"statusCode": 404, "body": json.dumps({"error": "Route not found"})}
