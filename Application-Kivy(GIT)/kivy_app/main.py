from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from queue import Queue, Empty
import requests
import speech_recognition as sr
import pyttsx3
import threading
import os
import pygame

# Constants
FLASK_URL = "http://127.0.0.1:5000/ask"
STARTUP_SOUND = "startup.mp3"

class JarvisApp(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.padding = "10dp"
        self.spacing = "10dp"
        self.speaking = False
        self.speech_queue = Queue()

        self.speech_engine = pyttsx3.init()
        self.speech_engine.setProperty("rate", 170)
        self.speech_engine.setProperty("volume", 1.0)

        voices = self.speech_engine.getProperty('voices')
        if voices:
            for voice in voices:
                if "en" in voice.languages:
                    self.speech_engine.setProperty('voice', voice.id)
                    break

        self.startup_label = MDLabel(
            text="Initializing J.A.R.V.I.S...",
            halign="center",
            theme_text_color="Custom",
            text_color=(0, 1, 1, 1),
            font_style="H5",
        )
        self.add_widget(self.startup_label)

        Clock.schedule_once(self.startup_sequence, 2)

    def startup_sequence(self, dt):
        messages = [
            "Systems Online...",
            "Voice Interface Ready...",
            "Awaiting Command..."
        ]
        for i, msg in enumerate(messages):
            Clock.schedule_once(lambda dt, m=msg: setattr(self.startup_label, 'text', m), i * 1.2)
        
        Clock.schedule_once(lambda dt: (self.remove_widget(self.startup_label), self.init_ui()), len(messages) * 1.2)
        
        if os.path.exists(STARTUP_SOUND):
            threading.Thread(target=self.play_startup_sound, daemon=True).start()

    def play_startup_sound(self):
        pygame.mixer.init()
        pygame.mixer.music.load(STARTUP_SOUND)
        pygame.mixer.music.play()

    def init_ui(self):
        self.label = MDLabel(
            text="🎙️ Ask J.A.R.V.I.S.",
            halign="center",
            theme_text_color="Custom",
            text_color=(0, 1, 1, 1),
            font_style="H4"
        )
        self.add_widget(self.label)

        self.scroll_view = MDScrollView()
        self.chat_history = MDLabel(
            text="Jarvis: Awaiting input...",
            theme_text_color="Custom",
            text_color=(0, 1, 1, 1),
            halign="left",
            size_hint_y=None,
            text_size=(self.width, None)
        )
        self.scroll_view.add_widget(self.chat_history)
        self.add_widget(self.scroll_view)

        self.text_input = MDTextField(
            hint_text="Type your message...",
            size_hint_x=0.9,
            pos_hint={"center_x": 0.5},
            on_text_validate=self.send_message
        )
        self.add_widget(self.text_input)

        button_layout = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="48dp",
            padding="5dp"
        )

        self.speak_button = MDIconButton(
            icon="microphone",
            on_release=self.speech_to_text,
            theme_text_color="Custom",
            text_color=(0, 1, 0, 1)
        )
        self.send_button = MDRaisedButton(
            text="Send",
            md_bg_color=(0, 0.6, 1, 1),
            on_release=self.send_message
        )

        button_layout.add_widget(self.speak_button)
        button_layout.add_widget(self.send_button)
        self.add_widget(button_layout)

        Window.bind(on_key_down=self._on_key_down)

    def _on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if keycode == 40:  # Enter key
            self.send_message(None)

    def send_message(self, instance):
        user_message = self.text_input.text.strip()
        if not user_message:
            return
        
        self.append_chat("You", user_message)
        self.text_input.text = ""

        threading.Thread(target=self.fetch_response, args=(user_message,), daemon=True).start()

    def fetch_response(self, message):
        try:
            response = requests.post(FLASK_URL, json={"message": message}, timeout=None)
            if response.status_code == 200:
                ai_response = response.json().get("response", "No response from AI")
            else:
                ai_response = "Server Error: " + str(response.status_code)
        except requests.exceptions.RequestException:
            ai_response = "Error: Could not connect to server!"
        
        Clock.schedule_once(lambda dt: self.append_chat("Jarvis", ai_response))
        self.speech_queue.put(ai_response)
        if not self.speaking:
            self.start_speaking()

    def append_chat(self, speaker, message):
        current_text = self.chat_history.text
        new_entry = f"\n\n👤 You: {message}" if speaker == "You" else f"\n🤖 Jarvis: {message}"
        self.chat_history.text = current_text + new_entry
        self.chat_history.texture_update()
        self.chat_history.height = self.chat_history.texture_size[1]
        self.scroll_view.scroll_y = 0

    def start_speaking(self):
        if self.speaking:
            return

        def speak():
            self.speaking = True
            while True:
                try:
                    message = self.speech_queue.get_nowait()
                except Empty:
                    break
                self.speech_engine.say(message)
                self.speech_engine.runAndWait()
            self.speaking = False

        threading.Thread(target=speak, daemon=True).start()

    def speech_to_text(self, instance):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.append_chat("Jarvis", "🎙️ Listening...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                user_message = recognizer.recognize_google(audio)
                self.text_input.text = user_message
                self.send_message(None)
            except sr.UnknownValueError:
                self.append_chat("Jarvis", "Sorry, I didn't catch that.")
            except sr.RequestError:
                self.append_chat("Jarvis", "Error: Speech recognition service unavailable.")
            except Exception as e:
                self.append_chat("Jarvis", f"Error: {str(e)}")

class JarvisMobileApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        self.theme_cls.theme_style = "Dark"
        return JarvisApp()

if __name__ == "__main__":
    JarvisMobileApp().run()
