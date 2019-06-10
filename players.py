import cards
import pprint
from game_consts import GameState, PlayerRole, STARTING_HAND


class Player(cards.Deck):
    """
    A player is essentially a Deck with decision making function or AI component if it is a bot
    that returns a valid action for the Table/Board.

    The player has the knowledge of Table status in the form of a dictionary (as it is mutable, thus passed by ref)
    so all validation is done by the player

    Possible decisions, each decision has to be enum maybe:
    - Query the board status (i.e. current round, player status), AI most likely need a lot more
    - Query the last round
    - Attempt to play a card
    - Play the validate move

    The player also implements method to play from the terminal
    if it is not a bot.

    """
    def __init__(self, *args, ai_component=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.role = PlayerRole.UNKNOWN
        self.AI = ai_component
        self._table_status = None  # This is found in Table and updated through Table
        self.score = 0

    def connect_to_table(self, table):
        self._table_status = table

    def add_ai(self, ai_comp):
        self.AI = ai_comp
        ai_comp.connect_to_player(self)

    def make_decision(self, game_state, sub_state):
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
            if input("Reshuffle? (y/n)").lower() == 'y':
                return self.request_reshuffle()
        if game_state == GameState.BIDDING:
            if sub_state == 0:
                if self.AI:
                    return self.AI.make_a_bid()
                return self.make_a_bid()
            else:
                if self.AI:
                    return self.AI.call_partner()
                return self.call_partner()
        if game_state == GameState.PLAYING:
            if self.AI:
                play = self.AI.make_a_play(sub_state)
                [_, pos] = self.check_card_in(play)
                return self.remove_card(pos)
            return self.make_a_play(sub_state)

    def make_a_bid(self):
        """
        The procedure to make a bid
        :return: A valid bid number
        """
        while True:
            bid = input("Please input a bid in the format 'number' + 'suit' \n"
                        "To pass, enter nothing. \n"
                        "e.g 4d is 4 Diamond, 6n is 6 No Trump \n")

            if not bid:
                return 0

            bid = cards.convert_bid_string(bid)
            if bid < 0:
                print("Error in processing bid")
                continue

            if self._table_status["bid"] < bid:
                return bid
            else:
                if bid > 75:
                    print("You cannot bid beyond 7 No Trump")
                else:
                    print("You might need to bid higher")

    def call_partner(self):
        """
        The procedure to call a partner
        :return: A valid card value
        """
        current_card_values = self.get_deck_values()
        while True:
            partner = input("Please call your partner card. Enter card number + suit number \n"
                            "e.g. qs is Queen Spade, 8c is 8 Clubs, ah is Ace Hearts\n")

            partner = cards.convert_input_string(partner)
            if partner in current_card_values:
                print("Please call a card outside of your hand")
            elif cards.card_check(partner):
                return partner
            else:
                print("Invalid card call")

    def make_a_play(self, substate):
        """
        The procedure to make a play in a round
        :return: A valid Card
        """
        while True:
            play = input("Please play a card.Enter card number + suit number \n"
                         "e.g. qs is Queen Spade, 8c is 8 Clubs, ah is Ace Hearts\n")
            if play == "v":
                pprint.pprint(self._table_status)
            else:
                play = cards.convert_input_string(play)
                if play > 0:
                    if substate == 0:
                        valid = self.check_for_valid_plays(play, True)
                    else:
                        valid = self.check_for_valid_plays(play, False)

                    if valid:
                        [_, pos] = self.check_card_in(play)
                        return self.remove_card(pos)

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
        suit_points = 0
        card_points = []
        current_suit = 1
        card_position = 0
        for (i, card) in enumerate(self.cards):
            if card.suit() != current_suit:
                suit_points += (i-card_position) // 5
                card_position = i
                current_suit = card.suit()
            card_points.append(max(0, card.number() - 10))
        suit_points += (STARTING_HAND-card_position) // 5
        return suit_points + sum(card_points)

    def request_reshuffle(self):
        # Players can choose NOT to reshuffle
        # But always reshuffle for simplicity
        return True


class MainPlayer(Player):
    def __init__(self, *args, ai_component=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.AI = ai_component
        self.table_status = None  # This is found in Table and updated through Table
        self.selectable = True

    def make_a_play(self):
        pass


