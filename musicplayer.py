import sys
import os
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QWidget, QLabel, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Database setup
        self.db_connection = sqlite3.connect("playlist.db")
        self.cursor = self.db_connection.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS playlist (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, path TEXT)"
        )
        self.db_connection.commit()

        # Initialize GUI
        self.init_ui()

        # Media Player setup
        self.media_player = QMediaPlayer()
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.playlist = QMediaPlaylist()
        self.media_player.setPlaylist(self.playlist)
        self.playlist.currentIndexChanged.connect(self.update_current_track)

        # Load playlist from database
        self.load_playlist()

    def init_ui(self):
        self.setWindowTitle("Music Player")
        self.setGeometry(100, 100, 600, 400)

        # Widgets
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.playlist_list_widget = QListWidget(self)
        self.playlist_list_widget.itemDoubleClicked.connect(self.play_track)

        self.play_button = QPushButton("Play", self)
        self.play_button.clicked.connect(self.play_pause)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop)

        self.add_button = QPushButton("Add Track", self)
        self.add_button.clicked.connect(self.add_track)

        self.remove_button = QPushButton("Remove Track", self)
        self.remove_button.clicked.connect(self.remove_track)

        self.position_label = QLabel("00:00", self)
        self.duration_label = QLabel("00:00", self)

        # Layout
        main_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.add_button)
        controls_layout.addWidget(self.remove_button)

        main_layout.addWidget(self.playlist_list_widget)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.position_label)
        main_layout.addWidget(self.duration_label)

        self.central_widget.setLayout(main_layout)

    def add_track(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Music File", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            file_name = os.path.basename(file_path)
            self.cursor.execute("INSERT INTO playlist (title, path) VALUES (?, ?)", (file_name, file_path))
            self.db_connection.commit()
            self.load_playlist()

    def remove_track(self):
        selected_item = self.playlist_list_widget.currentItem()
        if selected_item:
            track_id = int(selected_item.data(Qt.UserRole))
            self.cursor.execute("DELETE FROM playlist WHERE id=?", (track_id,))
            self.db_connection.commit()
            self.load_playlist()

    def load_playlist(self):
        self.playlist_list_widget.clear()
        self.cursor.execute("SELECT id, title FROM playlist")
        playlist_data = self.cursor.fetchall()
        for row in playlist_data:
            track_id, title = row
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, track_id)
            self.playlist_list_widget.addItem(item)

    def play_track(self, item):
        track_id = int(item.data(Qt.UserRole))
        self.cursor.execute("SELECT path FROM playlist WHERE id=?", (track_id,))
        path = self.cursor.fetchone()[0]
        media_content = QMediaContent(QUrl.fromLocalFile(path))
        self.playlist.clear()
        self.playlist.addMedia(media_content)
        self.playlist.setCurrentIndex(0)
        self.media_player.play()

    def play_pause(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def stop(self):
        self.media_player.stop()

    def update_position(self, position):
        self.position_label.setText(self.format_time(position))

    def update_duration(self, duration):
        self.duration_label.setText(self.format_time(duration))

    def update_current_track(self, index):
        item = self.playlist_list_widget.item(index)
        if item:
            self.playlist_list_widget.setCurrentItem(item)

    def format_time(self, milliseconds):
        total_seconds = milliseconds // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return "{:02}:{:02}".format(minutes, seconds)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Exit", "Are you sure you want to exit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Close the database connection on exit
            self.db_connection.close()
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())
