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

    def update_memory(self):
        return

    def reset_memory(self):
        return

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
        """

        :return: int - the bid
        """
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
        """

        :return: int - the card value
        """
        player_cards = self.player.get_deck_values()
        other_cards = []
        for i in range(4):
            for j in range(13):
                current_card = (i + 1) * 100 + j + 2
                if current_card not in player_cards:
                    other_cards.append(current_card)
        return random.choice(other_cards)

    def make_a_play(self, sub_state):
        """

        :param sub_state:
        :return: int - card value
        """
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

        self.bid_weigh = 0.3
        self.high_card_factor = 1.2
        self.low_suit_factor = 0.5
        self.trumping_factor = 2
        self.low_suit_factor = 0.5

        self.unplayed_cards = []
        [self.unplayed_cards.append([i+2 for i in range(13)]) for _ in range(4)]

    def request_reshuffle(self):
        return True

    def make_a_bid(self):
        # TODO: execute estimate_wins only once
        # Be careful when getting max_bid as it is 0-index but suits are 1-index
        est_wins = self.estimate_wins()
        max_est = max(est_wins)
        max_bid = [math.ceil(est)-3 for est in est_wins]
        favourable_suit = [i+1 for i, est in enumerate(est_wins) if est == max_est]
        if len(favourable_suit) > 1:
            favourable_suit = random.choice(favourable_suit)
        else:
            favourable_suit = favourable_suit[0]

        bid_num = self.table_status["bid"] // 10
        bid_suit = self.table_status["bid"] % 10
        if bid_suit == favourable_suit:
            if bid_num < max_bid[favourable_suit]:
                return 10 + self.table_status["bid"]
        else:
            loss_reward = self.bid_weigh*((8-bid_num)-(max_bid[bid_suit-1]+1))
            max_bid[favourable_suit-1] += int(loss_reward)
            next_bid_num = bid_num + 1 * (favourable_suit < bid_suit)
            if next_bid_num <= max_bid[favourable_suit-1]:
                return next_bid_num*10 + favourable_suit
        return 0

    def call_partner(self):
        """

        :return: int - the card value
        """
        player_cards = self.player.get_deck_values()
        card_suits = [cards.get_card_suit(crd) for crd in player_cards]
        card_nums = [cards.get_card_number(crd) for crd in player_cards]
        trump_suit = self.table_status["bid"] % 10
        trump_nums = [num for suit, num in zip(card_suits, card_nums) if suit == trump_suit]

        if 14 not in trump_nums:
            return trump_suit*100 + 14
        if 13 not in trump_nums:
            return trump_suit*100 + 13
        if 12 not in trump_nums:
            return trump_suit*100 + 12

        suit_values = []

        for i in range(4):
            suit_values.append(sum([num for suit, num in zip(card_suits, card_nums) if suit == i+1]))

        min_val = min(suit_values)
        weakest_suit = [i + 1 for i, val in enumerate(suit_values) if val == min_val]
        if len(weakest_suit) > 1:
            weakest_suit = random.choice(weakest_suit)
        else:
            weakest_suit = weakest_suit[0]

        all_nums = [i+2 for i in range(13)]
        weak_nums = [num for suit, num in zip(card_suits, card_nums) if suit == weakest_suit]
        [all_nums.remove(num) for num in weak_nums]
        return weakest_suit*100 + max(all_nums)

    def make_a_play(self, sub_state):
        """

        :param sub_state:
        :return: int - card value
        """
        # TODO: Recall last round and update memory

        # Get valid plays
        if sub_state == 0:
            card_values = self.get_valid_plays(True)
        else:
            card_values = self.get_valid_plays(False)

        n_cards = len(card_values)
        card_viability = [1] * n_cards
        card_nums = [cards.get_card_number(play) for play in card_values]
        card_suits = [cards.get_card_suit(play) for play in card_values]
        high_cards = [max(card_set) + (i+1)*100 if card_set else 0 for i, card_set in enumerate(self.unplayed_cards)]

        suit_counts = [0] * 4
        for i in range(4):
            suit_counts[i] = card_suits.count(i+1)

        non_empty_suits = [i+1 for i, count in enumerate(suit_counts) if count]
        suit_counts = [count for count in suit_counts if count]

        min_suit_count = min(suit_counts)
        low_suits = [suit for suit, counts in zip(non_empty_suits, suit_counts) if counts == min_suit_count]

        for i in range(n_cards):
            card_viability[i] += any([card_suits[i] == s for s in low_suits]) / min_suit_count * self.low_suit_factor

        # Leading-specific viability
        if sub_state == 0:
            for i in range(n_cards):
                card_viability[i] += any([card_values[i] == card for card in high_cards]) * self.high_card_factor
        else:
            # Get the played cards
            played_cards = [card.value if card else None for card in self.table_status["played cards"]]
            played_nums = [cards.get_card_number(card) if card else 0 for card in played_cards]
            played_suits = [cards.get_card_suit(card) if card else 0 for card in played_cards]
            leading_card = self.table_status["played cards"][self.table_status["leading player"]]
            leading_suit = leading_card.suit()

            # Find any trump cards
            #trumped = any([suit == self.table_status['trump suit'] for suit in played_suits])

            # Find the highest number played,
            max_played_num = max([num for num, suit in zip(played_nums, played_suits) if suit == leading_suit])
            max_trump_played = [num for suit, num in zip(played_suits, played_nums)
                                if suit == self.table_status['trump suit']]
            if max_trump_played:
                max_trump_played = max(max_trump_played)
            else:
                max_trump_played = 0

            for i in range(n_cards):
                # Favour highest cards
                card_viability[i] += (card_suits[i] == leading_suit and card_values[i] == high_cards[leading_suit-1]) \
                                     * self.high_card_factor

                # Favour low cards if trumped
                if max_trump_played > 0:
                    card_viability[i] -= card_nums[i]/7 * (card_suits[i] != self.table_status['trump suit'])

                # Favour low cards if cannot higher
                if max(card_nums) < max_played_num:
                    card_viability[i] += 1 / card_nums[i]

                # Favour low trump cards which wins if trumping is possible
                if card_suits[i] == self.table_status['trump suit'] and\
                        card_nums[i] > max_trump_played:
                    card_viability[i] += 1 / card_nums[i] * self.trumping_factor

        if self.table_status["partner reveal"]:
            # Not implemented as original
            pass

        best_viability = max(card_viability)
        best_cards = [play for viability, play in zip(card_viability, card_values) if viability == best_viability]
        return random.choice(best_cards)

    def update_memory(self):
        played_cards = [card.value for card in self.table_status["played cards"]]

        for val in played_cards:
            suit = cards.get_card_suit(val)
            num = cards.get_card_number(val)

            self.unplayed_cards[suit-1].remove(num)

    def reset_memory(self):
        self.unplayed_cards = []
        [self.unplayed_cards.append([i+2 for i in range(13)]) for _ in range(4)]

    def estimate_wins(self):
        player_cards = self.player.get_deck_values()
        card_suits = [cards.get_card_suit(crd) for crd in player_cards]
        card_nums = [cards.get_card_number(crd) for crd in player_cards]

        n_cards = []
        for i in range(4):
            n_cards.append(card_suits.count(i+1))

        bids = [0] * 5
        trump_points = [num-10 if num >= 10 else 0.001 for num in card_nums]
        non_trump_points = [self.calc_win_points(num, n_cards[suit-1]) if num > 10 else 0.001
                            for (num, suit) in zip(card_nums, card_suits)]

        for trump_call in range(5):
            for suit in range(4):
                valid_cards = [crd_suit == suit+1 for crd_suit in card_suits]
                if suit == trump_call:
                    points = sum([pts for valid, pts in zip(valid_cards, trump_points) if valid])
                    bids[trump_call] += points*n_cards[suit] * self.weigh1
                else:
                    points = sum([pts for valid, pts in zip(valid_cards, non_trump_points) if valid])
                    bids[trump_call] += points*math.log(n_cards[suit]+1) * self.weigh2

        return bids

    def calc_win_points(self, card_num, n_cards):
        """
        Calculate the points which affects the bidding decision depending on which card is considered
        and the number of card available
        :param card_num: int 2-14
        :param n_cards: int
        :return: float score
        """

        num = max(0, card_num-10)

        if not n_cards:
            return 0

        if num <= n_cards:
            return math.exp(n_cards-1)-1

        return 19.167/n_cards







