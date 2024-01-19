from unittest import TestCase
import os

import cv2
import numpy as np
from PIL import Image
from poker2.scraper2.gg_table import GGTable
from tools.screen_operations import check_if_image_in_range, binary_pil_to_cv2


class TestGGTable(TestCase):
    def init_table(self, screenshot_file, i, j):

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        adjusted_path = os.path.join(current_file_dir, screenshot_file)
        entireScreenPIL = Image.open(adjusted_path)
        width = 1920
        height =  1080
        rows = 2
        cols = 3
        top_margin = 46
        bottom_margin = 94

        adjusted_height = height - top_margin - bottom_margin
        w = int(width / cols)
        h = 470
        cropped = entireScreenPIL.crop((j * w, top_margin + i * h, (j+1)*w, top_margin + (i+1)*h))

        cropped.save('tmp.png')
        t = GGTable('gg6max')
        t.set_image(cropped)
        return t

    def test_my_turn(self):
        table = self.init_table('screenshots/gg/WIN_20230728_20_51_55_Pro.jpg', 1, 2)
        assert table.is_my_turn() == True
        table = self.init_table('screenshots/gg/WIN_20230728_20_51_55_Pro.jpg', 1, 1)
        assert table.is_my_turn() == False

    def test_save_my_cards(self):
        filenames = next(os.walk('./screenshots/gg'), (None, None, []))[2]
        card1_template, card2_template = [], []
        count, count2  = 1, 1
        for filename in filenames:
            for i in range(2):
                for j in range(3):
                    table = self.init_table('screenshots/gg/' + filename, i, j)
                    if table.is_my_turn():
                        match = False
                        for template in card1_template:
                            template_cv2 = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
                            if check_if_image_in_range(template_cv2, table.screenshot, 280,351, 299, 389, False):
                                match = True
                                break
                        if match == False:
                            img = table.screenshot
                            card1 = img.crop((281,352, 298, 388))
                            card1.save('../../tmp/mycards/card1-' + str(count) + '.png')
                            count += 1
                            card1_template.append(card1)
                        match = False
                        for template in card2_template:
                            template_cv2 = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
                            if check_if_image_in_range(template_cv2, table.screenshot, 312,349, 332, 389, False):
                                match = True
                                break
                        if match == False:
                            img = table.screenshot
                            card2 = img.crop((314, 350, 329, 386))
                            card2.save('../../tmp/mycards/card2-' + str(count2) + '.png')
                            count2 += 1
                            card2_template.append(card2)

    def test_my_cards(self):
        table = self.init_table('screenshots/gg/WIN_20230728_20_51_55_Pro.jpg', 1, 2)
        assert table.is_my_turn() == True
        table.get_my_cards()
        assert table.my_cards == ['7S', '6H']

    def test_get_dealer_position(self):
        table = self.init_table('screenshots/gg/WIN_20230728_20_48_19_Pro.jpg', 1, 0)
        assert table.get_dealer_position() == True
        assert table.dealer_position == 5
        table = self.init_table('screenshots/gg/WIN_20230728_20_52_22_Pro.jpg', 1, 1)
        assert table.get_dealer_position() == True
        assert table.dealer_position == 2
        table = self.init_table('screenshots/gg/WIN_20230728_20_52_22_Pro.jpg', 0, 1)
        assert table.get_dealer_position() == True
        assert table.dealer_position == 1
        table = self.init_table('screenshots/gg/WIN_20230728_20_52_22_Pro.jpg', 0, 0)
        assert table.get_dealer_position() == True
        assert table.dealer_position == 0
        table = self.init_table('screenshots/gg/WIN_20230728_20_52_22_Pro.jpg', 1, 0)
        assert table.is_my_turn() == True
        assert table.get_dealer_position() == True
        assert table.dealer_position == 4
        table = self.init_table('screenshots/gg/WIN_20230728_20_52_22_Pro.jpg', 0, 2)
        assert table.is_my_turn() == True
        assert table.get_dealer_position() == True
        assert table.dealer_position == 3
        table = self.init_table('screenshots/gg/WIN_20230728_20_51_55_Pro.jpg', 1, 2)
        assert table.is_my_turn() == True
        assert table.get_dealer_position() == True
        assert table.dealer_position == 1
