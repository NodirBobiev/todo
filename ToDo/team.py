from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, abort
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
    
    if check_owner is False and check_member:
        relation = db.execute(
            "SELECT * FROM userteam WHERE user_id = ? AND team_id = ?",
            (g.user['id'], id)
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
        "SELECT tsk.id, tsk.title, tsk.team_id, tsk.stage"
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
    
    query = f"SELECT username, id FROM user WHERE id IN ({placeholders})"
    users = db.execute(query).fetchall()

    return render_template('team/content.html', tasks=tasks, team = team, users=users)


@bp.route('/team/<int:id>/get/users', methods=['GET'])
@login_required
def get_users(id):
    get_team(id, check_owner=True)
    db = get_db()
    rows = db.execute( 
        "SELECT user.id, username FROM userteam, user"
        f" WHERE team_id = {id} AND user.id = user_id ORDER BY user_id"
    ).fetchall()  

    users = list()
    for row in rows:
        users.append({"username": row["username"], "id":row["id"]})
    return jsonify({"users":users})


@bp.route('/team/<int:id>/get/inviteds', methods=['GET'])
@login_required
def get_inviteds(id):
    get_team(id, check_owner=True)
    db = get_db()
    rows = db.execute( 
        "SELECT user.id, username FROM invitation, user"
        f" WHERE team_id = {id} AND user.id = user_id ORDER BY user_id"
    ).fetchall()  

    users = list()
    for row in rows:
        users.append({"username": row["username"], "id":row["id"]})
    return jsonify({"users":users})


@bp.route('/team/<int:team_id>/cancel/invite/<int:user_id>', methods=['POST'])
@login_required
def cancel_invite(team_id, user_id):
    get_team(team_id, check_owner=True)
    db = get_db()

    invitation_rel = db.execute(
        f"SELECT * FROM invitation WHERE (user_id = {user_id} AND team_id = {team_id})"
    ).fetchone()

    if invitation_rel is not None:
        db.execute(
            f"DELETE FROM invitation WHERE id = {invitation_rel['id']}",
        )
        db.commit()
    else:
        abort(500)
    return jsonify({"result":"OK"})


@bp.route('/team/<int:team_id>/invite/user/<int:user_id>', methods=['POST'])
@login_required
def invite_user(team_id, user_id):
    get_team(team_id, check_owner=True)
    db = get_db()
    
    userteam_rel = db.execute(
        f"SELECT * FROM userteam WHERE (user_id = {user_id} AND team_id = {team_id})"
    ).fetchone()

    invitation_rel = db.execute(
        f"SELECT * FROM invitation WHERE (user_id = {user_id} AND team_id = {team_id})"
    ).fetchone()

    user = db.execute(
        f"SELECT * FROM user WHERE id = {user_id}"
    ).fetchone()

    if user is not None and userteam_rel is None and invitation_rel is None:
        db.execute(
            f"INSERT INTO invitation (user_id, team_id) VALUES({user_id}, {team_id})"
        )
        db.commit()
    else:
        abort(500)
    return jsonify({"result": "OK"})


@bp.route('/team/<int:id>/manageusers', methods=['GET'])
@login_required
def manage_users(id):
    team = get_team(id, check_owner=True)
    return render_template('team/manageusers.html', team=team)


@bp.route('/team/<int:id>/adduser', methods=['POST'])
@login_required
def add_user(id):
    team = get_team(id, check_owner=True)
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


@bp.route('/team/<int:team_id>/kick/user/<int:user_id>', methods=['POST'])
@login_required
def kick_user(team_id, user_id):
    team = get_team(team_id, check_owner=True)
    if team['owner_id'] == user_id:
        abort(403)
    else:
        db = get_db()
        relation = db.execute(
            f"SELECT * FROM userteam WHERE (user_id = {user_id} AND team_id = {team_id})"
        ).fetchone()

        if relation is not None:
            db.execute(
                "DELETE FROM userteam WHERE id = ?",
                (relation['id'],)
            )
            db.commit()
        
        else:
            abort(500)
    return jsonify({"result": "OK"})


@bp.route('/team/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    team = get_team(id, check_owner=True)
    db = get_db()
    db.execute(
        "DELETE FROM userteam WHERE team_id = ?",
        (id,)
    )
    db.execute(
        "DELETE FROM team WHERE id = ?",
        (id,)
    )
    db.commit()
    flash(f"Team {team['title']} has been successfully deleted.")
    return redirect(url_for('team.index'))
    

@bp.route('/team/<int:team_id>/leave', methods=['POST'])
@login_required
def user_leave(team_id):
    team = get_team(team_id)
    db = get_db()
    db.execute(
        f"DELETE FROM userteam WHERE (user_id = {g.user['id']} AND team_id = {team_id})"
    )
    db.commit()
    return redirect(url_for("team.index"))

