import pygame
import cards
import view
import random
import copy
import time
import pprint
from signalslot import Signal
from ai_comp import ai
from enum import Enum

NUM_OF_PLAYERS = 4
STARTING_HAND = 13
HIGHEST_CARD = 414
LOWEST_CARD = 102
VIEW_TRANSPARENT = False

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

    def __init__(self, x, y, width, height, clear_colour, autoplay=False):
        # TODO: Reduce the amount of update_table call
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.table_font = pygame.font.SysFont("None", 30)
        self.player_font = pygame.font.SysFont("None", 30)

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

        w_deck = min(self.height, self.width) * 0.18
        l_deck = min(self.width, self.height) * 0.7
        # This is not a deck as it will never be drawn
        self.discard_deck = cards.prepare_playing_cards(int(w_deck*0.7), int(w_deck*0.9))

        playerx = ((self.width - l_deck)//2,
                   0,
                   (self.width - l_deck)//2,
                   self.width - w_deck)
        playery = (self.height - w_deck,
                   (self.height - l_deck)//2,
                   0,
                   (self.height - l_deck)//2)

        spacing = 20

        playfield_margins = 10
        margins_with_w_deck = w_deck + playfield_margins
        playfield_x = margins_with_w_deck
        playfield_y = margins_with_w_deck
        playfield_width = self.width - margins_with_w_deck * 2
        playfield_height = self.height - margins_with_w_deck * 2

        playdeckx = (playfield_x + (playfield_width - margins_with_w_deck) // 2,
                     playfield_x,
                     playfield_x + (playfield_width - margins_with_w_deck) // 2,
                     playfield_x + playfield_width - margins_with_w_deck)
        playdecky = (playfield_y + playfield_height - margins_with_w_deck,
                     playfield_y + (playfield_height - margins_with_w_deck) // 2,
                     playfield_y,
                     playfield_y + (playfield_height - margins_with_w_deck) // 2)

        stats_width = 100
        self.stats_height = 100
        stats_spacing = 10
        self.player_stats_x = (playdeckx[0] - stats_width - stats_spacing,
                               playdeckx[1],
                               playdeckx[2] + w_deck + stats_spacing,
                               playdeckx[3])
        self.player_stats_y = (playdecky[0] + w_deck - self.stats_height,
                               playdecky[1] - self.stats_height - stats_spacing,
                               playdecky[2],
                               playdecky[3] + w_deck + stats_spacing)

        self.player_stats = [[], [], [], []]

        for i in range(4):
            vert = i % 2 == 1
            self.players.append(Player(playerx[i], playery[i],
                                       l_deck, w_deck,
                                       spacing, vert_orientation=vert,
                                       deck_reveal=cards.DeckReveal.HIDE_ALL))
            self.players[i].connect_to_table(self.table_status)
            if i > 0:
                self.players[i].add_ai(ai.RandomAI(self.table_status))

            self.players_playzone.append(cards.Deck(playdeckx[i], playdecky[i],
                                         w_deck, w_deck, 0))
            for j in range(3):
                surf = pygame.Surface((stats_width, self.stats_height / 3), pygame.SRCALPHA)
                rendered_text = self.player_font.render("Player {0:d}".format(i), True,
                                                        (255, 0, 255)).convert_alpha()
                self.center_text_on_surface(surf, rendered_text,
                                            (255, 255, 255, 255 * VIEW_TRANSPARENT))
                self.player_stats[i].append(surf)
        if autoplay:
            self.players[0].add_ai(ai.RandomAI(self.table_status))
        announcer_margins = 5
        announcer_spacing = announcer_margins + w_deck
        self.announcer_x = playfield_x + announcer_spacing
        self.announcer_y = playfield_y + announcer_spacing
        self.announcer_width = playfield_width - 2 * announcer_spacing
        self.announcer_height = playfield_height - 2 * announcer_spacing
        self.announcer_line = []
        for i in range(3):
            surf = pygame.Surface((self.announcer_width, self.announcer_height/3), pygame.SRCALPHA)
            self.announcer_line.append(surf)

        self.update_all_players(role=True, wins=True)

        self.write_message("Press P to play!")

        self.ongoing = False

    def center_text_on_surface(self, surf, rendered_text, clear_colour):
        line_center = surf.get_rect().center
        text_rect = rendered_text.get_rect(center=line_center)
        surf.fill(clear_colour)
        surf.blit(rendered_text, text_rect)

    def write_message(self, text, delay_time=0.5, line=0, update_now=True):
        """
        Write a message into the center board surface (announcer)
        :param text: String to be displayed on the center board
        :param delay_time: How much delay to put once the string is display
        :param line: Which line of the announcer to write to
        :return: None
        """
        if 0 <= line < len(self.announcer_line):
            print(text)
            text = text.strip('\n')
            rendered_text = self.table_font.render(text, True, (255, 255, 255)).convert_alpha()
            self.center_text_on_surface(self.announcer_line[line], rendered_text,
                                        (255, 255, 255, 255*VIEW_TRANSPARENT))
            if update_now:
                self.update_table.emit()
                time.sleep(delay_time)

    def update_players_role(self, player_num, update_now=True):
        self.player_stats[player_num][1].fill((255, 255, 255, 255*VIEW_TRANSPARENT))
        if self.players[player_num].role == PlayerRole.DEFENDER:
            rendered_text = self.player_font.render("Defender", True, (0, 64, 192)).convert_alpha()
            self.center_text_on_surface(self.player_stats[player_num][1], rendered_text,
                                        (255, 255, 255, 255 * VIEW_TRANSPARENT))
        elif self.players[player_num].role == PlayerRole.ATTACKER:
            rendered_text = self.player_font.render("Attacker", True, (192, 0, 0)).convert_alpha()
            self.center_text_on_surface(self.player_stats[player_num][1], rendered_text,
                                        (255, 255, 255, 255 * VIEW_TRANSPARENT))
        if update_now:
            self.update_table.emit()

    def update_player_wins(self, player_num, update_now=True):
        self.player_stats[player_num][2].fill((255, 255, 255, 255*VIEW_TRANSPARENT))
        if self.players[player_num].score > 1:
            rendered_text = self.player_font.render("Wins: {0:d}".format(self.players[player_num].score), True,
                                                    (255, 255, 255)).convert_alpha()
        else:
            rendered_text = self.player_font.render("Win: {0:d}".format(self.players[player_num].score), True,
                                                    (255, 255, 255)).convert_alpha()
        self.center_text_on_surface(self.player_stats[player_num][2], rendered_text,
                                    (255, 255, 255, 255 * VIEW_TRANSPARENT))
        if update_now:
            self.update_table.emit()

    def update_all_players(self, role=False, wins=True):
        for i in range(4):
            if wins:
                self.update_player_wins(i, update_now=False)
            if role:
                self.update_players_role(i, update_now=False)
        self.update_table.emit()

    def display_current_player(self, current=-1):
        if current >= 0:
            print("Player {0:d}\n".format(current))
        for i in range(4):
            rendered_text = self.player_font.render("Player {0:d}".format(i), True,
                                                    (255, 0, 255)).convert_alpha()
            if i == current:
                self.center_text_on_surface(self.player_stats[i][0], rendered_text,
                                            (0, 64, 0, 255))
            else:
                self.center_text_on_surface(self.player_stats[i][0], rendered_text,
                                            (255, 255, 255, 255 * VIEW_TRANSPARENT))

        self.update_table.emit()

    def update_team_scores(self):
        if self.table_status['partner reveal']:
            msg = "Defender: {0:d}/{2:d}, Attacker: {1:d}/{3:d}\n".format(self.table_status['defender']['wins'],
                                                                          self.table_status['attacker']['wins'],
                                                                          self.table_status['defender']['target'],
                                                                          self.table_status['attacker']['target'])
            self.write_message(msg, line=2)
        else:
            msg = "Defender: {0:d}?/{1:d}, Attacker: ?/{2:d}\n".format(self.table_status['defender']['wins'],
                                                                       self.table_status['defender']['target'],
                                                                       self.table_status['attacker']['target'])
            self.write_message(msg, line=2)

    def get_pos(self):
        return self.x, self.y

    def continue_game(self):
        """
        This is where the FSM is. State transition should occur here.
        What takes place in the state should be in a function.
        :return: None
        """
        # TODO: Adjust the timing of sleep
        if self.game_state == GameState.DEALING:
            self.shuffle_and_deal()
            self.write_message("Shuffle Complete!")
            self.game_state = GameState.POINT_CHECK

        elif self.game_state == GameState.POINT_CHECK:
            if self.check_reshuffle():
                self.write_message('Reshuffle Initiated!')
                self.game_state = GameState.ENDING
            else:
                self.write_message('No Reshuffle needed!')
                self.game_state = GameState.BIDDING

        elif self.game_state == GameState.BIDDING:
            self.write_message("Start to Bid")
            self.start_bidding()
            self.game_state = GameState.PLAYING

        elif self.game_state == GameState.PLAYING:
            self.update_all_players(role=True, wins=True)
            self.update_team_scores()
            while self.current_round < 13:
                self.play_a_round()
                self.current_round += 1
            self.write_message("Game Set! Press P to play again!")
            self.ongoing = False
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
        print("Player Point Count")
        for i, player in enumerate(self.players):
            print("Player {0:d}: {1:d}".format(i, player.get_card_points()))
            if player.get_card_points() < 4:
                print("Player: {0:d}".format(i))
                return player.make_decision(self.game_state, 0)

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
        msg = "Current Bid: {0:d} {1:s}".format(self.table_status["bid"] // 10,
                                                cards.get_suit_string(self.table_status["bid"] % 10))
        self.write_message(msg, line=1, delay_time=0)
        msg = 'Bid Leader: Player {0:d}'.format((current_player - passes - 1 * (not first_player)) % 4)
        self.write_message(msg, line=2)
        self.display_current_player(current_player)

        while passes < NUM_OF_PLAYERS - 1:
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
            msg = "Current Bid: {0:d} {1:s}".format(self.table_status["bid"] // 10,
                                                    cards.get_suit_string(self.table_status["bid"] % 10))
            self.write_message(msg, line=1, update_now=False)
            msg = 'Bid Leader: Player {0:d}'.format((current_player - passes - 1 * (not first_player)) % 4)
            self.write_message(msg, line=2, update_now=False)
            self.display_current_player(current_player)
            time.sleep(1)

        self.write_message("Player {0:d} is the bid winner!".format(current_player), delay_time=1.5)

        self.display_current_player(current_player)
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
            self.table_status["leading player"] = (current_player + 1) % 4
        self.table_status['defender']['target'] = self.table_status["bid"] // 10 + 6
        self.table_status['attacker']['target'] = 14 - self.table_status['defender']['target']

        # Set the roles of the players
        self.players[current_player].role = PlayerRole.DEFENDER

        self.write_message('Bidding Complete')
        msg = 'Trump: {1:s}, Partner: {0:s}'.format(cards.get_card_string(self.table_status["partner"]),
                                                    cards.get_suit_string(self.table_status['trump suit']))
        self.write_message(msg, line=1)

    def play_a_round(self):
        """
        Ask each player to play a valid card and determine the winner of the round
        :return: None
        """
        # Leading player starts with the leading card, which determines the leading suit
        current_player = self.table_status['leading player']
        self.display_current_player(current_player)
        leading_card = self.players[current_player].make_decision(self.game_state, 0)
        self.table_status["played cards"][current_player] = leading_card
        self.players_playzone[current_player].add_card(leading_card)
        self.update_table.emit()
        time.sleep(0.5)
        if not self.table_status['partner reveal']:
            if leading_card.value == self.table_status['partner']:
                self.table_status['partner reveal'] = True
                self.write_message("Partner Revealed!", delay_time=1)
                self.reveal_all_roles(current_player)
                self.update_all_players(role=True, wins=False)
        # Subsequent player make their plays, following suit if possible
        for _ in range(3):
            current_player += 1
            current_player %= 4
            self.display_current_player(current_player)
            print("Player {0:d}\n".format(current_player))
            card = self.players[current_player].make_decision(self.game_state, 1)
            self.players_playzone[current_player].add_card(card)
            self.table_status["played cards"][current_player] = card

            # Reveal the roles once the partner card is played
            if not self.table_status['partner reveal']:
                if card.value == self.table_status['partner']:
                    self.table_status['partner reveal'] = True
                    self.write_message("Partner Revealed!", delay_time=1)
                    self.reveal_all_roles(current_player)
                    self.update_all_players(role=True, wins=False)
            self.update_table.emit()
            time.sleep(0.5)

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
                self.write_message("Trump Broken!", delay_time=1)

        # Determine which players to check for winner, and determine winner
        valid_nums = [card_nums[i] * ((follow_suits[i] and not trump_played) or trumps[i]) for i in range(4)]
        winning_player = valid_nums.index(max(valid_nums))
        self.write_message("Player {0:d} wins!\n".format(winning_player), delay_time=1)
        self.players[winning_player].score += 1
        self.update_player_wins(winning_player)

        # Clean up the cards, update score, set the next leading player, update round history
        for deck in self.players_playzone:
            self.discard_deck.append(deck.remove_card())

        if self.players[winning_player].role == PlayerRole.DEFENDER:
            self.table_status['defender']['wins'] += 1
        elif self.players[winning_player].role == PlayerRole.ATTACKER:
            self.table_status['attacker']['wins'] += 1

        self.table_status['leading player'] = winning_player
        self.table_status['round history'].append(copy.copy(self.table_status["played cards"]))
        self.update_team_scores()

        # TODO: Add function to reflect the score on the screen. Kinda added

        self.update_table.emit()

    def reveal_all_roles(self, partner):
        self.players[partner].role = PlayerRole.DEFENDER
        self.table_status['defender']['wins'] += self.players[partner].score
        for i in range(4):
            if self.players[i].role == PlayerRole.UNKNOWN:
                self.players[i].role = PlayerRole.ATTACKER
                self.table_status['attacker']['wins'] += self.players[i].score

    def reset_game(self):
        for player in self.players:
            while not player.is_empty():
                self.discard_deck.append(player.remove_card())
            player.score = 0
            player.role = PlayerRole.UNKNOWN

        for i in range(4):
            self.update_players_role(i)
            self.update_player_wins(i)
        self.table_status['defender']['wins'] = 0
        self.table_status['attacker']['wins'] = 0
        self.current_round = 0
        self.write_message("", line=1, update_now=False)
        self.write_message("", line=2)
        self.display_current_player()
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
            if input("Low points hand detected! Reshuffle?").lower() == 'y':
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
            # TODO: Make a more natural input parsing
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
            # TODO: Make a more natural input parsing
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

    def make_a_play(self, substate):
        """
        The procedure to make a play in a round
        :return: A valid Card
        """
        while True:
            # TODO: Make a more natural input parsing
            play = input("Please play a card. Enter suit number + card number\n"
                         "i.e 412 is Spade Queen, 108 is Clubs 8, 314 is Hearts Ace\n")
            if play == "v":
                pprint.pprint(self._table_status)
            else:
                play = int(play)
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


class MainPlayer(cards.PlayerDeck):
    def __init__(self, *args, ai_component=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.AI = ai_component
        self.table_status = None  # This is found in Table and updated through Table

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

            # milliseconds = self.clock.tick(self.fps)
            # self.playtime += milliseconds / 1000.0

            # self.draw_function()

        pygame.quit()


if __name__ == '__main__':
    test_view = TestView(900, 600, clear_colour=(0, 0, 0))
    test_view.run()
