# ui/threads.py
from PyQt6.QtCore import QThread, pyqtSignal
from core.epub_handler import compress_epub_file


class CompressionThread(QThread):
    """
    Runs the EPUB compression in a background thread to avoid freezing the UI.
    """

    # Signals to communicate with the main UI thread
    log_message = pyqtSignal(str)  # For sending log messages
    progress_update = pyqtSignal(int, str)  # (percentage, message)
    file_finished = pyqtSignal(dict)  # (stats_dict) when a single file is done
    all_finished = pyqtSignal()  # When all files in the batch are done

    def __init__(self, file_list, output_dir, options, parent=None):
        super().__init__(parent)
        self.file_list = file_list
        self.output_dir = output_dir
        self.options = options
        self.is_running = True

    def run(self):
        """The main work of the thread."""
        total_files = len(self.file_list)
        for i, input_path in enumerate(self.file_list):
            if not self.is_running:
                break

            self.log_message.emit(f"\n--- Processing file {i + 1}/{total_files} ---")

            try:
                # Construct the output path
                base_name = os.path.basename(input_path)
                name, ext = os.path.splitext(base_name)
                output_path = os.path.join(self.output_dir, f"{name}_compressed{ext}")

                # The core compression logic is called here
                stats = compress_epub_file(
                    input_path,
                    output_path,
                    self.options,
                    log_callback=self.log_message.emit,
                    progress_callback=self.progress_update.emit,
                )

                # Add file paths to stats for UI update
                stats["input_path"] = input_path
                stats["output_path"] = output_path

                self.file_finished.emit(stats)

            except Exception as e:
                import traceback

                error_msg = (
                    f"FATAL ERROR compressing {os.path.basename(input_path)}: {e}"
                )
                self.log_message.emit(error_msg)
                self.log_message.emit(traceback.format_exc())
                self.progress_update.emit(
                    100, "Error Occurred"
                )  # Set progress to 100 to stop
                # We can emit an error signal if needed

        self.all_finished.emit()

    def stop(self):
        """Stops the thread gracefully."""
        self.is_running = False


# This import is needed inside the thread to avoid circular dependencies
# if you decide to move more logic around.
import os
