from flask import Flask, render_template, request, session, redirect, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from cs50 import SQL

from helpers import login_required, validate_parsed_data 

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
            flash("No username :(")
            return redirect("/register")

        password = request.form.get("password")
        if not password:
            flash("No password :(")
            return redirect("/register")

        if not request.form.get("confirmation"):
            flash("No confirmation :(")
            return redirect("/register")
        
        rows = db.execute(
            "SELECT username FROM users WHERE username = ?",
            request.form.get("username")
        )

        if len(rows) > 0:
            flash("Username not unique :(")
            return redirect("/register")
        
        if request.form.get("password") != request.form.get("confirmation"):
            flash("Confirmation must match password :(")
            return redirect("/register")

        hashed_password = generate_password_hash(password) # type: ignore

        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            request.form.get("username"), hashed_password
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
            flash("Must provide username. Nice try")
            return redirect("/login")
        
        password = request.form.get("password")
        if not password:
            flash("Must provide password. Nice try")
            return redirect("/login")

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?",
            request.form.get("username")
        )


        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password): # type: ignore
            flash("Username taken or password wrong")
            return redirect("/login")

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
    recent = db.execute(
        "SELECT tabs.*, users.username FROM tabs \
        JOIN users ON tabs.user_id = users.id \
        ORDER BY tabs.id DESC LIMIT 10"
    )

    return render_template("index.html", recent=recent)


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
    # Probably could've used a helper function or two here but oh well
    TITLE_LENGTH = 200
    ARTIST_LENGTH = 150
    if request.method == "POST":
        name = request.form.get("name")
        name = name.rstrip() # type: ignore
        artist = request.form.get("artist")
        artist = artist.rstrip() #type: ignore
        #print(name, artist)

        if not name:
            flash("Invalid name length")
            return redirect("/create")
        if len(name) > TITLE_LENGTH:
            flash("Invalid title length")
            return redirect("/create")

        if not artist:
            flash("error, must have artist")
            return redirect("/create")
        if len(artist) > ARTIST_LENGTH:
            flash("Invalid artist length")
            return redirect("/create")

        parsed_data = {}
        content = ""
        
        #print(request.form)
        for key, value in request.form.items():
            # We already got these
            if key == "name" or key == "artist":
                continue
            
            else:
                # Get the keys organized
                parts = key.split("_")
                section_number = int(parts[1])
                input_type = parts[2]
                #print(f"parts: {parts}")

                if section_number not in parsed_data:
                    parsed_data[section_number] = {'type': '', 'line': {}}
                
                if input_type == 'type':
                    parsed_data[section_number]['type'] = value
                
                elif input_type == 'chords' or input_type == 'lyrics':
                    line_number = int(parts[3])
                    if line_number not in parsed_data[section_number]['line']:
                        parsed_data[section_number]['line'][line_number] = {'chords': '', 'lyrics': ''}
                    if input_type == 'chords':
                        parsed_data[section_number]['line'][line_number]['chords'] = value
                    elif input_type == 'lyrics':
                        parsed_data[section_number]['line'][line_number]['lyrics'] = value
        

        error = validate_parsed_data(parsed_data)
        if error:
            flash(error)
            return redirect("/create")

        verse_counter = 0

        #print(f'parsed data: {parsed_data}') 
        for section_number in sorted(parsed_data.keys()):
            #print(section_number, sorted(parsed_data.keys()))
            section = parsed_data[section_number]
            if section['type'] == 'verse':
                verse_counter += 1
                content += f"[{section['type'].capitalize()} {verse_counter}]\n"
            else:
                content += f"[{section['type'].capitalize()}]\n"

            for line_number in sorted(section['line'].keys()):
                #print(section_number, line_number)
                line = section['line'][line_number]
                #print(line)
                content += f"{line['chords'].rstrip()}\n{line['lyrics'].rstrip()}\n"
                content += '\n'

        #print(content)
        

        db.execute(
            "INSERT INTO tabs\
            (name, artist, user_id, content) VALUES \
            (?, ?, ?, ?)",
            name, artist, session["user_id"], content
        )

        new_row = db.execute(
            "SELECT id FROM tabs WHERE name = ?",
            name
        )
        new_id = new_row[0]['id']

        return redirect(f"/song/{new_id}")

    else:
        return render_template("create_tab.html")


# Definitely needed Gemini to explain how this works 😅
@app.route("/song/<int:song_id>")
@login_required
def songs(song_id):
    """Display song"""
    song = db.execute(
        "SELECT tabs.*, users.username FROM tabs \
        JOIN users ON tabs.user_id = users.id \
        WHERE tabs.id = ?",
        song_id,
    )

    if not song:
        flash("Song not found")
        return redirect("/search")

    favorited = db.execute(
        "SELECT * FROM favorites WHERE \
        user_id = ? and tab_id = ?",
        session["user_id"], song_id
    )

    is_favorited = len(favorited) > 0

    return render_template("song.html", song=song[0], is_favorited=is_favorited)


@app.route("/favorite")
@login_required
def favorite():
    """Display favorites"""
    favorites = db.execute(
        "SELECT tabs.* FROM tabs \
        JOIN favorites ON tabs.id = favorites.tab_id \
        WHERE favorites.user_id = ?", session["user_id"]
    )
    

    return render_template("favorites.html", favorites=favorites)


@app.route("/favorite/add/<int:song_id>", methods=["POST"])
@login_required
def add_favorite(song_id):
    """Add a song to user's list of favorites"""
    
    rows = db.execute(
        "SELECT * FROM favorites WHERE user_id = ? AND tab_id = ?",
        session["user_id"], song_id
    )
    
    if len(rows) == 1:
        db.execute("DELETE FROM favorites WHERE user_id = ? AND tab_id = ?",
            session["user_id"], song_id
        )

    else:
        db.execute(
            "INSERT INTO favorites (user_id, tab_id) \
            VALUES (?, ?)",
            session["user_id"], song_id
        )
    

    return redirect(f"/song/{song_id}")

if __name__ == "__main__":
    app.run(debug=True)
