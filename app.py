from flask import Flask, render_template, request, redirect, url_for, session
from flask import send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
import psutil
import logging
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Load secret key from environment, fail fast if missing
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")

# Auth logging setup
logging.basicConfig(
    filename="/app/logs/auth.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
auth_log = logging.getLogger("auth")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Load user credentials from environment
_username = os.environ.get("PI_CLOUD_USERNAME")
_password = os.environ.get("PI_CLOUD_PASSWORD")
if not _username or not _password:
    raise RuntimeError("PI_CLOUD_USERNAME and PI_CLOUD_PASSWORD must be set in .env.")

USERS = {
    _username: _password
}

LIBRARY = {
    "AI": "/home/pi/pi-cloud/AI",
    "Movies": "/home/pi/pi-cloud/Movies",
    "Music": "/home/pi/pi-cloud/Music",
    "Photos": "/home/pi/pi-cloud/Photos",
}

ICONS = {
    "AI": "🤖",
    "Movies": "🎬",
    "Music": "🎵",
    "Photos": "📷",
}

def get_folder_counts():
    folders = {}
    for name, path in LIBRARY.items():
        if os.path.exists(path):
            folders[name] = len(os.listdir(path))
        else:
            folders[name] = None
    return folders

def get_system_stats():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            temp = round(int(f.read()) / 1000, 1)
    except:
        temp = "N/A"
    return {
        "cpu": cpu,
        "ram_used": round(ram.used / 1e9, 1),
        "ram_total": round(ram.total / 1e9, 1),
        "ram_percent": ram.percent,
        "disk_used": round(disk.used / 1e9, 1),
        "disk_total": round(disk.total / 1e9, 1),
        "disk_percent": disk.percent,
        "temp": temp,
    }

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        ip = request.remote_addr
        if USERS.get(username) == password:
            session["user"] = username
            auth_log.info(f"SUCCESS | user={username} | ip={ip}")
            return redirect(url_for("index"))
        else:
            auth_log.warning(f"FAILED | user={username} | ip={ip}")
            error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    folders = get_folder_counts()
    stats = get_system_stats()
    return render_template("index.html", folders=folders, stats=stats, icons=ICONS, user=session["user"])

@app.route("/section/<name>")
def section(name):
    if "user" not in session:
        return redirect(url_for("login"))
    if name not in LIBRARY:
        return redirect(url_for("index"))
    path = LIBRARY[name]
    files = []
    media_items = []
    if os.path.exists(path):
        files = os.listdir(path)
        if name == "Movies":
            # Group movies with their posters
            movies = [f for f in files if f.endswith(('.mp4', '.mkv', '.avi', '.mov'))]
            for movie in movies:
                base = os.path.splitext(movie)[0]
                poster = next((f for f in files if f.startswith(base) and f.endswith(('.jpg', '.jpeg', '.png')) and 'poster' in f.lower()), None)
                media_items.append({
                    "file": movie,
                    "poster": poster,
                    "title": base.replace("-", " ").replace(".", " ").title()
                })
        else:
            media_items = [{"file": f, "poster": None, "title": f} for f in files]
    return render_template("section.html", name=name, files=files, media_items=media_items, icon=ICONS.get(name, "📁"), user=session["user"])

@app.route("/logs")
def logs():
    if "user" not in session:
        return redirect(url_for("login"))
    log_entries = []
    log_path = "/app/logs/auth.log"
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            for line in f.readlines():
                if "SUCCESS" in line or "FAILED" in line:
                    parts = line.strip().split("|")
                    if len(parts) == 3:
                        timestamp = parts[0].strip()
                        status = "SUCCESS" if "SUCCESS" in parts[0] else "FAILED"
                        user = parts[1].replace("user=", "").strip()
                        ip = parts[2].replace("ip=", "").strip()
                        log_entries.append({
                            "timestamp": timestamp,
                            "status": status,
                            "user": user,
                            "ip": ip
                        })
    log_entries.reverse()
    return render_template("logs.html", entries=log_entries, user=session["user"])

@app.route("/file/<category>/<filename>")
def serve_file(category, filename):
    if "user" not in session:
        return redirect(url_for("login"))
    if category not in LIBRARY:
        return redirect(url_for("index"))
    filepath = os.path.join(LIBRARY[category], filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    return send_file(filepath)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True, ssl_context=("certs/cert.pem", "certs/key.pem"))
