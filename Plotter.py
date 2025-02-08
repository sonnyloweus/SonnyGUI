import pyqtgraph as pg

class PlotWidget(pg.PlotWidget):
    """A PyQtGraph widget that updates dynamically."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Real-Time Experiment Data")
        self.setBackground("w")  # White background
        self.plot_line = self.plot([], [], pen=pg.mkPen(color="b", width=2))  # Blue line

    def updatePlot(self, data):
        """ Update the PyQtGraph plot dynamically."""
        x = list(range(len(data)))
        self.plot_line.setData(x, data)  # Update plot data