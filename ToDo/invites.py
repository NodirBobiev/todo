from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, abort
)
from werkzeug.exceptions import abort

from ToDo.auth import login_required
from ToDo.db import get_db

bp = Blueprint('invites', __name__)

@bp.route('/user/invites', methods=['GET'])
@login_required
def show():
    db = get_db()
    g.new_invites = 0
    
    # finding the teams that user received invitation from.
    teams = db.execute(
        "SELECT tm.title, tm.id, iv.seen FROM team tm JOIN invitation iv"
        f" WHERE (tm.id = iv.team_id AND iv.user_id = {g.user['id']})"
        " ORDER BY iv.seen"
    ).fetchall()
    
    # make all not seen invitations seen.
    db.execute(
        f"UPDATE invitation SET seen = 1 WHERE (user_id={g.user['id']} AND seen = 0)"
    )
    db.commit()
    return render_template("invites/invites.html", teams=teams)


@bp.route('/invite/team/<int:team_id>/respond/<int:code>', methods=['POST'])
@login_required
def respond(team_id, code):
    db = get_db()
    invite = db.execute(
        f"SELECT id FROM invitation WHERE (user_id={g.user['id']} AND team_id={team_id})"
    ).fetchone()

    if invite is None:
        abort(500)
    
    if code == 0 :
        try:
            db.execute(
                f"INSERT INTO userteam (user_id, team_id) VALUES({g.user['id']}, {team_id})"
            )
            db.commit()
        except:
            abort(403)
    db.execute(
        f"DELETE FROM invitation WHERE (user_id={g.user['id']} AND team_id = {team_id})"
    )
    db.commit()

    return jsonify({"result": "success"})   