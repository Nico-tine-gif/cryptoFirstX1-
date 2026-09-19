import os
os.environ['KIVY_NO_ARGS'] = '1'

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

class CryptoFirstX1Layout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10

        self.add_widget(Label(text='[b]CryptoFirstX1[/b]', markup=True, font_size='24sp', size_hint_y=0.2))

        self.output = TextInput(text='Ready...', readonly=True, size_hint_y=0.5, background_color=(0.1, 0.1, 0.1, 1))
        self.add_widget(self.output)

        self.run_btn = Button(text='Run Core Logic', size_hint_y=0.2, background_color=(0.2, 0.6, 0.2, 1))
        self.run_btn.bind(on_press=self.run_logic)
        self.add_widget(self.run_btn)

    def run_logic(self, instance):
        self.output.text = "Running...\n"
        Clock.schedule_once(self._execute_core, 0.1)

    def _execute_core(self, dt):
        try:
            # REPLACE THIS WITH YOUR ACTUAL CORE CODE LATER
            result = "Project Loaded Successfully!\n\n"
            result += "Core modules found in /core\n"
            result += "Blockchain monitor ready.\n"
            result += "P9/P10 Security gates active.\n"
            self.output.text = result
        except Exception as e:
            self.output.text = f"Error: {str(e)}"

class CryptoFirstX1App(App):
    def build(self):
        return CryptoFirstX1Layout()

if __name__ == '__main__':
    CryptoFirstX1App().run()
