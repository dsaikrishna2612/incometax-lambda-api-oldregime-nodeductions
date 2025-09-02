import json
import boto3

# Create SNS client
sns_client = boto3.client("sns")

def send_sms(mobile, message):
    """Send SMS using Amazon SNS"""
    response = sns_client.publish(
        PhoneNumber=mobile,   # must be in +91xxxxxxxxxx (E.164 format)
        Message=message
    )
    return response

def lambda_handler(event, context):
    path = event.get("rawPath", "/")
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    # ✅ Frontend Route
    if path == "/" and method == "GET":
        html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Income Tax Calculator</title>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    body{font-family:Arial,sans-serif;background:#f6f8fa;padding:24px}
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
      <label>Mobile Number (e.g. +919876543210)</label><input id="mobile" required />
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

    # ✅ Backend Route
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

            # ✅ Send SMS
            message = f"Hello {name}, your calculated tax is ₹{tax}. - TaxApp"
            send_sms(mobile, message)

            response = {
                "message": f"Hello {name}, your calculated tax is ₹{tax}. SMS sent to {mobile}",
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
