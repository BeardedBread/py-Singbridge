import pygame
import view
from signalslot import Signal


class GenericUI:
    def __init__(self, x, y, width, height):
        self.draw_update = Signal()

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.visible = True
        self.clear_colour = (0, 0, 0)
        self.outline_colour = (255, 0, 0)
        self.outline_thickness = 3
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
        draw_update = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.hold_function and self.collide_at(mouse_pos):
                if event.button == 1:
                    self.hold_function(mouse_pos)
                    draw_update = True

        if event.type == pygame.MOUSEBUTTONUP:
            mouse_pos = pygame.mouse.get_pos()
            if self.release_function and self.collide_at(mouse_pos):
                if event.button == 1:
                    #print('mouse click')
                    self.release_function(mouse_pos)
                    draw_update = True

        return draw_update

    def collide_at(self, pos):
        x0, y0 = self.get_offset_pos()
        #print(x0, y0, pos)
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
        #if self.visible:
        outline = (0, 0, self.rect.w, self.rect.h)
        pygame.draw.rect(self.background, self.outline_colour, outline, self.outline_thickness)
        rendered_text = self.font.render(self.text, True, self.text_colour).convert_alpha()
        rect_center = self.background.get_rect().center
        text_rect = rendered_text.get_rect(center=rect_center)
        self.background.blit(rendered_text, text_rect)

    def set_text(self, text):
        self.text = text
        self.redraw()


class Button(TextBox):

    def __init__(self, x, y, width, height, text='Button', text_size=25):
        self.button_down = False
        self.clicked = Signal()

        super().__init__(x, y, width, height, text=text, text_size=text_size)
        self.hold_function = self.hold
        self.release_function = self.release

        self.redraw()

    def redraw(self):
        if self.button_down:
            self.background.fill((255, 255, 255))
        else:
            super().redraw()
        #if self.visible:
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
            self.clicked.emit()
            self.redraw()


class ScrollList(GenericUI):

    def __init__(self, x, y, width, height, texts, text_size=25):
        super().__init__(x, y, width, height)
        self.list_selected = Signal(args=['text'])

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

    @property
    def selected(self):
        return self.__selected

    @selected.setter
    def selected(self, selected):
        if selected < 0:
            self.list_selected.emit(text='')
        else:
            self.list_selected.emit(text=self.texts[selected])
        self.__selected = selected

    def redraw(self):
        super().redraw()
        #if self.visible:
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
        draw_update = super().process_events(event)
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_pos = pygame.mouse.get_pos()
            if self.collide_at(mouse_pos):
                if event.button == 4:
                    self.scroll_up()
                    draw_update = True
                if event.button == 5:
                    self.scroll_down()
                    draw_update = True
        return draw_update

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
        x0, y0 = self.get_offset_pos()
        relative_pos_x = pos[0] - x0
        relative_pos_y = pos[1] - y0
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
        self.max_offset = max(0, current_y - self.height)
        self.redraw()
        self.draw_update.emit()


class CallPanel(GenericUI):
    """
    The panel to contain the UI for the player to make bids and call a partner.
    """

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.background.set_colorkey(None)
        self.confirm_output = Signal(args=['output'])

        self.text_size = 20
        margins = 5
        ui_width = 80
        ui_height = 25
        width_spacings = (width - 2.5 * ui_width - 2 * margins) / 4
        height_spacings = (height - 2 * margins - 3 * ui_height) / 4
        self.output_text = ['', '']

        self.list1 = ScrollList(margins+width_spacings, margins,
                                ui_width/2, height - 2*margins,
                                texts=[str(i) for i in range(20)], text_size=self.text_size)
        self.list1.list_selected.connect(lambda text, **z: self.print_list_selection(text, 0))

        self.list2 = ScrollList(margins+width_spacings*2+ui_width/2, margins,
                                ui_width, height - 2*margins,
                                texts=['a', 'b', 'c', 'd'], text_size=self.text_size)
        self.list2.list_selected.connect(lambda text, **z: self.print_list_selection(text, 1))

        self.output_box = TextBox(margins+width_spacings*3+ui_width*1.5, margins+height_spacings,
                                  ui_width, ui_height, text='-', text_size=self.text_size)

        self.confirm_button = Button(margins+width_spacings*3+ui_width*1.5, margins+height_spacings*2+ui_height,
                                     ui_width, ui_height, text='Call', text_size=self.text_size)
        self.confirm_button.clicked.connect(self.emit_output)
        self.cancel_button = Button(margins + width_spacings * 3 + ui_width * 1.5,
                                     margins + height_spacings * 3 + ui_height * 2,
                                     ui_width, ui_height, text='Pass', text_size=self.text_size)

        self.cancel_button.visible = False
        self.cancel_button.clicked.connect(self.cancelling)
        #self.children = [self.label1, self.list1, self.label2, self.list2,
        self.children = [self.list1, self.list2,
                         self.confirm_button, self.output_box, self.cancel_button]
        for element in self.children:
            element.parent = self

        self.redraw()

    def redraw(self, **kwargs):
        super().redraw()
        #self.background.fill((255,0,255))
        #if self.visible:
        outline = (0, 0, self.rect.w, self.rect.h)
        pygame.draw.rect(self.background, self.outline_colour, outline, self.outline_thickness)

        for element in self.children:
            if element.visible:
                self.background.blit(element.background, element.get_pos())

    def process_events(self, event):
        draw_update = False
        for element in self.children:
            if element.visible and element.process_events(event):
                draw_update = True

        if draw_update:
            self.redraw()
            return draw_update

    def print_list_selection(self, text, num,**kwargs):
        self.output_text[num] = text
        self.output_box.set_text(' '.join(self.output_text))

    def emit_output(self, **kwargs):
        initial = ''
        if self.output_text[1]:
            initial = self.output_text[1][0].lower()

        output = self.output_text[0].lower() + initial
        self.confirm_output.emit(output=output)

    def cancelling(self, **kwargs):
        self.confirm_output.emit(output='')


class TestScreen(view.PygView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        texts = [str(i) for i in range(20)]

        self.scroll_menu = ScrollList(100, 100, 100, 200, texts=texts)
        self.button = Button(300, 100, 50, 25, text_size=18)
        self.textbox = TextBox(300, 250, 200, 100, text="Test")
        self.panel = CallPanel(100, 100, 300, 150)
        #self.panel.confirm_output.connect(self.print_panel_output)

        #[self.scroll_menu, self.button, self.textbox]
        self.elements = [self.panel]

        self.double_clicking = False
        self.left_mouse_down = False
        self.double_click_event = pygame.USEREVENT + 1

        self.draw_function()

        pygame.display.flip()
        self.screen.blit(self.background, (0, 0))

    def draw_function(self):
        for element in self.elements:
            self.screen.blit(element.background, element.get_pos())
            self.screen.blit(element.background, element.get_pos())

    #def print_panel_output(self, output, **kwargs):
    #    print(output)

    def run(self):
        running = True
        while running:
            draw_update = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    if event.key == pygame.K_o:
                        self.panel.list1.replace_list([str(i+1) for i in range(7)])
                        draw_update = True

                for element in self.elements:
                    if element.process_events(event):
                        draw_update = True

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

            if draw_update:
                self.draw_function()

                pygame.display.flip()
                self.screen.blit(self.background, (0, 0))

        pygame.quit()


if __name__ == '__main__':
    test_view = TestScreen(640, 400, clear_colour=(0, 0, 0))
    test_view.run()
