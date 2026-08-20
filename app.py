import os
import secrets
import string
from functools import wraps
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, g

from database import get_db, init_db, DB_PATH, create_user
import drive_links

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production")

if not os.path.exists(DB_PATH):
    init_db(reset=True)


# ---------------------------------------------------------------- helpers

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def get_current_user():
    if "user_id" not in session:
        return None
    if "user" not in g:
        db = get_db()
        g.user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        db.close()
    return g.user


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        user = get_current_user()
        if not user or not user["is_admin"]:
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped


def generate_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def build_roadmap(user_id):
    """Return phases with their lessons + completion state + weighted progress."""
    db = get_db()
    phases = db.execute("SELECT * FROM phases ORDER BY position").fetchall()

    result = []
    core_total = 0
    core_done = 0
    phases_fully_done = 0
    first_incomplete_phase = None

    for phase in phases:
        lessons = db.execute(
            "SELECT * FROM lessons WHERE phase_id = ? ORDER BY position", (phase["id"],)
        ).fetchall()

        lesson_rows = []
        phase_weighted_total = 0
        phase_weighted_done = 0
        all_done = True

        for lesson in lessons:
            prog = db.execute(
                "SELECT completed FROM progress WHERE user_id = ? AND lesson_id = ?",
                (user_id, lesson["id"]),
            ).fetchone()
            completed = bool(prog and prog["completed"])
            if not completed:
                all_done = False
            phase_weighted_total += lesson["sub_count"]
            if completed:
                phase_weighted_done += lesson["sub_count"]
            file_count = db.execute(
                "SELECT COUNT(*) c FROM lesson_files WHERE lesson_id = ?", (lesson["id"],)
            ).fetchone()["c"]
            lesson_rows.append({
                "id": lesson["id"],
                "title": lesson["title"],
                "sub_count": lesson["sub_count"],
                "sub_unit": lesson["sub_unit"],
                "completed": completed,
                "file_count": file_count,
            })

        is_bonus_phase = phase["position"] == 7
        if not is_bonus_phase:
            core_total += phase_weighted_total
            core_done += phase_weighted_done
            if all_done:
                phases_fully_done += 1
            elif first_incomplete_phase is None:
                first_incomplete_phase = phase["position"]

        pct = round(100 * phase_weighted_done / phase_weighted_total) if phase_weighted_total else 0

        result.append({
            "id": phase["id"],
            "position": phase["position"],
            "title": phase["title"],
            "description": phase["description"],
            "hours_estimate": phase["hours_estimate"],
            "lessons": lesson_rows,
            "weighted_total": phase_weighted_total,
            "weighted_done": phase_weighted_done,
            "pct": pct,
            "all_done": all_done,
            "is_bonus": is_bonus_phase,
        })

    db.close()

    if first_incomplete_phase is None:
        first_incomplete_phase = 7 if phases_fully_done < 6 else None

    for p in result:
        if p["all_done"]:
            p["status"] = "done"
        elif p["position"] == first_incomplete_phase:
            p["status"] = "current"
        else:
            p["status"] = "locked"

    global_pct = round(100 * core_done / core_total) if core_total else 0

    return {
        "phases": result,
        "global_pct": global_pct,
        "phases_done": phases_fully_done,
        "phases_total": len([p for p in result if not p["is_bonus"]]),
        "current_phase": next((p for p in result if p["status"] == "current"), None),
    }


