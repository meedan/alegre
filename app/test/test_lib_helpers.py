import unittest

from app.test.base import BaseTestCase
from app.main.lib.helpers import context_matches

class TestHelpersBlueprint(BaseTestCase):
    def test_context_matches(self):
      self.assertTrue(context_matches({"has_custom_id":True,"team_id":1797}, {'team_id': 1797, 'has_custom_id': True, 'project_media_id': 872466}))
      self.assertTrue(context_matches({"has_custom_id":True,"team_id":[1797]}, {'team_id': 1797, 'has_custom_id': True, 'project_media_id': 872466}))
      self.assertFalse(context_matches({"has_custom_id":True,"team_id":1796}, {'team_id': 1797, 'has_custom_id': True, 'project_media_id': 872466}))
      self.assertFalse(context_matches({"has_custom_id":True,"team_id":[1796]}, {'team_id': 1797, 'has_custom_id': True, 'project_media_id': 872466}))
      self.assertTrue(context_matches({"has_custom_id":True,"team_id":[1796, 1797]}, {'team_id': 1797, 'has_custom_id': True, 'project_media_id': 872466}))
