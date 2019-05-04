import view
import pygame
import players


class GameScreen(view.PygView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = players.Table(0, 0, self.width, self.height, (0, 0, 255))
        self.table.update_table.connect(self.draw_table)
        self.draw_table()

    def load_assets(self):
        pass

    def draw_table(self, **kwargs):
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.table.background, self.table.get_pos())
        for player in self.table.players:
            self.screen.blit(player.deck_surface, player.get_pos())
        for playerzone in self.table.players_playzone:
            self.screen.blit(playerzone.deck_surface, playerzone.get_pos())
        self.screen.blit(self.table.announcer, (self.table.announcer_x, self.table.announcer_y))

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
                        print('add cards')
                        pass

            milliseconds = self.clock.tick(self.fps)
            #self.playtime += milliseconds / 1000.0

            #self.draw_function()

            #pygame.display.flip()
            #self.screen.blit(self.background, (0, 0))

        pygame.quit()


if __name__ == '__main__':

    main_view = GameScreen(640, 400, clear_colour=(255, 0, 0))

    main_view.run()