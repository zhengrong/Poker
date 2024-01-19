from unittest import TestCase

import pytest

import logging
import os
from PIL import Image
#from poker.scraper2.gg_table import GGTable
class TestGGTable(TestCase):
    def init_table(self, screenshot_file):
        # LOG_FILENAME = 'testing.log'
        logger = logging.getLogger('tester')
 #       t = GGTable(p, {}, 0.0)

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        adjusted_path = os.path.join(current_file_dir, 'screenshots', screenshot_file)
        t.entireScreenPIL = Image.open(adjusted_path)
        return t

    def test1(self):
        print('hello')