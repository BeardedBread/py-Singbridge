# STEP 1: Create a headless version, NO GRAPHICS
# STEP 1.5: You can do blocking calls
# Take it step-by-step: make sure one stage work first before going to the next
#
# STEP 2: Replace update_table with sending back to players
# STEP 3: Change write_message to send string back
import threading
import sys
import players
import ai
from game_consts import GameState, PlayerRole, STARTING_HAND, NUM_OF_PLAYERS
import random
import cards
from server import Server

class Table(Server):
    def __init__(self):
        super().__init__()
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
            #vert = i % 2 == 1

            self.players.append(players.Player())

            self.players[i].connect_to_table(self.table_status)
            if i > 0:
                self.players[i].add_ai(ai.VivianAI(self.table_status))

        self.discard_deck = self.prepare_playing_cards()

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
                print("Shuffle Complete!")
                self.reshuffling_players = []
                for i, player in enumerate(self.players):
                    if player.get_card_points() < 4:
                        print("Low points detected in Player {0:d}! ".format(i))
                        self.reshuffling_players.append(i)

                self.send_json_to_all({"shuffle": self.reshuffling_players})
                if not self.reshuffling_players:
                    print('No Reshuffle needed!')
                    self.game_state = GameState.BIDDING
                    #self.send_json_to_all({'state': self.game_state.value})
                    print("Start to Bid")
                    self.prepare_bidding()
                else:
                    self.current_player = self.reshuffling_players[0]
                    self.game_state = GameState.POINT_CHECK

            elif self.game_state == GameState.POINT_CHECK:
                reshuffle = self.check_reshuffle()
                self.send_json_to_all({"reshuff_res": reshuffle})
                if reshuffle:
                    #self.write_message('Reshuffle Initiated!', line=1)
                    self.game_state = GameState.ENDING
                else:
                    #self.write_message('No Reshuffle needed!')
                    self.game_state = GameState.BIDDING
                    #self.write_message("Start to Bid")
                    self.prepare_bidding()

            elif self.game_state == GameState.BIDDING:
                if self.bid_phase():
                    self.game_state = GameState.PLAYING
                    return
            elif self.game_state == GameState.PLAYING:
                self.play_the_game()
                self.declare_winner()
                self.ongoing = False
                self.game_state = GameState.ENDING
            else:
                self.block_wait_player_ready()
                print("All players ready!")
                self.reset_game()
                print(self.table_status, self.current_round)
                self.game_state = GameState.DEALING
                status = {"table": self.table_status, "round":self.current_round, 'state': self.game_state.value}
                self.send_json_to_all(status)

    def shuffle_and_deal(self):
        """
        Shuffle and deal the discard deck to the players, which should have 52 cards.
        :return: None
        """
        hands = {'deals': []}
        if self.discard_deck:
            for _ in range(10):
                random.shuffle(self.discard_deck)
            for player in self.players:
                for _ in range(STARTING_HAND):
                    player.add_card(self.discard_deck.pop())
                hands['deals'].append(player.cards)

        print(hands)    
        for conn in self.connected_players:
            self.send_json(conn, hands)

    def check_reshuffle(self):
        """
        Detect any possible reshuffle request within the players
        :return: True if reshuffle requested, else False
        """
        count = 0
        while(count < NUM_OF_PLAYERS):
            #self.write_message("Do you want a reshuffle?", line=1, update_now=False)
            #self.update_table.emit()
            if (self.current_player in self.reshuffling_players):
                if self.players[self.current_player].AI:
                    reshuffle = self.players[self.current_player].make_decision(self.game_state, 0)
                else:
                    self.send_json_to_player({"req_reshuff": self.current_player}, self.current_player)
                    reshuffle = self.wait_for_player_res(self.current_player) == 'True'
                if reshuffle:
                    return True

            self.current_player = (self.current_player + 1)%NUM_OF_PLAYERS
            count += 1
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
        print(msg)
        #self.display_current_player(self.current_player)
        msg = 'Bid Leader: Player {0:d}'.format((self.current_player - self.passes -
                                                 1 * (not self.first_player)) % NUM_OF_PLAYERS)
        print(msg)

        data = {'bid': 
                {'current': self.current_player, 
                'bid': self.table_status["bid"], 
                'previous': (self.current_player, self.table_status["bid"]), 
                'leader': (self.current_player - self.passes - 1 * (not self.first_player)) % NUM_OF_PLAYERS,
                    'substate': 0
                }
               }
        self.send_json_to_all(data)

    def bid_phase(self):
        """
        The bidding procedure. Flag up if player input required
        :return: Whether bidding is completed
        """
        # Highest bid: 7 NoTrump. No further check required
        while self.passes < NUM_OF_PLAYERS - 1 and self.table_status["bid"] < 75:
            if self.players[self.current_player].AI:
                player_bid = self.players[self.current_player].make_decision(self.game_state, 0)
            else:
                while True:
                    #self.send_json_to_player({"bid_request": 0}, self.current_player)
                    player_bid = int(self.wait_for_player_res(self.current_player))
                    if self.table_status["bid"] < player_bid or player_bid == 0:
                        self.send_json_to_player({"bid_res": (True, "",  self.table_status['bid'])}, self.current_player)
                        break
                    else:
                        if player_bid > 75:
                            self.send_json_to_player({"bid_res": (False, "You cannot bid beyond 7 No Trump", self.table_status['bid'])}, self.current_player)
                        else:
                            self.send_json_to_player({"bid_res": (False, "You might need to bid higher",  self.table_status['bid'])}, self.current_player)
            
            if player_bid < 0:
                return False
            if not player_bid:
                if not self.first_player:  # Starting bidder pass do not count at the start
                    self.passes += 1
            else:
                self.table_status["bid"] = player_bid
                self.passes = 0

            if self.first_player:
                self.first_player = False

            next_player = self.current_player
            if self.table_status["bid"] < 75:
                next_player += 1
                next_player %= NUM_OF_PLAYERS

                data = {'bid': 
                        {'current': next_player, 
                        'bid': self.table_status["bid"], 
                        'previous': (self.current_player, player_bid), 
                        'leader': (next_player- self.passes - 1 * (not self.first_player)) % NUM_OF_PLAYERS,
                        'substate': 0
                        }
                    }
                self.send_json_to_all(data)
                self.current_player = next_player
            #self.display_current_player(self.current_player)
        #if not self.require_player_input:
        self.send_json_to_all({"msg": "Player {0:d} is the bid winner!".format(self.current_player)})

        data = {'bid': 
                {'current': self.current_player, 
                'substate': 1}
                }
        self.send_json_to_all(data)
        #self.display_current_player(self.current_player)
        if self.players[self.current_player].AI:
            partner = self.players[self.current_player].make_decision(self.game_state, 1)
        else:
            partner = int(self.wait_for_player_res(self.current_player))
            # TODO: validate partner card here

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

        #msg = 'Trump: {1:s}, Partner: {0:s}'.format(cards.get_card_string(self.table_status["partner"]),
        #                                            cards.get_suit_string(self.table_status['trump suit']))
        self.send_json_to_all({"bid_complete":{
            "trump": cards.get_suit_string(self.table_status['trump suit']),
            "partner": cards.get_card_string(self.table_status["partner"]),
            "declarer": self.current_player}
        })
        return True

    def play_the_game(self):
        """
        Ask each player to play a valid card and determine the winner of the round
        This must work without pause if only bots are playing
        The function will exit after every player decision or if a user input is needed.
        If a user input is required, the function will continuously exit without proceeding to the next player
        until a valid input is received.

        :return: None
        """
        while self.current_round < 13:
            if not any(self.table_status["played cards"]):
                # Leading player starts with the leading card, which determines the leading suit
                self.current_player = self.table_status['leading player']
                if self.players[self.current_player].AI:
                    card = self.players[self.current_player].make_decision(self.game_state, 0)
                else:
                    while True:
                        self.send_json_to_player({"play_request": 0}, self.current_player)
                        card = int(self.wait_for_player_res(self.current_player))
                        # TODO: Validate card here
                        if self.check_for_valid_plays(card, True):
                            break
                self.players[self.current_player].cards.remove(card)
                self.table_status["played cards"][self.current_player] = card

            elif not all(self.table_status["played cards"]):
                # Subsequent player make their plays, following suit if possible
                if self.players[self.current_player].AI:
                    card = self.players[self.current_player].make_decision(self.game_state, 1)
                else:
                    while True:
                        self.send_json_to_player({"play_request": 0}, self.current_player)
                        card = int(self.wait_for_player_res(self.current_player))
                        # TODO: Validate card here
                        if self.check_for_valid_plays(card, False):
                            break
                self.players[self.current_player].cards.remove(card)
                self.table_status["played cards"][self.current_player] = card
            else:
                # Once all player played, find out who wins
                leading_card = self.table_status["played cards"][self.table_status['leading player']]
                card_suits = [cards.get_card_suit(card) for card in self.table_status["played cards"]]
                card_nums = [cards.get_card_number(card) for card in self.table_status["played cards"]]
                follow_suits = [suit == leading_card.suit() for suit in card_suits]
                trumps = [suit == self.table_status['trump suit'] for suit in card_suits]

                # Determine which players to check for winner, and determine winner
                if any(trumps):
                    valid_nums = [card_nums[i] * trumps[i] for i in range(NUM_OF_PLAYERS)]
                else:
                    valid_nums = [card_nums[i] * follow_suits[i] for i in range(NUM_OF_PLAYERS)]

                winning_player = valid_nums.index(max(valid_nums))
                #self.write_message("Player {0:d} wins!\n".format(winning_player), delay_time=1)
                self.players[winning_player].score += 1
                #self.update_player_wins(winning_player)

                # Clean up the cards, update score, set the next leading player, update round history
                #for deck in self.players_playzone:
                #    self.discard_deck.append(deck.remove_card())

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
                self.table_status["played cards"] = [0]*NUM_OF_PLAYERS
                self.current_round += 1

            # Break trump if the trump suit is played
            if not self.table_status['trump broken']:
                self.table_status['trump broken'] = card.suit() == self.table_status['trump suit']
                if self.table_status['trump broken']:
                    pass
                    #self.write_message("Trump broken!", delay_time=1)

            if not self.table_status['partner reveal']:
                if card.value == self.table_status['partner']:
                    self.table_status['partner reveal'] = True
                    self.reveal_all_roles(self.current_player)

            self.current_player += 1
            self.current_player %= NUM_OF_PLAYERS
            #self.update_table.emit()
            #time.sleep(0.5)

    def check_for_valid_plays(self, card, leading):
        """
        Check if the card played is valid
        :param card: int
        :param leading: bool
        :return:
        """
        player_cards = self.players[self.current_player].cards
        if card not in player_cards:
            return False
        card_suit = cards.get_card_suit(card)
        if leading:
            if not self.table_status['trump broken'] and \
                    card_suit == self.table_status['trump suit']:
                if any([not cards.get_card_suit(crd) == self.table_status['trump suit'] for crd in player_cards]):
                    return False
        else:
            leading_card_suit = cards.get_card_suit(self.table_status['played cards'][self.table_status["leading player"]])
            if not card_suit == leading_card_suit and \
                any([cards.get_card_suit(crd) == leading_card_suit for crd in player_cards]):
                return False

        return True

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
