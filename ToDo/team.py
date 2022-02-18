from ast import AsyncFunctionDef
from distutils.errors import DistutilsFileError
from signal import SIG_DFL
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from ToDo.auth import login_required
from ToDo.db import get_db

bp = Blueprint('team', __name__)

@bp.route('/')
def index():
    db = get_db()
    teams = []
    if g.user is not None:    
        teams_ids = db.execute(
            "SELECT team_id FROM userteam ut WHERE ut.user_id = ?",
            (g.user['id'], )
        ).fetchall()

        placeholders = ', '.join(list(str(i['team_id']) for i in teams_ids))
        query = f"SELECT * FROM team WHERE id IN ({placeholders})"
        teams = db.execute(query).fetchall()

    return render_template('team/index.html', teams = teams)

@bp.route('/team/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        error = None

        if not title:
            error = 'Title is required.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO team (title, owner_id) VALUES (?, ?)",
                (title, g.user['id'])
            )
            db.commit()

            team = db.execute(
                "SELECT id FROM team WHERE title = ?", 
                (title,)
            ).fetchone()
            db.execute(
                "INSERT INTO userteam (user_id, team_id) VALUES(?, ?)",
                (g.user['id'], team['id'],)
            )
            db.commit()
            return redirect(url_for('team.index'))
    
    return render_template('team/create.html', header_title = "New Team")

def get_team(id, check_member = True, check_owner=False):
    db = get_db()
    team = db.execute(
        "SELECT tm.id, title, owner_id, username"
        " FROM team tm JOIN user u ON tm.owner_id = u.id"
        " WHERE tm.id = ?",
        (id,)
    ).fetchone()

    if team is None:
        abort(404, f"Team id {id} doesn't exist.")
    
    if check_owner and team['owner_id'] != g.user['id']:
        abort(403)
    
    if check_member is False and check_member:
        relation = db.execute(
            "SELECT * FROM userteam WHERE (user_id, team_id) IN ((?,?))",
            ((g.user['id'], id),)
        ).fetchone()
        if relation is None:
            abort(403)

    return team

@bp.route('/team/<int:id>', methods = ['GET', 'POST'])
@login_required
def open_team(id):
    team = get_team(id)
    db = get_db()
    tasks = db.execute(
        "SELECT tsk.id, tsk.title, tsk.team_id"
        " FROM task tsk JOIN team t ON tsk.team_id = t.id"
        " WHERE t.id = ?",
        (id,)
    ).fetchall()

    users_ids = db.execute(
        "SELECT user_id FROM userteam ut"
        " JOIN team t ON ut.team_id = t.id"
        " WHERE t.id = ?",
        (id,)
    ).fetchall()

    
    placeholders = ', '.join(list(str(i['user_id']) for i in users_ids))
    
    query = f"SELECT username FROM user WHERE id IN ({placeholders})"
    users = db.execute(query).fetchall()

    return render_template('team/content.html', tasks=tasks, team = team, users=users)

@bp.route('/team/<int:id>/add', methods=['POST'])
@login_required
def add(id):
    team = get_team(id)
    username = request.form['username']
    db = get_db()
    user = db.execute(
        "SELECT * FROM user WHERE username = ?", (username,)
    ).fetchone()
    error = None

    if user is None:
        error = f"User {username} doesn't exist."
        
    if error is None:
        try:
            db.execute(
                "INSERT INTO userteam (user_id, team_id) VALUES(?, ?)",
                (user['id'], team['id'],)
            )
            db.commit()
        except db.IntegrityError:
            error = f"User {username} is already in the team."
        else:
            error = f"User {username} has been successfully added."
    
    flash(error)
    
    return redirect(url_for("team.open_team", id=id))



