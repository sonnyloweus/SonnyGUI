"""
=========
Quarky.py
=========
Main entry point for the Quarky GUI application.

This module initializes the GUI, handles application-level logic, and manages interactions between
different components.
"""

# TODO: Experiment Class Plotter
# TODO: include legend for plotter
# TODO: Saving Data Files, Screenshotting
# TODO: Make a separate thread for proxy connections

import sys, os
import math
import datetime
from pathlib import Path
from PyQt5.QtCore import (
    Qt, QSize, QThread, pyqtSignal, qInstallMessageHandler, qDebug,
    qInfo,
    qWarning,
    qCritical,
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

# Use absolute imports
from scripts.CoreLib.socProxy import makeProxy
from scripts.ExperimentThread import ExperimentThread
from scripts.QuarkTab import QQuarkTab
from scripts.VoltagePanel import QVoltagePanel
from scripts.AccountsPanel import QAccountPanel
from scripts.LogPanel import QLogPanel
from scripts.ConfigTreePanel import QConfigTreePanel
import scripts.Helpers as Helpers

### Importing the PythonDrivers --- not sure if it works currently since they aren't being used
script_directory = os.path.dirname(os.path.realpath(__file__))
script_parent_directory = os.path.dirname(script_directory)
try:
    os.add_dll_directory(os.path.join(script_parent_directory, 'PythonDrivers'))
except AttributeError:
    os.environ["PATH"] = script_parent_directory + '\\PythonDrivers' + ";" + os.environ["PATH"]

class Quarky(QMainWindow):
    """
    The class for the main Quarky application window.
    """

    ### Defining Signals
    rfsoc_connection_updated = pyqtSignal(str, str)
    """ The Signal sent to the accounts tab after an rfsoc connection attempt """

    def __init__(self):
        """
        Initializes an instance of a Quarky GUI application.

        **Important Attributes:**

        * experiment_worker (ExperimentThread): The instance of the experiment worker thread.
        * soc (Proxy): The instance of the RFSoC Proxy connection via Pyro4.
        * soccfg (QickConfig): The qick Config of the RFSoC.
        * central_widget (QWidget): The central widget of the Quarky GUI.
        """

        super().__init__()

        # Stores the thread that runs an experiment
        self.experiment_worker = None

        # Instance variables for the rfsoc connection
        self.soc = None
        self.soccfg = None
        self.soc_connected = False

        # Tracks the central tab module by the currently selected tab
        self.current_tab = None
        self.tabs_added = False

        self.setup_ui() # Setup up the PyQt UI

    def setup_ui(self):
        """
        Initializes the UI elements.
        """

        ### Central Widget, Layout, and Wrapper
        ### To support responsive resizing of content within a widget, the content must be within a layout & widget
        ### Thus, the central_layout contains all the elements of the UI within the wrapper widget
        ### central widget <-- central layout <-- wrapper <-- all content elements
        self.setWindowTitle("Quarky")
        self.resize(1000, 550)
        self.central_widget = QWidget() # Defining the central widget that holds everything
        self.central_widget.setMinimumSize(820, 400)
        self.central_widget.setObjectName("central_widget")
        self.central_layout = QVBoxLayout(self.central_widget)
        self.wrapper = QWidget()
        self.wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.wrapper.setObjectName("wrapper")

        ### Main layout (vertical) <-- (top bar) + (main splitter that has all panels)
        self.main_layout = QVBoxLayout(self.wrapper)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setObjectName("main_layout")

        ### Top Control Bar (contains loading and experiment run buttons + progress bar)
        self.top_bar = QHBoxLayout()
        self.top_bar.setContentsMargins(-1, 10, -1, 10)
        self.top_bar.setObjectName("top_bar")

        # Creating top bar items
        self.start_experiment_button = Helpers.create_button("▶","start_experiment",False,self.wrapper)
        self.stop_experiment_button = Helpers.create_button("⏹","stop_experiment",False,self.wrapper)
        self.soc_status_label = QLabel('<html><b>✖ Soc Disconnected</b></html>', self.wrapper)
        self.soc_status_label.setObjectName("soc_status_label")
        self.experiment_progress_bar = QProgressBar(self.wrapper, value=0)
        self.experiment_progress_bar.setObjectName("experiment_progress_bar")
        self.load_data_button = Helpers.create_button("Load Data","load_data_button",True,self.wrapper)
        self.load_experiment_button = Helpers.create_button("Load Experiment","load_experiment_button",True,self.wrapper)

        # Adding items to top bar, top bar to main layout
        self.top_bar.addWidget(self.start_experiment_button)
        self.top_bar.addWidget(self.stop_experiment_button)
        self.top_bar.addWidget(self.soc_status_label)
        self.top_bar.addWidget(self.experiment_progress_bar)
        self.top_bar.addWidget(self.load_data_button)
        self.top_bar.addWidget(self.load_experiment_button)
        self.main_layout.addLayout(self.top_bar)

        ### Main Splitter with Tabs, Voltage Panel, Config Tree
        self.main_splitter = QSplitter(self.wrapper)
        self.main_splitter.setLineWidth(2)
        self.main_splitter.setOpaqueResize(True) # Setting to False allows faster resizing (doesn't look as good)
        self.main_splitter.setHandleWidth(7)
        self.main_splitter.setChildrenCollapsible(True)
        self.main_splitter.setObjectName("main_splitter")

        ### The Central Tabs (contains experiment tabs and data tab)
        self.central_tabs = QTabWidget(self.main_splitter)
        central_tab_sizepolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        central_tab_sizepolicy.setHorizontalStretch(0)
        central_tab_sizepolicy.setVerticalStretch(0)
        central_tab_sizepolicy.setHeightForWidth(self.central_tabs.sizePolicy().hasHeightForWidth())
        self.central_tabs.setSizePolicy(central_tab_sizepolicy)
        self.central_tabs.setMinimumSize(QSize(400, 0))
        self.central_tabs.setTabPosition(QTabWidget.North)
        self.central_tabs.setTabShape(QTabWidget.Rounded)
        self.central_tabs.setUsesScrollButtons(True)
        self.central_tabs.setDocumentMode(True)
        self.central_tabs.setTabsClosable(True)
        self.central_tabs.setMovable(True)
        self.central_tabs.setTabBarAutoHide(False)
        self.central_tabs.setObjectName("central_tabs")
        # self.central_tabs.setStyleSheet("background-color: #F8F8F8")  # Light gray background
        #Template Experiment Tab
        template_experiment_tab = QQuarkTab()
        self.central_tabs.addTab(template_experiment_tab, "No Tabs Added")
        self.central_tabs.setCurrentIndex(0)

        ### Config Tree Panel
        self.config_tree_panel = QConfigTreePanel(self.main_splitter, template_experiment_tab.config)

        ### Side Tabs Panel (Contains voltage, accounts, and log panels)
        self.side_tabs = QTabWidget(self.main_splitter)
        side_tab_sizepolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        side_tab_sizepolicy.setHorizontalStretch(0)
        side_tab_sizepolicy.setVerticalStretch(0)
        side_tab_sizepolicy.setHeightForWidth(self.side_tabs.sizePolicy().hasHeightForWidth())
        self.side_tabs.setSizePolicy(side_tab_sizepolicy)
        self.side_tabs.setMinimumSize(QSize(175, 0))
        self.side_tabs.setTabPosition(QTabWidget.North)
        self.side_tabs.setTabShape(QTabWidget.Rounded)
        self.side_tabs.setDocumentMode(True)
        self.side_tabs.setTabsClosable(False)
        self.side_tabs.setMovable(False)
        self.side_tabs.setObjectName("side_tabs")

        ### Voltage Controller Panel
        self.voltage_controller_panel = QVoltagePanel()
        self.side_tabs.addTab(self.voltage_controller_panel, "Voltage")
        ### Accounts Panel
        self.accounts_panel = QAccountPanel(parent=self.central_tabs)
        self.side_tabs.addTab(self.accounts_panel, "Accounts")
        ### Log Panel
        self.log_panel = QLogPanel(parent=self.central_tabs)
        self.side_tabs.addTab(self.log_panel, "Log")
        self.side_tabs.setCurrentIndex(1) # select accounts panel by default

        # Defining the default sizes for the splitter
        self.main_splitter.setStretchFactor(0, 8)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2,1)
        self.main_layout.addWidget(self.main_splitter)
        self.main_layout.setStretch(0, 1) # make top bar small
        self.main_layout.setStretch(1, 10) # make main body large

        # Completing the hierarchy mentioned at the top
        self.wrapper.setLayout(self.main_layout)
        self.central_layout.addWidget(self.wrapper)
        self.setCentralWidget(self.central_widget)

        self.setup_signals()
        self.accounts_panel.load_accounts() # Loads all accounts saved within accounts folder

    def setup_signals(self):
        """
        Sets up all signals and slots of the main application window.
        """

        # Connecting the top bar buttons to their respective functions
        self.start_experiment_button.clicked.connect(self.run_experiment)
        self.stop_experiment_button.clicked.connect(self.load_experiment_file)
        self.load_experiment_button.clicked.connect(self.load_experiment_file)
        self.load_data_button.clicked.connect(self.load_data_file)

        # Tab Change and Close signals
        self.central_tabs.currentChanged.connect(self.change_tab)
        self.central_tabs.tabCloseRequested.connect(self.close_tab)

        # Signals for RFSoC from the accounts panel
        self.accounts_panel.rfsoc_attempt_connection.connect(self.connect_rfsoc)
        self.accounts_panel.rfsoc_disconnect.connect(self.disconnect_rfsoc)
        # Signals for the RFSoC to the accounts panel
        self.rfsoc_connection_updated.connect(self.accounts_panel.rfsoc_connection_updated)

        # Log message handler installation
        qInstallMessageHandler(self.log_panel.message_handler)
        self.test_logging()

    def test_logging(self):
        """
        Tests the logging functionality and displays respective message colors.
        """

        qDebug("This is a debug message.")
        qInfo("This is an info message.")
        qWarning("This is a warning message!")
        qCritical("This is a critical error!")

    def disconnect_rfsoc(self):
        """
        Disconnects the RFSoC instance.
        """
        self.soc = None
        self.soccfg = None
        self.soc_connected = False
        qInfo("Disconnected from RFSoC")

    def connect_rfsoc(self, ip_address):
        """
        Connects the RFSoC instance to the specified IP address.

        :param ip_address: The IP address of the RFSoC instance.
        :type ip_address: str
        """

        qInfo("Attempting to connect to RFSoC")
        if ip_address is not None:
            # Attempt RFSoC connection via makeProxy
            try:
                self.soc, self.soccfg = makeProxy(ip_address)
            except Exception as e:
                self.soc_connected = False
                self.soc_status_label.setText('<html><b>✖ Soc Disconnected</b></html>')
                QMessageBox.critical(None, "Error", "RFSoC connection to failed (see log).")
                qCritical("RFSoC connection to " + ip_address + " failed: " + str(e))
                self.rfsoc_connection_updated.emit(ip_address, 'failure') # emit failure to accounts tab
                return

            # Verifying RFSoc connection
            try:
                print("Available methods:", self.soc._pyroMethods)
                print("Configuration keys:", vars(self.soccfg))
            except Exception as e:
                # Connection invalid despite makeProxy success
                self.disconnect_rfsoc()
                self.soc_status_label.setText('<html><b>✖ Soc Disconnected</b></html>')
                QMessageBox.critical(None, "Error", "RFSoC connection invalid (see log).")
                qCritical("RFSoC connection to " + ip_address + " invalid: " + str(e))
                self.rfsoc_connection_updated.emit(ip_address, 'failure')
                return
            else:
                self.soc_connected = True
                self.soc_status_label.setText('<html><b>✔ Soc connected</b></html>')
                self.rfsoc_connection_updated.emit(ip_address, 'success') # emit success to accounts tab
        else:
            qCritical("RFSoC IP address is unspecified, param passed is " + str(ip_address))
            QMessageBox.critical(None, "Error", "RFSoC IP Address not given.")

    def run_experiment(self):
        """
        Runs the experiment instance of the current active tab via the RFSoC connection. This function is where the
        new Experiment Worker Thread is created and all signals for data updating and experiment termination
        are connected.
        """

        if self.soc_connected: # ensure RFSoC connection
            if self.current_tab.experiment_obj is None: # ensure tab is not a data tab
                qCritical("Attempted execution of a data tab (" + self.current_tab.tab_name +
                          ")rather than an experiment tab")
                QMessageBox.critical(None, "Error", "Tab is a Data tab.")
                return

            self.thread = QThread()

            # Handling config specific to the current tab
            UpdateConfig = self.config_tree_panel.config["Experiment Config"]
            BaseConfig = self.config_tree_panel.config["Base Config"]
            config = self.current_tab.config = BaseConfig | UpdateConfig # symmetric difference and intersection

            #########################################################################
            ### TODO: Setting up directories, filenames, and other things to be saved
            #########################################################################
            # Setting up variables necessary for saving data files, probably move to QuarkTab
            experiment_name = self.current_tab.tab_name
            date_time_now = datetime.datetime.now()
            date_time_string = date_time_now.strftime("%Y_%m_%d_%H_%M_%S")
            date_string = date_time_now.strftime("%Y_%m_%d")

            # Create experiment object using updated config and current tab's experiment instance
            experiment_instance = self.current_tab.experiment_instance
            self.experiment = experiment_instance(self.soccfg, config)
            # Creating the experiment worker from ExperimentThread
            self.experiment_worker = ExperimentThread(config, soccfg=self.soccfg, exp=self.experiment, soc=self.soc)
            self.experiment_worker.moveToThread(self.thread) # Move the ExperimentThread onto the actual QThread

            # Connecting started and finished signals
            self.thread.started.connect(self.experiment_worker.run) # run experiment
            self.experiment_worker.finished.connect(self.thread.quit) # stop thread
            self.experiment_worker.finished.connect(self.experiment_worker.deleteLater) # delete worker
            self.thread.finished.connect(self.thread.deleteLater) # delete thread
            self.thread.finished.connect(self.stop_experiment) # update UI

            # Connecting data related slots
            self.experiment_worker.updateData.connect(self.current_tab.update_data) # update data & plot
            self.experiment_worker.updateProgress.connect(self.update_progress) # update progress bar
            self.experiment_worker.RFSOC_error.connect(self.RFSOC_error) # connect any RFSoC errors

            # button and GUI updates
            self.experiment_progress_bar.setProperty("value", 1)
            self.start_experiment_button.setEnabled(False)
            self.stop_experiment_button.setEnabled(True)

            self.thread.start()
        else:
            qCritical("The RfSoC instance is not yet connected. Current soc has the value: " + self.soc)
            QMessageBox.critical(None, "Error", "RfSoC Disconnected.")
            return

    def stop_experiment(self):
        """
        Stop an Experiment if not auto-terminated and update respective UI.
        """

        if self.experiment_worker:
            self.experiment_worker.stop()

        self.stop_experiment_button.setEnabled(False)
        self.start_experiment_button.setEnabled(True)

    def closeEvent(self, event):
        """
        Overrides the default closeEvent() function in a PyQt widget by first ensuring all threads have stopped.

        :param event: The PyQt widget to close.
        :type event: QCloseEvent
        """

        self.stop_experiment()
        event.accept()

    def load_experiment_file(self):
        """
        Gets an .py experiment file per user input.
        """
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Open Python File", "..\\",
                                              "Python Files (*.py)", options=options)
        if not file:
            return
        else:
            path = Path(file)
            qInfo("Loading experiment file: " + str(path))
            self.create_experiment_tab(str(path)) # pass full path of the experiment file

    def create_experiment_tab(self, path):
        """
        Creates a new QQuarkTab instance for the new experiment tab.

        :param path: The path to the experiment file.
        :type path: str
        """

        tab_count = self.central_tabs.count()
        experiment_obj, experiment_name = Helpers.import_file(str(path)) # gets experiment object from file

        # Creating a new QQuarkTab that extracts all features from the experiment file (see QQuarkTab documentation)
        new_experiment_tab = QQuarkTab(experiment_obj, experiment_name, True)
        if new_experiment_tab.experiment_instance is None: # not valid experiment file
            qCritical("The experiment tab failed to be created - source of the error found in QQuarkTab module.")
            return

        # Handling UI updates: Update current tab, enable experiment running, update ConfigPanel
        tab_idx = self.central_tabs.addTab(new_experiment_tab, (experiment_name + ".py"))
        self.central_tabs.setCurrentIndex(tab_idx)
        self.start_experiment_button.setEnabled(True)
        self.config_tree_panel.set_config(new_experiment_tab.config)
        self.current_tab = new_experiment_tab

        # Remove the template tab created on GUI initialization
        if not self.tabs_added and tab_count == 1:
                self.central_tabs.removeTab(0)
        self.tabs_added = True

    def change_tab(self, idx):
        """
        Called upon tab change of the central tab widget. Updates UI and current tab attributes.

        :param idx: The index of the newly selected tab widget.
        :type idx: int
        """

        if self.central_tabs.count() != 0:
            self.current_tab = self.central_tabs.widget(idx)
            self.config_tree_panel.set_config(self.current_tab.config) # update config panel

            if self.current_tab.experiment_instance is None: # check if tab is a data or experiment tab
                self.start_experiment_button.setEnabled(False)
            else:
                self.start_experiment_button.setEnabled(True)

    def close_tab(self, idx):
        """
        Called upon a user closing a central experiment or data tab.

        :param idx: The index of the closed tab widget.
        :type idx: int
        """

        self.central_tabs.removeTab(idx)
        if self.central_tabs.count() == 0: # if no tabs remaining
            self.start_experiment_button.setEnabled(False)
            self.current_tab = None
        else:
            current_tab_idx = self.central_tabs.currentIndex() # get the tab changed to upon closure
            self.change_tab(current_tab_idx)

    def update_progress(self, sets_complete):
        """
        The function that updates the progress bar based on experiment progress.

        :param sets_complete: The number of sets of the experiment that have been completed
        :type sets_complete: int
        """

        # Getting the total reps and sets to be run from the experiment configs
        reps, sets = self.current_tab.config['reps'], self.current_tab.config['sets']
        self.experiment_progress_bar.setValue(math.floor(float(sets_complete) / sets * 100)) # calculate completed %
        self.experiment_progress_bar.setFormat(str(sets_complete * reps) + "/" + str(sets * reps)) # update text

    def RFSOC_error(self, e):
        """
        The function called when RFSoC returns an error to display
        """

        qCritical("RFSoC thew the error: " + str(e))
        QMessageBox.critical(None, "RFSOC error", "RfSoc has thrown an error (see log).")

    def load_data_file(self):
        """
        Gets an .h5 experiment file per user input.
        """

        # Load an data file
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, "Open Data h5 File", "..\\",
                                              "h5 Files (*.h5)", options=options)
        if not file:
            return
        else:
            self.create_data_tab(file)  # pass full path of the data file

    def create_data_tab(self, file):
        """
        Creates a new QQuarkTab instance for the new data tab.

        :param path: The path to the data file.
        :type path: str
        """

        tab_count = self.central_tabs.count()
        file_name = os.path.basename(file)
        # Creates the new QQuarkTab instance specifying not an experiment tab
        new_data_tab = QQuarkTab(None, file_name, False, file)

        # Handle UI updates
        tab_idx = self.central_tabs.addTab(new_data_tab, (file_name + ".h5"))
        self.central_tabs.setCurrentIndex(tab_idx)
        self.start_experiment_button.setEnabled(False)
        self.config_tree_panel.set_config(new_data_tab.config) # update config (when data files have config)
        self.current_tab = new_data_tab

        if not self.tabs_added:
            if tab_count == 1:
                self.central_tabs.removeTab(0)
        self.tabs_added = True

# Creating the Quarky GUI Main Window
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Quarky()
    ex.show()
    sys.exit(app.exec_())