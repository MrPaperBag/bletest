from flask import Flask, request, render_template_string, redirect, url_for, send_file
import subprocess
import requests
import os

ESP_URL = "http://192.168.1.8/color"

BASE_DIR = os.getcwd()              # ← this is pwd
PHOTO_PATH = os.path.join(BASE_DIR, "PHOTO.jpg")

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ESP RGB Control</title>
<style>
body {
    font-family: Arial;
    background: #111;
    color: #0f0;
    text-align: center;
}
input[type=range] { width: 90%; }
button {
    font-size: 20px;
    padding: 10px 20px;
    margin: 10px;
}
img {
    width: 90%;
    margin-top: 15px;
    border: 2px solid #0f0;
}
</style>
</head>
<body>

<h2>RGB LED Control</h2>

<form action="/set" method="get">
R<br><input type="range" name="r" min="0" max="255" value="255"><br>
G<br><input type="range" name="g" min="0" max="255" value="0"><br>
B<br><input type="range" name="b" min="0" max="255" value="255"><br><br>

Brightness<br>
<input type="range" name="br" min="0" max="100" value="100"><br><br>

<button type="submit">SET</button>
</form>

<hr>

<form action="/photo" method="post">
<button type="submit">GET IMAGE</button>
</form>

{% if photo %}
<img src="/photo.jpg">
{% endif %}

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(
        HTML,
        photo=os.path.exists(PHOTO_PATH)
    )

@app.route("/set")
def set_color():
    r = int(request.args.get("r", 0))
    g = int(request.args.get("g", 0))
    b = int(request.args.get("b", 0))
    br = int(request.args.get("br", 100))

    hex_color = f"{r:02x}{g:02x}{b:02x}"
    url = f"{ESP_URL}?c=%23{hex_color}&b={br}"

    try:
        requests.get(url, timeout=2)
    except Exception as e:
        print("ESP request failed:", e)
    take_photo()
    return redirect(url_for("index"))

@app.route("/photo", methods=["POST"])
def take_photo():
    subprocess.run(
        ["termux-camera-photo", PHOTO_PATH],
        check=False
    )
    return redirect(url_for("index"))

@app.route("/photo.jpg")
def serve_photo():
    if os.path.exists(PHOTO_PATH):
        return send_file(PHOTO_PATH, mimetype="image/jpeg")
    return "No photo", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
