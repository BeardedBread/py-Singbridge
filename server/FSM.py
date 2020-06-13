# STEP 1: Create a headless version, NO GRAPHICS
# STEP 1.5: You can do blocking calls
# Take it step-by-step: make sure one stage work first before going to the next
#
# STEP 2: Replace update_table with sending back to players
# STEP 3: Change write_message to send string back
import socket
import select
import threading
import sys
import players
from ai_comp import ai
from game_consts import GameState, PlayerRole, STARTING_HAND, NUM_OF_PLAYERS
import json

server = "localhost"
port = 5555

class Table():
    def __init__(self):
        # For gameplay
        self.game_state = GameState.ENDING
        self.reshuffling_players = []
        self.current_round = 0
        self.passes = 0
        self.current_player = 0
        self.first_player = False  # This is for bidding purposes
        self.players = []
        # Table status will be made known to the player by reference
        self.table_status = {'played cards': [0, 0, 0, 0], 'leading player': 0, 'trump suit': 1,
                             'trump broken': False, 'round history': [], 'bid': 0, 'partner': 0,
                             'partner reveal': False, 'defender': {'target': 0, 'wins': 0},
                             'attacker': {'target': 0, 'wins': 0}}
        
        for i in range(NUM_OF_PLAYERS):
            vert = i % 2 == 1

            self.players.append(players.Player())

            self.players[i].connect_to_table(self.table_status)
            if i > 0:
                self.players[i].add_ai(ai.VivianAI(self.table_status))

        self.discard_deck = self.prepare_playing_cards()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_players = []
        try:
            self.server.bind((server, port))
        except socket.error as e:
            str(e)

    def listening_for_players(self):
        self.server.listen()
        conn, addr = self.server.accept()
        conn.setblocking(False)
        print(addr, "Connected")
        self.connected_players.append(conn)
        response = {'msg': 'Please ready up'}
        conn.sendall(json.dumps(response).encode())

    def exit_game(self):
        for conn in self.connected_players:
            conn.close()

    def prepare_playing_cards(self):
        """
        Create the 52 playing cards. Should be called only once.
        """
        all_cards = []
        for i in range(4):
            for j in range(13):
                all_cards.append((i+1)*100 + j+2)
        return all_cards

    def play_game(self):
        """
        This is where the FSM is. State transition should occur here.
        What takes place in the state should be in a function.
        :return: None
        """
        while True:
            if self.game_state == GameState.DEALING:
                self.shuffle_and_deal()
                self.write_message("Shuffle Complete!")
                self.reshuffling_players = []
                for i, player in enumerate(self.players):
                    if player.get_card_points() < 4:
                        self.write_message("Low points detected in Player {0:d}! ".format(i))
                        self.reshuffling_players.append(i)

                if not self.reshuffling_players:
                    self.write_message('No Reshuffle needed!')
                    self.game_state = GameState.BIDDING
                    self.write_message("Start to Bid")
                    self.prepare_bidding()
                else:
                    self.current_player = self.reshuffling_players[0]
                    self.game_state = GameState.POINT_CHECK

            elif self.game_state == GameState.POINT_CHECK:
                reshuffle = self.check_reshuffle(game_events)
                if reshuffle:
                    self.write_message('Reshuffle Initiated!', line=1)
                    self.game_state = GameState.ENDING
                else:
                    self.write_message('No Reshuffle needed!')
                    self.game_state = GameState.BIDDING
                    self.write_message("Start to Bid")
                    self.prepare_bidding()

            elif self.game_state == GameState.BIDDING:
                bid_complete = self.start_bidding(game_events)
                if bid_complete:
                    self.game_state = GameState.PLAYING
                    self.update_all_players(role=True, wins=True)
                    self.update_team_scores()

            elif self.game_state == GameState.PLAYING:
                self.play_a_round(game_events)
                if self.current_round == 13:
                    self.declare_winner()
                    self.ongoing = False
                    self.game_state = GameState.ENDING
            else:
                ready = [False] * len(self.connected_players)
                while not all(ready):
                    replies, _, _ = select.select(self.connected_players,[],[])
                    for conn in replies:
                        data = conn.recv(1024).decode()
                        print(data)
                        if data == "ready":
                            num = self.connected_players.index(conn)
                            ready[num] = True
                print("All players ready!")
                self.reset_game()
                print(self.table_status, self.current_round)
                self.game_state = GameState.DEALING
                return

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

    def check_reshuffle(self, game_events):
        """
        Detect any possible reshuffle request within the players
        :return: True if reshuffle requested, else False
        """
        while(self.current_player == self.reshuffling_players[-1]):
            self.write_message("Do you want a reshuffle?", line=1, update_now=False)
            self.update_table.emit()
            reshuffle = self.players[self.current_player].make_decision(self.game_state, 0)

            if reshuffle:
                return True

            self.current_player = (self.current_player + 1)%NUM_OF_PLAYERS
            while self.current_player not in self.reshuffling_players:
                self.current_player = (self.current_player + 1) % NUM_OF_PLAYERS
        return False

    def prepare_bidding(self):
        # Randomly pick a starting player, whom also is the current bid winner
        self.current_player = random.randint(1, NUM_OF_PLAYERS) - 1
        print("Starting Player: {0:d}".format(self.current_player))
        self.passes = 0
        self.table_status["bid"] = 11  # Lowest Bid: 1 Club by default
        self.first_player = True  # Starting bidder "privilege" to raise the starting bid
        msg = "Current Bid: {0:d} {1:s}".format(self.table_status["bid"] // 10,
                                                cards.get_suit_string(self.table_status["bid"] % 10))
        self.write_message(msg, line=1, delay_time=0)
        self.display_current_player(self.current_player)
        msg = 'Bid Leader: Player {0:d}'.format((self.current_player - self.passes -
                                                 1 * (not self.first_player)) % NUM_OF_PLAYERS)
        self.write_message(msg, line=2, delay_time=0.5)

    def start_bidding(self, game_events):
        """
        The bidding procedure. Flag up if player input required
        :return: Whether bidding is completed
        """
        # Highest bid: 7 NoTrump. No further check required
        if self.passes < NUM_OF_PLAYERS - 1 and self.table_status["bid"] < 75:
            player_bid, msg = self.players[self.current_player].make_decision(self.game_state, 0)
            
            if msg:
                self.write_message(msg, delay_time=1, update_now=True)
            if player_bid < 0:
                return False
            self.write_message("", delay_time=0, update_now=False)
            if not player_bid:
                if not self.first_player:  # Starting bidder pass do not count at the start
                    self.passes += 1
            else:
                self.table_status["bid"] = player_bid
                self.passes = 0
                msg = "Current Bid: {0:d} {1:s}".format(self.table_status["bid"] // 10,
                                                        cards.get_suit_string(self.table_status["bid"] % 10))
                self.write_message(msg, line=1, update_now=False)
                msg = 'Bid Leader: Player {0:d}'.format(self.current_player)
                self.write_message(msg, line=2, update_now=True)

            if self.first_player:
                self.first_player = False

            if self.table_status["bid"] < 75:
                self.current_player += 1
                self.current_player %= NUM_OF_PLAYERS
            self.display_current_player(self.current_player)

        else:
            if not self.require_player_input:
                self.write_message("Player {0:d} is the bid winner!".format(self.current_player), delay_time=1)
                msg = "Player {0:d} is calling a partner...".format(self.current_player)
                self.write_message(msg, delay_time=1)
                self.display_current_player(self.current_player)
                while not partner:
                    partner, msg = self.players[self.current_player].make_decision(self.game_state, 1, game_events)
                if msg:
                    self.write_message(msg, delay_time=0, update_now=True)

                self.table_status["partner"] = partner

            # Setup the table status before the play starts
            self.table_status['partner reveal'] = False
            self.table_status["trump suit"] = self.table_status["bid"] % 10
            self.table_status["trump broken"] = False
            self.table_status['played cards'] = [0, 0, 0, 0]
            if self.table_status['trump suit'] == 5:
                self.table_status["leading player"] = self.current_player
            else:
                self.table_status["leading player"] = (self.current_player + 1) % NUM_OF_PLAYERS
            self.table_status['defender']['target'] = self.table_status["bid"] // 10 + 6
            self.table_status['attacker']['target'] = 14 - self.table_status['defender']['target']

            # Set the roles of the players
            self.players[self.current_player].role = PlayerRole.DECLARER

            self.write_message('Bidding Complete', delay_time=0)
            msg = 'Trump: {1:s}, Partner: {0:s}'.format(cards.get_card_string(self.table_status["partner"]),
                                                        cards.get_suit_string(self.table_status['trump suit']))
            self.write_message(msg, line=1, delay_time=1)
            return True

    def play_a_round(self, game_events):
        """
        Ask each player to play a valid card and determine the winner of the round
        This must work without pause if only bots are playing
        The function will exit after every player decision or if a user input is needed.
        If a user input is required, the function will continuously exit without proceeding to the next player
        until a valid input is received.

        :return: None
        """
        if not any(self.table_status["played cards"]):
            # Leading player starts with the leading card, which determines the leading suit
            if not self.require_player_input:
                if self.table_status['trump broken']:
                    self.write_message("Trump has been broken!", delay_time=0)
                else:
                    self.write_message("Trump is not broken", delay_time=0)
                self.current_player = self.table_status['leading player']
                self.display_current_player(self.current_player)
                if not self.players[self.current_player].AI:
                    self.require_player_input = True
                    return
                else:
                    card = self.players[self.current_player].make_decision(self.game_state, 0)
            else:
                card, msg = self.players[self.current_player].make_decision(self.game_state, 0, game_events)
                if msg:
                    self.write_message(msg, delay_time=0, update_now=True)
                if not type(card) is cards.Card:
                    if card:
                        self.update_table.emit()
                    return
                self.require_player_input = False

            self.table_status["played cards"][self.current_player] = card
            self.players_playzone[self.current_player].add_card(card)
        elif not all(self.table_status["played cards"]):
            # Subsequent player make their plays, following suit if possible
            if not self.require_player_input:
                self.display_current_player(self.current_player)
                if not self.players[self.current_player].AI:
                    self.require_player_input = True
                    return
                else:
                    card = self.players[self.current_player].make_decision(self.game_state, 1)
            else:
                card, msg = self.players[self.current_player].make_decision(self.game_state, 1, game_events)
                if msg:
                    self.write_message(msg, delay_time=0, update_now=False)
                if not type(card) is cards.Card:
                    if card:
                        self.update_table.emit()
                    return
                self.require_player_input = False

            self.players_playzone[self.current_player].add_card(card)
            self.table_status["played cards"][self.current_player] = card
        else:
            # Once all player played, find out who wins
            leading_card = self.table_status["played cards"][self.table_status['leading player']]
            card_suits = [card.suit() for card in self.table_status["played cards"]]
            card_nums = [card.number() for card in self.table_status["played cards"]]
            follow_suits = [suit == leading_card.suit() for suit in card_suits]
            trumps = [suit == self.table_status['trump suit'] for suit in card_suits]

            # Determine which players to check for winner, and determine winner
            if any(trumps):
                valid_nums = [card_nums[i] * trumps[i] for i in range(NUM_OF_PLAYERS)]
            else:
                valid_nums = [card_nums[i] * follow_suits[i] for i in range(NUM_OF_PLAYERS)]

            winning_player = valid_nums.index(max(valid_nums))
            self.write_message("Player {0:d} wins!\n".format(winning_player), delay_time=1)
            self.players[winning_player].score += 1
            self.update_player_wins(winning_player)

            # Clean up the cards, update score, set the next leading player, update round history
            for deck in self.players_playzone:
                self.discard_deck.append(deck.remove_card())

            for player in self.players:
                if player.AI:
                    player.AI.update_memory()

            if self.players[winning_player].role == PlayerRole.DECLARER or\
               self.players[winning_player].role == PlayerRole.PARTNER:
                self.table_status['defender']['wins'] += 1
            elif self.players[winning_player].role == PlayerRole.ATTACKER:
                self.table_status['attacker']['wins'] += 1

            self.table_status['leading player'] = winning_player
            self.table_status['round history'].append(copy.copy(self.table_status["played cards"]))
            self.update_team_scores()
            self.table_status["played cards"] = [0]*NUM_OF_PLAYERS
            self.current_round += 1
            self.update_table.emit()

            return

        # Break trump if the trump suit is played
        if not self.table_status['trump broken']:
            self.table_status['trump broken'] = card.suit() == self.table_status['trump suit']
            if self.table_status['trump broken']:
                self.write_message("Trump broken!", delay_time=1)

        if not self.table_status['partner reveal']:
            if card.value == self.table_status['partner']:
                self.table_status['partner reveal'] = True
                self.write_message("Partner Revealed!", delay_time=1)
                self.reveal_all_roles(self.current_player)
                self.update_all_players(role=True, wins=False)

        self.current_player += 1
        self.current_player %= NUM_OF_PLAYERS
        self.update_table.emit()
        time.sleep(0.5)

    def write_message(self, text, delay_time=0.5, line=0, update_now=True):
        """
        Write a message into the center board surface (announcer)
        :param text: String to be displayed on the center board
        :param delay_time: How much delay to put once the string is display
        :param line: Which line of the announcer to write to
        :param update_now:
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
        """
        Update the display of the player roles. Blank if UNKNOWN
        :param player_num:
        :param update_now:
        :return:
        """
        self.player_stats[player_num][1].fill((255, 255, 255, 255*VIEW_TRANSPARENT))
        role_text = ''
        colour = (0, 239, 224)
        if self.players[player_num].role == PlayerRole.DECLARER:
            role_text = 'Declarer'
        elif self.players[player_num].role == PlayerRole.ATTACKER:
            role_text = 'Attacker'
            colour = (225, 0, 0)
        elif self.players[player_num].role == PlayerRole.PARTNER:
            role_text = 'Partner'
        rendered_text = self.player_font.render(role_text, True, colour).convert_alpha()
        self.center_text_on_surface(self.player_stats[player_num][1], rendered_text,
                                    (255, 255, 255, 255 * VIEW_TRANSPARENT))
        if update_now:
            self.update_table.emit()

    def update_player_wins(self, player_num, update_now=True, clear=False):
        """
        Update the display of player's number of wins.
        :param player_num:
        :param update_now:
        :param clear:
        :return:
        """
        self.player_stats[player_num][2].fill((255, 255, 255, 255*VIEW_TRANSPARENT))
        if not clear:
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

    def update_all_players(self, role=False, wins=True, clear_wins=False):
        for i in range(NUM_OF_PLAYERS):
            if wins:
                self.update_player_wins(i, update_now=False, clear=clear_wins)
            if role:
                self.update_players_role(i, update_now=False)
        self.update_table.emit()

    def display_current_player(self, current=-1):
        if current >= 0:
            print("Player {0:d}\n".format(current))
        for i in range(NUM_OF_PLAYERS):
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
            msg = "Declarer: {0:d}/{2:d}, Attacker: {1:d}/{3:d}\n".format(self.table_status['defender']['wins'],
                                                                          self.table_status['attacker']['wins'],
                                                                          self.table_status['defender']['target'],
                                                                          self.table_status['attacker']['target'])
            self.write_message(msg, line=2)
        else:
            msg = "Declarer: {0:d}?/{1:d}, Attacker: ?/{2:d}\n".format(self.table_status['defender']['wins'],
                                                                       self.table_status['defender']['target'],
                                                                       self.table_status['attacker']['target'])
            self.write_message(msg, line=2)


    def reveal_all_roles(self, partner):
        """
        Update all roles once the partner card is shown
        Also updates the partner to the player number
        :param partner:
        :return:
        """
        self.players[partner].role = PlayerRole.PARTNER
        self.table_status["partner"] = partner
        self.table_status['defender']['wins'] += self.players[partner].score
        for i in range(NUM_OF_PLAYERS):
            if self.players[i].role == PlayerRole.UNKNOWN:
                self.players[i].role = PlayerRole.ATTACKER
                self.table_status['attacker']['wins'] += self.players[i].score

    def declare_winner(self):
        if self.table_status['attacker']['wins'] >= self.table_status['attacker']['target']:
            self.write_message("Attacker wins! Press P to play again!")
        if self.table_status['defender']['wins'] >= self.table_status['defender']['target']:
            self.write_message("Declarer wins! Press P to play again!")

    def reset_game(self):
        """
        Reset all variables for the next game
        :return:
        """
        for player in self.players:
            while not player.is_empty():
                self.discard_deck.append(player.remove_card())
            player.score = 0
            player.role = PlayerRole.UNKNOWN
            if player.AI:
                player.AI.reset_memory()

        #for i in range(NUM_OF_PLAYERS):
            #self.update_players_role(i)
            #self.update_player_wins(i, clear=True)
        self.table_status['defender']['wins'] = 0
        self.table_status['attacker']['wins'] = 0
        self.table_status["played cards"] = [0]*NUM_OF_PLAYERS
        self.table_status['round history'] = []
        self.current_round = 0
        #self.write_message("", line=1, update_now=False)
        #self.write_message("", line=2)
        #self.display_current_player()
        #self.update_table.emit()
