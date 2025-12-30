from flask import redirect, session
from functools import wraps

# just copied this basically from problem set 9/finance lol
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def validate_parsed_data(parsed_data):
    """Make sure data is what we want before it goes into the database"""
    LINE_LENGTH = 75
    VALID_SECTIONS = ["verse", "chorus", "bridge", "intro", "outro", "solo"]
    for section_number in parsed_data:
        section_type = parsed_data[section_number]['type'].lower()
        if section_type not in VALID_SECTIONS:
            return "Invalid section type"
        for line_number in parsed_data[section_number]['line']:
            line = parsed_data[section_number]['line'][line_number]
            if not line['chords']:
                return "Chords cannot be empty"
            if len(line['chords']) > LINE_LENGTH:
                return "Chord line too long"
            if len(line['lyrics']) > LINE_LENGTH:
                return "Lyrics line too long"

