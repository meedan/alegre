import os
from app import blueprint
from app.main import create_app, db

app = create_app(os.getenv('BOILERPLATE_ENV', 'dev'))
app.register_blueprint(blueprint)
app.app_context().push()