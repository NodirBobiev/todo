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
                "INSERT INTO task (title, team_id) VALUES(?,?)",
                (title, team_id)
            )
            db.commit()
            return redirect(url_for('team.index'))
    return render_template("team/create.html", header_title = "New task")