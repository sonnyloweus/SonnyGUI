import random
import time
from PyQt5.QtCore import QThread, pyqtSignal

class ExperimentWorker(QThread):
    """
    This class is used to run an experiment, used on a separate QThread than the main loop.
    Communicates through signals to be thread-safe
    """
    data_generated = pyqtSignal(list)  # Signal to send experiment data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True  # Control flag for stopping the thread

    def run(self):
        """Generate data and emit it in real-time."""
        data = []
        while self.running:
            new_value = random.uniform(0, 10)  # Generate a random number
            data.append(new_value)
            if len(data) > 100:  # Keep dataset fixed length
                data.pop(0)

            self.data_generated.emit(data)  # Send data to the plot worker
            time.sleep(0.1)  # Simulate faster data update

    def stop(self):
        """Stop the thread gracefully."""
        self.running = False
