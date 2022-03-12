function deleteGrandParent(element){
    element.parentNode.parentNode.remove()
}

function respond(element, id, code){
    req = $.ajax({
        url: Flask.url_for('invites.respond', {'team_id': id, "code": code}),
        type: 'POST',
        success: function(data){
            deleteGrandParent(element);
        },
        error: function(data){
            alert("Oops, Something went wrong. Please update the webpage!");
        }
    });
    return req;
}
