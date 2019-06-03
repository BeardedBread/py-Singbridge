"""
This file contains the AI used in the game, which is called
during decision making procedure.
All AI procedure should ending up producing a valid option,
never an invalid one.
AI also possess information on the table to facilitate decision making.
AI should output the card play as int, and the actual Card is played in the Player class
AI possesses the table knowledge and the hand
"""
import random

class randomAI:

    def __init__(self, table_status, player=None):
        self.player = player
        self.table_status = table_status

    def connect_to_player(self, player):
        self.player = player

    def get_valid_plays(self):
        pass

    def request_reshuffle(self):
        if random.randint(0, 1):
            return True
        return False

    def make_a_bid(self):
        if self.player:
            current_round_bid = self.table_status["bid"] // 10
            current_suit_bid = self.table_status["bid"] % 10
            gen_bid = random.randint(1, 7)*10 + random.randint(1, 5)
            if gen_bid > self.table_status["bid"]:
                if current_suit_bid == 5:
                    return (current_round_bid+1)*10 + 1
                else:
                    return self.table_status["bid"]+1

    def call_partner(self):
        pass

    def make_a_play(self, sub_state):
        pass