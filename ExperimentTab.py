import sys, os, inspect
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

from init.initialize import BaseConfig

class QTabExperiment(QWidget):

    def __init__(self, experiment_obj=None, experiment_name=None):
        super().__init__()

        ### Experiment Variables ###
        self.experiment_obj = experiment_obj
        self.experiment_name = str(experiment_name)
        self.config = {"Experiment Config": {}, "Base Config": BaseConfig}

        self.experiment_type = None
        self.experiment_instance = None  # The actual experiment object
        if experiment_obj is not None:
            self.extractExperimentInstance(experiment_obj)

        ### Setting up the Tab
        self.setObjectName(self.experiment_name)
        self.group_tab_widget = QWidget(self)
        self.group_tab_widget.setGeometry(QRect(10, 10, 571, 393))
        self.group_tab_widget.setObjectName("group_tab_widget")

        ### Plotter within Experiment
        self.plot_layout = QHBoxLayout(self.group_tab_widget)
        self.plot_layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_layout.setObjectName("plot_layout")
        self.plot_toolbar = QVBoxLayout()
        self.plot_toolbar.setObjectName("plot_toolbar")

        self.copy_plot_button = QToolButton(self.group_tab_widget)
        self.copy_plot_button.setText("📋")
        self.copy_plot_button.setObjectName("copy_plot_button")
        self.plot_toolbar.addWidget(self.copy_plot_button)
        self.save_data_button = QToolButton(self.group_tab_widget)
        self.save_data_button.setText("💾")
        self.save_data_button.setObjectName("save_data_button")
        self.plot_toolbar.addWidget(self.save_data_button)

        spacerItem = QSpacerItem(28, 318, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.plot_toolbar.addItem(spacerItem)
        self.plot_layout.addLayout(self.plot_toolbar)
        self.plot_widget = QWidget(self.group_tab_widget)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plot_widget.sizePolicy().hasHeightForWidth())
        self.plot_widget.setSizePolicy(sizePolicy)
        self.plot_widget.setMinimumSize(QSize(375, 0))
        self.plot_widget.setObjectName("plot_widget")
        self.plot_layout.addWidget(self.plot_widget)
        self.plot_layout.setStretch(0, 1)
        self.plot_layout.setStretch(1, 10)

    def extractExperimentInstance(self, experiment_obj):
        for name, obj, in inspect.getmembers(experiment_obj):
            if name == self.experiment_name:
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
                    # if issubclass(obj, AveragerProgram):
                    #     self.experiment_type = 'Averager'
                    #     qInfo('Averager program, good to go!')
                    # elif issubclass(obj, RAveragerProgram):
                    #     self.experiment_type = 'RAverager'
                    #     qInfo('RAverager program, good to go!')
                    # elif issubclass(obj, NDAveragerProgram):
                    #     self.experiment_type = 'NDAverager'
                    #     qInfo('NDAverager program, good to go!')
                    # else:
                    #     msgBox = QMessageBox()
                    #     msgBox.setText("Error. Unrecognised class: " + self.experiment_name + ". Restart program.")
                    #     msgBox.setWindowTitle("Error -- unrecognised class.")
                    #     msgBox.exec()
                    #     return

                    return

        if self.experiment_instance is None:
            QMessageBox.critical(None, "Error", "No Experiment Class matching File Name Found.")

