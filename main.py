from nesco import NescoPrepaid
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QLineEdit, QPushButton, QTableView
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt, QAbstractTableModel, QObject, QThread, Signal


class Worker(QObject):
    finished = Signal()
    error = Signal(str)
    result = Signal(object)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            res = self.fn(*self.args, **self.kwargs)
            self.result.emit(res)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

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

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # Called by the view for EVERY cell it needs to draw.
        # index.row() / index.column() tell you which cell.
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data[index.row()][index.column()]
            return str(value)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        # This is where the CUSTOM HEADER comes from.
        # 'section' = column index (if horizontal) or row index (if vertical)
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        else:
            return str(section + 1)  # row numbers 1,2,3...


class Bill(QWidget):
    def __init__(self):
        super().__init__()
        self.meter = None
        self.resize(820, 600)
        self.setui()
        
    def setui(self):
        self.masterlayout = QVBoxLayout()
        self.basic_info = QVBoxLayout()
        search_bar = QHBoxLayout()
        self.results = QVBoxLayout()
        
        validator = QIntValidator(0, 2147483647, self)
        
        search_number = QLineEdit()
        search_number.setValidator(validator)
        
        #! Temporary - to be removed
        search_number.setText('44901319')
        
        search_button = QPushButton("Search")
        search_button.clicked.connect(lambda : self.heavy_search(search_number))
        
        self.cst_name = QLabel()
        self.cst_address = QLabel()
        self.cst_office = QLabel()
        self.cst_balance = QLabel()
        
        self.month = QLabel()
        self.recharge_amount = QLabel()
        self.usage_amount = QLabel()
        
        self.recharge_table = QTableView()
        self.recharge_table.verticalHeader().setVisible(False)
        
        
        search_bar.addWidget(search_number)
        search_bar.addWidget(search_button)
        search_bar.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.basic_info.addLayout(search_bar)
        self.basic_info.addWidget(self.cst_name)
        self.basic_info.addWidget(self.cst_address)
        self.basic_info.addWidget(self.cst_office)
        self.basic_info.addWidget(self.cst_balance)
        self.basic_info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.results.addWidget(QLabel("<h2>Monthly Consumption: </h2>"))
        self.results.addWidget(self.month)
        self.results.addWidget(self.recharge_amount)
        self.results.addWidget(self.usage_amount)
        self.results.addWidget(QLabel("<h2>Recharges: </h2>"))
        self.results.addWidget(self.recharge_table)
        self.masterlayout.addLayout(self.basic_info)
        self.masterlayout.addLayout(self.results)
        
        
        
        
        self.masterlayout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        
        self.setLayout(self.masterlayout)
        
    def heavy_search(self, search_number):
        number = search_number.text()
        if number == '':
            return
        
        self.thread = QThread()
        self.worker = Worker(self.fetch_data, int(number))
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.result.connect(self.on_result)
        self.worker.error.connect(self.on_error)
        
        self.thread.start()

        
    def fetch_data(self, number):
        # runs on the worker thread — no widget access allowed here
        self.meter = NescoPrepaid(number)
        customer_info = self.meter.get_customer_info()
        balance = float(self.meter.get_balance())
        consumption = self.meter.get_monthly_consumption()
        recharge_data, recharge_headers = self.meter.get_recharge_history()
        return {
            'customer_info': customer_info,
            'balance': balance,
            'consumption': consumption,
            'recharge_data': recharge_data,
            'recharge_headers': recharge_headers,
        }
    
    def on_result(self, res):
        # runs back on the main thread — safe to touch widgets here
        data = res['customer_info']
        self.cst_name.setText(f"Name: {data['Name']}")
        self.cst_address.setText(f"Address: {data['Address']}")
        self.cst_office.setText(f"Electricity Office: {data['Electricity Office']}")

        balance = res['balance']
        self.cst_balance.setText(f"Balance: {balance}")
        if balance < 100:
            self.cst_balance.setStyleSheet("Color: Red")
            self.cst_balance.setText(f"Balance: {balance}  <Please Recharge>")

        cdata = res['consumption']
        self.month.setText(f"Month: {cdata['Month']}")
        self.recharge_amount.setText(f"Recharge: {cdata['Recharge']}")
        self.usage_amount.setText(f"Usage: {cdata['Usage']}")

        model = TableModel(res['recharge_data'], res['recharge_headers'])
        self.recharge_table.setModel(model)
        self.recharge_table.resizeColumnsToContents()
        self.recharge_table.horizontalHeader().setStretchLastSection(True)
        self.width = self.recharge_table.width()
    def on_error(self, e):
        print(e)
        
        

App = QApplication([])
main_window = Bill() 
main_window.show()
App.exec()