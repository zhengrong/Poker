"""Recognize table"""
import json
import logging
import os

import PIL.Image

from poker.scraper.table_scraper_nn import predict
from poker.scraper.table_setup_actions_and_signals import CARD_SUITES, CARD_VALUES
from poker.tools.helper import get_dir
from poker.tools.screen_operations import is_template_in_search_area, binary_pil_to_cv2, ocr, \
    is_template_in_search_area2, is_template_in_search_area3

log = logging.getLogger(__name__)
import configparser

class TableScraper:
    def __init__(self, config_name):
        self.my_cards1_template = {}
        self.my_cards2_template = {}
        config = configparser.ConfigParser()
        config.read('../../config/' + config_name + '.ini')
        self.templates = {}
        for template in config.items('template'):
            img = PIL.Image.open('../../config/' + config['template'][template[0]])
            self.templates[template[0]] = img
        self.load_my_cards_template(config)

        self.table_dict = config
        self.screenshot = None

        self.total_players = 6
        self.my_cards = None
        self.table_cards = None
        self.current_round_pot = None
        self.total_pot = None
        self.dealer_position = None
        self.players_in_game = None
        self.player_funds = None
        self.player_pots = None
        self.call_value = None
        self.raise_value = None
        self.call_button = None
        self.raise_button = None
        self.tlc = None


    def lost_everything(self):
        """Check if lost everything has occurred"""
        return is_template_in_search_area(self.table_dict, self.screenshot,
                                          'lost_everything', 'lost_everything_search_area')

    def im_back(self):
        """Check if I'm back button is visible"""
        return is_template_in_search_area(self.table_dict, self.screenshot,
                                          'im_back', 'buttons_search_area')

    def resume_hand(self):
        """Check if I'm back button is visible"""
        return is_template_in_search_area(self.table_dict, self.screenshot,
                                          'resume_hand', 'buttons_search_area')

    def get_my_cards(self):
        """Get my cards"""
        self.my_cards = []

        for value in CARD_VALUES:
            for suit in CARD_SUITES:
                name = value.lower() + suit.lower()
                if name in self.my_cards1_template:
                    search_area = self.table_dict['main']['my_card1_area']
                    if is_template_in_search_area2(self.screenshot, self.my_cards1_template.get(name), search_area):
                        self.my_cards.append(value + suit)
        for value in CARD_VALUES:
            for suit in CARD_SUITES:
                name = value.lower() + suit.lower()
                if name in self.my_cards2_template:
                    search_area = self.table_dict['main']['my_card2_area']
                    if is_template_in_search_area2(self.screenshot, self.my_cards2_template.get(name), search_area):
                        self.my_cards.append(value + suit)

        if len(self.my_cards) != 2:
            log.warning("My cards not recognized")
        log.info(f"My cards: {self.my_cards}")


    def get_table_cards(self):
        """Get the cards on the table"""
        self.table_cards = []
        for value in CARD_VALUES:
            for suit in CARD_SUITES:
                if is_template_in_search_area(self.table_dict, self.screenshot,
                                              value.lower() + suit.lower(), 'table_cards_area'):
                    self.table_cards.append(value + suit)
        log.info(f"Table cards: {self.table_cards}")
        if len(self.table_cards) == 1 or len(self.table_cards) == 2:
            log.warning(f"Only recognized {len(self.table_cards)} cards on the table. "
                        f"This can happen if cards are sliding in or if some of the templates are wrong")
            return False
        return True

    def get_dealer_position(self):  # pylint: disable=inconsistent-return-statements
        """Determines position of dealer, where 3=myself, continous counter clockwise"""
        for i in range(self.total_players):
            template = self.templates['dealer_button' + str(i)]
            search_area = json.loads(self.table_dict['main']['button_search_area'].replace('\'', '\"'))
            if is_template_in_search_area3(self.screenshot, template, search_area[str(i)]):
                self.dealer_position = i
                log.info(f"Dealer found at position {i}")
                return True
        log.warning("No dealer found.")
        self.dealer_position = -1
        return False

    def fast_fold(self):
        """Find out if fast fold button is present"""
        return is_template_in_search_area(self.table_dict, self.screenshot,
                                          'fast_fold_button', 'my_turn_search_area')

    def is_my_turn(self):
        """Check if it's my turn"""
        my_turn = is_template_in_search_area2(self.screenshot,
                                          self.templates['my_turn_template'], self.table_dict['main']['my_turn_search_area'])
        log.info(f"Is it my turn? {my_turn}")
        return my_turn

    def get_players_in_game(self):
        """
        Get players in the game by checking for covered cards.

        Return: list of ints
        """
        self.players_in_game = [0]  # assume myself in game
        for i in range(1, self.total_players):
            if is_template_in_search_area(self.table_dict, self.screenshot,
                                          'covered_card', 'covered_card_area', str(i)):
                self.players_in_game.append(i)
        log.info(f"Players in game: {self.players_in_game}")
        return True

    def get_my_funds(self):
        self.get_players_funds(my_funds_only=True)

    def get_players_funds(self, my_funds_only=False, skip=[]):  # pylint: disable=dangerous-default-value
        """
        Get funds of players

        Returns: list of floats

        """
        if my_funds_only:
            counter = 1
        else:
            counter = self.total_players

        self.player_funds = []
        for i in range(counter):
            if i in skip:
                funds = 0
            else:
                funds = ocr(self.screenshot, 'player_funds_area', self.table_dict, str(i))
            self.player_funds.append(funds)
        log.info(f"Player funds: {self.player_funds}")
        return True

    def other_players_names(self):
        """Read other player names"""

    def get_pots(self):
        """Get current and total pot"""
        self.current_round_pot = ocr(self.screenshot, 'current_round_pot', self.table_dict, fast=True)
        log.info(f"Current round pot {self.current_round_pot}")
        self.total_pot = ocr(self.screenshot, 'total_pot_area', self.table_dict)
        log.info(f"Total pot {self.total_pot}")

    def get_player_pots(self, skip=[]):  # pylint: disable=dangerous-default-value
        """Get pots of the players"""
        self.player_pots = []
        for i in range(self.total_players):
            if i in skip:
                funds = 0
            else:
                funds = ocr(self.screenshot, 'player_pot_area', self.table_dict, str(i))
            self.player_pots.append(funds)
        log.info(f"Player pots: {self.player_pots}")

        return True

    def has_call_button(self):
        """Chek if call button is visible"""
        self.call_button = is_template_in_search_area(self.table_dict, self.screenshot,
                                                      'call_button', 'buttons_search_area')
        log.info(f"Call button found: {self.call_button}")
        return self.call_button

    def has_raise_button(self):
        """Check if raise button is present"""
        self.raise_button = is_template_in_search_area(self.table_dict, self.screenshot,
                                                       'raise_button', 'buttons_search_area')
        log.info(f"Raise button found: {self.raise_button}")
        return self.raise_button

    def has_bet_button(self):
        """Check if bet button is present"""
        self.bet_button = is_template_in_search_area(self.table_dict, self.screenshot,
                                                     'bet_button', 'buttons_search_area')
        log.info(f"Bet button found: {self.bet_button}")
        return self.bet_button

    def has_check_button(self):
        """Check if check button is present"""
        self.check_button = is_template_in_search_area(self.table_dict, self.screenshot,
                                                       'check_button', 'buttons_search_area')
        log.info(f"Check button found: {self.check_button}")
        return self.check_button

    def has_all_in_call_button(self):
        """Check if all in call button is present"""
        return is_template_in_search_area(self.table_dict, self.screenshot,
                                          'all_in_call_button', 'buttons_search_area')

    def get_call_value(self):
        """Read the call value from the call button"""
        self.call_value = ocr(self.screenshot, 'call_value', self.table_dict)
        log.info(f"Call value: {self.call_value}")
        if round(self.call_value) >= 90:
            log.warning("Correcting call value from >90")
            self.call_value -= 90
        return self.call_value

    def get_raise_value(self):
        """Read the value of the raise button"""
        self.raise_value = ocr(self.screenshot, 'raise_value', self.table_dict)
        log.info(f"Raise value: {self.raise_value}")
        if round(self.raise_value) >= 90:
            log.warning("Correcting raise value from >90")
            self.raise_value -= 90
        return self.raise_value

    def get_game_number_on_screen2(self):
        """Game number"""
        self.game_number = ocr(self.screenshot, 'game_number', self.table_dict)
        log.debug(f"Game number: {self.game_number}")
        return self.game_number

    def crop_image(self, original, left, top, right, bottom):
        # original.show()
        width, height = original.size  # Get dimensions
        cropped_example = original.crop((left, top, right, bottom))
        # cropped_example.show()
        return cropped_example

    def get_utg_from_abs_pos(self, abs_pos, dealer_pos):
        utg_pos = (abs_pos - dealer_pos + 4) % self.total_players
        return utg_pos

    def get_abs_from_utg_pos(self, utg_pos, dealer_pos):
        abs_pos = (utg_pos + dealer_pos - 4) % self.total_players
        return abs_pos

    def get_raisers_and_callers(self, p, reference_pot):
        first_raiser = np.nan
        second_raiser = np.nan
        first_caller = np.nan

        for n in range(5):  # n is absolute position of other player, 0 is player after bot
            i = (
                        self.dealer_position + n + 3 - 2) % 5  # less myself as 0 is now first other player to my left and no longer myself
            self.logger.debug("Go through pots to find raiser abs: {0} {1}".format(i, self.other_players[i]['pot']))
            if self.other_players[i]['pot'] != '':  # check if not empty (otherwise can't convert string)
                if self.other_players[i]['pot'] > reference_pot:
                    # reference pot is bb for first round and bot for second round
                    if np.isnan(first_raiser):
                        first_raiser = int(i)
                        first_raiser_pot = self.other_players[i]['pot']
                    else:
                        if self.other_players[i]['pot'] > first_raiser_pot:
                            second_raiser = int(i)

        first_raiser_utg = self.get_utg_from_abs_pos(first_raiser, self.dealer_position)
        highest_raiser = np.nanmax([first_raiser, second_raiser])
        second_raiser_utg = self.get_utg_from_abs_pos(second_raiser, self.dealer_position)

        first_possible_caller = int(self.big_blind_position_abs_op + 1) if np.isnan(highest_raiser) else int(
            highest_raiser + 1)
        self.logger.debug("First possible potential caller is: " + str(first_possible_caller))

        # get first caller after raise in preflop
        for n in range(first_possible_caller, 5):  # n is absolute position of other player, 0 is player after bot
            self.logger.debug(
                "Go through pots to find caller abs: " + str(n) + ": " + str(self.other_players[n]['pot']))
            if self.other_players[n]['pot'] != '':  # check if not empty (otherwise can't convert string)
                if (self.other_players[n]['pot'] == float(
                        p.selected_strategy['bigBlind']) and not n == self.big_blind_position_abs_op) or \
                        self.other_players[n]['pot'] > float(p.selected_strategy['bigBlind']):
                    first_caller = int(n)
                    break

        first_caller_utg = self.get_utg_from_abs_pos(first_caller, self.dealer_position)

        # check for callers between bot and first raiser. If so, first raiser becomes second raiser and caller becomes first raiser
        first_possible_caller = 0
        if self.position_utg_plus == 3: first_possible_caller = 1
        if self.position_utg_plus == 4: first_possible_caller = 2
        if not np.isnan(first_raiser):
            for n in range(first_possible_caller, first_raiser):
                if self.other_players[n]['status'] == 1 and \
                        not (self.other_players[n]['utg_position'] == 5 and p.selected_strategy['bigBlind']) and \
                        not (self.other_players[n]['utg_position'] == 4 and p.selected_strategy['smallBlind']) and \
                        not (self.other_players[n]['pot'] == ''):
                    second_raiser = first_raiser
                    first_raiser = n
                    first_raiser_utg = self.get_utg_from_abs_pos(first_raiser, self.dealer_position)
                    second_raiser_utg = self.get_utg_from_abs_pos(second_raiser, self.dealer_position)
                    break

        self.logger.debug("First raiser abs: " + str(first_raiser))
        self.logger.info("First raiser utg+" + str(first_raiser_utg))
        self.logger.debug("Second raiser abs: " + str(second_raiser))
        self.logger.info("Highest raiser abs: " + str(highest_raiser))
        self.logger.debug("First caller abs: " + str(first_caller))
        self.logger.info("First caller utg+" + str(first_caller_utg))

        return first_raiser, second_raiser, first_caller, first_raiser_utg, second_raiser_utg, first_caller_utg

    def derive_preflop_sheet_name(self, t, h, first_raiser_utg, first_caller_utg, second_raiser_utg):
        first_raiser_string = 'R' if not np.isnan(first_raiser_utg) else ''
        first_raiser_number = str(first_raiser_utg + 1) if first_raiser_string != '' else ''

        second_raiser_string = 'R' if not np.isnan(second_raiser_utg) else ''
        second_raiser_number = str(second_raiser_utg + 1) if second_raiser_string != '' else ''

        first_caller_string = 'C' if not np.isnan(first_caller_utg) else ''
        first_caller_number = str(first_caller_utg + 1) if first_caller_string != '' else ''

        round_string = '2' if h.round_number == 1 else ''

        sheet_name = str(t.position_utg_plus + 1) + \
                     round_string + \
                     str(first_raiser_string) + str(first_raiser_number) + \
                     str(second_raiser_string) + str(second_raiser_number) + \
                     str(first_caller_string) + str(first_caller_number)

        if h.round_number == 2:
            sheet_name = 'R1R2R1A2'

        self.preflop_sheet_name = sheet_name
        return self.preflop_sheet_name

    def load_my_cards_template(self, config):
        folder = config['main']['my_cards_folder']
        self.my_cards1_template = {}
        for value in CARD_VALUES:
            for suit in CARD_SUITES:
                file_name = '../../config/' + folder + '/card1-' + value.lower() + suit.lower() + '.png'
                if os.path.exists(file_name):
                    template = PIL.Image.open(file_name)
                    self.my_cards1_template[value.lower()+suit.lower()] = template
                file_name = '../../config/' + folder + '/card2-' + value.lower() + suit.lower() + '.png'
                if os.path.exists(file_name):
                    template = PIL.Image.open(file_name)
                    self.my_cards2_template[value.lower()+suit.lower()] = template
