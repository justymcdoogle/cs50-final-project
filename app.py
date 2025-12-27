from flask import Flask, render_template, request, session, redirect, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL

from helpers import login_required 

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database
db = SQL("sqlite:///tabs.db")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        if not request.form.get("username"):
            return "No username :("
        
        if not request.form.get("password"):
            return "No password :("

        if not request.form.get("confirmation"):
            return "No confirmation :("
        
        rows = db.execute("SELECT username FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) > 0:
            return "Username not unique :("
        
        if request.form.get("password") != request.form.get("confirmation"):
            return "Confirmation must match password :("

        hashed_password = generate_password_hash(request.form.get("password"))

        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            request.form.get("username"),
            hashed_password,
        )

        rows = db.execute(
            "SELECT id FROM users WHERE username = ?",
            request.form.get("username")
        )

        session["user_id"] = rows[0]['id']

        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return "Must provide username. L"
        elif not request.form.get("password"):
            return "Must provide password. L"

        rows = db.execute(
        "SELECT * FROM users WHERE username = ?",
        request.form.get("username")
        )


        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return "invalid user/password. Lol"

        session["user_id"] = rows[0]["id"]

        return redirect("/")
    
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")

@app.route("/")
@login_required
def index():
    """Homepage"""
    return render_template("index.html")

@app.route("/search")
@login_required
def search():
    """Search for tabs"""
    # This is thanks to Gemini :)
    query = request.args.get("q")

    if query:
        songs = db.execute(
            "SELECT * FROM tabs WHERE \
            name LIKE ? OR artist LIKE ? \
            ORDER BY name ASC",
            ("%" + query + "%"),
            ("%" + query + "%")
        )

    else:
        songs = []

    return render_template("search.html", songs=songs)

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Create a new tab"""
    if request.method == "POST":
        return "nothing for now..."

    else:
        return render_template("create_tab.html")

@app.route("/favorite")
@login_required
def favorite():
    if request.method == "POST":
        return "nothing for now..."

    else:
        return render_template("favorites.html")


# Definitely needed Gemini to explain how this works 😅
@app.route("/song/<int:song_id>")
@login_required
def songs(song_id):
    """Display song"""
    song = db.execute(
        "SELECT * FROM tabs WHERE id = ?",
        song_id,
    )

    if not song:
        return "Song not found", 404

    return render_template("song.html", song=song[0])

if __name__ == "__main__":
    app.run(debug=True)
