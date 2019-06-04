"""
This module contains the Card class and the Deck class
Card contains the information of a playing card
Deck is used as a Card container
"""
import pygame
import view
import os
import random
from enum import Enum

CLEARCOLOUR = (0, 99, 0)

# LUT for mapping int to cards symbols
CARDS_SYMBOLS = {14: "A", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7",
                 8: "8", 9: "9", 10: "10", 11: "J", 12: "Q", 13: "K",
                 100: "Clubs", 200: "Diamonds", 300: "Hearts", 400: "Spades", 500: "No Trump",
                 }

INPUT_SYMBOLS = {"c": 100, "d": 200, "h": 300, "s": 400, "n":500, "a": 14,
                 "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
                 "8": 8, "9": 9, "10": 10, "j": 11, "q": 12, "k": 13,
                 }


class DeckReveal(Enum):
    SHOW_ALL = 1
    HIDE_ALL = 2
    ANY = 3


class DeckSort(Enum):
    ASCENDING = 1
    DESCENDING = 2
    NOSORT = 3


class Card(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, value, hidden=False, image_data=None, backimage_data=None, parent=None):
        super().__init__()
        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.value = value
        self.hidden = hidden
        self.parent = parent

        self.image = None
        self.backimage = None

        if image_data:
            self.image = image_data
            self.image = pygame.transform.scale(self.image, (self.width, self.height))

        if backimage_data:
            self.backimage = backimage_data
            self.backimage = pygame.transform.scale(self.backimage, (self.width, self.height))
        # Display Value for Debug Purposes
        #myfont = pygame.font.SysFont("None", 16)
        #mytext = myfont.render(str(self.value), True, (0, 0, 0))
        #mytext = mytext.convert_alpha()
        #self.image.blit(mytext, (0, 0))

        self._layer = 0

    def get_pos(self):
        return self.x, self.y

    def suit(self):
        return get_card_suit(self.value)

    def number(self):
        return get_card_number(self.value)

    def value_info(self):
        return self.suit(), self.number()


