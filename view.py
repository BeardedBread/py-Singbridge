import pygame


class PygView(object):

    def __init__(self, width=640, height=400, fps=60, clear_colour=(0, 0, 0)):
        """Initialize pygame, window, background, font,...
        """
        pygame.init()
        pygame.display.set_caption("Press ESC to quit")
        self.width = width
        self.height = height
        #self.height = width // 4
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)
        self.background = pygame.Surface(self.screen.get_size())
        self.background.fill(clear_colour)
        self.background = self.background.convert()
        self.clock = pygame.time.Clock()
        self.fps = fps
        #self.playtime = 0.0
        self.font = pygame.font.SysFont('mono', 20, bold=True)

    def run(self):
        """The mainloop
        """
        pass
