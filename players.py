import pygame
import cards
import view
import random
import copy
from signalslot import Signal

from enum import Enum

NUM_OF_PLAYERS = 4
STARTING_HAND = 13
HIGHEST_CARD = 414
LOWEST_CARD = 102


class GameState(Enum):
    DEALING = 0
    POINT_CHECK = 1
    BIDDING = 2
    PLAYING = 3
    ENDING = 4

class PlayerRole(Enum):
    UNKNOWN = 0
    ATTACKER = 1
    DEFENDER = 2

class Table:
    """
    A Table is the place where all actions takes place. It is essentially a FSM, doing different
    routines at each state. It needs to keep track of the score, roles, and the rules. It needs
    to ask each player for decisions and respond to them accordingly. The table will also need
    to inform any decision to the Main Screen so that it can update the screen to reflect that
    change through the use of callbacks (Signal and Slot).

    FSM cycles
    ---
    Preloop - Prepare the cards once
            - Initiate Players and connect them to the Table
    1.  Shuffle and Deal out cards to Players.
    2a. Detect weak hands and ask for reshuffle.
    2b. Return to (1) if any reshuffle occurs, otherwise proceed.
    3.  Bidding round. Randomly pick a starting player, in clockwise manner
        ask for a bid until it is valid.
    3b. Proceed only if 3 consecutive skips are detected.
    3c. Ask the winner of the bid a card not in their hand.
    3d. Set up the player roles, trump suit, rounds to win for both side
    3e.  Play the game. Start with bid winner if NO TRUMP, otherwise
        Starting next to the bid winner.
    4a.  With the first player, ask for any card, excluding trump suits if trump
        is not broken
    4b. With subsequent players, ask for cards that follow the suit of the first player
        , include trump suit if trump is broken. Ask for any card if the player cannot
        follow suit.
    4c. Once all 4 players has made valid plays, announce results, update scoring. Announce
        player roles if the partner card is played. Break trump if trump is played.
    4d. Repeat 4 until 13 rounds are made. Maybe add early win if confirmed one side wins
    5.  Ask for a new game. Go back to 1 if true.

    All played cards go into a hidden discard pile.

    """
    update_table = Signal()

    def __init__(self, x, y, width, height, clear_colour):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # For gameplay
        self.game_state = GameState.DEALING
        self.current_round = 0
        self.players = []
        self.players_playzone = []
        # Table status will be made known to the player by reference
        self.table_status = {'played cards': [0, 0, 0, 0], 'leading player': 0, 'trump suit': 1,
                             'trump broken': False, 'round history': [], 'bid': 0, 'partner': 0,
                             'partner reveal': False, 'defender': {'target': 0, 'wins': 0},
                             'attacker': {'target': 0, 'wins': 0}}

        # Prepare the surfaces for displaying
        self.background = pygame.Surface((self.width, self.height))
        self.background.fill(clear_colour)
        self.background = self.background.convert()

        self.discard_deck = cards.prepare_playing_cards(50, 50)  # This is not a deck as it will never be drawn

        w_deck = min(self.height, self.width) * 0.15
        l_deck = min(self.width, self.height) * 0.7

        playerx = ((self.width - l_deck)//2,
                   0,
                   (self.width - l_deck)//2,
                   self.width - w_deck)
        playery = (self.height - w_deck,
                   (self.height - l_deck)//2,
                   0,
                   (self.height - l_deck)//2)

        spacing = 20

        for i in range(4):
            #if i == 0:
            #    self.players.append(MainPlayer(playerx[i], playery[i],
            #                                   l_deck, w_deck,
            #                                   spacing))
            #else:
            vert = i % 2 == 1
            self.players.append(Player(playerx[i], playery[i],
                                       l_deck, w_deck,
                                       spacing, vert_orientation=vert,
                                       deck_reveal=cards.DeckReveal.HIDE_ALL))
            self.players[i].connect_to_table(self.table_status)

        playfield_margins = 10
        margins_with_w_deck = w_deck + playfield_margins
        playfield_x = margins_with_w_deck
        playfield_y = margins_with_w_deck
        playfield_width = self.width - margins_with_w_deck* 2
        playfield_height = self.height - margins_with_w_deck* 2

        playdeckx = (playfield_x + (playfield_width - margins_with_w_deck) // 2,
                   playfield_x,
                   playfield_x + (playfield_width - margins_with_w_deck) // 2,
                   playfield_x + playfield_width - margins_with_w_deck)
        playdecky = (playfield_y + playfield_height - margins_with_w_deck,
                   playfield_y + (playfield_height - margins_with_w_deck) // 2,
                   playfield_y,
                   playfield_y + (playfield_height - margins_with_w_deck) // 2)
        for i in range(4):
            self.players_playzone.append(cards.Deck(playdeckx[i], playdecky[i],
                                           w_deck, w_deck, 0))

        announcer_margins = 5
        announcer_spacing = announcer_margins + w_deck
        self.announcer_x = playfield_x + announcer_spacing
        self.announcer_y = playfield_y + announcer_spacing
        announcer_width =  playfield_width - 2 * announcer_spacing
        announcer_height =  playfield_height - 2 * announcer_spacing
        self.announcer = pygame.Surface((announcer_width, announcer_height), pygame.SRCALPHA)
        self.table_font = pygame.font.SysFont("None", 30)
        self.write_message("Testing....")

    def write_message(self, text):
        """
        Write a message into the center board surface (announcer)
        :param text: String to be displayed on the center board
        :return: None
        """
        rendered_text = self.table_font.render(text, True, (255,0,0)).convert_alpha()
        self.announcer.blit(rendered_text, (50, 50))

    def get_pos(self):
        return self.x, self.y

    def start_game(self):
        """
        This is where the FSM is. State transition should occur here.
        What takes place in the state should be in a function.
        :return: None
        """
        #while(True):
        if self.game_state == GameState.DEALING:
            self.shuffle_and_deal()
            print("Shuffle Complete!")
            self.game_state = GameState.POINT_CHECK

        elif self.game_state == GameState.POINT_CHECK:
            if self.check_reshuffle():
                print('Reshuffle Initiated!')
                self.game_state = GameState.ENDING
            else:
                print('No Reshuffle needed!')
                self.game_state = GameState.BIDDING

        elif self.game_state == GameState.BIDDING:
            print("Start to Bid")
            self.start_bidding()
            self.game_state = GameState.ENDING

        elif self.game_state == GameState.PLAYING:
            while self.current_round < 14:
                self.play_a_round()
                self.current_round += 1
            self.game_state = GameState.ENDING
        else:
            self.reset_game()
            self.game_state = GameState.DEALING

    def shuffle_and_deal(self):
        """
        Shuffle and deal the discard deck to the players, which should have 52 cards.
        :return: None
        """
        if self.discard_deck:
            for i in range(10):
                random.shuffle(self.discard_deck)
            for player in self.players:
                for i in range(STARTING_HAND):
                    player.add_card(self.discard_deck.pop())
            self.update_table.emit()

    def check_reshuffle(self):
        """
        Detect any possible reshuffle request within the players
        :return: True if reshuffle requested, else False
        """
        for player in self.players:
            print(player.get_card_points())
            if player.get_card_points() < 4:
                if input("Reshuffle?").lower() == 'y':
                    return True

    def start_bidding(self):
        """
        The bidding procedure.
        :return:
        """
        # Randomly pick a starting player, whom also is the current bid winner
        current_player = random.randint(1, NUM_OF_PLAYERS) - 1
        print("Starting Player: {0:d}".format(current_player))
        passes = 0
        self.table_status["bid"] = 11  # Lowest Bid: 1 Club by default

        first_player = True  # Starting bidder "privilege" to raise the starting bid
        while passes < NUM_OF_PLAYERS - 1:
            print("Player {0:d}\n-----".format(current_player))
            print("Current Bid: {0:d}".format(self.table_status["bid"]))
            print('Bid Leader: Player {0:d}'.format((current_player-passes-1*(not first_player))% 4))
            print("Passes: {0:d}".format(passes))
            player_bid = self.players[current_player].make_decision(self.game_state, 0)
            if not player_bid:
                if not first_player:  # Starting bidder pass do not count at the start
                    passes += 1
            else:
                self.table_status["bid"] = player_bid
                passes = 0
                if player_bid == 75:  # Highest bid: 7 NoTrump. No further check required
                    break

            if first_player:
                first_player = False
            current_player += 1
            current_player %= 4

        print("Player {0:d} is the bid winner!".format(current_player))
        print("Player {0:d}\n-----".format(current_player))
        # Ask for the partner card
        self.table_status["partner"] = self.players[current_player].make_decision(self.game_state, 1)

        # Setup the table status before the play starts
        self.table_status['partner reveal'] = False
        self.table_status["trump suit"] = self.table_status["bid"] % 10
        self.table_status["trump broken"] = False
        self.table_status['played cards'] = [0, 0, 0, 0]
        if self.table_status['trump suit'] == 5:
            self.table_status["leading player"] = current_player
        else:
            self.table_status["leading player"] = current_player + 1
        self.table_status['defender']['target'] = self.table_status["bid"] // 10 + 6
        self.table_status['attacker']['target'] = 14 - self.table_status['defender']['target']

        # Set the roles of the players
        self.players[current_player].role = PlayerRole.DEFENDER
        for _ in range(3):
            current_player += 1
            current_player %= 4
            is_partner, _ = self.players[current_player].check_card_in(self.table_status["partner"])
            if is_partner:
                self.players[current_player].role = PlayerRole.DEFENDER
            else:
                self.players[current_player].role = PlayerRole.ATTACKER

        print('Bidding Complete')
        print(self.table_status)

    def play_a_round(self):
        """
        Ask each player to play a valid card and determine the winner of the round
        :return: None
        """
        # Leading player starts with the leading card, which determines the leading suit
        current_player = self.table_status['leading player']
        leading_card = self.players[current_player].make_decision(self.game_state, 0)
        self.table_status["played cards"][current_player] = leading_card.value
        self.players_playzone[current_player].add_card(leading_card)

        # Subsequent player make their plays, following suit if possible
        for _ in range(3):
            current_player += 1
            current_player %= 4
            card = self.players[current_player].make_decision(self.game_state, 1)
            self.players_playzone[current_player].add_card(card)
            self.table_status["played cards"][current_player] = card.value

            # Reveal the roles once the partner card is played
            if not self.table_status['partner reveal']:
                if card.value == self.table_status['partner']:
                    self.table_status['partner reveal'] = True

        # Once all player played, find out who wins
        card_suits = [card.suit() for card in self.table_status["played cards"]]
        card_nums = [card.number() for card in self.table_status["played cards"]]
        follow_suits = [suit == leading_card.suit() for suit in card_suits]
        trumps = [suit == self.table_status['trump suit'] for suit in card_suits]
        trump_played = any(trumps)
        # Break trump if the trump suit is played
        if not self.table_status['trump broken']:
            if trump_played:
                self.table_status['trump broken'] = True
        # Determine which players to check for winner, and determine winner
        valid_nums = [card_nums[i] * ((follow_suits[i] and not trump_played) or trumps[i]) for i in range(4)]
        winning_player = valid_nums.index(max(valid_nums))

        # Clean up the cards, update score, set the next leading player, update round history
        for deck in self.players_playzone:
            self.discard_deck.append(deck.remove_card())

        if winning_player.role == PlayerRole.DEFENDER:
            self.table_status['defender']['wins'] += 1
        else:
            self.table_status['attacker']['wins'] += 1

        self.table_status['leading player'] = winning_player
        self.table_status['round history'].append(copy.copy(self.table_status["played cards"]))

    def reset_game(self):
        # TODO: Reset the game
        for player in self.players:
            print(len(player.cards))
            while not player.is_empty():
                self.discard_deck.append(player.remove_card())
        print(len(self.discard_deck))
        self.update_table.emit()


class Player(cards.Deck):
    """
    A player is essentially a Deck with decision making function or AI component if it is a bot
    that returns a valid action for the Table/Board.

    The player has the knowledge of Table status in the form of a dictatary (as it is mutable, thus passed by ref)
    so all validation is done by the player

    Possible decisions, each decision has to be enum maybe:
    - Query the board status (i.e. current round, player status), AI most likely need a lot more
    - Query the last round
    - Attempt to play a card
    - Play the validate move

    """
    def __init__(self, *args, ai_component=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.role = PlayerRole.UNKNOWN
        self.AI = ai_component
        self._table_status = None # This is found in Table and updated through Table

    def connect_to_table(self, table):
        self._table_status = table

    def make_decision(self, game_state, sub_state):
        """
        The player will need to make a decision depending on the game state and sub-state
        :param game_state: Current game state
        :param sub_state: Sub-state which affects the output for the current game state
        :return: For Bidding: Either a bid or a partner call
                 For Playing: A Card
        """
        if game_state == GameState.BIDDING:
            if sub_state == 0:
                return self.make_a_bid()
            else:
                return self.call_partner()

    def make_a_bid(self):
        """
        The procedure to make a bid
        :return: A valid bid number
        """
        while True:
            bid = input("Please input a bid in the format 'number' + 'suit' \n"
                        "To pass, enter nothing. \n"
                        "i.e. 42 is 4 Diamond, 65 is 6 No Trump \n"
                        "Suit Number: 1-Club 2-Diamond 3-Hearts 4-Spades 5-NoTrump\n")

            if not bid:
                return 0
            try:
                bid = int(bid)
            except ValueError:
                print("Please enter integer only")
            if self._table_status["bid"] < bid and self.bid_check(bid):
                return bid
            else:
                if bid > 75:
                    print("You cannot bid beyond 7 No Trump")
                else:
                    print("Invalid bid")

    @staticmethod
    def bid_check(value):
        rounds = value // 10
        suit = value % 10
        return rounds <= 5 and 1 <= suit <= 5

    def call_partner(self):
        """
        The procedure to call a partner
        :return: A valid card value
        """
        current_card_values = self.get_deck_values()
        while True:
            partner = input("Please call your partner card. Enter suit number + card number\n"
                            "i.e 412 is Spade Queen, 108 is Clubs 8, 314 is Hearts Ace\n")
            try:
                partner = int(partner)
                if partner in current_card_values:
                    print("Please call a card outside of your hand")
                elif cards.card_check(partner):
                    return partner
                else:
                    print("Invalid card call")
            except ValueError:
                print("Please enter integer only")

    def make_a_play(self):
        """
        The procedure to make a play in a round
        :return: A valid Card
        """
        # TODO: Write the procedure of selecting a card
        return 1

    def view_last_round(self):
        pass

    def check_for_valid_plays(self):
        pass

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



class MainPlayer(cards.PlayerDeck):
    def __init__(self, *args, ai_component=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.AI = ai_component
        self.table_status = None # This is found in Table and updated through Table

    def connect_to_table(self, table):
        self.table_status = table

    def make_a_bid(self):
        pass

    def make_a_play(self):
        pass

    def view_last_round(self):
        pass

    def check_for_valid_moves(self):
        pass

class TestView(view.PygView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = Table(0, 0, self.width, self.height, (0, 0, 255))
        self.table.update_table.connect(self.draw_table)
        self.draw_table()

    def draw_table(self, **kwargs):
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.table.background, self.table.get_pos())
        for player in self.table.players:
            self.screen.blit(player.deck_surface, player.get_pos())
        for playerzone in self.table.players_playzone:
            self.screen.blit(playerzone.deck_surface, playerzone.get_pos())
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_p:
                        print('add cards')
                        pass

            milliseconds = self.clock.tick(self.fps)
            #self.playtime += milliseconds / 1000.0

            #self.draw_function()

        pygame.quit()



if __name__ == '__main__':
    test_view = TestView(900, 600, clear_colour=(0, 0, 0))
    test_view.run()