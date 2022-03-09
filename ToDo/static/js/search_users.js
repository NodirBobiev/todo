var team_users;
var invt_users;
var users;

$(document).ready(function(){
    ///---
});

loadTeamUsers(team_id);
loadInvitedUsers(team_id)
loadUsers();

function loadUsers(){
    req = $.ajax({
        url: Flask.url_for('auth.get_users'),
        type: 'GET',
        success: function(data){
            users = data['users'];
            filterUsers();
        }
    });
    return req;
}

function loadInvitedUsers(id){
    req = $.ajax({
        url: Flask.url_for('team.get_inviteds', {"id": id}),
        type: 'GET',
        success: function(data){
            invt_users = data['users'];
            filterUsers();
        }
    });
    return req;
}

function loadTeamUsers(id){
    req = $.ajax({
        url: Flask.url_for('team.get_users', {"id": id}),
        type: 'GET',
        success: function(data){
            team_users = data['users'];
            filterUsers();
        }
    });
    return req;
}

function kickUser(id){
    req = $.ajax({
        url: Flask.url_for('team.kick_user', {"team_id": team_id, "user_id": id}),
        type: 'POST',
        success: function(data){
            for( let i = 0; i < team_users.length; i ++ )
            {
                if( team_users[i]["id"] === id ){
                    team_users.splice(i, 1);
                    break;
                }
            }
            filterUsers();
        }
    })
}
function inviteUser(id){
    req = $.ajax({
        url: Flask.url_for('team.invite_user', {"team_id": team_id, "user_id": id}),
        type: 'POST',
        success: function(data){
            for( let i = 0; i < users.length; i ++ )
            {
                if( users[i]["id"] === id ){
                    invt_users.push(users[i]);
                    invt_users.sort(function(a,b){return a['id']-b['id']})
                    break;
                }
            }
            filterUsers();
        }
    })
}
function cancelInvite(id){
    req = $.ajax({
        url: Flask.url_for('team.cancel_invite', {"team_id": team_id, "user_id": id}),
        type: 'POST',
        success: function(data){
            for( let i = 0; i < invt_users.length; i ++ )
            {
                if( invt_users[i]["id"] === id ){
                    invt_users.splice(i, 1);
                    break;
                }
            }
            filterUsers();
        }
    })
}

function spawnRow({username="", id=-1, member=false, invited=false}={}){
    let dv = document.createElement("div");
    let ph = document.createElement("p");
    let bt = document.createElement("button");
    ph.innerText = username;
    
    dv.classList.add("usr-row");
    bt.classList.add("btn");
    if( member ){
        dv.classList.add("usr-mbr");
        bt.classList.add("btn-danger");
        bt.setAttribute('onclick', 'kickUser('+id+')');
        bt.innerText = "Kick";
    }
    else if( invited ){
        dv.classList.add("usr-inv");
        bt.classList.add("btn-danger");
        bt.setAttribute('onclick', 'cancelInvite('+id+')');
        bt.innerText = "Cancel";
    }
    else{
        bt.classList.add("btn-success");
        bt.setAttribute('onclick', 'inviteUser('+id+')');
        bt.innerHTML = "Invite";
    }
    dv.appendChild(ph);
    dv.appendChild(bt);
    return dv;
}


function filterUsers(){
    let input = document.getElementById("searchInput").value.toUpperCase()
    let pool = document.getElementById("users-pool");
    while( pool.firstChild ){
        pool.removeChild(pool.lastChild)
    }

    if( team_users ){
        for( let user of team_users ){
            if( user['username'].toUpperCase().indexOf(input) != -1 ){
                pool.appendChild(spawnRow({username:user['username'], id:user['id'], member:true}));
            }
        }
    }
    if( invt_users ){
        for( let user of invt_users ){
            if( user['username'].toUpperCase().indexOf(input) != -1 ){
                pool.appendChild(spawnRow({username:user['username'], id:user['id'], invited:true}));
            }
        }
    }

    if( users && input !== "" ){
        let team_index = 0, inv_index = 0;
        for( let user of users ){
            // checking among users that are already in team.
            while( team_index < team_users.length && user['id'] > team_users[team_index]['id'] )
                team_index += 1
            if( team_index < team_users.length && user['id'] === team_users[team_index]['id'] )
                continue;

            // checking among users that are invited.
            while( inv_index < invt_users.length && user['id'] > invt_users[inv_index]['id'] )
                inv_index += 1
            if( inv_index < invt_users.length && user['id'] === invt_users[inv_index]['id'] )
                continue;
            
            if( user['username'].toUpperCase().indexOf(input) != -1 ){
                pool.appendChild(spawnRow({username:user['username'], id:user['id'], member:false}));
            }
        }
    }
}