import cards
import pprint
#import pygame
from game_consts import GameState, PlayerRole, STARTING_HAND


ip = "localhost"
port = 5555

class Player():
    """
    """
    def __init__(self, ai_component=None):
        self.role = PlayerRole.UNKNOWN
        self.AI = ai_component
        self._table_status = None  # This is found in Table and updated through Table
        self.score = 0
        self.cards = []

    def connect_to_table(self, table):
        self._table_status = table

    def add_ai(self, ai_comp):
        self.AI = ai_comp
        ai_comp.connect_to_player(self)
        self.selectable = False
    
    def add_card(self, value):
        self.cards.append(value)
    
    def remove_card(self):
        return self.cards.pop()

    def make_decision(self, game_state, sub_state, game_events=None):
        """
        The player will need to make a decision depending on the game state and sub-state
        :param game_state: Current game state
        :param sub_state: Sub-state which affects the output for the current game state
        :return: For Bidding: Either a bid or a partner call, int
                 For Playing: A Card
                 For Reshuffle: bool, True to reshuffle, False otherwise
        """
        if game_state == GameState.POINT_CHECK:
            if self.AI:
                return self.AI.request_reshuffle()
            return self.request_reshuffle(game_events=game_events)
        if game_state == GameState.BIDDING:
            if sub_state == 0:
                if self.AI:
                    return self.AI.make_a_bid()
                return self.make_a_bid(game_events=game_events)
            else:
                if self.AI:
                    return self.AI.call_partner()
                return self.call_partner(game_events=game_events)
        if game_state == GameState.PLAYING:
            if self.AI:
                play = self.AI.make_a_play(sub_state)
                [_, pos] = self.check_card_in(play)
                return self.remove_card(pos)
            return self.make_a_play(sub_state, game_events=game_events)

    def make_a_bid(self, game_events=None):
        """
        The procedure to make a bid
        :return: A valid bid number
        """
        msg = ''
        while True:
            bid = input("Please input a bid in the format 'number' + 'suit' \n"
                        "To pass, enter nothing. \n"
                        "e.g 4d is 4 Diamond, 6n is 6 No Trump \n")

            if not bid:
                return 0, msg

            bid = cards.convert_bid_string(bid)
            if bid < 0:
                print("Error in processing bid")
                continue

            if self._table_status["bid"] < bid:
                return bid, msg
            else:
                if bid > 75:
                    print("You cannot bid beyond 7 No Trump")
                else:
                    print("You might need to bid higher")

    def call_partner(self, game_events=None):
        """
        The procedure to call a partner
        :return: A valid card value
        """
        current_card_values = self.get_deck_values()
        msg = ''
        while True:
            partner = input("Please call your partner card. Enter card number + suit number \n"
                            "e.g. qs is Queen Spade, 8c is 8 Clubs, ah is Ace Hearts\n")

            partner = cards.convert_input_string(partner)
            if partner in current_card_values:
                print("Please call a card outside of your hand")
            elif cards.card_check(partner):
                return partner, msg
            else:
                print("Invalid card call")

    def make_a_play(self, substate, game_events=None):
        """
        The procedure to make a play in a round
        :return: A valid Card
        """
        msg = ''
        while True:
            play = input("Please play a card.Enter card number + suit number \n"
                         "e.g. qs is Queen Spade, 8c is 8 Clubs, ah is Ace Hearts\n")
            #if play == "v":
            #    pprint.pprint(self._table_status)
            #else:
            play = cards.convert_input_string(play)
            if play > 0:
                valid = self.check_for_valid_plays(play, substate == 0)

                if valid:
                    [_, pos] = self.check_card_in(play)
                    return self.remove_card(pos), msg

                print("Invalid play")

    def view_last_round(self):
        pass

    def check_for_valid_plays(self, card, leading):
        """
        Check if the card played is valid
        :param card: int
        :param leading: bool
        :return:
        """
        if not self.check_card_in(card):
            return False
        card_suit = cards.get_card_suit(card)
        if leading:
            if not self._table_status['trump broken'] and \
                    card_suit == self._table_status['trump suit']:
                if any([not cards.get_card_suit(crd) == self._table_status['trump suit'] for crd in self.get_deck_values()]):
                    return False
        else:
            leading_card_suit = self._table_status['played cards'][self._table_status["leading player"]].suit()
            if not card_suit == leading_card_suit and \
                any([cards.get_card_suit(crd) == leading_card_suit for crd in
                    self.get_deck_values()]):
                return False

        return True

    def get_card_points(self):
        self.cards.sort()
        suit_points = 0
        card_points = []
        current_suit = 1
        card_position = 0
        for (i, card) in enumerate(self.cards):
            card_suit = cards.get_card_suit(card)
            card_num = cards.get_card_number(card)
            if card_suit != current_suit:
                suit_points += (i-card_position) // 5
                card_position = i
                current_suit = card_suit
            card_points.append(max(0, card_num - 10))
        suit_points += (STARTING_HAND-card_position) // 5
        return suit_points + sum(card_points)

    def request_reshuffle(self, game_events=None):
        # Players can choose NOT to reshuffle
        return input("Reshuffle? (y/n)").lower() == 'y'

    def is_empty(self):
        return len(self.cards) == 0

