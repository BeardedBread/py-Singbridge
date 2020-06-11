from FSM import Table
import traceback
if __name__ == "__main__":
    table = Table()
    table.listening_for_players()

    try:
        table.play_game()
    except Exception as e:
        track = traceback.format_exc()
        print(track)
    table.exit_game()