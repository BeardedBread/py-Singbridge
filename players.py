import pygame
import cards
import view
from signalslot import Signal


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

        self.players = []
        self.players_playzone = []
        self.table_status = {'played cards': [0,0,0,0], 'leading player': 0, 'trump suit': 1,
                             'trump broken': False, 'round history': [], 'bid': 0}

        self.background = pygame.Surface((self.width, self.height))
        self.background.fill(clear_colour)
        self.background = self.background.convert()

        self.discard_deck = [] # This is not a deck as it will never be drawn

        w_deck = min(self.height, self.width) * 0.15
        l_deck = min(self.width, self.height) * 0.6

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
            if i == 0:
                self.players.append(MainPlayer(playerx[i], playery[i],
                                               l_deck, w_deck,
                                               spacing))
            else:
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
        playfield_width = self.width - (margins_with_w_deck)* 2
        playfield_height = self.height - (margins_with_w_deck)* 2

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
        rendered_text = self.table_font.render(text, True, (255,0,0)).convert_alpha()
        self.announcer.blit(rendered_text, (50, 50))

    def get_pos(self):
        return self.x, self.y


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