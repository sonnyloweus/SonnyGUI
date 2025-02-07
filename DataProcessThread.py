from PyQt5.QtCore import QThread, pyqtSignal

class DataWorker(QThread):
    """Thread responsible for processing and preparing data for plotting."""
    data_ready = pyqtSignal(list)  # Signal to send processed data to the main GUI thread

    def __init__(self):
        super().__init__()
        self.running = True

    def receiveData(self, data):
        """Receives data from the experiment and processes it before plotting."""
        if self.running:
            # perform some data processing
            self.data_ready.emit(data)  # Send processed data to the GUI thread

    def stop(self):
        """Stop the thread gracefully."""
        self.running = False
