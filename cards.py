"""
This module contains the Card class and the Deck class
Card contains the information of a playing card
Deck is used as a Card container
"""
import pygame
import view
import os
import threading
import random
from enum import Enum

CLEARCOLOUR = (0, 99, 0)

# LUT for mapping int to cards symbols
CARDS_SYMBOLS = {14: "A", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7",
                 8: "8", 9: "9", 10: "10", 11: "J", 12: "Q", 13: "K",
                 100: "Clubs", 200: "Diamonds", 300: "Hearts", 400: "Spades", 500: "No Trump",
                 }

INPUT_SYMBOLS = {"c": 100, "d": 200, "h": 300, "s": 400, "n": 500, "a": 14,
                 "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
                 "8": 8, "9": 9, "10": 10, "j": 11, "q": 12, "k": 13,
                 }
BID_SYMBOLS = {"c": 100, "d": 200, "h": 300, "s": 400, "n": 500}


class DeckReveal(Enum):
    SHOW_ALL = 1
    HIDE_ALL = 2
    ANY = 3


class DeckSort(Enum):
    ASCENDING = 1
    DESCENDING = 2
    NOSORT = 3


class Card(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, value, hidden=False, image_data=None,
                 backimage_data=None, parent=None, angle=0):
        super().__init__()
        self.x = x
        self.y = y

        self.width = width
        self.height = height
        self.angle = angle

        self.value = value
        self.hidden = hidden
        self.parent = parent

        self.original_image = None
        self.original_backimage = None
        self.image = None
        self.backimage = None
        self.rect = None

        self.add_image(image_data, backimage_data)
        self._layer = 0

    def add_image(self, image, backimage=None):
        if image:
            self.original_image = image
            self.original_image = pygame.transform.scale(self.original_image, (self.width, self.height))
            self.image = pygame.transform.rotate(self.original_image, self.angle)

            self.rect = self.image.get_rect()

        if backimage:
            self.original_backimage = backimage
            self.original_backimage = pygame.transform.scale(self.original_backimage, (self.width, self.height))
            self.backimage = pygame.transform.rotate(self.original_backimage, self.angle)

    def set_angle(self, angle):
        if self.original_image:
            self.image = pygame.transform.rotate(self.original_image, angle)

        if self.original_backimage:
            self.backimage = pygame.transform.rotate(self.original_backimage, angle)

        self.angle = angle

        self.rect = self.image.get_rect()

    def get_pos(self):
        return self.x, self.y

    def set_pos(self, x, y):
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

    def suit(self):
        return get_card_suit(self.value)

    def number(self):
        return get_card_number(self.value)

    def value_info(self):
        return self.suit(), self.number()


