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
        self.outline_colour = (255, 0, 0)
        self.text_colour = (255, 255, 255)

        self.background = pygame.Surface((self.width, self.height))
        self.background.fill(self.clear_colour)
        self.background.set_colorkey(self.clear_colour)
        self.background = self.background.convert()

        self.hold_function = None
        self.release_function = None

        self.parent = None
        self.children = None

    def process_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.hold_function and self.collide_at(mouse_pos):
                self.hold_function(mouse_pos)

        if event.type == pygame.MOUSEBUTTONUP:
            mouse_pos = pygame.mouse.get_pos()
            if self.release_function and self.collide_at(mouse_pos):
                mouse_pos = pygame.mouse.get_pos()
                if event.button == 1:
                    print('mouse click')
                    self.release_function(mouse_pos)

    def collide_at(self, pos):
        x0, y0 = self.get_offset_pos()
        rect_check = pygame.rect.Rect(x0, y0, self.rect.width, self.rect.height)
        return rect_check.collidepoint(pos)

    def redraw(self):
        self.background.fill(self.clear_colour)

    def get_pos(self):
        return self.x, self.y

    def get_offset_pos(self):
        x, y = 0, 0
        if self.parent:
            x, y = self.parent.get_offset_pos()

        return x+self.x, y+self.y

    def set_pos(self, x, y):
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

