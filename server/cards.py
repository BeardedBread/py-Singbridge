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


def card_check(value):
    return 1 <= get_card_suit(value) <= 4 \
           and 2 <= get_card_number(value) <= 14