class Deck():

    def __init__(self, x, y, length, width, spacing, deck_reveal=DeckReveal.SHOW_ALL,
                 sort_order=DeckSort.ASCENDING, vert_orientation=False, draw_from_last=False, selectable=False,
                 flip=False):
        super().__init__()
        self.x = x
        self.y = y

        self.length = length
        self.width = width
        self.default_spacing = spacing

        self.deck_reveal = deck_reveal
        self.vert_orientation = vert_orientation
        self.flip = flip

        self.draw_from_last = draw_from_last
        self.sort_order = sort_order
        self.selectable = selectable
        self.selected_card = -1

        self.cards = []
        self.line_width = 5
        if self.is_horizontal():
            self.background = pygame.Surface((self.length, self.width))
            self.background.fill(CLEARCOLOUR)
            pygame.draw.rect(self.background, (255, 255, 255), self.background.get_rect(), self.line_width)

            self.background = self.background.convert()
            self.background.set_colorkey(CLEARCOLOUR)
            self.deck_surface = self.background.copy()
            self.rect = pygame.rect.Rect(x, y, length, width)
        else:
            self.background = pygame.Surface((self.width, self.length))
            self.background.fill(CLEARCOLOUR)
            pygame.draw.rect(self.background, (255, 255, 255), self.background.get_rect(), self.line_width)
            self.background = self.background.convert()
            self.background.set_colorkey(CLEARCOLOUR)
            self.deck_surface = self.background.copy()
            self.rect = pygame.rect.Rect(x, y, width, length)

        self._layer = 1

    def set_selectable(self, state):
        self.selectable = state

    def add_card(self, card, position=0):
        # TODO: Add a function to add additional cards, to optimise number of recalculations
        card.parent = self
        if self.vert_orientation:
            card.set_angle(90)
        else:
            card.set_angle(0)
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
            total_card_length = self.cards[0].width + self.default_spacing * (number_of_cards - 1)
            if total_card_length <= self.length - 2 * self.line_width:
                start_point = (self.length - total_card_length) / 2
                spacing = self.default_spacing
            else:
                start_point = self.line_width
                spacing = (self.length - self.cards[0].width - 2*self.line_width)/(number_of_cards-1)

            for (i, card) in enumerate(self.cards):
                x = start_point + spacing * i
                y = (self.width - self.cards[0].height) / 2
                if self.is_horizontal():
                    card.set_pos(x, y)
                else:
                    card.set_pos(y, x)

        self.update_deck_display()

    def update_deck_display(self):
        """
        Blits the cards onto the deck surface. Called when the deck is modified.
        :return: None
        """
        self.deck_surface.fill(CLEARCOLOUR)
        self.deck_surface.blit(self.background, (0, 0))
        if not self.is_empty():
            cards_to_draw = self.cards
            if self.draw_from_last:
                cards_to_draw = reversed(cards_to_draw)

            for i, card in enumerate(cards_to_draw):
                selected = (i == self.selected_card)
                image_to_draw = card.image

                if self.deck_reveal == DeckReveal.HIDE_ALL:
                    image_to_draw = card.backimage

                    if self.flip:
                        image_to_draw = pygame.transform.flip(image_to_draw, self.vert_orientation,
                                                              not self.vert_orientation)

                self.deck_surface.blit(image_to_draw, (card.x - selected * card.x * 0.5 *
                                                       (-1)**self.flip * self.vert_orientation,
                                                       card.y - selected * card.y * 0.5 *
                                                       (-1)**self.flip * (not self.vert_orientation)))

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

    def remove_selected_card(self):
        if self.selected_card >= 0:
            card = self.remove_card(self.selected_card)
            self.deselect_card()
            return card

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

    def deselect_card(self):
        self.selected_card = -1
        self.update_deck_display()

    def get_selected_card(self, pos):
        """
        Get the selected card based on the mouse pos, offset to give the relative position in the deck.
        The selected card position is stored in the deck
        :param pos: Absolute position of the mouse
        :return: bool: whether the card selected is the same as before
        """
        if self.selectable:
            relative_pos_x = pos[0] - self.x
            relative_pos_y = pos[1] - self.y
            mouse_pos = (relative_pos_x, relative_pos_y)
            prev_selected = self.selected_card
            self.selected_card = -1
            if not self.draw_from_last:
                for i, card in enumerate(reversed(self.cards)):
                    if card.rect.collidepoint(mouse_pos):
                        self.selected_card = len(self.cards) - 1 - i
                        break
            else:
                for i, card in enumerate(self.cards):
                    if card.rect.collidepoint(mouse_pos):
                        self.selected_card = i
                        break

            self.update_deck_display()
            return prev_selected == self.selected_card and self.selected_card >= 0
        return False


class SpriteSheet(object):
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error:
            print('Unable to load spritesheet image:', filename)
            raise Exception("Cannot load image")

    # Load a specific image from a specific rectangle
    def image_at(self, rectangle, colorkey=None):
        """
        Loads image from x,y,x+width,y+height
        :param rectangle: tuple: (x, y, width, height)
        :param colorkey: tuple (R,G,B), the transparency colour
        :return: the image
        """
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image

    def images_at(self, rects, colorkey = None):
        """
        Loads multiple images, supply a list of coordinates
        :param rects:
        :param colorkey:
        :return:
        """
        return [self.image_at(rect, colorkey) for rect in rects]

    def load_strip(self, rect, image_count, colorkey = None):
        """
        Loads a strip of images and returns them as a list
        :param rect:
        :param image_count:
        :param colorkey:
        :return:
        """
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)


