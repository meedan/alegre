import os
import unittest

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from app import blueprint
from app.main import create_app, db
from app.main.model import image

from app.main.lib.image_hash import compute_phash_int
from PIL import Image

app = create_app(os.getenv('BOILERPLATE_ENV') or 'dev')
app.register_blueprint(blueprint)
app.app_context().push()

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

@manager.command
def run():
  port = os.getenv('ALEGRE_PORT') or 5000
  app.run(host='0.0.0.0', port=port, threaded=True)

@manager.command
def test():
  """Runs the unit tests."""
  tests = unittest.TestLoader().discover('app/test', pattern='test*.py')
  result = unittest.TextTestRunner(verbosity=2).run(tests)
  return 0 if result.wasSuccessful() else 1

@manager.command
def phash(path):
  im = Image.open(path).convert('RGB')
  phash = compute_phash_int(im)
  print(phash, "{0:b}".format(phash), sep=" ")

if __name__ == '__main__':
  manager.run()
