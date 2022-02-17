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
    teams = db.execute(
        "SELECT p.id, title, owner_id, username"
        " From team p JOIN user u ON p.owner_id = u.id"
    ).fetchall()
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
            return redirect(url_for('team.index'))
    
    return render_template('team/create.html', header_title = "New Team")

def get_team(id, check_owner=True):
    team = get_db().execute(
        "SELECT p.id, title, owner_id, username"
        " FROM team p JOIN user u ON p.owner_id = u.id"
        " WHERE p.id = ?",
        (id,)
    ).fetchone()

    if team is None:
        abort(404, f"Team id {id} doesn't exist.")
    
    if check_owner and team['owner_id'] != g.user['id']:
        abort(403)
    
    return team

@bp.route('/team/<int:id>', methods = ['GET', 'POST'])
@login_required
def team(id):
    team = get_team(id)
    teams = []
    return render_template('team/index.html', teams = teams)
