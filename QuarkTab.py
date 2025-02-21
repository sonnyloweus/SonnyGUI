import sys, os, inspect
import h5py
import numpy as np
from pathlib import Path
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QLayout,
    QSpacerItem,
    QToolButton,
    QMessageBox
)
import pyqtgraph as pg

from Init.initialize import BaseConfig

class QQuarkTab(QWidget):

    def __init__(self, experiment_obj=None, tab_name=None, is_experiment=True, dataset_file=None):
        super().__init__()

        ### Experiment Variables ###
        self.experiment_obj = experiment_obj
        self.tab_name = str(tab_name)
        self.config = {"Experiment Config": {}, "Base Config": BaseConfig}
        self.is_experiment = is_experiment
        self.data = dataset_file

        self.experiment_type = None
        self.experiment_instance = None  # The actual experiment object

        ### Setting up the Tab
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        ### Plotter within Tab
        self.plot_layout = QHBoxLayout(self)
        self.plot_layout.setContentsMargins(5, 5, 5, 5)
        self.plot_layout.setObjectName("plot_layout")

        # Plot Button Toolbar
        self.plot_toolbar = QVBoxLayout()
        self.plot_toolbar.setObjectName("plot_toolbar")
        self.copy_plot_button = QToolButton()
        self.copy_plot_button.setText("📋")
        self.copy_plot_button.setObjectName("copy_plot_button")
        self.save_data_button = QToolButton()
        self.save_data_button.setText("💾")
        self.save_data_button.setObjectName("save_data_button")
        self.plot_toolbar.addWidget(self.copy_plot_button)
        self.plot_toolbar.addWidget(self.save_data_button)
        spacerItem = QSpacerItem(28, 318, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.plot_toolbar.addItem(spacerItem)
        self.plot_layout.addLayout(self.plot_toolbar)

        # The actual plot itself
        self.plot_widget = pg.GraphicsLayoutWidget(self)
        self.plot_widget.setBackground("w")
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_widget.setMinimumSize(QSize(375, 0))
        self.plot_widget.setObjectName("plot_widget")

        self.plot_layout.addWidget(self.plot_widget)
        self.plot_layout.setStretch(0, 1)
        self.plot_layout.setStretch(1, 10)

        self.setLayout(self.plot_layout)

        if self.is_experiment and experiment_obj is not None:
            self.extract_experiment_instance(experiment_obj)
        elif not self.is_experiment and dataset_file is not None:
            self.import_data()

    def extract_experiment_instance(self, experiment_obj):
        for name, obj, in inspect.getmembers(experiment_obj):
            if name == self.tab_name:
                if inspect.isclass(obj):
                    print("found class instance: " + name)

                    ### create instance of experiment
                    self.experiment_instance = obj

                    ### reset the config
                    if (not hasattr(self.experiment_instance, "config_template")
                            or self.experiment_instance.config_template is None):
                        QMessageBox.critical(None, "Error", "No Config Template given.")
                    ### HANDLE CONFIG ERROR HANDLING
                    else:
                        self.config["Experiment Config"] = self.experiment_instance.config_template

                    # HANDLE EXPERIMENT TYPE????
                    self.experiment_type = None
                    ### check what kind of experiment class it is

                    return

        if self.experiment_instance is None:
            QMessageBox.critical(None, "Error", "No Experiment Class matching File Name Found.")

    def import_data(self):
        with h5py.File(self.data, "r") as f:

            # Extract the x-axis (assume it's labeled 'x_pts')
            x_data = None
            if 'x_pts' in f:
                x_data = list(f['x_pts'])

            print(x_data)
            print(f.keys())

            # Iterate through all datasets in the file
            for key in f.keys():
                if key == 'x_pts':  # Skip x-axis itself
                    continue
                var = f[key]

                # Ensure it's plottable
                if isinstance(var, h5py.Dataset):
                    y_data = list(var)
                    if len(x_data) == len(y_data):
                        plot = self.plot_widget.addPlot(title=key)
                        plot.plot(x_data, y_data, pen=None, symbol='o', symbolSize=3, symbolBrush='b', name=key)  # Scatter plot
                        plot.showGrid(x=True, y=True)
                        self.plot_widget.nextRow()
                    else:
                        print(f"Skipping {key}: x_data and y_data length mismatch ({len(x_data)} vs {len(y_data)})")

    def update_data(self, data):
        print("updating data")