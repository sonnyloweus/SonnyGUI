import sys, os
import math
import datetime
from pathlib import Path
from PyQt5.QtCore import (
    Qt, QSize, QThread
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
from QuarkTab import QQuarkTab
from VoltagePanel import QVoltagePanel
from ConfigTree import QConfigTree
import Helpers

path = os.getcwd()
try:
    os.add_dll_directory(os.path.dirname(path) + '\\PythonDrivers')
except AttributeError:
    os.environ["PATH"] = os.path.dirname(path) + '\\PythonDrivers' + ";" + os.environ["PATH"]

class Quarky(QMainWindow):

    def __init__(self):
        super().__init__()

        self.experiment_worker = None

        self.soc = None
        self.soccfg = None
        self.soc_connected = False

        self.ip_address = None
        # self.ip_address =  "192.168.1.7" ### Need to change to accounts tab

        self.current_tab = None
        self.tabs_added = False
        self.setup_ui()

    def setup_ui(self):
        ### Central Widget
        self.setWindowTitle("Quarky")
        self.resize(1000, 550)
        self.central_widget = QWidget()
        self.central_widget.setMinimumSize(820, 400)
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
        self.experiment_progress_bar.setProperty("value", 0) # Show a peek of blue
        self.experiment_progress_bar.setObjectName("experiment_progress_bar")
        self.experiment_stopwatch = QLabel(self.wrapper)
        self.experiment_stopwatch.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self.experiment_stopwatch.setText('<html><b>00.00ms</b></html>')
        self.experiment_stopwatch.setObjectName("experiment_stopwatch")
        self.load_data_button = QPushButton("Load Data", self.wrapper)
        self.load_data_button.setObjectName("load_data_button")
        self.load_config_button = QPushButton("Load Config", self.wrapper)
        self.load_config_button.setObjectName("load_config_button")
        self.load_experiment_button = QPushButton("Load Experiment", self.wrapper)
        self.load_experiment_button.setObjectName("load_experiment_button")

        self.top_bar.addWidget(self.start_experiment_button)
        self.top_bar.addWidget(self.stop_experiment_button)
        self.top_bar.addWidget(self.soc_status_label)
        self.top_bar.addWidget(self.experiment_progress_bar)
        self.top_bar.addWidget(self.experiment_stopwatch)
        self.top_bar.addWidget(self.load_data_button)
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
        self.central_tabs = QTabWidget(self.main_splitter)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.central_tabs.sizePolicy().hasHeightForWidth())
        self.central_tabs.setSizePolicy(sizePolicy)
        self.central_tabs.setMinimumSize(QSize(400, 0))
        self.central_tabs.setTabPosition(QTabWidget.North)
        self.central_tabs.setTabShape(QTabWidget.Rounded)
        self.central_tabs.setUsesScrollButtons(True)
        self.central_tabs.setDocumentMode(True)
        self.central_tabs.setTabsClosable(True)
        self.central_tabs.setMovable(True)
        self.central_tabs.setTabBarAutoHide(False)
        self.central_tabs.setObjectName("experiment_tabs")
        self.central_tabs.setStyleSheet("background-color: #F8F8F8")  # Light gray background

        ### Template Experiment Tab
        template_experiment_tab = QQuarkTab()
        self.central_tabs.addTab(template_experiment_tab, "No Tabs Added")
        self.central_tabs.setCurrentIndex(0)

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
        if self.ip_address is not None:
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
        # self.load_config_button.clicked.connect(self.load_experiment_file)
        self.load_experiment_button.clicked.connect(self.load_experiment_file)
        self.load_data_button.clicked.connect(self.load_data_file)

        self.central_tabs.currentChanged.connect(self.change_tab)
        self.central_tabs.tabCloseRequested.connect(self.close_tab)

    def run_experiment(self):
        if self.soc_connected:
            if self.current_tab.experiment_obj is None:
                QMessageBox.critical(None, "Error", "Tab is a Data tab.")
                return

            self.thread = QThread()

            ### Handling config
            UpdateConfig = self.config_tree_panel.config["Experiment Config"]
            BaseConfig = self.config_tree_panel.config["Base Config"]
            self.current_tab.config = BaseConfig | UpdateConfig
            config = BaseConfig | UpdateConfig

            experiment_instance = self.current_tab.experiment_instance
            experiment_name = self.current_tab.tab_name
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
            self.thread.started.connect(self.current_tab.clear_plots)
            self.experiment_worker.finished.connect(self.thread.quit)
            self.experiment_worker.finished.connect(self.experiment_worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(self.stop_experiment)

            self.experiment_worker.updateData.connect(self.current_tab.update_data)
            self.experiment_worker.updateProgress.connect(self.update_progress)
            self.experiment_worker.RFSOC_error.connect(self.RFSOC_error)

            # button and GUI updates
            self.experiment_progress_bar.setProperty("value", 1)  # Show a peek of blue
            self.start_experiment_button.setEnabled(False)
            self.stop_experiment_button.setEnabled(True)

            self.thread.start()
        else:
            QMessageBox.critical(None, "Error", "RfSoc Disconnected.")
            return

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
        tab_count = self.central_tabs.count()
        experiment_obj, experiment_name = Helpers.import_file(str(path))
        new_experiment_tab = QQuarkTab(experiment_obj, experiment_name, True)

        ### not valid experiment file
        if new_experiment_tab.experiment_instance is None:
            return

        tab_idx = self.central_tabs.addTab(new_experiment_tab, (experiment_name + ".py"))
        self.central_tabs.setCurrentIndex(tab_idx)
        self.start_experiment_button.setEnabled(True)
        self.config_tree_panel.set_config(new_experiment_tab.config)
        self.current_tab = new_experiment_tab

        if not self.tabs_added:
            if tab_count == 1:
                self.central_tabs.removeTab(0)
        self.tabs_added = True

    def change_tab(self, idx):
        ### Changing the current focused tab
        tab_count = self.central_tabs.count()
        if tab_count != 0:
            self.current_tab = self.central_tabs.widget(idx)
            self.config_tree_panel.set_config(self.current_tab.config)
            if self.current_tab.experiment_instance is None:
                self.start_experiment_button.setEnabled(False)
            else:
                self.start_experiment_button.setEnabled(True)

    def close_tab(self, idx):
        ### Closing a tab
        tab_count = self.central_tabs.count()
        self.central_tabs.removeTab(idx)
        if tab_count == 1:
            self.start_experiment_button.setEnabled(False)
            self.current_tab = None
        else:
            current_tab_idx = self.central_tabs.currentIndex()
            self.change_tab(current_tab_idx)

    def update_progress(self, sets_complete):
        ### Function to run to update the progress bar
        reps, sets = self.current_tab.config['reps'], self.current_tab.config['sets']
        self.experiment_progress_bar.setValue(math.floor(float(sets_complete) / sets * 100))
        self.experiment_progress_bar.setFormat(
            str(sets_complete * reps) + "/" + str(sets * reps))

    def RFSOC_error(self, e):
        ### RFSOC Error
        QMessageBox.critical(None, "RFSOC error", "RfSoc has thrown an error: " + str(e))

    def load_data_file(self):
        ### Load an data file
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Open Data h5 File", "..\\",
                                              "h5 Files (*.h5)", options=options)
        if not file:
            return  # user pressed cancel
        else:
            self.create_data_tab(file)

    def create_data_tab(self, file):
        ### Creating a new data tab
        tab_count = self.central_tabs.count()
        file_name = os.path.basename(file)
        new_data_tab = QQuarkTab(None, file_name, False, file)

        tab_idx = self.central_tabs.addTab(new_data_tab, (file_name + ".h5"))
        self.central_tabs.setCurrentIndex(tab_idx)
        self.start_experiment_button.setEnabled(False)
        self.config_tree_panel.set_config(new_data_tab.config)
        self.current_tab = new_data_tab

        if not self.tabs_added:
            if tab_count == 1:
                self.central_tabs.removeTab(0)
        self.tabs_added = True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Quarky()
    ex.show()
    sys.exit(app.exec_())