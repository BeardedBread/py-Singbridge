import view
import pygame


class game_screen(view.PygView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def load_assets(self):
        pass

    def draw_function(self):
        pass

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

    main_view = game_screen(640, 400, clear_colour=(255, 0, 0))

    main_view.run()