class Deck():

    def __init__(self, x, y, length, width, spacing, deck_reveal=DeckReveal.SHOW_ALL,
                 sort_order=DeckSort.ASCENDING, vert_orientation=False, draw_from_last=False):
        super().__init__()
        self.x = x
        self.y = y

        self.length = length
        self.width = width
        self.default_spacing = spacing

        self.deck_reveal = deck_reveal
        self.vert_orientation = vert_orientation
        self.draw_from_last = draw_from_last
        self.sort_order = sort_order

        self.cards = []

        if self.is_horizontal():
            self.background = pygame.Surface((self.length, self.width))
            self.background.fill(CLEARCOLOUR)
            pygame.draw.rect(self.background, (255, 255, 255), self.background.get_rect(), 5)

            self.background = self.background.convert()
            self.background.set_colorkey(CLEARCOLOUR)
            self.deck_surface = self.background.copy()
        else:
            self.background = pygame.Surface((self.width, self.length))
            self.background.fill(CLEARCOLOUR)
            pygame.draw.rect(self.background, (255, 255, 255), self.background.get_rect(), 5)
            self.background = self.background.convert()
            self.background.set_colorkey(CLEARCOLOUR)
            self.deck_surface = self.background.copy()

        self._layer = 1

    def add_card(self, card, position=0):
        # TODO: Add a function to add additional cards, to optimise number of recalculations
        card.parent = self
        number_of_cards = len(self.cards)

        if number_of_cards == 0:
            self.cards.append(card)
        else:
            if self.sort_order == DeckSort.NOSORT:
                self.cards.insert(position, card)
            else:
                if self.sort_order == DeckSort.DESCENDING:
                    self.cards.reverse()

                if card.value < self.cards[0].value:
                    self.cards.insert(0, card)
                elif card.value > self.cards[-1].value:
                    self.cards.append(card)
                else:
                    lo = 0
                    hi = number_of_cards

                    while abs(lo-hi) != 1:
                        pos = (lo + hi) // 2
                        if card.value > self.cards[pos].value:
                            lo = pos
                        else:
                            hi = pos

                    self.cards.insert(hi, card)

                if self.sort_order == DeckSort.DESCENDING:
                    self.cards.reverse()

        self.set_card_positions()

    def set_card_positions(self):
        """
        Calculate the card positions, given the spacing.
        If there is too many cards for the given spacing, the spacing is adjusted to fit.
        :return: None
        """
        number_of_cards = len(self.cards)

        if number_of_cards > 0:
            if self.is_horizontal():
                total_card_length = self.cards[0].width + self.default_spacing * (number_of_cards-1)
                if total_card_length <= self.length:
                    start_point = (self.length - total_card_length)/2
                    for (i, card) in enumerate(self.cards):
                        card.x = start_point + self.default_spacing * i
                        card.y = (self.width - self.cards[0].height) / 2
                else:
                    adjusted_spacing = (self.length - self.cards[0].width)/(number_of_cards-1)

                    start_point = 0
                    for (i, card) in enumerate(self.cards):
                        card.x = start_point + adjusted_spacing * i
                        card.y = (self.width - self.cards[0].height) / 2
            else:
                total_card_length = self.cards[0].height + self.default_spacing * (number_of_cards-1)

                if total_card_length <= self.length:
                    start_point = (self.length - total_card_length)/2
                    for (i, card) in enumerate(self.cards):
                        card.y = start_point + self.default_spacing * i
                        card.x = (self.width - self.cards[0].width) / 2
                else:
                    adjusted_spacing = (self.length - self.cards[0].height)/(number_of_cards-1)

                    start_point = 0
                    for (i, card) in enumerate(self.cards):
                        card.y = start_point + adjusted_spacing * i
                        card.x = (self.width - self.cards[0].width)/ 2

        self.update_deck_display()

    def update_deck_display(self):
        """
        Blits the cards onto the deck surface. Called when the deck is modified.
        :return: None
        """
        self.deck_surface.fill(CLEARCOLOUR)
        self.deck_surface.blit(self.background, (0, 0))
        if not self.is_empty():
            if self.draw_from_last:
                for card in reversed(self.cards):
                    if self.deck_reveal == DeckReveal.SHOW_ALL:
                        self.deck_surface.blit(card.image, (card.x, card.y))
                    elif self.deck_reveal == DeckReveal.HIDE_ALL:
                        self.deck_surface.blit(card.backimage, (card.x, card.y))
            else:
                for card in self.cards:
                    if self.deck_reveal == DeckReveal.SHOW_ALL:
                        self.deck_surface.blit(card.image, (card.x, card.y))
                    elif self.deck_reveal == DeckReveal.HIDE_ALL:
                        self.deck_surface.blit(card.backimage, (card.x, card.y))

    def remove_card(self, pos=-1):
        """
        Remove a card from the deck.
        Check first if the card is in deck to get the position
        :param pos: Position of the card to be removed
        :return: Card
        """
        if not self.is_empty():
            if pos < 0:
                card = self.cards.pop()
            else:
                card = self.cards.pop(pos)
            self.set_card_positions()
            return card
        return None

    def is_horizontal(self):
        return not self.vert_orientation

    def is_empty(self):
        return len(self.cards) == 0

    def get_pos(self):
        return self.x, self.y

    def get_deck_values(self):
        values = []
        for card in self.cards:
            values.append(card.value)
        return values

    def check_card_in(self, value):
        card_values = self.get_deck_values()
        if value in card_values:
            return True, card_values.index(value)
        return False, -1


class SpriteSheet(object):
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error:
            print('Unable to load spritesheet image:', filename)
            raise Exception("Cannot load image")

    # Load a specific image from a specific rectangle
    def image_at(self, rectangle, colorkey=None):
        "Loads image from x,y,x+offset,y+offset"
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image
    # Load a whole bunch of images and return them as a list
    def images_at(self, rects, colorkey = None):
        "Loads multiple images, supply a list of coordinates"
        return [self.image_at(rect, colorkey) for rect in rects]
    # Load a whole strip of images
    def load_strip(self, rect, image_count, colorkey = None):
        "Loads a strip of images and returns them as a list"
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)

