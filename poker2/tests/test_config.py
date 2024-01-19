import json
from unittest import TestCase
import configparser
class TestConfig(TestCase):
    def test_load_config(self):
        config = configparser.ConfigParser()
        config.read('../config/gg6max.ini')
        assert config['main']['table_name']
        player_funds = config['main']['player_funds_area']
        funds_area = json.loads(player_funds.replace('\'', '\"'))
        assert funds_area['0']

