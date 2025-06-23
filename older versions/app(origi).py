from flask import Flask, request, render_template_string, redirect, url_for
import requests
import json
from datetime import datetime
import os

app = Flask(__name__)

ACCESS_TOKEN = "9038fa7fd36c30e2bb1c550607d3cad97fbb3ae9fc2f10e6bd446e49aa1e"
CONFESSIONS_FILE = "confessions.json"

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Anonymous Confession</title>
</head>
<body style="font-family:sans-serif;text-align:center;margin-top:50px">
    <h2>Submit Your Anonymous Confession</h2>
    <form method="POST">
        <textarea name="confession" rows="8" cols="60" placeholder="Write your confession here..." required></textarea><br><br>
        <button type="submit">Submit</button>
    </form>
    {% if link %}
    <p>Your confession is live: <a href="{{ link }}" target="_blank">{{ link }}</a></p>
    {% endif %}
    <p><a href="{{ url_for('recent') }}">View Recent Confessions</a></p>
</body>
</html>
"""

HTML_RECENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Recent Confessions</title>
</head>
<body style="font-family:sans-serif;text-align:center;margin-top:50px">
    <h2>Recent Anonymous Confessions</h2>
    {% if confessions %}
        <ul style="list-style:none;padding:0;">
        {% for c in confessions %}
            <li style="margin-bottom:20px;">
                <a href="{{ c['url'] }}" target="_blank">{{ c['title'] }} ({{ c['timestamp'] }})</a><br>
                <em>{{ c['preview'] }}</em>
            </li>
        {% endfor %}
        </ul>
    {% else %}
        <p>No confessions yet.</p>
    {% endif %}
    <p><a href="{{ url_for('confess') }}">Back to Submit</a></p>
</body>
</html>
"""

def load_confessions():
    if not os.path.exists(CONFESSIONS_FILE):
        return []
    with open(CONFESSIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_confessions(confessions):
    with open(CONFESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(confessions, f, ensure_ascii=False, indent=2)

@app.route("/", methods=["GET", "POST"])
def confess():
    if request.method == "POST":
        text = request.form["confession"]
        title = "Anonymous Confession"
        content = [{"tag": "p", "children": [str(text)]}]

        response = requests.post("https://api.telegra.ph/createPage", data={
            "access_token": ACCESS_TOKEN,
            "title": title,
            "content": json.dumps(content),
            "return_content": True
        })

        print("Telegraph response:", response.text)

        if response.ok and response.json().get("ok"):
            page_url = response.json()["result"]["url"]

            # Save confession details
            confessions = load_confessions()
            confessions.insert(0, {  # newest first
                "url": page_url,
                "title": title,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "preview": text[:100] + ("..." if len(text) > 100 else "")
            })
            save_confessions(confessions)

            return render_template_string(HTML_FORM, link=page_url)
        else:
            return f"Failed to publish. Telegraph says: {response.text}", 500

    return render_template_string(HTML_FORM, link=None)

@app.route("/recent")
def recent():
    confessions = load_confessions()
    return render_template_string(HTML_RECENT, confessions=confessions)

if __name__ == "__main__":
    app.run(debug=True)
