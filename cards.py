"""
This module contains the Card class and the Deck class
Card contains the information of a playing card
Deck is used as a Card container
"""
import pygame
import view
import os
from enum import Enum


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
        self.image.blit(mytext, (0,0))

        self._layer = 0

    def get_pos(self):
        return self.x, self.y


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
            self.background.fill((0, 255, 0))
            self.background = self.background.convert()
            self.deck_surface = self.background.copy()
        else:
            self.background = pygame.Surface((self.width, self.length))
            self.background.fill((0, 255, 0))
            self.background = self.background.convert()
            self.deck_surface = self.background.copy()

        self._layer = 1

    def add_card(self, card, position=0):
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
        number_of_cards = len(self.cards)
        if self.is_horizontal():
            total_card_length = self.cards[0].width + self.default_spacing * (number_of_cards-1)
            if total_card_length <= self.length:
                start_point = (self.length - total_card_length)/2
                for (i, card) in enumerate(self.cards):
                    card.x = start_point + self.default_spacing * (i-1)
                    card.y = (self.width - self.cards[0].height)/ 2
            else:
                adjusted_spacing = (self.length - self.cards[0].width)/(number_of_cards-1)

                start_point = 0
                for (i, card) in enumerate(self.cards):
                    card.x = start_point + adjusted_spacing * i
                    card.y = (self.width - self.cards[0].height)/ 2
        else:
            total_card_length = self.cards[0].height + self.default_spacing * (number_of_cards-1)
            if total_card_length <= self.length:
                start_point = (self.length - total_card_length)/2
                for (i, card) in enumerate(self.cards):
                    card.y = start_point + self.default_spacing * (i-1)
                    card.x = (self.width - self.cards[0].width)/ 2
            else:
                adjusted_spacing = (self.length - self.cards[0].height)/(number_of_cards-1)

                start_point = 0
                for (i, card) in enumerate(self.cards):
                    card.y = start_point + adjusted_spacing * i
                    card.x = (self.width - self.cards[0].width)/ 2

        self.update_deck_display()

    def update_deck_display(self):
        self.deck_surface.blit(self.background, (0, 0))
        if self.draw_from_last:
            for card in reversed(self.cards):
                self.deck_surface.blit(card.image, (card.x, card.y))
        else:
            for card in self.cards:
                self.deck_surface.blit(card.image, (card.x, card.y))

    def remove_card(self):
        pass

    def is_horizontal(self):
        return not self.vert_orientation

    def get_pos(self):
        return self.x, self.y

    def print_deck_values(self):
        values = ""
        for card in self.cards:
            values = values + str(card.value) + ' '
        print(values)


class PlayerDeck(Deck):
     def get_selected_card(self, pos):
         # TODO: convert pos to card num, deselect if no card is clicked or out of range

         # TODO: check if card num is selected, set selected, otherwise use it (by removing)
         pass

DATA_FOLDER = "data"

class test_screen(view.PygView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:  # try to load images from the harddisk
            card_img = pygame.image.load(os.path.join(DATA_FOLDER, 'diamond.jpg'))
        except:
            raise Exception("Cannot load image")  # print error message and exit program
        self.test_card = Card(50, 0, 50, 75, 111, image_data=card_img)
        self.test_deck = Deck(100, 100, 200, 100, 25)
        self.test_deck.add_card(Card(50, 0, 50, 75, 412, image_data=card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 315, image_data=card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 210, image_data=card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 103, image_data=card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 405, image_data=card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 112, image_data=card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 301, image_data=card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 206, image_data=card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 206, image_data=card_img))
        self.test_deck.add_card(Card(50, 0, 50, 75, 206, image_data=card_img))

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
                    if event.key == pygame.K_p:
                        print('add cards')
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
