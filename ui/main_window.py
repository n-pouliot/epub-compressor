# ui/main_window.py
import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QSlider,
    QLabel,
    QCheckBox,
    QProgressBar,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

# Import your custom widgets and thread
from .widgets import DragDropArea, LogPanel
from .threads import CompressionThread
from core.epub_handler import get_epub_info


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPUB Compressor Pro")
        self.setGeometry(100, 100, 1200, 800)

        self.file_list = []
        self.output_dir = os.path.expanduser("~")  # Default to home dir
        self.compression_thread = None

        self.init_ui()
        self.load_styles()  # Load default theme
        self.update_output_dir_label()

    def init_ui(self):
        # --- Main Layout ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Splitter for adjustable panes
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- Left Pane: Settings and File Selection ---
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        splitter.addWidget(left_pane)

        # File Selection Group
        file_group = QGroupBox("1. Select Files")
        file_layout = QVBoxLayout()

        self.file_list_widget = QListWidget()
        self.file_list_widget.setAlternatingRowColors(True)
        self.file_list_widget.itemSelectionChanged.connect(
            self.on_file_selection_changed
        )
        file_layout.addWidget(self.file_list_widget)

        self.drag_drop_area = DragDropArea()
        self.drag_drop_area.filesDropped.connect(self.add_files_to_list)
        file_layout.addWidget(self.drag_drop_area)

        browse_button = QPushButton("Browse for Files")
        browse_button.clicked.connect(self.browse_for_files)
        file_layout.addWidget(browse_button)

        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        # Compression Settings Group
        settings_group = QGroupBox("2. Compression Settings")
        settings_layout = QFormLayout()

        # Toggles
        self.cb_compress_images = QCheckBox("Compress Images")
        self.cb_compress_images.setChecked(True)
        self.cb_minify_html = QCheckBox("Minify HTML")
        self.cb_minify_html.setChecked(True)
        self.cb_minify_css = QCheckBox("Minify CSS")
        self.cb_minify_css.setChecked(True)
        self.cb_strip_fonts = QCheckBox("Strip All Fonts (Significant Reduction)")

        settings_layout.addRow(self.cb_compress_images)
        settings_layout.addRow(self.cb_minify_html)
        settings_layout.addRow(self.cb_minify_css)
        settings_layout.addRow(self.cb_strip_fonts)

        # Image Quality Slider
        self.image_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.image_quality_slider.setRange(10, 95)
        self.image_quality_slider.setValue(75)
        self.image_quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.image_quality_slider.setTickInterval(10)
        self.image_quality_label = QLabel(
            f"Image Quality: {self.image_quality_slider.value()}"
        )
        self.image_quality_slider.valueChanged.connect(
            lambda v: self.image_quality_label.setText(f"Image Quality: {v}")
        )
        settings_layout.addRow(self.image_quality_label, self.image_quality_slider)

        settings_group.setLayout(settings_layout)
        left_layout.addWidget(settings_group)

        # Output Directory Group
        output_group = QGroupBox("3. Output")
        output_layout = QVBoxLayout()
        self.output_dir_label = QLabel()
        output_layout.addWidget(self.output_dir_label)
        browse_output_button = QPushButton("Change Output Directory")
        browse_output_button.clicked.connect(self.select_output_directory)
        output_layout.addWidget(browse_output_button)
        output_group.setLayout(output_layout)
        left_layout.addWidget(output_group)

        left_layout.addStretch()

        # --- Right Pane: Info, Progress, and Log ---
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        splitter.addWidget(right_pane)

        # Info & Summary Group
        self.info_group = QGroupBox("File Info / Summary")
        info_layout = QFormLayout()
        self.info_original_size = QLabel("N/A")
        self.info_final_size = QLabel("N/A")
        self.info_reduction = QLabel("N/A")
        self.info_image_count = QLabel("N/A")
        self.info_font_count = QLabel("N/A")
        info_layout.addRow("Original Size:", self.info_original_size)
        info_layout.addRow("Est. Final Size:", self.info_final_size)
        info_layout.addRow("Est. Reduction:", self.info_reduction)
        info_layout.addRow("Images:", self.info_image_count)
        info_layout.addRow("Fonts:", self.info_font_count)
        self.info_group.setLayout(info_layout)
        right_layout.addWidget(self.info_group)

        # Control & Progress Group
        progress_group = QGroupBox("4. Execute")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label = QLabel("Ready to start.")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_button = QPushButton("Start Compression")
        self.start_button.clicked.connect(self.start_compression)
        self.start_button.setObjectName("StartButton")  # For styling

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.start_button)
        progress_group.setLayout(progress_layout)
        right_layout.addWidget(progress_group)

        # Log Panel Group
        log_group = QGroupBox("Operation Log")
        log_layout = QVBoxLayout()
        self.log_panel = LogPanel()
        log_layout.addWidget(self.log_panel)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)

        # Set splitter sizes
        splitter.setSizes([350, 650])

        # Theme toggle button
        self.theme_button = QPushButton("Toggle Dark/Light Mode")
        self.theme_button.clicked.connect(self.toggle_theme)
        left_layout.addWidget(self.theme_button)
        self.current_theme = "light"

    def browse_for_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select EPUB files", os.path.expanduser("~"), "EPUB Files (*.epub)"
        )
        if files:
            self.add_files_to_list(files)

    def add_files_to_list(self, paths):
        for path in paths:
            if path not in self.file_list:
                self.file_list.append(path)
                item = QListWidgetItem(os.path.basename(path))
                item.setData(Qt.ItemDataRole.UserRole, path)  # Store full path
                self.file_list_widget.addItem(item)
        if self.file_list_widget.count() > 0:
            self.file_list_widget.setCurrentRow(0)

    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir
        )
        if directory:
            self.output_dir = directory
            self.update_output_dir_label()

    def update_output_dir_label(self):
        self.output_dir_label.setText(f"Current: {self.output_dir}")

    def on_file_selection_changed(self):
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            self.clear_info_panel()
            return

        path = selected_items[0].data(Qt.ItemDataRole.UserRole)
        info = get_epub_info(path)
        if info:
            self.info_original_size.setText(
                f"{info['total_size'] / 1024 / 1024:.2f} MB"
            )
            self.info_image_count.setText(
                f"{info['images']} ({info['image_size'] / 1024:.1f} KB)"
            )
            self.info_font_count.setText(
                f"{info['fonts']} ({info['font_size'] / 1024:.1f} KB)"
            )
            # Add estimation logic here later
            self.info_final_size.setText("~ MB")
            self.info_reduction.setText("~ %")
        else:
            self.clear_info_panel()

    def clear_info_panel(self):
        self.info_original_size.setText("N/A")
        self.info_final_size.setText("N/A")
        self.info_reduction.setText("N/A")
        self.info_image_count.setText("N/A")
        self.info_font_count.setText("N/A")

    def start_compression(self):
        if not self.file_list:
            QMessageBox.warning(
                self, "No Files", "Please add at least one EPUB file to compress."
            )
            return

        # Fidelity Warning
        if self.cb_strip_fonts.isChecked():
            reply = QMessageBox.question(
                self,
                "Fidelity Warning",
                "Stripping fonts will cause the EPUB to use system default fonts, which can significantly alter the book's appearance and layout.\n\nAre you sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.start_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_panel.clear()

        options = {
            "compress_images": self.cb_compress_images.isChecked(),
            "minify_html": self.cb_minify_html.isChecked(),
            "minify_css": self.cb_minify_css.isChecked(),
            "strip_fonts": self.cb_strip_fonts.isChecked(),
            "image_options": {
                "quality": self.image_quality_slider.value(),
                "max_width": 1200,  # Example, could be made configurable
                "max_height": 1600,
                "convert_to_jpeg": True,
            },
        }

        self.compression_thread = CompressionThread(
            self.file_list, self.output_dir, options
        )
        self.compression_thread.log_message.connect(self.log_panel.add_log)
        self.compression_thread.progress_update.connect(self.update_progress)
        self.compression_thread.file_finished.connect(self.on_file_finished)
        self.compression_thread.all_finished.connect(self.on_all_finished)
        self.compression_thread.start()

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{message} - %p%")
        self.progress_label.setText(message)

    def on_file_finished(self, stats):
        # Update the specific item in the list view
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == stats["input_path"]:
                orig_size_mb = stats["original_size"] / 1024 / 1024
                final_size_mb = stats["final_size"] / 1024 / 1024
                item.setText(
                    f"{os.path.basename(stats['input_path'])} ({orig_size_mb:.2f}MB -> {final_size_mb:.2f}MB, {stats['reduction_percent']:.1f}% saved)"
                )
                break

    def on_all_finished(self):
        self.start_button.setEnabled(True)
        self.progress_label.setText("All tasks complete.")
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Success", "All EPUB files have been processed.")
        # Clear list after successful compression
        self.file_list_widget.clear()
        self.file_list.clear()

    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
        else:
            self.current_theme = "light"
        self.load_styles()

    def load_styles(self):
        try:
            theme_path = os.path.join(
                "assets", "styles", f"{self.current_theme}_theme.qss"
            )
            with open(theme_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Stylesheet not found: {theme_path}")
            # Apply a default basic style if file is missing
            self.setStyleSheet("QMainWindow { background-color: #e0e0e0; }")

    def closeEvent(self, event):
        """Ensure thread is stopped when closing window."""
        if self.compression_thread and self.compression_thread.isRunning():
            self.compression_thread.stop()
            self.compression_thread.wait()  # Wait for thread to finish
        event.accept()
