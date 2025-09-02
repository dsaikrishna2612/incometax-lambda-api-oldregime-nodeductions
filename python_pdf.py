import json
import boto3
from io import BytesIO
from fpdf import FPDF
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

ses_client = boto3.client("ses")

# ✅ Generate PDF using fpdf2
def generate_pdf(name, age, email, mobile, income, tax):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Income Tax Report", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Name: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Age: {age}", ln=True)
    pdf.cell(200, 10, txt=f"Email: {email}", ln=True)
    pdf.cell(200, 10, txt=f"Mobile: {mobile}", ln=True)
    pdf.cell(200, 10, txt=f"Annual Income: ₹{income}", ln=True)
    pdf.cell(200, 10, txt=f"Calculated Tax: ₹{tax}", ln=True)

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

# ✅ Send email with SES
def send_email_with_pdf(to_email, pdf_bytes, filename="TaxReport.pdf"):
    sender = "azure2612sai@gmail.com"  # Must be verified in SES
    subject = "Your Income Tax Calculation Report"
    body_text = "Hello,\n\nPlease find attached your tax calculation report.\n\nRegards,\nTax App"

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    msg.attach(MIMEText(body_text, "plain"))

    part = MIMEApplication(pdf_bytes)
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)

    response = ses_client.send_raw_email(
        Source=sender,
        Destinations=[to_email],
        RawMessage={"Data": msg.as_string()}
    )
    return response

def lambda_handler(event, context):
    path = event.get("rawPath", "/")
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    # ✅ Frontend Route (serve HTML form)
    if path == "/" and method == "GET":
        html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Income Tax Calculator</title>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    body{font-family:Inter,Arial,sans-serif;background:#f6f8fa;padding:24px}
    .card{max-width:600px;margin:40px auto;background:#fff;padding:20px;border-radius:10px;box-shadow:0 6px 18px rgba(10,10,10,0.06)}
    input,button{width:100%;padding:10px;margin:8px 0;border-radius:6px;border:1px solid #dfe3e8}
    button{background:#2563eb;color:#fff;border:none;cursor:pointer}
    #result{margin-top:12px;padding:12px;border-radius:6px;background:#eef2ff}
    label{font-size:0.9rem;color:#333}
  </style>
</head>
<body>
  <div class="card">
    <h2>Income Tax Calculator</h2>
    <form id="taxForm">
      <label>Name</label><input id="name" required />
      <label>Age</label><input id="age" type="number" required />
      <label>Email</label><input id="email" type="email" required />
      <label>Mobile Number</label><input id="mobile" required />
      <label>Annual Income (₹)</label><input id="income" type="number" step="0.01" required />
      <button type="submit">Calculate</button>
    </form>
    <div id="result"></div>
  </div>

  <script>
    document.getElementById('taxForm').addEventListener('submit', async function(e){
      e.preventDefault();
      const payload = {
        name: document.getElementById('name').value,
        age: document.getElementById('age').value,
        email: document.getElementById('email').value,
        mobile: document.getElementById('mobile').value,
        income: document.getElementById('income').value
      };
      const resp = await fetch('/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      if (resp.ok) {
        document.getElementById('result').innerHTML = '<strong>' + data.message + '</strong><br/>Tax: ₹' + data.tax;
      } else {
        document.getElementById('result').innerText = 'Error: ' + (data.error || JSON.stringify(data));
      }
    });
  </script>
</body>
</html>"""
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": html
        }

    # ✅ Backend Route (calculate + email)
    elif path == "/calculate" and method == "POST":
        try:
            body = json.loads(event.get("body", "{}"))
            name = body.get("name")
            age = int(body.get("age", 0))
            email = body.get("email")
            mobile = body.get("mobile")
            income = float(body.get("income", 0))

            # Tax calculation
            if income <= 250000:
                tax = 0
            elif income <= 500000:
                tax = (income - 250000) * 0.05
            elif income <= 1000000:
                tax = (250000 * 0.05) + (income - 500000) * 0.20
            else:
                tax = (250000 * 0.05) + (500000 * 0.20) + (income - 1000000) * 0.30

            tax = round(tax, 2)

            # Generate PDF
            pdf_bytes = generate_pdf(name, age, email, mobile, income, tax)

            # Send Email
            send_email_with_pdf(email, pdf_bytes)

            response = {
                "message": f"Hello {name}, your calculated tax is ₹{tax}. Report sent to {email}",
                "tax": tax
            }

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(response)
            }

        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)})
            }

    else:
        return {"statusCode": 404, "body": json.dumps({"error": "Route not found"})}
