import view
import pygame
import players
import random
import pickle
import sys

class GameScreen(view.PygView):

    def __init__(self, *args, autoplay=False, view_all_cards=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = players.Table(0, 0, self.width, self.height, (0, 32, 0),
                                   autoplay=autoplay, view_all_cards=view_all_cards)
        self.table.update_table.connect(self.draw_table)
        self.draw_table()

    def load_assets(self):
        pass

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

        pygame.display.flip()

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
                        if not self.table.ongoing:
                            self.table.ongoing = True
                    #if event.key == pygame.K_l:
            if self.table.ongoing:
                self.table.continue_game()

            milliseconds = self.clock.tick(self.fps)
            #self.playtime += milliseconds / 1000.0

            #self.draw_function()

            #pygame.display.flip()
            #self.screen.blit(self.background, (0, 0))

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

    main_view = GameScreen(800, 600, clear_colour=(255, 0, 0),
                           autoplay=AUTOPLAY, view_all_cards=VIEW_ALL_CARDS)

    main_view.run()