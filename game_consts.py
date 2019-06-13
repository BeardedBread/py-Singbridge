from enum import Enum
import pygame

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


NUM_OF_PLAYERS = 4
STARTING_HAND = 13
HIGHEST_CARD = 414
LOWEST_CARD = 102
DOUBLE_CLICK_EVENT = pygame.USEREVENT + 1
DOUBLE_CLICK_TIMING = 300
CALL_EVENT = pygame.USEREVENT + 2
