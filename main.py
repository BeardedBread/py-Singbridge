import view
import pygame
import table
import random
import pickle
import sys
#import queue
#import threading

class GameScreen(view.PygView):

    def __init__(self, *args, autoplay=False, view_all_cards=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = table.Table(0, 0, self.width, self.height, (0, 32, 0),
                                   autoplay=autoplay, view_all_cards=view_all_cards)
        self.table.update_table.connect(self.draw_table)
        self.draw_table()
        #self.player_commands = queue.Queue(1)
        #self.player_thread = threading.Thread(target=self.get_player_inputs)
        self.running = False

    def draw_table(self, **kwargs):
        # TODO: optimise this by only redrawing the parts that changes
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.table.background, self.table.get_pos())
        for player in self.table.players:
            self.screen.blit(player.deck_surface, player.get_pos())
        for playerzone in self.table.players_playzone:
            self.screen.blit(playerzone.deck_surface, playerzone.get_pos())
        for i, announcer_line in enumerate(self.table.announcer_line):
            self.screen.blit(announcer_line, (self.table.announcer_x,
                                              self.table.announcer_y+self.table.announcer_height*i/3))
        for i, player_stats in enumerate(self.table.player_stats):
            for j, stats_line in enumerate(player_stats):
                self.screen.blit(stats_line, (self.table.player_stats_x[i],
                                              self.table.player_stats_y[i]+self.table.stats_height*j/3))

        for element in self.table.UI_elements:
            if element.visible:
                self.screen.blit(element.background, element.get_pos())

        pygame.display.flip()


    #def get_player_inputs(self):
    #    while self.running:
    #        if not self.player_commands.full():
    #            player_cmd = input("Enter something:")
    #            self.player_commands.put(player_cmd)

    def run(self):
        self.running = True
        #self.player_thread.start()
        while self.running:
            draw_update = False
            all_events = pygame.event.get()
            for event in all_events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_p:
                        if not self.table.ongoing:
                            self.table.ongoing = True
                self.table.process_UI(event)
            if self.table.ongoing:
                self.table.continue_game(all_events)


            #if not self.player_commands.empty():
            #    player_cmd = self.player_commands.get()
            #    print("Player Command Received: " + player_cmd)

        pygame.quit()


if __name__ == '__main__':
    AUTOPLAY = False
    VIEW_ALL_CARDS = False

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
            prev_command = command

    rng_state = random.getstate()
    with open('last_game_rng.rng', 'wb') as f:
        pickle.dump(rng_state, f)

    with open('seeds/test_seed.rng', 'rb') as f:
        rng_state = pickle.load(f)
    random.setstate(rng_state)

    main_view = GameScreen(900, 600, clear_colour=(255, 0, 0),
                           autoplay=True, view_all_cards=VIEW_ALL_CARDS)

    main_view.run()