from app.test.base import BaseTestCase
from app.main.lib.similarity_measures import (
  cosine_similarity,
  angular_similarity,
)

class TestSimilarityMeasures(BaseTestCase):
  def test_cosine_similarity(self):
    self.assertEqual(1, cosine_similarity([1,2,3], [1,2,3]))
    self.assertEqual(0, cosine_similarity([1,2,3], [0,0,0]))

  def test_angular_similarity(self):
    self.assertEqual(1, angular_similarity([1,2,3], [1,2,3]))

if __name__ == '__main__':
    unittest.main()
