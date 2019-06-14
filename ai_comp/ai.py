"""
This file contains the AI used in the game, which is called
during decision making procedure.
All AI procedure should ending up producing a valid option,
never an invalid one.
AI also possess information on the table to facilitate decision making.
AI should output the card play as int, and the actual Card is played in the Player class
AI possesses the table knowledge and the hand
AI should not modify the player cards and table data. They are read only.
"""
import random
import cards


class BaseAI:
    """
    A base class for AI implementation.
    """
    def __init__(self, table_status, player=None):
        self.player = player
        self.table_status = table_status

    def connect_to_player(self, player):
        self.player = player

    def request_reshuffle(self):
        pass

    def make_a_bid(self):
        pass

    def call_partner(self):
        pass

    def make_a_play(self, sub_state):
        pass

    def get_valid_plays(self, leading):
        all_plays = self.player.get_deck_values()
        possible_plays = None
        if leading:
            if not self.table_status['trump broken']:
                possible_plays = [card for card in all_plays
                                  if not cards.get_card_suit(card) == self.table_status['trump suit']]
        else:
            leading_suit = self.table_status['played cards'][self.table_status["leading player"]].suit()
            possible_plays = [card for card in all_plays
                              if cards.get_card_suit(card) == leading_suit]

        if not possible_plays:
            return all_plays
        return possible_plays


class RandomAI(BaseAI):
    def request_reshuffle(self):
        if random.randint(0, 1):
            return True
        return False

    def make_a_bid(self):
        if self.player:
            current_round_bid = self.table_status["bid"] // 10
            current_suit_bid = self.table_status["bid"] % 10
            bid_threshold = int(current_round_bid*1.5 + current_suit_bid*0.5)
            gen_bid = random.randint(0, bid_threshold)
            print(gen_bid)
            if gen_bid <= 1:
                if current_suit_bid == 5:
                    return (current_round_bid+1)*10 + 1
                else:
                    return self.table_status["bid"]+1

    def call_partner(self):
        player_cards = self.player.get_deck_values()
        other_cards = []
        for i in range(4):
            for j in range(13):
                current_card = (i + 1) * 100 + j + 2
                if current_card not in player_cards:
                    other_cards.append(current_card)
        return random.choice(other_cards)

    def make_a_play(self, sub_state):
        if sub_state == 0:
            valid_plays = self.get_valid_plays(True)
        else:
            valid_plays = self.get_valid_plays(False)

        return random.choice(valid_plays)


class VivianAI(BaseAI):

    def __init__(self, table_status, player=None):
        super().__init__(table_status, player=None)
