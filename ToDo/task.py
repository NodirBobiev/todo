from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from ToDo.auth import login_required
from ToDo.team import get_team
from ToDo.db import get_db

bp = Blueprint('task', __name__)

@bp.route('/team/<int:team_id>/create', methods=['GET', 'POST'])
@login_required
def create(team_id):
    team = get_team(team_id)
    if request.method == 'POST':
        title = request.form['title']
        error = None

        if title is None:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO task (title, team_id, stage) VALUES(?,?,?)",
                (title, team['id'], 0)
            )
            db.commit()
            return redirect(url_for('team.open_team', id=team_id))
    return render_template("team/create.html", header_title = "New task")


@bp.route('/team/<int:team_id>/delete/<int:task_id>', methods=['POST'])
@login_required
def delete(team_id, task_id):
    get_team(team_id)
    db = get_db()
    task = db.execute(
        "SELECT * FROM task WHERE id = ?", (task_id,)
    ).fetchone()
    error = None

    if task is None:
        error = f"Task id {task_id} doesn't exist"
    
    if team_id != task['team_id']:
        error = f"Task id {task_id} doesn't belong to Team id {team_id}."
    
    if error is not None:
        flash(error)
    else:
        db.execute(
            "DELETE FROM task WHERE id = ?", (task_id,)
        )
        db.commit()

    return redirect(url_for("team.open_team", id=team_id))


@bp.route('/team/<int:team_id>/task/<int:task_id>/staged/<int:stage>/', methods=['POST'])
@login_required
def staged(team_id, stage, task_id):
    get_team(team_id)
    db = get_db()
    task = db.execute(
        f"SELECT * FROM task WHERE (id = {task_id} AND team_id = {team_id})"
    ).fetchone()

    if task is None:
        flash(f"Task id {task_id} doesn't exist")
    else:
        db.execute(
            f"UPDATE task SET stage = {stage} WHERE id = {task_id}"
        )
        db.commit()
    return redirect(url_for("team.open_team", id=team_id))

