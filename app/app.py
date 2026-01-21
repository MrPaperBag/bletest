from flask import Flask, request, render_template_string, redirect, url_for, send_file, jsonify
import subprocess
import requests
import os
import sys
import socket
import platform
import ipaddress
import re
import concurrent.futures

ESP_URL = "http://192.168.1.8/color"

BASE_DIR = os.getcwd()
PHOTO_PATH = os.path.join(BASE_DIR, "PHOTO.jpg")
PULL_FILE = os.path.join(BASE_DIR, "..", "shouldipull")


app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ESP RGB Control</title>
<style>
body {
    background:#111;
    color:#0f0;
    font-family:Arial;
    text-align:center;
}
input[type=range] { width:90%; }
button {
    font-size:20px;
    padding:10px 20px;
    margin:10px;
}
img {
    width:90%;
    margin-top:15px;
    border:2px solid #0f0;
}
</style>
</head>
<body>

<h2>RGB LED Control</h2>

<form action="/set">
R<br><input type="range" name="r" min="0" max="255" value="255"><br>
G<br><input type="range" name="g" min="0" max="255" value="0"><br>
B<br><input type="range" name="b" min="0" max="255" value="255"><br><br>

Brightness<br>
<input type="range" name="br" min="0" max="100" value="100"><br><br>

<button>SET</button>
</form>

<hr>

<form action="/photo" method="post">
<button>GET IMAGE</button>
</form>

{% if photo %}
<img src="/photo.jpg">
{% endif %}

<hr>

<form action="/pull" method="post">
<button style="color:red;">PULL</button>
</form>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(
        HTML,
        photo=os.path.exists(PHOTO_PATH)
    )

@app.route("/home")
def home():
    return "now you are home" 

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
    except:
        pass
    take_photo()
    return redirect(url_for("index"))

@app.route("/photo", methods=["POST"])
def take_photo():
    subprocess.run(["termux-camera-photo", PHOTO_PATH], check=False)
    return redirect(url_for("index"))

@app.route("/photo.jpg")
def serve_photo():
    if os.path.exists(PHOTO_PATH):
        return send_file(PHOTO_PATH, mimetype="image/jpeg")
    return "No photo", 404

@app.route("/cwd")
def serve_cwd():
    return os.getcwd()


def _get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        try:
            s.close()
        except Exception:
            pass
    return ip


def scan_network(subnet=None, timeout=5, workers=100):
    """Scan the local network for connected devices.

    Args:
        subnet: CIDR string (e.g. '192.168.1.0/24'). If None, uses detected IP with /24.
        timeout: ping timeout in seconds.
        workers: number of parallel ping workers.

    Returns:
        List of dicts: [{'ip': '192.168.1.10', 'mac': 'aa:bb:cc:dd:ee:ff'}, ...]
    """
    if subnet is None:
        local_ip = _get_local_ip()
        try:
            net = ipaddress.ip_network(f"{local_ip}/24", strict=False)
        except Exception:
            net = ipaddress.ip_network("127.0.0.1/32")
    else:
        net = ipaddress.ip_network(subnet, strict=False)

    hosts = [str(h) for h in net.hosts()]

    def _ping(ip):
        plat = platform.system().lower()
        if plat.startswith("windows"):
            cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
        else:
            cmd = ["ping", "-c", "1", "-W", str(int(timeout)), ip]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return ip
        except Exception:
            return None

    # Run ping sweep
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_ping, ip) for ip in hosts]
        # wait for completion
        for _ in concurrent.futures.as_completed(futures):
            pass

    # Parse ARP cache to get MAC addresses
    try:
        arp = subprocess.check_output(["arp", "-a"], stderr=subprocess.DEVNULL, universal_newlines=True)
    except Exception:
        arp = ""

    # Regex to capture IP and MAC-like token
    mac_pattern = re.compile(r"([0-9a-fA-F]{2}(?:[:-][0-9a-fA-F]{2}){5})")
    ip_pattern = re.compile(r"(\d+\.\d+\.\d+\.\d+)")

    devices = []
    for line in arp.splitlines():
        ip_m = ip_pattern.search(line)
        mac_m = mac_pattern.search(line)
        if ip_m and mac_m:
            ip = ip_m.group(1)
            mac = mac_m.group(1).replace('-', ':').lower()
            devices.append({"ip": ip, "mac": mac})

    # Deduplicate by IP preserving order
    seen = set()
    out = []
    for d in devices:
        if d["ip"] not in seen:
            seen.add(d["ip"])
            out.append(d)

    return out


@app.route("/scan")
def scan_route():
    devices = scan_network()
    return jsonify(devices)



@app.route("/pull", methods=["POST"])
def pull_and_exit():
    with open(PULL_FILE, "w") as f:
        f.write("yes")

    # immediate hard exit (no Flask cleanup)
    os._exit(0)

if __name__ == "__main__":
    # PORT 80 (won't actually bind in Termux)
    app.run(host="0.0.0.0", port=8080)
