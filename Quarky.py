import sys, os, inspect
import h5py
import math
import datetime
import numpy as np
from pathlib import Path
from PyQt5.QtCore import (
    Qt, QSize, QRect, QObject, QThread, pyqtSignal, pyqtSlot, qCritical
)

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSplitter,
    QMessageBox,
    QFileDialog,
    QTabWidget,
    QSizePolicy
)

from CoreLib.socProxy import makeProxy
from ExperimentThread import ExperimentThread
from ExperimentTab import QTabExperiment
from VoltagePanel import QVoltagePanel
from ConfigTree import QConfigTree
import Helpers
from qick import RAveragerProgram, AveragerProgram, NDAveragerProgram

path = os.getcwd()
try:
    os.add_dll_directory(path + '\\PythonDrivers')
except AttributeError:
    os.environ["PATH"] = path + '\\PythonDrivers' + ";" + os.environ["PATH"]

class Quarky(QMainWindow):

    def __init__(self):
        super().__init__()

        self.experiment_worker = None

        self.soc = None
        self.soccfg = None
        self.soc_connected = False
        self.ip_address = None
        # self.ip_address =  "192.168.1.7" ### Need to change to accounts tab

        self.curr_experiment_tab = None
        self.tabs_added = False
        self.setup_ui()

    def setup_ui(self):
        ### Central Widget
        self.setWindowTitle("Quarky")
        self.resize(1000, 550)
        self.central_widget = QWidget()
        self.central_widget.setMinimumSize(800, 400)
        self.central_widget.setObjectName("central_widget")
        
        self.wrapper = QWidget()
        self.wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.wrapper.setObjectName("wrapper")

        ### Main layout (vertical)
        self.main_layout = QVBoxLayout(self.wrapper)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setObjectName("main_layout")

        ### Top Control Bar
        self.top_bar = QHBoxLayout()
        self.top_bar.setContentsMargins(-1, 10, -1, 10)
        self.top_bar.setObjectName("top_bar")

        self.start_experiment_button = QPushButton("▶", self.wrapper)
        self.start_experiment_button.setObjectName("start_experiment")
        self.start_experiment_button.setEnabled(False)
        self.stop_experiment_button = QPushButton("⏹", self.wrapper)
        self.stop_experiment_button.setEnabled(False)
        self.stop_experiment_button.setObjectName("stop_experiment")
        self.soc_status_label = QLabel(self.wrapper)
        self.soc_status_label.setText('<html><b>✖ Soc Disconnected</b></html>')
        self.soc_status_label.setObjectName("soc_status_label")
        self.experiment_progress_bar = QProgressBar(self.wrapper)
        self.experiment_progress_bar.setProperty("value", 1) # Show a peek of blue
        self.experiment_progress_bar.setObjectName("experiment_progress_bar")
        self.experiment_stopwatch = QLabel(self.wrapper)
        self.experiment_stopwatch.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self.experiment_stopwatch.setText('<html><b>00.00ms</b></html>')
        self.experiment_stopwatch.setObjectName("experiment_stopwatch")
        self.load_config_button = QPushButton("Load Config", self.wrapper)
        self.load_config_button.setObjectName("load_config_button")
        self.load_experiment_button = QPushButton("Load Experiment", self.wrapper)
        self.load_experiment_button.setObjectName("load_experiment_button")

        self.top_bar.addWidget(self.start_experiment_button)
        self.top_bar.addWidget(self.stop_experiment_button)
        self.top_bar.addWidget(self.soc_status_label)
        self.top_bar.addWidget(self.experiment_progress_bar)
        self.top_bar.addWidget(self.experiment_stopwatch)
        self.top_bar.addWidget(self.load_config_button)
        self.top_bar.addWidget(self.load_experiment_button)
        self.main_layout.addLayout(self.top_bar)

        ### Main Splitter with Tabs, Voltage Panel, Config Tree
        self.main_splitter = QSplitter(self.wrapper)
        self.main_splitter.setLineWidth(2)
        self.main_splitter.setOrientation(Qt.Horizontal)
        self.main_splitter.setOpaqueResize(True)
        self.main_splitter.setHandleWidth(7)
        self.main_splitter.setChildrenCollapsible(True)
        self.main_splitter.setObjectName("main_splitter")

        ### Experiment Tabs
        self.experiment_tabs = QTabWidget(self.main_splitter)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.experiment_tabs.sizePolicy().hasHeightForWidth())
        self.experiment_tabs.setSizePolicy(sizePolicy)
        self.experiment_tabs.setMinimumSize(QSize(400, 0))
        self.experiment_tabs.setTabPosition(QTabWidget.North)
        self.experiment_tabs.setTabShape(QTabWidget.Rounded)
        self.experiment_tabs.setUsesScrollButtons(True)
        self.experiment_tabs.setDocumentMode(True)
        self.experiment_tabs.setTabsClosable(True)
        self.experiment_tabs.setMovable(True)
        self.experiment_tabs.setTabBarAutoHide(False)
        self.experiment_tabs.setObjectName("experiment_tabs")
        self.experiment_tabs.setStyleSheet("background-color: #F8F8F8")  # Light gray background

        ### Template Experiment Tab
        template_experiment_tab = QTabExperiment()
        self.experiment_tabs.addTab(template_experiment_tab, "No Tabs Added")
        self.experiment_tabs.setCurrentIndex(0)

        ### Config Tree
        self.config_tree_panel = QConfigTree(self.main_splitter, template_experiment_tab.config)

        ### Voltage Controller Panel
        self.voltage_controller_panel = QVoltagePanel(self.main_splitter)

        self.main_splitter.setStretchFactor(0, 8)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2,1)
        self.main_layout.addWidget(self.main_splitter)
        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 10)

        self.wrapper.setLayout(self.main_layout)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.wrapper)
        self.setCentralWidget(self.central_widget)

        self.setup_signals()
        self.connect_rfsoc(self.ip_address)

    def connect_rfsoc(self, ip_address):
        print("Attempting to connect to RFSoC")

        if ip_address is not None:
            self.soc, self.soccfg = makeProxy(ip_address)
            try:
                print("Available methods:", self.soc._pyroMethods)
                print("Configuration keys:", vars(self.soccfg))
            except Exception as e:
                self.soc_connected = False
                self.soc_status_label.setText('<html><b>✖ Soc Disconnected</b></html>')
                QMessageBox.critical(None, "Error", "RfSoc connection failed: " + str(e))
                return
            else:
                self.soc_connected = True
                self.soc_status_label.setText('<html><b>✔ Soc connected</b></html>')
        else:
            QMessageBox.critical(None, "Error", "RfSoc ip Address not given ")

    def setup_signals(self):
        # Signal Connecting
        self.start_experiment_button.clicked.connect(self.run_experiment)
        self.stop_experiment_button.clicked.connect(self.load_experiment_file)
        self.load_config_button.clicked.connect(self.load_experiment_file)
        self.load_experiment_button.clicked.connect(self.load_experiment_file)

        self.experiment_tabs.currentChanged.connect(self.change_experiment_tab)
        self.experiment_tabs.tabCloseRequested.connect(self.close_experiment_tab)

    def run_experiment(self):
        if self.soc_connected:
            self.thread = QThread()

            ### Handling config
            UpdateConfig = self.config_tree_panel.config["Experiment Config"]
            BaseConfig = self.config_tree_panel.config["Base Config"]
            self.curr_experiment_tab.config = BaseConfig | UpdateConfig
            config = BaseConfig | UpdateConfig

            experiment_instance = self.curr_experiment_tab.experiment_instance
            experiment_name = self.curr_experiment_tab.experiment_name
            date_time_now = datetime.datetime.now()
            date_time_string = date_time_now.strftime("%Y_%m_%d_%H_%M_%S")
            date_string = date_time_now.strftime("%Y_%m_%d")

            ########################################################
            ### Setting up directories, filenames, and other things to be saved
            ########################################################

            ### Create experiment object using updated config
            self.experiment = experiment_instance(self.soccfg, config)
            self.experiment_worker = ExperimentThread(config, soccfg=self.soccfg, exp=self.experiment, soc=self.soc)
            self.experiment_worker.moveToThread(self.thread)  # Move the ExperimentThread onto the actual QThread

            self.thread.started.connect(self.experiment_worker.run)
            self.experiment_worker.finished.connect(self.experiment_worker.quit)
            self.experiment_worker.finished.connect(self.experiment_worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(self.stop_experiment)

            self.worker.updateData.connect(self.curr_experiment_tab.update_data)
            self.worker.updateProgress.connect(self.update_progress)
            self.worker.RFSOC_error.connect(self.RFSOC_error)

            # button and GUI updates
            self.experiment_progress_bar.setProperty("value", 1)  # Show a peek of blue
            self.start_experiment_button.setEnabled(False)
            self.stop_experiment_button.setEnabled(True)

            self.thread.start()
        else:
            QMessageBox.critical(None, "Error", "RfSoc Disconnected.")

    def stop_experiment(self):
        ### Stop an Experiment and all threads.
        if self.experiment_worker:
            self.experiment_worker.stop()

        self.stop_experiment_button.setEnabled(False)
        self.start_experiment_button.setEnabled(True)

    def closeEvent(self, event):
        ### Ensure all threads stop before closing.
        self.stop_experiment()
        event.accept()

    def load_experiment_file(self):
        ### Load an experiment file and read config
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Open Python File", "..\\",
                                              "Python Files (*.py)", options=options)
        if not file:
            return  # user pressed cancel
        else:
            path = Path(file)
            self.create_experiment_tab(str(path))

    def create_experiment_tab(self, path):
        ### Creating a new experiment tab
        tab_count = self.experiment_tabs.count()
        experiment_obj, experiment_name = Helpers.import_file(str(path))
        new_experiment_tab = QTabExperiment(experiment_obj, experiment_name)

        ### not valid experiment file
        if new_experiment_tab.experiment_instance is None:
            return

        tab_idx = self.experiment_tabs.addTab(new_experiment_tab, (experiment_name+".py"))
        self.experiment_tabs.setCurrentIndex(tab_idx)
        self.start_experiment_button.setEnabled(True)
        self.config_tree_panel.set_config(new_experiment_tab.config)
        self.curr_experiment_tab = new_experiment_tab

        if not self.tabs_added:
            if tab_count == 1:
                self.experiment_tabs.removeTab(0)
        self.tabs_added = True

    def change_experiment_tab(self, idx):
        ### Changing the current focused tab
        tab_count = self.experiment_tabs.count()
        if tab_count != 0:
            self.curr_experiment_tab = self.experiment_tabs.widget(idx)
            self.config_tree_panel.set_config(self.curr_experiment_tab.config)

    def close_experiment_tab(self, idx):
        ### Closing an experiment tab
        tab_count = self.experiment_tabs.count()
        self.experiment_tabs.removeTab(idx)
        if tab_count == 1:
            self.start_experiment_button.setEnabled(False)
            self.curr_experiment_tab = None
        else:
            current_tab_idx = self.experiment_tabs.currentIndex()
            self.change_experiment_tab(current_tab_idx)

    def updateProgress(self, sets_complete, reps, sets):
        ### Function to run to update the progress bar
        self.experiment_progress_bar.setValue(math.floor(float(sets_complete) / sets * 100))
        self.experiment_progress_bar.setFormat(
            str(sets_complete * reps) + "/" + str(sets * reps))

    def RFSOC_error(self, e):
        ### RFSOC Error
        QMessageBox.critical(None, "RFSOC error", "RfSoc has thrown an error: " + str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Quarky()
    ex.show()
    sys.exit(app.exec_())