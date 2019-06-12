import pygame
import view
from signalslot import Signal


class GenericUI:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.visible = True
        self.clear_colour = (0, 0, 0)

class Button(GenericUI):
    clicked = Signal()

    def __init__(self, x, y, width, height, texts=[], text_size=25):
        super().__init__(x, y, width, height)


class ScrollList(GenericUI):

    def __init__(self, x, y, width, height, texts=[], text_size=25):
        super().__init__(x, y, width, height)

        self.background = pygame.Surface((self.width, self.height))
        self.background.fill(self.clear_colour)
        self.background.set_colorkey(self.clear_colour)
        self.background = self.background.convert()
        self.font = pygame.font.SysFont("None", text_size)
        self.texts = texts
        self.text_rects = []
        self.y_offset = 0
        self.selected = -1
        self.outline_thickness = 3

        current_y = self.outline_thickness
        for text in texts:
            rendered_text = self.font.render(text, True, (0, 64, 192)).convert_alpha()
            text_rect = rendered_text.get_rect()
            text_rect.x = 0
            text_rect.y = current_y
            text_rect.width = self.width
            self.text_rects.append(text_rect)
            current_y += text_rect.height
        self.max_offset = max(0, current_y-self.height-self.outline_thickness)
        self.redraw()

    def redraw(self):
        self.background.fill(self.clear_colour)
        if self.visible:
            outline = (0, 0, self.rect.w, self.rect.h)
            pygame.draw.rect(self.background, (255, 0, 0), outline, self.outline_thickness)
            i = 0
            for text, text_rect in zip(self.texts, self.text_rects):
                if i == self.selected:
                    pygame.draw.rect(self.background, (255, 0, 0), text_rect)
                rendered_text = self.font.render(text, True, (255, 255, 192)).convert_alpha()

                self.background.blit(rendered_text, text_rect)
                i += 1

    def offset_text_rects(self, offset):
        self.y_offset += offset
        if -self.max_offset <= self.y_offset <= 0:
            for text_rect in self.text_rects:
                text_rect.y += offset
        self.y_offset = max(-self.max_offset, self.y_offset)
        self.y_offset = min(0, self.y_offset)


    def scroll_down(self, offset=10):
        """
        To scroll down, all elements should shift up
        :param offset:
        :return:
        """
        self.offset_text_rects(-offset)
        self.redraw()

    def scroll_up(self, offset=10):
        self.offset_text_rects(offset)
        self.redraw()

    def check_click_pos(self, pos):
        relative_pos_x = pos[0] - self.x
        relative_pos_y = pos[1] - self.y
        mouse_pos = (relative_pos_x, relative_pos_y)
        for i, rect in enumerate(self.text_rects):
            if rect.collidepoint(mouse_pos):
                self.selected = i
                self.redraw()
                return

    def get_pos(self):
        return self.x, self.y


class TestScreen(view.PygView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        texts = [str(i) for i in range(20)]

        self.scroll_menu = ScrollMenu(100, 100, 100, 200, texts=texts)

        self.double_clicking = False
        self.left_mouse_down = False
        self.double_click_event = pygame.USEREVENT + 1

    def draw_function(self):
        self.screen.blit(self.scroll_menu.background, self.scroll_menu.get_pos())

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                if event.type == pygame.MOUSEBUTTONUP:
                    mouse_pos = pygame.mouse.get_pos()
                    if event.button == 1:
                        print('mouse click')
                        if self.scroll_menu.rect.collidepoint(mouse_pos):
                            print('here')
                            self.scroll_menu.check_click_pos(mouse_pos)

                        if self.double_clicking:
                            pygame.time.set_timer(self.double_click_event, 0)
                            print('Double clicked')
                            self.double_clicking = False
                        else:
                            self.double_clicking = True
                            pygame.time.set_timer(self.double_click_event, 200)

                    if self.scroll_menu.rect.collidepoint(mouse_pos):
                        if event.button == 4:
                            self.scroll_menu.scroll_up()
                        if event.button == 5:
                            self.scroll_menu.scroll_down()

                if event.type == self.double_click_event:
                    pygame.time.set_timer(self.double_click_event, 0)
                    self.double_clicking = False
                    print('double click disabled')

            self.draw_function()

            pygame.display.flip()
            self.screen.blit(self.background, (0, 0))

        pygame.quit()


if __name__ == '__main__':
    test_view = TestScreen(640, 400, clear_colour=(0, 0, 0))
    test_view.run()
