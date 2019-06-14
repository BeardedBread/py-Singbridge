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
import math


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


class VivianAI(RandomAI):

    def __init__(self, table_status, player=None):
        super().__init__(table_status, player=player)

        self.weigh1 = 0.15
        self.weigh2 = 0.002

    def request_reshuffle(self):
        return True

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

    def estimate_wins(self):
        player_cards = self.player.get_deck_values()
        card_suits = [cards.get_card_suit(crd) for crd in player_cards]
        card_nums = [cards.get_card_number(crd) for crd in player_cards]

        n_cards = []
        for i in range(4):
            n_cards.append(card_suits.count(i))

        bids = [0] * 5
        trump_points = [num-10 if num >=10 else 0.001 for num in card_nums]
        non_trump_points = [self.calc_win_points(num, n_cards[suit]) if num >= 10 else 0.001
                            for (num, suit) in zip(card_nums, card_suits)]

        for trump_call in range(5):
            for suit in range(4):
                valid_cards = [crd_suit == suit for crd_suit in card_suits]
                if suit == trump_call:
                    points = sum([pts for valid, pts in zip(valid_cards, trump_points) if valid])
                    bids[trump_call] = points*n_cards[suit]
                else:
                    points = sum([pts for valid, pts in zip(valid_cards, non_trump_points) if valid])
                    bids[trump_call] = points*math.log(n_cards[suit]+1)

    def calc_win_points(self, card_num, n_cards):
        """
        Calculate the points which affects the bidding decision depending on which card is considered
        and the number of card available
        :param card_num: int 2-14
        :param n_cards: int
        :return: float score
        """

        num = min(0, card_num-10)

        if not n_cards:
            return 0

        if num <= n_cards:
            return math.exp(n_cards-1)-1

        return 19.167/n_cards







