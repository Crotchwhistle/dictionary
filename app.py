import sys
import requests
import json
import webbrowser
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QMessageBox, QLabel, QScrollArea, QDialog
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from bs4 import BeautifulSoup
from PyQt5.QtGui import QPixmap

BASE_URL = 'https://api.dictionaryapi.dev/api/v2/entries/en/'
CACHE_FILE = 'cache.json'

class DictionaryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.cache = self.load_cache()
        self.initUI()
        self.player = QMediaPlayer()

    def initUI(self):
        self.setWindowTitle('Dictionary App')

        layout = QVBoxLayout()

        self.word_input = QLineEdit(self)
        self.word_input.setPlaceholderText('Enter a word')
        layout.addWidget(self.word_input)

        self.definition_button = QPushButton('Get Definition', self)
        self.definition_button.clicked.connect(self.get_definition)
        layout.addWidget(self.definition_button)

        self.synonyms_button = QPushButton('Get Synonyms', self)
        self.synonyms_button.clicked.connect(self.get_synonyms)
        layout.addWidget(self.synonyms_button)

        self.pronunciation_button = QPushButton('Hear Pronunciation', self)
        self.pronunciation_button.clicked.connect(self.hear_pronunciation)
        layout.addWidget(self.pronunciation_button)

        self.open_images_button = QPushButton('Open Images in Browser', self)
        self.open_images_button.clicked.connect(self.open_images_in_browser)
        layout.addWidget(self.open_images_button)

        self.result_area = QTextEdit(self)
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        self.clear_cache_button = QPushButton('Clear Cache', self)
        self.clear_cache_button.clicked.connect(self.clear_cache)
        layout.addWidget(self.clear_cache_button)

        self.setLayout(layout)

    def fetch_data(self, word, data_type):
        if word in self.cache and data_type in self.cache[word]:
            return self.cache[word][data_type], True
        response = requests.get(f"{BASE_URL}{word}")
        if response.status_code == 200:
            data = response.json()
            if data:
                return data, False
        self.show_error(response)
        return None, False

    def get_definition(self):
        word = self.word_input.text().strip()
        if not word:
            QMessageBox.information(self, 'Input Error', 'Please enter a word')
            return
        data, from_cache = self.fetch_data(word, 'definition')
        if data:
            if from_cache:
                self.result_area.setText(data)
                print(f'Definition for "{word}" fetched from cache')
            else:
                definitions = [definition['definition'] for meaning in data[0].get('meanings', []) for definition in meaning.get('definitions', [])]
                result = '\n'.join(definitions)
                self.result_area.setText(result)
                self.cache[word] = self.cache.get(word, {})
                self.cache[word]['definition'] = result
                print(f'Definition for "{word}" fetched from API')

    def get_synonyms(self):
        word = self.word_input.text().strip()
        if not word:
            QMessageBox.information(self, 'Input Error', 'Please enter a word')
            return
        data, from_cache = self.fetch_data(word, 'synonyms')
        if data:
            if from_cache:
                self.result_area.setText(data)
                print(f'Synonyms for "{word}" fetched from cache')
            else:
                synonyms = [synonym for meaning in data[0].get('meanings', []) for definition in meaning.get('definitions', []) for synonym in definition.get('synonyms', [])]
                result = ', '.join(synonyms) if synonyms else "No synonyms found"
                self.result_area.setText(result)
                self.cache[word] = self.cache.get(word, {})
                self.cache[word]['synonyms'] = result
                print(f'Synonyms for "{word}" fetched from API')

    def hear_pronunciation(self):
        word = self.word_input.text().strip()
        if not word:
            QMessageBox.information(self, 'Input Error', 'Please enter a word')
            return
        data, _ = self.fetch_data(word, 'pronunciation')
        if data:
            audio_url = next((phonetic['audio'] for phonetic in data[0].get('phonetics', []) if 'audio' in phonetic and phonetic['audio']), None)
            if audio_url:
                self.player.setMedia(QMediaContent(QUrl(audio_url)))
                self.player.play()
                print(f'Playing pronunciation for "{word}"')
            else:
                QMessageBox.information(self, 'Pronunciation', 'No pronunciation audio found')

    def get_images(self):
        pass

    def fetch_images(self, word):
        search_url = f"https://www.google.com/search?tbm=isch&q={word}"
        response = requests.get(search_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            images = [img['src'] for img in soup.find_all('img', limit=5)]
            return images
        self.show_error(response)
        return None

    def show_images(self, images):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Images for {self.word_input.text().strip()}")
        layout = QVBoxLayout(dialog)

        scroll_area = QScrollArea(dialog)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        for img_url in images:
            label = QLabel()
            label.setPixmap(QPixmap(img_url))
            scroll_layout.addWidget(label)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        dialog.setLayout(layout)
        dialog.exec_()

    def open_images_in_browser(self):
        word = self.word_input.text().strip()
        if not word:
            QMessageBox.information(self, 'Input Error', 'Please enter a word')
            return
        search_url = f"https://www.google.com/search?tbm=isch&q={word}"
        webbrowser.open(search_url)
        print(f'Opening images for "{word}" in browser')

    def clear_cache(self):
        self.cache.clear()
        self.save_cache()
        print("Cache cleared")

    def show_error(self, response):
        error_message = f"Error fetching data: {response.status_code}\n{response.json()}"
        QMessageBox.critical(self, "Error", error_message)

    def load_cache(self):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_cache(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f)

    def closeEvent(self, event):
        self.save_cache()
        event.accept()

def main():
    app = QApplication(sys.argv)
    ex = DictionaryApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()