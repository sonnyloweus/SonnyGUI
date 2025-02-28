"""
============
QuarkyTab.py
============
The custom QQuarkTab class for the central tabs module of the main application.

Each QQuarkTab is either an experiment tab or a data tab that stores its own object attributes, configuration,
data, and plotting.
"""

import inspect
import numpy as np
from PyQt5.QtCore import Qt, QSize, qCritical, QRect
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QMessageBox,
    QLabel,
    QComboBox,
)
import pyqtgraph as pg

from scripts.Init.initialize import BaseConfig
import scripts.Helpers as Helpers

class QQuarkTab(QWidget):
    """
    The class for QQuarkTabs that make up the central tabular module.
    """

    def __init__(self, experiment_obj=None, tab_name=None, is_experiment=True, dataset_file=None):
        """
        Initializes an instance of a QQuarkTab widget.

        :param experiment_obj: The experiment module object extracted from an experiment file.
        :type experiment_obj: Experiment Module
        :param tab_name: The name of the tab widget.
        :type tab_name: str
        :param is_experiment: Whether the tab corresponds to an experiment or dataset.
        :type is_experiment: bool
        :param dataset_file: The path to the dataset file.
        :type dataset_file: str

        **Important Attributes:**

        * experiment_obj (Experiment Module): The experiment module object that was passed.
        * experiment_instance (Experiment Class): An initialized instance of the experiment module with the config.
        * config (dict): The configuration of the QQuarkTab experiment/dataset.
        * data (dict): The data of the QQuarkTab experiment/dataset.
        * plots (pyqtgraph.PlotWidget[]): Array of the pyqtgraph plots of the data.
        * plot_widget (pyqtgraph.GraphicsLayoutWidget): The graphics layout of the plotting area
        """

        super().__init__()

        ### Experiment Variables
        self.experiment_obj = experiment_obj
        self.tab_name = str(tab_name)
        self.config = {"Experiment Config": {}, "Base Config": BaseConfig} # default conifg found in initializ.py
        self.is_experiment = is_experiment
        self.data = None
        self.experiment_instance = None  # The actual experiment instance
        self.plots = []

        self.experiment_type = None # Not currently used

        # Can specify an alternative colormap (e.g., 'viridis', 'inferno', etc.)
        cmap = pg.colormap.get('viridis')
        self.lut = cmap.getLookupTable()

        ### Setting up the Tab
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        ### Plotter within Tab
        self.plot_layout = QVBoxLayout(self)
        self.plot_layout.setContentsMargins(5, 0, 5, 0)
        self.plot_layout.setSpacing(0)
        self.plot_layout.setObjectName("plot_layout")

        ### Plot Utilities Bar
        self.plot_utilities_container = QWidget()
        self.plot_utilities_container.setMaximumHeight(35)
        self.plot_utilities = QHBoxLayout(self.plot_utilities_container)
        self.plot_utilities.setContentsMargins(0, 0, 0, 0)
        self.plot_utilities.setSpacing(5)
        self.plot_utilities.setObjectName("plot_utilities")
        self.copy_plot_button = Helpers.create_button("Copy", "copy_plot_button", True)
        self.save_data_button = Helpers.create_button("Save", "save_data_button", True)
        spacerItem = QSpacerItem(0, 30, QSizePolicy.Expanding, QSizePolicy.Expanding) # spacer
        self.plot_method_label = QLabel("Plot Method: ")  # coordinate of the mouse over the current plot
        self.plot_method_label.setStyleSheet("font-size: 10px;")
        self.plot_method_label.setObjectName("coord_label")
        self.plot_method_combo = QComboBox()
        self.plot_method_combo.setGeometry(QRect(10, 10, 150, 26))
        self.plot_method_combo.setObjectName("plot_method_combo")
        self.plot_method_combo.addItems(["Auto (default)"]) # Plotting Options Dropdown
        self.coord_label = QLabel("X: ___ Y: ___")  # coordinate of the mouse over the current plot
        self.coord_label.setFixedWidth(100)
        self.coord_label.setStyleSheet("font-size: 10px;")
        self.coord_label.setObjectName("coord_label")

        self.plot_utilities.addWidget(self.copy_plot_button)
        self.plot_utilities.addWidget(self.save_data_button)
        self.plot_utilities.addItem(spacerItem)
        self.plot_utilities.addWidget(self.plot_method_label)
        self.plot_utilities.addWidget(self.plot_method_combo)
        self.plot_utilities.addItem(spacerItem)
        self.plot_utilities.addWidget(self.coord_label)
        self.plot_layout.addWidget(self.plot_utilities_container)

        # The actual plot itself (lots of styling attributes
        self.plot_widget = pg.GraphicsLayoutWidget(self)
        self.plot_widget.setBackground("w")
        self.plot_widget.ci.setSpacing(2)  # Reduce spacing
        self.plot_widget.ci.setContentsMargins(3, 3, 3, 3)  # Adjust margins of plots
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_widget.setMinimumSize(QSize(375, 0))
        self.plot_widget.setObjectName("plot_widget")

        self.plot_layout.addWidget(self.plot_widget)
        self.plot_layout.setStretch(0, 1)
        self.plot_layout.setStretch(1, 10)

        self.setLayout(self.plot_layout)
        self.setup_signals()

        # either extract experiment instance of the dataset file depending on the tab type
        if self.is_experiment and self.experiment_obj is not None:
            self.extract_experiment_instance()
        elif not self.is_experiment and dataset_file is not None:
            self.load_dataset_file(dataset_file)

    def setup_signals(self):
        # self.plot_method_combo.currentIndexChanged.connect(self.plot_method_changed)
        self.plot_widget.scene().sigMouseMoved.connect(self.update_coordinates) # coordinates viewer

    def load_dataset_file(self, dataset_file):
        """
        Takes the dataset file and loads the dict, before calling the plotter.

        :param dataset_file: The path to the dataset file.
        :type dataset_file: str
        """

        self.data = Helpers.h5_to_dict(dataset_file)
        self.plot_data()

    def extract_experiment_instance(self):
        """
        From the experiment module of the specific tab, find the correct class to make an instance of.

        TODO: Based on the Experiment Class to-be set.
        """

        ############ Need to Revamp after Experiment Class set ############
        # Loop through all members (classes) of the experiment module to find the matching one
        for name, obj, in inspect.getmembers(self.experiment_obj):
            if name == self.tab_name:
                if inspect.isclass(obj):
                    print("found class instance: " + name)

                    ### create instance of experiment
                    self.experiment_instance = obj

                    ### set the config
                    if (not hasattr(self.experiment_instance, "config_template")
                            or self.experiment_instance.config_template is None):
                        QMessageBox.critical(None, "Error", "No Config Template given.")
                    ############ HANDLE CONFIG ERROR HANDLING #############
                    else:
                        self.config["Experiment Config"] = self.experiment_instance.config_template

                    # HANDLE EXPERIMENT TYPE????
                    self.experiment_type = None
                    ### check what kind of experiment class it is
                    return

        # Verify experiment_instance
        if self.experiment_instance is None:
            qCritical("No Experiment Class instance found within the module give. Must adhere to the experiment " +
                      "class template provided.")
            QMessageBox.critical(None, "Error", "No Experiment Class Found.")

    def clear_plots(self):
        """
        Clears the plots.
        """

        self.plot_widget.ci.clear()
        self.plots = []

    def update_coordinates(self, pos):
        """
        Updates the coordinates label to reflect the cursor's location on a plot's axis.

        :param pos: The coordinates of the cursor
        :type pos: tuple
        """

        # find the active plot
        for plot in self.plots:
            vb = plot.vb  # ViewBox of each plot
            if plot.sceneBoundingRect().contains(pos):
                self.plot_widget.setCursor(Qt.CrossCursor) # make cursor cross-hairs
                mouse_point = vb.mapSceneToView(pos) # translate location to axis coordinates
                x, y = mouse_point.x(), mouse_point.y()
                self.coord_label.setText(f"X: {x:.2f} Y: {y:.2f}")
                break

    def plot_data(self):
        """
        Plots the data of the QQuarkTab experiment/dataset.
        """

        plotting_method = self.plot_method_combo.currentText() # Get the Plotting Method

        if plotting_method != "Auto (default)":
            return

        self.clear_plots()
        num_plots = 0
        f = self.data
        if 'data' in self.data:
            f = self.data['data']
        for name, data in f.items():
            if isinstance(data, int):
                continue
            if isinstance(data, list):
                data = np.array(data[0][0])
            shape = data.shape

            # 1D data -> 2D Plots
            if len(shape) == 1:
                x_data = None
                if 'x_pts' in f:
                    x_data = list(f['x_pts'])
                    # Iterate through all keys in the file
                    if name == 'x_pts':
                        continue
                    y_data = list(data)
                    if len(x_data) == len(y_data):
                        num_plots += 1
                        plot = self.plot_widget.addPlot()
                        plot.plot(x_data, y_data, pen=None, symbol='o', symbolSize=3, symbolBrush='b',
                                  name=name)  # Scatter plot
                        plot.setLabel("left", name)
                        plot.showGrid(x=True, y=True)
                        self.plots.append(plot)
                        self.plot_widget.nextRow()
            elif len(shape) == 2:
                num_plots += 1
                plot = self.plot_widget.addPlot(title=name)
                # 2-column data -> IQ scatter plot
                if shape[1] == 2:
                    plot.plot(data[:, 0], data[:, 1], pen=None, symbol="o")
                    self.plot_widget.nextRow()
                # General 2D data -> Heatmap
                else:
                    img = pg.ImageItem(data.T)  # Transpose for correct orientation
                    img.setLookupTable(self.lut)
                    plot.addItem(img)
                    if num_plots % 2 == 0:
                        self.plot_widget.nextRow()
                self.plots.append(plot)
        # print("plotted", self.data)

    def process_data(self, data):
        self.data = data

        ### check what set number is being run
        set_num = data['data']['set_num']
        if set_num == 0:
            self.data_cur = data
        elif set_num > 0:
            avgi = (self.data_cur['data']['avgi'][0][0] * (set_num) + data['data']['avgi'][0][0]) / (set_num + 1)
            avgq = (self.data_cur['data']['avgq'][0][0] * (set_num) + data['data']['avgq'][0][0]) / (set_num + 1)
            self.data_cur['data']['avgi'][0][0] = avgi
            self.data_cur['data']['avgq'][0][0] = avgq
        self.data['data']['avgi'][0][0] = self.data_cur['data']['avgi'][0][0]
        self.data['data']['avgq'][0][0] = self.data_cur['data']['avgq'][0][0]

        ### create a diction to feed into the plot widget for labels
        # plot_labels = {
        #     "x label": self.experiment.cfg["x_pts_label"],
        #     "y label": self.experiment.cfg["y_pts_label"],
        # }
        ### check for if the y label is none (for single varible sweep) and set the y label to I/Q or amp/phase
        # if plot_labels["y label"] == None:
        #     plot_labels["y label 1"] = "I (a.u.)"
        #     plot_labels["y label 2"] = "Q (a.u.)"

    def update_data(self, data):
        """
        Is the slot for the emission of data from the experiment thread.
        Calls the methods to process and plot the data.
        """

        self.process_data(data)
        self.plot_data()