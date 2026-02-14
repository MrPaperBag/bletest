from flask import Flask, Response, request, jsonify
import threading
import time
import requests
import os

DEFAULT_URL = "http://192.168.1.9"

app = Flask(__name__)

timers = {}
timer_id_counter = 0
lock = threading.Lock()

last_color = "#ffffff"
last_brightness = 100

fade = {
    "mode": None,
    "end": 0,
    "stop": False
}
fade_thread = None

# ---------- FILE FLAGS ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SHOULD_I_PULL_FILE = os.path.join(BASE_DIR, "shouldipull")
SHOULD_I_START_FILE = os.path.join(BASE_DIR, "shouldistart")

def write_flag(path, value):
    try:
        with open(path, "w") as f:
            f.write(str(value))
            f.flush()
            os.fsync(f.fileno())
        print(f"[FLAG WRITE] {path} = {value}")
    except Exception as e:
        print(f"[FLAG ERROR] {e}")

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()


def send_color(base, hex_color, brightness):
    try:
        brightness = max(0, min(100, int(brightness)))
        encoded = requests.utils.quote(hex_color)
        requests.get(f"{base}/color?c={encoded}&b={brightness}", timeout=2)
    except:
        pass


def stop_fade():
    fade["stop"] = True
    fade["mode"] = None


