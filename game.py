import view
import pygame
import table
import traceback


class GameScreen(view.PygView):

    def __init__(self, *args, autoplay=False, view_all_cards=False, terminal=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = table.Table(0, 0, self.width, self.height, (0, 32, 0),
                                   autoplay=autoplay, view_all_cards=view_all_cards, terminal=terminal)
        self.table.update_table.connect(self.draw_table)
        self.draw_table()
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

    def run(self):
        self.running = True
        try:
            while self.running:
                all_events = pygame.event.get()
                for event in all_events:
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                if (self.table.continue_game(all_events)  == 2):
                    input("Input any key to continue")
                    self.running = False
        except:
            track = traceback.format_exc()
            print(track)
        self.table.client.close()
        pygame.quit()
