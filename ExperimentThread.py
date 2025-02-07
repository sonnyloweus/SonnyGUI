import random
import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from PyQt5.QtWidgets import (
    QMessageBox,
)

class ExperimentWorker(QThread):
    """
    This class is used to run an experiment, used on a separate QThread than the main loop.
    Communicates through signals to be thread-safe
    """
    dataGenerated = pyqtSignal(list)  # Signal to send experiment data

    def __init__(self, experimentObject, config, parent=None):
        super().__init__()
        self.config = config
        self.experimentObject = experimentObject  # This is already instantiated
        self.running = True

    def run(self):
        print(self.config)
        if self.experimentObject is None:
            QMessageBox.critical(None, "Error", "No Experiment Instance available.")
            return

        data = []
        x = 0
        while self.running:
            y = self.experimentObject.compute(x)
            data.append(y)
            self.dataGenerated.emit(data)
            x += 0.1
            time.sleep(0.1)  # Simulate real-time data streaming

    def stop(self):
        self.running = False