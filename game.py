import kivy
kivy.require('1.9.1')

from os.path import join, exists
from random import random
from kivy.app import App
from kivy.base import EventLoop
from kivy.animation import Animation
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.metrics import dp

class Message(Label):
    text = StringProperty()
    fadeout = NumericProperty(2.)

    def on_text(self, instance, value):
        fade = Animation(opacity=1, duration=2.)
        if self.fadeout:
             fade += Animation(duration=self.fadeout)
             fade += Animation(opacity=0, duration=2.)
        fade.start(self)

class Movement(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def move(self, *args):
        self.pos = Vector(*self.velocity) + self.pos

class PowerUp(Movement):
    bonus_type = 0
    score = 10

class Block(Widget):
    curr_life = NumericProperty(1)
    block_type = NumericProperty(0)
    score = NumericProperty(10)

    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            self.curr_life -= 1
            offset_x = abs((ball.center_x - self.center_x) / (self.width / 2))
            if offset_x > 1:
                ball.velocity_x = -1 * ball.velocity_x
            else:
                ball.velocity_y = -1 * ball.velocity_y
            if self.curr_life <= 0:
                return self.score

    def on_curr_life(self, instance, value):
        if value <= 0:
            self.block_type = 0
            self.canvas.clear()
            if random() < 0.2:
                bonus = PowerUp()
                bonus.center = self.center
                bonus.velocity_y = dp(-4)
                self.add_widget(bonus)
                self.parent.parent.parent.bonus.append(bonus)

class GameBlocks(BoxLayout):
    data = {'title': False, 'blocks': []}
    blocks_left = NumericProperty(0)

    def level_file(self, file):
        return join('Level', file + '.txt')

    def load_level(self, level='default'):
        if not exists(self.level_file(level)):
            return False
        self.data = {'title': False, 'blocks': []}
        with open(self.level_file(level)) as f:
            for line in f:
                try:
                    index = line.index('[') + 1
                    end = line.index(']')
                    if not self.data['title']:
                        self.data['title'] = line[index:end]
                except ValueError:
                    try:
                        line.index(',')
                        a = line.split(',')
                        row = []
                        for b in a:
                            row.append(b.strip().split(':'))
                        self.data['blocks'].append(row)
                    except:
                        pass
        return self.data['title']

    def render_blocks(self):
        self.clear_widgets()
        for r in self.data['blocks']:
            row = BoxLayout(orientation='horizontal')
            for data in r:
                block = Block()
                block.block_type = int(data[0])
                block.curr_life = int(data[1])
                block.score = int(data[1]) * 10
                if not int(data[0]):
                    block.opacity = 0
                else:
                    self.blocks_left += 1
                row.add_widget(block)
            self.add_widget(row)
            
class GamePaddle(Movement):
    def bounce_ball(self, ball):
        if (self.collide_widget(ball) and ball.y > dp(50) and ball.velocity_y != 0):
            vx, vy = ball.velocity
            offset = (ball.center_x - self.center_x) / 15
            ball.velocity = offset, -1 * vy + dp(0.1)

class GameBall(Movement):
    pass

class BlockBusterGame(Widget):
    score = NumericProperty(0)
    life = NumericProperty(3)
    player = ObjectProperty(None)
    ball = ObjectProperty(None)
    game_blocks = ObjectProperty(None)
    message = ObjectProperty(None)
    title = StringProperty()
    main_menu = 'menu'
    move_enabled = False
    bonus = []

    def __init__(self, **kwargs):
        super(BlockBusterGame, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 1.0 / 60.0)
        Clock.schedule_once(self.enable_move, 6.0)
        EventLoop.window.bind(on_key_down=self._on_keyboard)
        EventLoop.window.bind(on_key_up=self._on_keyboard_up)

    def enable_move(self, *args):
        self.move_enabled = True

    def serve_ball(self, vel=(0, 0)):
        self.ball.center_x = self.player.center_x
        self.ball.center_y = dp(70)
        self.ball.velocity = vel

    def blocks_interact(self):
        # handle bonuses
        for i in range(len(self.bonus)):
            self.bonus[i].move()
            if self.bonus[i].collide_widget(self.player):
                bonus = self.bonus.pop(i)
                self.score += bonus.score
                bonus.parent.remove_widget(bonus)
            elif self.bonus[i].y <= 0:
                bonus = self.bonus.pop(i)
                bonus.parent.remove_widget(bonus)

        # check for box hitting
        for row in self.game_blocks.children:
            for block in row.children:
                # ignore if invisible/destroyed
                if block.block_type:
                    s = block.bounce_ball(self.ball)
                    if s:
                        self.score += s
                        self.game_blocks.blocks_left -= 1
                        return # avoid destroying more than one block at a time

    def update(self, dt):
        if not self.move_enabled: return
        self.ball.move()
        self.player.move()

        # bounce off blocks and handle bonuses
        self.blocks_interact()

        # bounce ball off paddles
        self.player.bounce_ball(self.ball)

        # bounce ball off sides and top
        if (self.ball.x < self.x) or (self.ball.x > self.width - self.ball.width):
            self.ball.velocity_x *= -1
        if self.ball.top > self.height:
            self.ball.velocity_y *= -1

        # move ball together with paddle if ball is stopped
        if self.ball.velocity_y == 0:
            self.ball.center_x = self.player.center_x

        # loose a life if falls off bottom
        if self.ball.y < self.y:
            self.life -= 1
            self.serve_ball()

        # end game if no blocks left
        if self.game_blocks.blocks_left <= 0:
            self.message.fadeout = 0
            self.message.text = 'Congratulations!'
            self.move_enabled = False
            Clock.schedule_once(self.back, 6)

    # keyboard control of the paddle
    def _on_keyboard(self, window, key, *largs):
        if key == 276: #left
            self.player.velocity_x = dp(-5)
        elif key == 275: #right
            self.player.velocity_x = dp(5)
        elif key == 32: #spacebar
            if not self.move_enabled: return
            if self.ball.velocity_y == 0:
                self.ball.velocity_y = dp(4)
        elif key == 27: #escape
            self.back()
        else:
            self.player.velocity_x = 0
        return True
            
    def _on_keyboard_up(self, *args):
        self.player.velocity_x = 0

    def on_touch_move(self, touch):
        if not self.move_enabled: return
        # move paddle
        if touch.y < dp(100):
            self.player.center_x = touch.x

    def on_touch_up(self, touch):
        if not self.move_enabled: return
        # launch ball if sitting on paddle
        if self.ball.velocity_y == 0:
            self.ball.velocity_y = dp(4)

    def on_life(self, instance, value):
        # Game Over if run out of lives
        if value <= 0:
            self.message.fadeout = 0
            self.message.text = 'Game Over'
            self.move_enabled = False
            Clock.schedule_once(self.back, 6)

    def on_title(self, instance, value):
        self.message.text = value

    def back(self, *args):
        App.get_running_app().root.current = self.main_menu

class GameApp(App):
    def build(self):
        root = BlockBusterGame()
        title = root.game_blocks.load_level()
        root.title = title
        root.game_blocks.render_blocks()
        root.serve_ball()
        return root

if __name__ == '__main__':
    GameApp().run()