# ---------------------------------------------------------------- auth

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()

        from werkzeug.security import check_password_hash
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            default_page = url_for("admin_students") if user["is_admin"] else url_for("dashboard")
            return redirect(request.args.get("next") or default_page)

        flash("Email ou mot de passe incorrect.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------- pages

@app.route("/")
def index():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    user = get_current_user()
    return redirect(url_for("admin_students") if user["is_admin"] else url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    roadmap = build_roadmap(user["id"])
    return render_template("dashboard.html", user=user, roadmap=roadmap, active="dashboard")


@app.route("/roadmap")
@login_required
def roadmap_view():
    user = get_current_user()
    roadmap = build_roadmap(user["id"])
    return render_template("roadmap.html", user=user, roadmap=roadmap, active="roadmap")


@app.route("/lesson/<int:lesson_id>/toggle", methods=["POST"])
@login_required
def toggle_lesson(lesson_id):
    user = get_current_user()
    db = get_db()
    existing = db.execute(
        "SELECT completed FROM progress WHERE user_id = ? AND lesson_id = ?",
        (user["id"], lesson_id),
    ).fetchone()

    if existing:
        new_state = 0 if existing["completed"] else 1
        db.execute(
            "UPDATE progress SET completed = ?, completed_at = ? WHERE user_id = ? AND lesson_id = ?",
            (new_state, datetime.utcnow().isoformat() if new_state else None, user["id"], lesson_id),
        )
    else:
        db.execute(
            "INSERT INTO progress (user_id, lesson_id, completed, completed_at) VALUES (?,?,1,?)",
            (user["id"], lesson_id, datetime.utcnow().isoformat()),
        )
    db.commit()
    db.close()

    return redirect(request.referrer or url_for("roadmap_view"))


def _attach_files_and_links(resources, db):
    out = []
    for r in resources:
        files = db.execute(
            "SELECT * FROM resource_files WHERE resource_id = ? ORDER BY position", (r["id"],)
        ).fetchall()
        file_list = [
            {"name": f["name"], "url": drive_links.drive_view_url(f["drive_id"], f["mime_type"])}
            for f in files
        ]
        out.append({
            "id": r["id"], "title": r["title"], "subtitle": r["subtitle"], "tag": r["tag"],
            "files": file_list,
            "primary_url": file_list[0]["url"] if len(file_list) == 1 else None,
        })
    return out


@app.route("/library")
@login_required
def library():
    user = get_current_user()
    db = get_db()
    ebooks = _attach_files_and_links(
        db.execute("SELECT * FROM resources WHERE category = 'ebook' ORDER BY id").fetchall(), db
    )
    themes = _attach_files_and_links(
        db.execute("SELECT * FROM resources WHERE category = 'theme' ORDER BY id").fetchall(), db
    )
    bonus = _attach_files_and_links(
        db.execute("SELECT * FROM resources WHERE category = 'bonus' ORDER BY id").fetchall(), db
    )
    db.close()
    roadmap = build_roadmap(user["id"])
    return render_template(
        "library.html", user=user, ebooks=ebooks, themes=themes, bonus=bonus,
        roadmap=roadmap, active="library",
    )


@app.route("/resource/<int:resource_id>")
@login_required
def resource_detail(resource_id):
    user = get_current_user()
    db = get_db()
    resource = db.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
    if not resource:
        db.close()
        flash("Ressource introuvable.")
        return redirect(url_for("library"))
    files = db.execute(
        "SELECT * FROM resource_files WHERE resource_id = ? ORDER BY position", (resource_id,)
    ).fetchall()
    db.close()

    file_list = [
        {"name": f["name"], "view_url": drive_links.drive_view_url(f["drive_id"], f["mime_type"])}
        for f in files
    ]
    return render_template(
        "resource_detail.html", user=user, resource=resource, files=file_list, active="library",
    )


@app.route("/lesson/<int:lesson_id>")
@login_required
def lesson_detail(lesson_id):
    user = get_current_user()
    db = get_db()
    lesson = db.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    if not lesson:
        db.close()
        flash("Leçon introuvable.")
        return redirect(url_for("roadmap_view"))

    phase = db.execute("SELECT * FROM phases WHERE id = ?", (lesson["phase_id"],)).fetchone()
    files = db.execute(
        "SELECT * FROM lesson_files WHERE lesson_id = ? ORDER BY position", (lesson_id,)
    ).fetchall()
    prog = db.execute(
        "SELECT completed FROM progress WHERE user_id = ? AND lesson_id = ?",
        (user["id"], lesson_id),
    ).fetchone()
    db.close()

    video_files = []
    other_files = []
    for f in files:
        item = {
            "name": f["name"],
            "preview_url": drive_links.drive_preview_url(f["drive_id"]),
            "view_url": drive_links.drive_view_url(f["drive_id"], f["mime_type"]),
        }
        if f["mime_type"].startswith("video/"):
            video_files.append(item)
        else:
            other_files.append(item)

    return render_template(
        "lesson_detail.html", user=user, lesson=lesson, phase=phase,
        video_files=video_files, other_files=other_files,
        completed=bool(prog and prog["completed"]), active="roadmap",
    )


# ---------------------------------------------------------------- admin

@app.route("/admin")
@admin_required
def admin_students():
    db = get_db()
    students = db.execute(
        "SELECT * FROM users WHERE is_admin = 0 ORDER BY name COLLATE NOCASE"
    ).fetchall()
    db.close()

    rows = []
    for s in students:
        roadmap = build_roadmap(s["id"])
        rows.append({"user": s, "roadmap": roadmap})

    admin = get_current_user()
    new_password = session.pop("new_student_password", None)
    new_student_email = session.pop("new_student_email", None)
    return render_template(
        "admin_students.html", user=admin, rows=rows, active="admin",
        new_password=new_password, new_student_email=new_student_email,
    )


@app.route("/admin/students/new", methods=["POST"])
@admin_required
def admin_new_student():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not name or not email:
        flash("Nom et email sont obligatoires.")
        return redirect(url_for("admin_students"))

    password = generate_password()
    new_id = create_user(email, name, password, is_admin=0)

    if new_id is None:
        flash(f"Un compte existe déjà avec l'email {email}.")
    else:
        session["new_student_password"] = password
        session["new_student_email"] = email

    return redirect(url_for("admin_students"))


@app.route("/admin/students/<int:student_id>")
@admin_required
def admin_student_detail(student_id):
    db = get_db()
    student = db.execute("SELECT * FROM users WHERE id = ? AND is_admin = 0", (student_id,)).fetchone()
    db.close()
    if not student:
        flash("Élève introuvable.")
        return redirect(url_for("admin_students"))

    roadmap = build_roadmap(student["id"])
    admin = get_current_user()
    return render_template(
        "admin_student_detail.html", user=admin, student=student, roadmap=roadmap, active="admin",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
