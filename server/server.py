from FSM import Table
import traceback
import random
import pickle

LOAD_LAST = True

if __name__ == "__main__":
    table = Table()
    table.listening_for_players()

    if LOAD_LAST:
        with open('last_game_rng.rng', 'rb') as f:
            rng_state = pickle.load(f)
        random.setstate(rng_state)
    else:
        rng_state = random.getstate()
        with open('last_game_rng.rng', 'wb') as f:
            pickle.dump(rng_state, f)

    try:
        table.play_game()
    except Exception as e:
        track = traceback.format_exc()
        print(track)
    table.exit_game()