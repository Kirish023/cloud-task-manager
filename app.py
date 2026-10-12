from flask import Flask, render_template, request, redirect, session
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "change-this-to-something-random-later"

def get_db_connection():
    conn = sqlite3.connect("tasks.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            email TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            done INTEGER DEFAULT 0
        )
    """)
    return conn

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper

@app.route("/", methods=["GET", "POST"])
def details():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        email = request.form["email"]

        conn = get_db_connection()
        cur = conn.execute(
            "INSERT INTO users (name, age, email) VALUES (?, ?, ?)",
            (name, age, email)
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()

        session["user_id"] = user_id
        session["name"] = name

        return redirect("/tasks")

    return render_template("details.html")

@app.route("/tasks")
@login_required
def tasks():
    conn = get_db_connection()
    task_list = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("index.html", tasks=task_list, name=session["name"])

@app.route("/add", methods=["POST"])
@login_required
def add_task():
    task_text = request.form["task"]
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO tasks (content, user_id) VALUES (?, ?)",
        (task_text, session["user_id"])
    )
    conn.commit()
    conn.close()
    return redirect("/tasks")

@app.route("/complete/<int:task_id>")
@login_required
def complete_task(task_id):
    conn = get_db_connection()
    conn.execute(
        "UPDATE tasks SET done = CASE WHEN done = 0 THEN 1 ELSE 0 END WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    )
    conn.commit()
    conn.close()
    return redirect("/tasks")

@app.route("/delete/<int:task_id>")
@login_required
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    )
    conn.commit()
    conn.close()
    return redirect("/tasks")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