class PlayerDeck(Deck):
    # TODO: Maybe merge with Regular Deck
     def get_selected_card(self, pos):
         # TODO: convert pos to card num, deselect if no card is clicked or out of range

         # TODO: check if card num is selected, set selected, otherwise use it (by removing)
         pass


DATA_FOLDER = "resource"


def prepare_playing_cards(display_w, display_h):
    """
    Create the 52 playing cards. Should be called only once.
    :param int display_w: Card width
    :param int display_h: Card Height
    :return: The list of 52 Cards
    :rtype: List of <Cards>
    """
    #try:  # try to load images from the harddisk
    #    card_img = pygame.image.load(os.path.join(DATA_FOLDER, 'diamond.jpg'))
    #except:
    #    raise Exception("Cannot load image")  # print error message and exit program
    card_sprites = SpriteSheet(os.path.join(DATA_FOLDER, 'card_spritesheet.png'))
    all_cards = []
    offset = 0
    spacing = 0
    width = 71
    height = 96
    suits_position = [2, 3, 1, 0]
    card_backimg = card_sprites.image_at((offset + (width+spacing)*3, 5*(height+spacing) + offset, width, height))
    for i in range(4):
        y = suits_position[i] * (height+spacing) + offset
        for j in range(13):
            if j < 12:
                x = offset + (width+spacing)*(j+1)
            else:
                x = offset
            card_img = card_sprites.image_at((x, y, width, height))
            all_cards.append(Card(0, 0, display_w, display_h, (i+1)*100 + j+2,
                                  image_data=card_img, backimage_data=card_backimg))

    return all_cards


def card_check(value):
    return 1 <= get_card_suit(value) <= 4 \
           and 2 <= get_card_number(value) <= 14


def get_card_suit(value):
    return value // 100


def get_card_number(value):
    return value % 100


def get_card_string(value):
    suit = get_card_suit(value) * 100
    num = get_card_number(value)
    return CARDS_SYMBOLS[num] + ' ' + CARDS_SYMBOLS[suit]


def get_suit_string(value):
    return CARDS_SYMBOLS[value*100]


def convert_input_string(string):
    try:
        return INPUT_SYMBOLS[string[0:-1]] + INPUT_SYMBOLS[string[-1]]
    except KeyError:
        return -1


def convert_bid_string(string):
    try:
        return int(string[0])*10 + INPUT_SYMBOLS[string[1]]//100
    except KeyError:
        return -1
    except ValueError:
        return -1

class test_screen(view.PygView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        all_cards = prepare_playing_cards(50, 75)
        self.test_card = all_cards[15]
        self.test_deck = Deck(100, 100, 200, 100, 25)
        self.test_deck.add_card(all_cards[0])
        self.test_deck.add_card(all_cards[13])
        self.test_deck.add_card(all_cards[35])
        self.test_deck.add_card(all_cards[51])

    def draw_function(self):
        self.screen.blit(self.test_card.image, self.test_card.get_pos())
        self.screen.blit(self.test_deck.deck_surface, self.test_deck.get_pos())

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_r:
                        card = self.test_deck.remove_card()
                        del card
                        print('remove cards')

                    if event.key == pygame.K_a:
                        self.test_deck.add_card(Card(50, 0, 50, 75, random.randint(1, 500), image_data=self.card_img))
                        print('remove cards')
                        pass

            milliseconds = self.clock.tick(self.fps)
            #self.playtime += milliseconds / 1000.0

            self.draw_function()

            pygame.display.flip()
            self.screen.blit(self.background, (0, 0))

        pygame.quit()


if __name__ == '__main__':
    test_view = test_screen(640, 400, clear_colour=(0, 0, 0))
    test_view.run()
