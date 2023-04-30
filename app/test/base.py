# from flask_testing import TestCase
# from unittest import TestCase
from flask_unittest import ClientTestCase
from app.main import db
from manage import app


class BaseTestCase(ClientTestCase):
    """ Base Tests """

    def create_app(self):
        app.config.from_object('app.main.config.TestingConfig')
        return app

    def setUp(self):
        self.app = create_app()
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