DATA_FOLDER = "resource"


def prepare_playing_cards(display_w, display_h):
    """
    Create the 52 playing cards. Should be called only once.
    :param int display_w: Card width
    :param int display_h: Card Height
    :return: The list of 52 Cards
    :rtype: List of <Cards>
    """
    card_sprites = SpriteSheet(os.path.join(DATA_FOLDER, 'card_spritesheet.png'))
    all_cards = []
    offset = 0
    spacing = 0
    width = 71
    height = 96
    suits_position = [2, 3, 1, 0]
    card_backimg = card_sprites.image_at((offset + (width+spacing)*9, 5*(height+spacing) + offset, width, height))
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
    string = string.lower()
    try:
        if string[0:-1].isalnum() and string[-1].isalpha():
            return INPUT_SYMBOLS[string[0:-1]] + INPUT_SYMBOLS[string[-1]]
        return -1
    except KeyError:
        return -1


def convert_bid_string(string):
    string = string.lower()
    try:
        if len(string)>1 and string[0].isdecimal() and string[1].isalpha():
            return int(string[0])*10 + BID_SYMBOLS[string[1]]//100
        return -1
    except KeyError:
        return -1


class TestScreen(view.PygView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        all_cards = prepare_playing_cards(50, 75)
        self.test_card = all_cards[15]
        self.test_decks = []
        self.test_decks.append(Deck(100, 100, 200, 100, 25, selectable=True))
        self.test_decks.append(Deck(500, 100, 200, 100, 25, selectable=True, vert_orientation=True))
        self.test_decks[0].add_card(all_cards[0])
        self.test_decks[0].add_card(all_cards[13])
        self.test_decks[0].add_card(all_cards[35])
        self.test_decks[0].add_card(all_cards[51])
        self.test_decks[1].add_card(all_cards[20])
        self.test_decks[1].add_card(all_cards[21])
        self.test_decks[1].add_card(all_cards[5])
        self.test_decks[1].add_card(all_cards[14])

        self.left_mouse_down = False
        self.double_clicking = False
        self.double_click_event = pygame.USEREVENT + 1

    def draw_function(self):
        self.screen.blit(self.test_card.image, self.test_card.get_pos())
        for deck in self.test_decks:
            self.screen.blit(deck.deck_surface, deck.get_pos())

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                mouse_clicks = event.type == pygame.MOUSEBUTTONDOWN
                if self.left_mouse_down and not mouse_clicks:
                    print('mouse click')
                    mouse_pos = pygame.mouse.get_pos()
                    for deck in self.test_decks:
                        if deck.rect.collidepoint(mouse_pos):
                            reselect = deck.get_selected_card(mouse_pos)

                            if self.double_clicking:
                                pygame.time.set_timer(self.double_click_event, 0)
                                print('Double clicked')
                                if reselect:
                                    deck.remove_selected_card()
                                self.double_clicking = False
                            else:
                                self.double_clicking = True
                                pygame.time.set_timer(self.double_click_event, 200)
                                if reselect:
                                    deck.deselect_card()

                if event.type == self.double_click_event:
                    pygame.time.set_timer(self.double_click_event, 0)
                    self.double_clicking = False
                    print('double click disabled')

                self.left_mouse_down = mouse_clicks

            self.draw_function()

            pygame.display.flip()
            self.screen.blit(self.background, (0, 0))

        pygame.quit()


if __name__ == '__main__':
    test_view = TestScreen(640, 400, clear_colour=(0, 0, 0))
    test_view.run()
