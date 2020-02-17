import unittest
import json
from flask import current_app as app
import numpy as np
from PIL import Image

from app.main import db, ds
from app.test.base import BaseTestCase
from app.main.lib.imagehash import compute_phash_int

class TestImageSimilaryBlueprint(BaseTestCase):
  def test_image_phash(self):
    im1 = Image.open('./app/test/data/lenna-512.jpg').convert('RGB')
    p1 = compute_phash_int(im1)
    im2 = Image.open('./app/test/data/lenna-512.png').convert('RGB')
    p2 = compute_phash_int(im2)
    self.assertEqual(p1, p2)


if __name__ == '__main__':
  unittest.main()
