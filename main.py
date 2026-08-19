from nesco import NescoPrepaid
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QLineEdit, QPushButton, QTableView
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt, QAbstractTableModel

class TableModel(QAbstractTableModel):
    """
    A model wraps your raw data (a list) and tells the QTableView
    how to read it. The view NEVER touches your list directly —
    it always asks the model.
    """

    def __init__(self, data, headers):
        super().__init__()
        self._data = data        # list of lists/tuples, e.g. [[1,"A",3.5], [2,"B",7.1]]
        self._headers = headers  # list of column names, e.g. ["ID", "Name", "Score"]

    def rowCount(self, parent=None):
        # Tells the view how many rows exist
        return len(self._data)

    def columnCount(self, parent=None):
        # Tells the view how many columns exist
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        # Called by the view for EVERY cell it needs to draw.
        # index.row() / index.column() tell you which cell.
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            return str(value)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # This is where the CUSTOM HEADER comes from.
        # 'section' = column index (if horizontal) or row index (if vertical)
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._headers[section]
        else:
            return str(section + 1)  # row numbers 1,2,3...


class Bill(QWidget):
    def __init__(self):
        super().__init__()
        self.meter = None
        self.resize(700, 1200)
        self.setui()
        
    def setui(self):
        self.masterlayout = QVBoxLayout()
        
        search_number = QLineEdit()
        
        #! Temporary - to be removed
        search_number.setText('44901319')
        
        search_button = QPushButton("Search")
        validator = QIntValidator(0, 2147483647, self)
        search_number.setValidator(validator)
        
        search_button.clicked.connect(lambda : self.search(search_number))
        
        self.basic_info = QVBoxLayout()
        search_bar = QHBoxLayout()

        self.cst_name = QLabel()
        self.cst_address = QLabel()
        self.cst_office = QLabel()
        self.cst_balance = QLabel()
        
        monthly_consumption_header = QLabel("<h2>Monthly Consumption: </h2>")
        self.monthly_consumption_table = QTableView()
        recharge_header = QLabel("<h2>Recharges: </h2>")
        self.recharge_table = QTableView()
        search_bar.addWidget(search_number)
        search_bar.addWidget(search_button)
        search_bar.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.basic_info.addLayout(search_bar)
        self.basic_info.addWidget(self.cst_name)
        self.basic_info.addWidget(self.cst_address)
        self.basic_info.addWidget(self.cst_office)
        self.basic_info.addWidget(self.cst_balance)
        self.basic_info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.masterlayout.addLayout(self.basic_info)
        self.masterlayout.addWidget(monthly_consumption_header)
        self.masterlayout.addWidget(self.monthly_consumption_table)
        self.masterlayout.addWidget(recharge_header)
        self.masterlayout.addWidget(self.recharge_table)
        
        
        self.masterlayout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        
        self.setLayout(self.masterlayout)
        
    def search(self, search_number):
        if search_number.text() == '':
            return
        self.meter = NescoPrepaid(int(search_number.text()))
        data = self.meter.get_customer_info()

        self.cst_name.setText(f"Name: {data['Name']}")
        self.cst_address.setText(f"Address: {data['Address']}")
        self.cst_office.setText(f"Electricity Office: {data['Electricity Office']}")
        balance = float(self.meter.get_balance())
        self.cst_balance.setText(f"Balance: {balance}")
        if balance < 100:
            self.cst_balance.setStyleSheet("Color: Red")
            self.cst_balance.setText(f"Balance: {balance}  <Please Recharge>")
            
        consumtion_data, consumtion_hearers = self.meter.get_monthly_consumption()
        comsumtion_model = TableModel(consumtion_data, consumtion_hearers)
        self.monthly_consumption_table.setModel(comsumtion_model)
        
        recharge_data, rechage_headers = self.meter.get_recharge_history()
        rechage_model = TableModel(recharge_data, rechage_headers)
        self.recharge_table.setModel(rechage_model)
        
        
        
        

App = QApplication([])
main_window = Bill() 
main_window.show()
App.exec()