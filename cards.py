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

# LUT for mapping int to cards symbols
CARDS_SYMBOLS = {14: "A", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7",
                 8: "8", 9: "9", 10: "10", 11: "J", 12: "Q", 13: "K",
                 100: "Clubs", 200: "Diamonds", 300: "Hearts", 400: "Spades", 500: "No Trump",
                 "C": 100, "D": 200, "H": 300, "S": 400, "A": 14}


class DeckReveal(Enum):
    SHOW_ALL = 1
    HIDE_ALL = 2
    ANY = 3


class DeckSort(Enum):
    ASCENDING = 1
    DESCENDING = 2
    NOSORT = 3


class Card(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, value, hidden=False, image_data=None, parent=None):
        super().__init__()
        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.value = value
        self.hidden = hidden
        self.parent = parent

        if image_data:
            self.image = image_data.convert()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))

        # Display Value for Debug Purposes
        myfont = pygame.font.SysFont("None", 16)
        mytext = myfont.render(str(self.value), True, (0, 0, 0))
        mytext = mytext.convert_alpha()
        self.image.blit(mytext, (0, 0))

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
            self.background = pygame.Surface((self.length, self.width), pygame.SRCALPHA)
            pygame.draw.rect(self.background, (255, 255, 255), self.background.get_rect(), 5)
            #self.background.fill((0, 255, 0))
            self.background = self.background.convert_alpha()
            self.deck_surface = self.background.copy()
        else:
            self.background = pygame.Surface((self.width, self.length), pygame.SRCALPHA)
            pygame.draw.rect(self.background, (255, 255, 255), self.background.get_rect(), 5)
            #self.background.fill((0, 255, 0))
            self.background = self.background.convert_alpha()
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
        # TODO: Fix vertical card positioning
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
                    # TODO: make sure that deck length is always longer than card width
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
                        card.y = start_point + self.default_spacing * (i-1)
                        card.x = (self.width - self.cards[0].width) / 2
                else:
                    adjusted_spacing = (self.length - self.cards[0].height)/(number_of_cards-1)

                    start_point = 0
                    for (i, card) in enumerate(self.cards):
                        card.y = start_point + adjusted_spacing * i
                        card.x = (self.width - self.cards[0].width)/ 2

        self.update_deck_display()

    def update_deck_display(self):
        self.deck_surface.fill((0, 0, 0, 0))
        self.deck_surface.blit(self.background, (0, 0))
        if not self.is_empty():
            if self.draw_from_last:
                for card in reversed(self.cards):
                    self.deck_surface.blit(card.image, (card.x, card.y))
            else:
                for card in self.cards:
                    self.deck_surface.blit(card.image, (card.x, card.y))

    def remove_card(self, pos=-1):
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


class PlayerDeck(Deck):
    # TODO: Maybe merge with Regular Deck
     def get_selected_card(self, pos):
         # TODO: convert pos to card num, deselect if no card is clicked or out of range

         # TODO: check if card num is selected, set selected, otherwise use it (by removing)
         pass


DATA_FOLDER = "data"


def prepare_playing_cards(width, height):
    """
    Create the 52 playing cards. Should be called only once.
    :param int width: Card width
    :param int height: Card Height
    :return: The list of 52 Cards
    :rtype: List of <Cards>
    """
    try:  # try to load images from the harddisk
        card_img = pygame.image.load(os.path.join(DATA_FOLDER, 'diamond.jpg'))
    except:
        raise Exception("Cannot load image")  # print error message and exit program

    all_cards = []

    for i in range(4):
        for j in range(13):
            all_cards.append(Card(0, 0, width, height, (i+1)*100 + j+2, image_data=card_img))

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


class test_screen(view.PygView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:  # try to load images from the harddisk
            data_path = os.path.join(DATA_FOLDER, 'diamond.jpg')
            self.card_img = pygame.image.load(data_path)
        except:
            raise Exception("Cannot load image")  # print error message and exit program

        self.test_card = Card(50, 0, 50, 75, 111, image_data=self.card_img)
        self.test_deck = Deck(100, 100, 200, 100, 25)
        self.test_deck.add_card(Card(50, 0, 50, 75, 315, image_data=self.card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 210, image_data=self.card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 103, image_data=self.card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 405, image_data=self.card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 112, image_data=self.card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 301, image_data=self.card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 206, image_data=self.card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 206, image_data=self.card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 206, image_data=self.card_img))

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
