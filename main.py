import random
import pickle
import sys
import game

"""
This script is to run the game. It would process any input argument and pass into the game.
"""

if __name__ == '__main__':
    AUTOPLAY = True
    VIEW_ALL_CARDS = True
    TERMINAL = False

    if len(sys.argv) > 1:
        prev_command = ""
        for command in sys.argv[1:]:
            if prev_command == "--seed" or prev_command == "-s":
                try:
                    with open(command, 'rb') as f:
                        # The protocol version used is detected automatically, so we do not
                        # have to specify it.
                        rng_state = pickle.load(f)
                    random.setstate(rng_state)
                except:
                    print("RNG File not Found")
            if command == "--view-all" or command == "-va":
                VIEW_ALL_CARDS = True
            if command == "--auto" or command == "-a":
                AUTOPLAY = True
            if command == "--terminal" or command == "-t":
                TERMINAL = True
            prev_command = command

    rng_state = random.getstate()
    with open('last_game_rng.rng', 'wb') as f:
        pickle.dump(rng_state, f)

    with open('seeds/test_seed.rng', 'rb') as f:
        rng_state = pickle.load(f)
    random.setstate(rng_state)

    main_view = game.GameScreen(800, 600, clear_colour=(255, 0, 0),
                           autoplay=AUTOPLAY, view_all_cards=VIEW_ALL_CARDS, terminal=TERMINAL)

    main_view.run()