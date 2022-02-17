import os

from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY = 'dev',
        DATABASE=os.path.join(app.instance_path, "ToDo.sqlite")
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent = True)
    else:
        app.config.from_mapping(test_config)
    
    try: 
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import team
    app.register_blueprint(team.bp)
    app.add_url_rule('/', endpoint='index')

    from . import task
    app.register_blueprint(task.bp)

    @app.route("/hello")
    def hello():
        return 'Hello World!'
    
    return app