class TextBox(GenericUI):
    def __init__(self, x, y, width, height, text='Button', text_size=25):
        super().__init__(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont("None", text_size)
        self.outline_thickness = 3

        self.redraw()

    def redraw(self):
        super().redraw()
        if self.visible:
            outline = (0, 0, self.rect.w, self.rect.h)
            pygame.draw.rect(self.background, self.outline_colour, outline, self.outline_thickness)
            rendered_text = self.font.render(self.text, True, self.text_colour).convert_alpha()
            rect_center = self.background.get_rect().center
            text_rect = rendered_text.get_rect(center=rect_center)
            self.background.blit(rendered_text, text_rect)


class Button(TextBox):

    clicked = Signal()

    def __init__(self, x, y, width, height, text='Button', text_size=25):
        self.button_down = False

        super().__init__(x, y, width, height, text=text, text_size=text_size)
        self.hold_function = self.hold
        self.release_function = self.release

        self.redraw()

    def redraw(self):
        if self.button_down:
            self.background.fill((255, 255, 255))
        else:
            super().redraw()
        if self.visible:
            outline = (0, 0, self.rect.w, self.rect.h)
            pygame.draw.rect(self.background, self.outline_colour, outline, self.outline_thickness)
            rendered_text = self.font.render(self.text, True, self.text_colour).convert_alpha()
            rect_center = self.background.get_rect().center
            text_rect = rendered_text.get_rect(center=rect_center)
            self.background.blit(rendered_text, text_rect)

    def hold(self, *args):
        if not self.button_down:
            self.button_down = True
            self.redraw()

    def release(self, *args):
        if self.button_down:
            self.button_down = False
            self.redraw()


class ScrollList(GenericUI):
    selected = Signal()

    def __init__(self, x, y, width, height, texts, text_size=25):
        super().__init__(x, y, width, height)

        self.font = pygame.font.SysFont("None", text_size)
        self.texts = texts
        self.text_rects = []
        self.y_offset = 0
        self.selected = -1
        self.outline_thickness = 3
        self.selected_colour = (255, 0, 0)
        self.max_offset = 0

        self.replace_list(texts)
        self.release_function = self.check_click_pos


    def redraw(self):
        super().redraw()
        if self.visible:
            outline = (0, 0, self.rect.w, self.rect.h)
            pygame.draw.rect(self.background, self.outline_colour, outline, self.outline_thickness)
            i = 0
            for text, text_rect in zip(self.texts, self.text_rects):
                if i == self.selected:
                    pygame.draw.rect(self.background, self.selected_colour, text_rect)
                rendered_text = self.font.render(text, True, self.text_colour).convert_alpha()

                self.background.blit(rendered_text, text_rect)
                i += 1

    def process_events(self, event):
        super().process_events(event)
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_pos = pygame.mouse.get_pos()
            if self.collide_at(mouse_pos):
                if event.button == 4:
                    self.scroll_up()
                if event.button == 5:
                    self.scroll_down()

    def offset_text_rects(self, offset):
        prev_offset = self.y_offset
        self.y_offset += offset
        self.y_offset = max(-self.max_offset, self.y_offset)
        self.y_offset = min(0, self.y_offset)
        #if -self.max_offset <= self.y_offset <= 0:
        for text_rect in self.text_rects:
            text_rect.y += self.y_offset - prev_offset

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

    def check_click_pos(self, *args):
        pos = args[0]
        relative_pos_x = pos[0] - self.x
        relative_pos_y = pos[1] - self.y
        mouse_pos = (relative_pos_x, relative_pos_y)
        for i, rect in enumerate(self.text_rects):
            if rect.collidepoint(mouse_pos):
                self.selected = i
                self.redraw()
                return

    def reset_scroll(self):
        self.offset_text_rects(-self.y_offset)

    def add_item(self, text):
        prev_offset = self.y_offset
        self.reset_scroll()
        self.texts.append(text)
        current_y = self.text_rects[-1].y + self.text_rects[-1].height
        rendered_text = self.font.render(text, True, self.text_colour).convert_alpha()
        text_rect = rendered_text.get_rect()
        text_rect.x = 0
        text_rect.y = current_y
        text_rect.width = self.width
        self.text_rects.append(text_rect)
        self.max_offset = max(0, self.max_offset+text_rect.height)
        self.offset_text_rects(prev_offset)
        self.scroll_down(text_rect.height)
        self.redraw()

    def remove_item(self, pos=-1):
        prev_offset = self.y_offset
        self.reset_scroll()
        n_items = len(self.texts)
        if self.texts and 0 <= pos < n_items:
            print('removing')
            self.texts.pop(pos)
            text_rect = self.text_rects.pop(pos)
            self.selected = min(self.selected, n_items-2)
            if self.texts and pos < len(self.texts):
                for rect in self.text_rects[pos:]:
                    rect.y -= text_rect.height
            self.max_offset = max(0, self.max_offset-text_rect.height)
            self.offset_text_rects(prev_offset)
            self.scroll_up(text_rect.height)
            self.redraw()

    def replace_list(self, texts):
        self.texts = texts
        self.text_rects = []
        current_y = self.outline_thickness
        self.selected = -1
        for text in texts:
            rendered_text = self.font.render(text, True, self.text_colour).convert_alpha()
            text_rect = rendered_text.get_rect()
            text_rect.x = 0
            text_rect.y = current_y
            text_rect.width = self.width
            self.text_rects.append(text_rect)
            current_y += text_rect.height
        self.max_offset = max(0, current_y - self.height - self.outline_thickness)
        self.redraw()


class CallPanel(GenericUI):
    """
    The panel to contain the UI for the player to make bids and call a partner.
    """
    send_output = Signal()

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

        self.text_size = 20
        margins = 5
        ui_width = 75
        ui_height = 25
        width_spacings = (width - 3 * ui_width - 2 * margins) / 4
        height_spacings = (height - 2 * margins - 2 * ui_height) / 3

        self.label1 = TextBox(margins+width_spacings, margins,
                              ui_width, ui_height, text='List1', text_size=self.text_size)
        self.list1 = ScrollList(margins+width_spacings, margins+ui_height,
                                ui_width, height - 2*margins-ui_height,
                                texts=[str(i) for i in range(4)], text_size=self.text_size)
        self.label2 = TextBox(margins+width_spacings*2+ui_width, margins,
                              ui_width, ui_height, text='List2', text_size=self.text_size)
        self.list2 = ScrollList(margins+width_spacings*2+ui_width, margins+ui_height,
                                ui_width, height - 2*margins-ui_height,
                                texts=['a', 'b', 'c', 'd'], text_size=self.text_size)

        self.output_box = TextBox(margins+width_spacings*3+ui_width*2, margins+height_spacings,
                                  ui_width, ui_height, text_size=self.text_size)

        self.confirm_button = Button(margins+width_spacings*3+ui_width*2, margins+height_spacings*2,
                                     ui_width, ui_height, text='OK', text_size=self.text_size)

        self.children = [self.label1, self.list1, self.label2, self.list2,
                         self.confirm_button, self.output_box]
        for element in self.children:
            element.parent = self

        self.redraw()

    def redraw(self):
        super().redraw()
        for element in self.children:
            self.background.blit(element.background, element.get_pos())

    def process_events(self, event):
        for element in self.children:
            element.process_events(event)
        self.redraw()


class TestScreen(view.PygView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        texts = [str(i) for i in range(20)]

        self.scroll_menu = ScrollList(100, 100, 100, 200, texts=texts)
        self.button = Button(300, 100, 50, 25, text_size=18)
        self.textbox = TextBox(300, 250, 200, 100, text="Test")
        self.panel = CallPanel(0, 0, 300, 150)

        #[self.scroll_menu, self.button, self.textbox]
        self.elements = [self.panel]

        self.double_clicking = False
        self.left_mouse_down = False
        self.double_click_event = pygame.USEREVENT + 1

    def draw_function(self):
        for element in self.elements:
            self.screen.blit(element.background, element.get_pos())
            self.screen.blit(element.background, element.get_pos())

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_o:
                        self.scroll_menu.add_item(str('A'))
                    if event.key == pygame.K_p:
                        self.scroll_menu.remove_item(0)
                    if event.key == pygame.K_i:
                        self.scroll_menu.replace_list(['a','b','c'])

                for element in self.elements:
                    element.process_events(event)

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        print('mouse click')
                        if self.double_clicking:
                            pygame.time.set_timer(self.double_click_event, 0)
                            print('Double clicked')
                            self.double_clicking = False
                        else:
                            self.double_clicking = True
                            pygame.time.set_timer(self.double_click_event, 200)

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
