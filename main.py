import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.base import EventLoop
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from game import BlockBusterGame

class MenuScreen(Screen):
    def load_game(self):
        if self.manager.has_screen('game_screen'):
            self.manager.remove_widget(self.manager.get_screen('game_screen'))
        game_screen = GameScreen(name='game_screen')
        game_screen.level = 'default'
        self.manager.add_widget(game_screen)
        self.manager.current = 'game_screen'

class LevelScreen(Screen):
    def load_level(self, level='default'):
        if self.manager.has_screen('game_screen'):
            self.manager.remove_widget(self.manager.get_screen('game_screen'))
        game_screen = GameScreen(name='game_screen')
        game_screen.level = level
        self.manager.add_widget(game_screen)
        self.manager.current = 'game_screen'

class GameScreen(Screen):
    level = StringProperty()
    
    def on_level(self, instance, value):
        self.clear_widgets()
        game = BlockBusterGame()
        title = game.game_blocks.load_level(self.level)
        game.title = title
        game.game_blocks.render_blocks()
        game.serve_ball()
        self.add_widget(game)

class MainApp(App):
    def build(self):
        Builder.load_file('game.kv')
        EventLoop.window.bind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, window, key, *largs):
        if key == 27: #escape
            self.root.current = 'menu'
        return True

if __name__ == '__main__':
    MainApp().run()