def fade_worker(mode, duration, base):
    global last_brightness

    fade["stop"] = False
    fade["mode"] = mode
    fade["end"] = time.time() + duration

    duration = max(1, duration)

    start = int(last_brightness)
    target = 0 if mode == "down" else 100

    step_size = 5
    step = -step_size if mode == "down" else step_size

    steps = max(1, abs(target - start) // step_size)
    step_delay = duration / steps

    current = start

    while True:
        if fade["stop"]:
            return

        current += step

        if mode == "down" and current <= target:
            current = target
        if mode == "up" and current >= target:
            current = target

        send_color(base, last_color, current)
        last_brightness = current

        if current == target:
            break

        time.sleep(step_delay)

    if mode == "down":
        send_color(base, "#000000", 0)
        last_brightness = 0
    else:
        send_color(base, last_color, 100)
        last_brightness = 100

    fade["mode"] = None


def start_fade(mode, duration, base):
    global fade_thread
    stop_fade()
    time.sleep(0.05)

    fade_thread = threading.Thread(
        target=fade_worker,
        args=(mode, duration, base),
        daemon=True
    )
    fade_thread.start()


def timer_thread(tid, delay, action, base):
    time.sleep(delay)

    with lock:
        if tid not in timers:
            return

    stop_fade()

    if action == "on":
        send_color(base, last_color, last_brightness or 100)
    else:
        send_color(base, "#000000", 0)

    with lock:
        timers.pop(tid, None)


@app.route("/turn_on")
def turn_on():
    global last_color, last_brightness

    stop_fade()

    base = request.args.get("url", DEFAULT_URL)
    color = request.args.get("color") or last_color
    brightness = int(request.args.get("brightness", last_brightness))

    last_color = color
    last_brightness = brightness

    send_color(base, color, brightness)
    return jsonify({"status": "on"})


@app.route("/turn_off")
def turn_off():
    global last_brightness
    stop_fade()
    base = request.args.get("url", DEFAULT_URL)
    send_color(base, "#000000", 0)
    last_brightness = 0
    return jsonify({"status": "off"})


@app.route("/fade")
def fade_api():
    mode = request.args.get("mode")
    duration = int(request.args.get("duration", 30))
    base = request.args.get("url", DEFAULT_URL)

    start_fade(mode, duration, base)
    return jsonify({"status": "started"})


@app.route("/stop_fade")
def stop_fade_api():
    stop_fade()
    return jsonify({"status": "stopped"})


@app.route("/fade_status")
def fade_status():
    if fade["mode"] is None:
        return jsonify(None)

    remaining = int(fade["end"] - time.time())
    if remaining < 0:
        remaining = 0

    return jsonify({
        "mode": fade["mode"],
        "remaining": remaining,
        "brightness": int(last_brightness)
    })


@app.route("/brightness")
def brightness_status():
    return jsonify({"brightness": int(last_brightness)})


@app.route("/add_timer")
def add_timer():
    global timer_id_counter

    delay = int(request.args.get("delay", 0))
    action = request.args.get("action")
    base = request.args.get("url", DEFAULT_URL)

    stop_fade()

    with lock:
        timer_id_counter += 1
        tid = timer_id_counter

        t = threading.Thread(
            target=timer_thread,
            args=(tid, delay, action, base),
            daemon=True
        )
        timers[tid] = {
            "id": tid,
            "delay": delay,
            "action": action,
            "start": time.time()
        }
        t.start()

    return jsonify({"status": "ok"})


@app.route("/list_timers")
def list_timers():
    now = time.time()
    active = []

    with lock:
        for t in timers.values():
            remaining = int(t["delay"] - (now - t["start"]))
            if remaining < 0:
                remaining = 0
            active.append({
                "id": t["id"],
                "action": t["action"],
                "remaining": remaining
            })

    return jsonify(active)


@app.route("/remove_timer")
def remove_timer():
    tid = int(request.args.get("id"))
    with lock:
        timers.pop(tid, None)
    return jsonify({"status": "removed"})


# -------- PANEL ROUTES (WRITE + EXIT) --------

@app.route("/pull")
def pull():
    write_flag(SHOULD_I_PULL_FILE, "yes")
    threading.Timer(0.3, shutdown_server).start()
    return "OK - pulling and shutting down"


@app.route("/off_panel")
def off_panel():
    write_flag(SHOULD_I_START_FILE, "no")
    threading.Timer(0.3, shutdown_server).start()
    return "OK - off and shutting down"


HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ESP Light</title>

<style>
body {
    margin:0;
    background:#0e1117;
    font-family:Arial;
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    height:100vh;
}

.container {
    display:flex;
    gap:16px;
}

.card {
    background:#161b22;
    padding:25px;
    border-radius:16px;
    width:360px;
}

.side {
    background:#161b22;
    padding:20px;
    border-radius:16px;
    width:140px;
    display:flex;
    flex-direction:column;
    justify-content:center;
}

input, button {
    width:100%;
    margin:6px 0;
    padding:10px;
    border-radius:8px;
    border:none;
}

button { cursor:pointer; color:white; }

.on { background:#238636; }
.off { background:#da3633; }
.fade { background:#6f42c1; }
.timer { background:#30363d; }

.row {
    display:flex;
    justify-content:space-between;
    background:#0f141a;
    padding:6px;
    margin:4px 0;
    border-radius:6px;
}
</style>
</head>
<body>

<div class="container">

<div class="card">
<h3>ESP Light</h3>

<label>ESP URL</label>
<input id="urlBox" value="__DEFAULT_URL__">

<input type="color" id="color" value="#ff0000">

<label>Brightness</label>
<input type="range" id="brightness" min="0" max="100" value="100">

<button class="on" onclick="turnOn()">ON</button>
<button class="off" onclick="turnOff()">OFF</button>

<hr>

<h4>Fade</h4>

<input id="fadeUp" placeholder="Fade IN seconds">
<button class="fade" onclick="startFade('up')">Fade In</button>

<input id="fadeDown" placeholder="Fade OUT seconds">
<button class="fade" onclick="startFade('down')">Fade Out</button>

<div id="fadeList"></div>

<hr>

<h4>Timers</h4>

<input id="onDelay" placeholder="Turn ON after seconds">
<button class="timer" onclick="addTimer('on')">Add ON Timer</button>

<input id="offDelay" placeholder="Turn OFF after seconds">
<button class="timer" onclick="addTimer('off')">Add OFF Timer</button>

<div id="timerList"></div>
</div>

<div class="side">
<button class="off" onclick="panelOff()">OFF</button>
<button class="on" onclick="panelPull()">PULL</button>
</div>

</div>

<script>
function baseURL(){
    return document.getElementById("urlBox").value.trim();
}

function turnOn(){
    const c = document.getElementById("color").value;
    const b = document.getElementById("brightness").value;
    fetch(`/turn_on?url=${baseURL()}&color=${encodeURIComponent(c)}&brightness=${b}`);
}

function turnOff(){
    fetch(`/turn_off?url=${baseURL()}`);
}

function startFade(mode){
    const duration = mode==='up'
        ? document.getElementById("fadeUp").value
        : document.getElementById("fadeDown").value;

    fetch(`/fade?mode=${mode}&duration=${duration}&url=${baseURL()}`);
}

function panelPull(){
    fetch("/pull");
}

function panelOff(){
    fetch("/off_panel");
}

function updateFade(){
    fetch("/fade_status")
    .then(r=>r.json())
    .then(f=>{
        const div=document.getElementById("fadeList");
        div.innerHTML="";
        if(f){
            div.innerHTML=`
                <div class="row">
                    <span>
                        Fading ${f.mode} (${f.remaining}s)<br>
                        Brightness: ${f.brightness}
                    </span>
                    <button onclick="fetch('/stop_fade')">X</button>
                </div>`;
        }
    });
}

function addTimer(action){
    const delay = action==='on'
        ? document.getElementById("onDelay").value
        : document.getElementById("offDelay").value;

    fetch(`/add_timer?delay=${delay}&action=${action}&url=${baseURL()}`)
    .then(updateTimers);
}

function removeTimer(id){
    fetch(`/remove_timer?id=${id}`).then(updateTimers);
}

function updateTimers(){
    fetch("/list_timers")
    .then(r=>r.json())
    .then(data=>{
        const div=document.getElementById("timerList");
        div.innerHTML="";
        data.forEach(t=>{
            div.innerHTML+=`
                <div class="row">
                    <span>${t.action} in ${t.remaining}s</span>
                    <button onclick="removeTimer(${t.id})">X</button>
                </div>`;
        });
    });
}

setInterval(()=>{
    updateTimers();
    updateFade();
},1000);
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return Response(HTML.replace("__DEFAULT_URL__", DEFAULT_URL), mimetype="text/html")


if __name__ == "__main__":
    write_flag(SHOULD_I_PULL_FILE, "no")
    write_flag(SHOULD_I_START_FILE, "yes")

    print("Open: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)
