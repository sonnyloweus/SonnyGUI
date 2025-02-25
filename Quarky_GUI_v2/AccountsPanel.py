import os
import json
from ipaddress import ip_address

from PyQt5.QtCore import QSize, QRect, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QSizePolicy,
    QGroupBox,
    QLabel,
    QScrollArea,
    QFrame,
    QVBoxLayout,
    QListWidget,
    QAbstractItemView,
    QListWidgetItem,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
)

class QAccountPanel(QWidget):

    ### Signals
    rfsoc_attempt_connection = pyqtSignal(str) # argument is ip_address
    rfsoc_disconnect = pyqtSignal()

    def __init__(self, parent=None):
        super(QAccountPanel, self).__init__(parent)

        self.current_account_name = None
        self.current_account_item = None
        self.default_account_name = None
        self.default_account_item = None
        self.connected_account_name = None

        self.root_dir = os.path.dirname(os.path.realpath(__file__))
        self.account_dir = os.path.join(self.root_dir, 'accounts')

        sizepolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizepolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setMinimumSize(QSize(175, 0))
        self.setSizePolicy(sizepolicy)
        self.setObjectName("accounts_panel")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Scrollable area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # self.scroll_area.setGeometry(QRect(0, 0, 175, 500))
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setFrameShadow(QFrame.Plain)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setObjectName("scroll_area")

        self.scroll_area_content = QWidget()
        self.scroll_area_content.setObjectName("scroll_area_content")
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_content)
        self.scroll_area_layout.setContentsMargins(0, 0, 0, 0)

        # Accounts Group
        self.accounts_group = QGroupBox("Accounts")
        self.accounts_group.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.accounts_group.setObjectName("accounts_group")
        self.accounts_layout = QVBoxLayout(self.accounts_group)
        self.accounts_layout.setContentsMargins(0, 0, 0, 0)
        self.accounts_layout.setObjectName("accounts_layout")

        # List of Accounts
        self.accounts_list = QListWidget()
        self.accounts_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.accounts_list.setAlternatingRowColors(False)
        self.accounts_list.setSortingEnabled(True)
        self.accounts_list.setObjectName("accounts_list")
        self.accounts_layout.addWidget(self.accounts_list)

        # Account Editing Layout
        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(5, 0, 5, 0)
        self.form_layout.setVerticalSpacing(2)
        self.form_layout.setObjectName("form_layout")
        self.name_label = QLabel()
        self.name_label.setText("Name")
        self.name_label.setObjectName("name_label")
        self.form_layout.setWidget(0, QFormLayout.LabelRole, self.name_label)
        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("name_edit")
        self.form_layout.setWidget(0, QFormLayout.FieldRole, self.name_edit)
        self.ip_label = QLabel()
        self.ip_label.setText("IP")
        self.ip_label.setObjectName("ip_label")
        self.form_layout.setWidget(1, QFormLayout.LabelRole, self.ip_label)
        self.ip_edit = QLineEdit()
        self.ip_edit.setObjectName("ip_edit")
        self.form_layout.setWidget(1, QFormLayout.FieldRole, self.ip_edit)
        self.accounts_layout.addLayout(self.form_layout)

        # Account Buttons
        self.form_button_layout = QVBoxLayout()
        self.form_button_layout.setSpacing(0)
        self.form_button_layout.setObjectName("form_button_layout")

        self.save_button = QPushButton("Up to Date")
        self.save_button.setObjectName("save_button")
        self.save_button.setEnabled(False)
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("delete_button")
        self.delete_button.setEnabled(True)
        self.create_new_button = QPushButton("Create as New")
        self.create_new_button.setObjectName("create_new_button")
        self.create_new_button.setEnabled(False)
        self.set_default_button = QPushButton("Set as Default")
        self.set_default_button.setObjectName("set_default_button")
        self.set_default_button.setEnabled(False)
        self.connect_button = QPushButton("Connect")
        self.connect_button.setObjectName("connect_button")
        self.connect_button.setEnabled(True)

        self.form_button_layout.addWidget(self.save_button)
        self.form_button_layout.addWidget(self.delete_button)
        self.form_button_layout.addWidget(self.create_new_button)
        self.form_button_layout.addWidget(self.set_default_button)
        self.form_button_layout.addWidget(self.connect_button)

        # Adding all Layouts Together
        self.accounts_layout.addLayout(self.form_button_layout)
        self.accounts_group.setLayout(self.accounts_layout)

        self.scroll_area_layout.addWidget(self.accounts_group)
        self.scroll_area_content.setLayout(self.scroll_area_layout)
        self.scroll_area.setWidget(self.scroll_area_content)

        self.main_layout.addWidget(self.scroll_area)
        self.setLayout(self.main_layout)

        ########## Load in Accounts Here
        self.setup_signals()

    def setup_signals(self):
        self.save_button.clicked.connect(self.update_account)
        self.delete_button.clicked.connect(self.delete_account)
        self.create_new_button.clicked.connect(self.create_account)
        self.set_default_button.clicked.connect(self.set_as_default)
        self.connect_button.clicked.connect(self.attempt_connection_or_disconnect)

        self.ip_edit.textChanged.connect(self.unsaved_indicate)
        self.name_edit.textChanged.connect(self.unsaved_indicate)
        self.accounts_list.currentItemChanged.connect(self.select_item)

    def load_accounts(self):
        self.current_account_name = None
        self.current_account_item = None
        self.accounts_list.clear()

        default_file = os.path.join(self.account_dir, "default.json")
        if not os.path.exists(self.account_dir) or not os.path.exists(default_file):
            os.makedirs(self.account_dir)
            template_file = os.path.join(self.account_dir, "template.json")

            with open(default_file, "w") as f:
                json.dump({"default_account_name": "template"}, f, indent=4)
            with open(template_file, "w") as f:
                json.dump({"ip_address": "111.111.1.111", "account_name": "template"}, f, indent=4)

        with open(default_file, "r") as f:
            data = json.load(f)
            self.default_account_name = data["default_account_name"]

        for file in os.listdir(self.account_dir):
            if file.endswith(".json") and file != "default.json":
                with open(os.path.join(self.account_dir, file), "r") as f:
                    data = json.load(f)
                    name = data["account_name"]
                    ip = data["ip_address"]
                    if name == self.default_account_name:
                        item = QListWidgetItem(str(name + ' (default)'))
                        self.default_account_item = item
                        if self.current_account_name is None or self.current_account_item is None:
                            self.current_account_name = self.default_account_name
                            self.current_account_item = item
                    else:
                        item = QListWidgetItem(str(name))
                    self.accounts_list.addItem(item)

        self.select_item(self.current_account_item)
        self.saved_indicate()

    def attempt_connection_or_disconnect(self):
        if self.connected_account_name is None:
            ip_address = self.ip_edit.text().strip()
            if ip_address and all(char.isdigit() or char == '.' for char in ip_address):
                self.rfsoc_attempt_connection.emit(ip_address)
            else:
                QMessageBox.critical(None, "Error", "IP address " + ip_address + " invalid.")
        else:
            self.rfsoc_disconnect.emit()
            self.connect_button.setText("Connect")
            self.connected_account_name = None
            self.load_accounts()
            self.ip_edit.setDisabled(False)
            self.name_edit.setDisabled(False)
            self.saved_indicate()


    def unsaved_indicate(self):
        self.save_button.setText("Save")
        self.save_button.setEnabled(True)
        self.create_new_button.setEnabled(True)
        self.set_default_button.setEnabled(False)

    def saved_indicate(self):
        self.save_button.setText("Up to Date")
        self.save_button.setEnabled(False)
        self.create_new_button.setEnabled(False)
        self.set_default_button.setEnabled(True)

    def disable_since_connected(self):
        self.save_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.create_new_button.setEnabled(False)
        self.set_default_button.setEnabled(False)
        self.ip_edit.setDisabled(True)
        self.name_edit.setDisabled(True)

    def update_account(self):
        if self.current_account_name:
            new_ip_address = self.ip_edit.text().strip()
            new_account_name = self.name_edit.text()
            if not self.validate_account_input(new_ip_address, new_account_name, 'update'): return

            # Load the existing JSON file
            file = os.path.join(self.account_dir, self.current_account_name + '.json')
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    data["ip_address"] = new_ip_address
                    data["account_name"] = new_account_name
                with open(file, "w") as f:
                    json.dump(data, f, indent=4)
                new_filename = (new_account_name.strip() + ".json")
                os.rename(file, os.path.join(self.account_dir, new_filename))

                if self.current_account_name == self.default_account_name:
                    self.update_default_account_name(new_account_name, self.current_account_item)
                    self.current_account_item.setText(new_account_name + ' (default)')
                else:
                    self.current_account_item.setText(new_account_name)

                self.current_account_name = new_account_name
                self.saved_indicate()
            except (json.JSONDecodeError, FileNotFoundError):
                QMessageBox.critical(None, "Error", "Error updating Json file.")
                return

    def validate_account_input(self, new_ip_address, new_account_name, purpose):
        invalid_chars = r'.\/:*?"<>| '
        if any(char in new_account_name for char in invalid_chars):
            QMessageBox.critical(None, "Error", "Invalid account name. No " + invalid_chars + "or spaces.")
            return False
        if not new_ip_address or not new_account_name:
            QMessageBox.critical(None, "Error", "IP address or account name cannot be empty.")
            return False
        if not all(part.isdigit() and 0 <= int(part) <= 255 for part in new_ip_address.split('.') if part):
            QMessageBox.critical(None, "Error", "IP address invalid.")
            return False

        if purpose == 'create':
            # no duplicate account names
            for idx in range(self.accounts_list.count()):
                item = self.accounts_list.item(idx)
                account_name = item.text().strip()
                if account_name.endswith("(default)"): account_name = account_name[:-9]
                if account_name.startswith("✔"): account_name = account_name[1:]
                account_name = account_name.strip()
                if account_name == new_account_name:
                    QMessageBox.critical(None, "Error", "Account name already exists.")
                    return False

        return True

    def update_default_account_name(self, new_default_account_name, new_default_account_item):
        default_file = os.path.join(self.account_dir, "default.json")
        try:
            self.default_account_name = new_default_account_name
            self.default_account_item = new_default_account_item
            with open(default_file, "w") as f:
                json.dump({"default_account_name": new_default_account_name}, f, indent=4)
        except (json.JSONDecodeError, FileNotFoundError):
            QMessageBox.critical(None, "Error", "Error updating default file.")
            return

    def create_account(self):
        new_ip_address = self.ip_edit.text().strip()
        new_account_name = self.name_edit.text()
        if not self.validate_account_input(new_ip_address, new_account_name, 'create'): return

        new_filename = (new_account_name.strip() + ".json")
        new_account_file = os.path.join(self.account_dir,new_filename)

        with open(new_account_file, "w") as f:
            json.dump({"ip_address": str(new_ip_address), "account_name": str(new_account_name)}, f, indent=4)

        item = QListWidgetItem(str(new_account_name))
        self.accounts_list.addItem(item)
        self.select_item(item)

    def select_item(self, current, previous=None):
        if current is not None:
            account_name = current.text().strip()
            if account_name.endswith("(default)"): account_name = account_name[:-9]
            if account_name.startswith("✔"): account_name = account_name[1:]
            self.current_account_name = account_name.strip()
            self.current_account_item = current
            self.accounts_list.setCurrentItem(current)

            file = os.path.join(self.account_dir, self.current_account_name + '.json')
            with open(file, "r") as f:
                data = json.load(f)
                name = data["account_name"]
                ip = data["ip_address"]
                self.name_edit.setText(name)
                self.ip_edit.setText(ip)

            if self.connected_account_name is not None:
                self.disable_since_connected()
            else:
                self.saved_indicate()

    def delete_account(self):
        if self.current_account_name == self.default_account_name:
            QMessageBox.critical(None, "Error", "Cannot delete default account.")
            return
        file = os.path.join(self.account_dir, self.current_account_name + '.json')
        if os.path.exists(file):
            os.remove(file)
        else:
            QMessageBox.critical(None, "Error", "Cannot find file with account name.")
            return
        selected_item_row_idx = self.accounts_list.currentRow()
        self.accounts_list.takeItem(selected_item_row_idx)
        if self.current_account_name == self.connected_account_name:
            self.rfsoc_disconnect.emit()

        self.select_item(self.default_account_item)

    def set_as_default(self):
        self.update_default_account_name(self.current_account_name, self.current_account_item)
        self.load_accounts()

    def rfsoc_connection_updated(self, ip_address, status):
        if status == 'success':
            self.connected_account_name = self.current_account_name
            if self.current_account_name == self.default_account_name:
                self.current_account_item.setText('✔ ' + self.current_account_name + ' (default)')
            else:
                self.current_account_item.setText('✔ ' + self.current_account_name)

            self.connect_button.setText("Disconnect")
            print("Connection established.")
            self.disable_since_connected()
        else:
            self.connected_account_name = None
            print("Connection not successful.")
            self.saved_indicate()

    ### Connect (give '✔ ' + ) --- add signal back that says success or not (if success, then
    ### give the checkmark and change connected_account_name
    ### if connected, prevent any changes. must disconnect first (disenable buttons maybe lock lineedits