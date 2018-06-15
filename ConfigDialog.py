import sys
from PyQt5.QtWidgets import (QWidget, QPushButton, QLineEdit, QLabel, QGridLayout,
    QDialog, QApplication, QMessageBox)
from PyQt5.QtCore import Qt
import ConfigStorage

class ConfigDialog(QDialog):
    def __init__(self, data):
        super(ConfigDialog, self).__init__()
        self.data = data
        self.returnVal = []
        self.setWindowTitle("Окно конфигурации")

        lbl1 = QLabel("Левый передний")
        lbl2 = QLabel("Ед")
        lbl3 = QLabel("см")
        lbl4 = QLabel("Ед")
        lbl5 = QLabel("см")
        lbl6 = QLabel("Ед")
        lbl7 = QLabel("см")
        lbl8 = QLabel("Ед")
        lbl9 = QLabel("см")
        lbl10 = QLabel("Максимум")
        lbl11 = QLabel("Среднее")
        lbl12 = QLabel("Правый передний")
        lbl13 = QLabel("Левый задний")
        lbl14 = QLabel("Левый передний")

        self.vLFMaxCm = ConfigStorage.get_setting('suspension_config.ini', 'Suspension', 'LFMax')
        self.vLFRefCm = ConfigStorage.get_setting('suspension_config.ini', 'Suspension', 'LFRef')
        self.vRFMaxCm = ConfigStorage.get_setting('suspension_config.ini', 'Suspension', 'RFMax')
        self.vRFRefCm = ConfigStorage.get_setting('suspension_config.ini', 'Suspension', 'RFRef')

        self.vLRMaxCm = ConfigStorage.get_setting('suspension_config.ini', 'Suspension', 'LRMax')
        self.vLRRefCm = ConfigStorage.get_setting('suspension_config.ini', 'Suspension', 'LRRef')
        self.vRRMaxCm = ConfigStorage.get_setting('suspension_config.ini', 'Suspension', 'RRMax')
        self.vRRRefCm = ConfigStorage.get_setting('suspension_config.ini', 'Suspension', 'RRRef')

        self.LFMax = QLineEdit(str(self.data[0]))
        self.LFMaxCm = QLineEdit(str(self.vLFMaxCm))
        self.LFRef = QLineEdit(str(self.data[1]))
        self.LFRefCm = QLineEdit(str(self.vLFRefCm))

        self.RFMax = QLineEdit(str(self.data[2]))
        self.RFMaxCm = QLineEdit(str(self.vRFMaxCm))
        self.RFRef = QLineEdit(str(self.data[3]))
        self.RFRefCm = QLineEdit(str(self.vRFRefCm))

        self.LRMax = QLineEdit(str(self.data[4]))
        self.LRMaxCm = QLineEdit(str(self.vLRMaxCm))
        self.LRRef = QLineEdit(str(self.data[5]))
        self.LRRefCm = QLineEdit(str(self.vLRRefCm))

        self.RRMax = QLineEdit(str(self.data[6]))
        self.RRMaxCm = QLineEdit(str(self.vRRMaxCm))
        self.RRRef = QLineEdit(str(self.data[7]))
        self.RRRefCm = QLineEdit(str(self.vRRRefCm))

        self.btnAccept = QPushButton("Принять")
        self.btnAccept.clicked.connect(self.get_val)
        self.btnReject = QPushButton("Отменить")
        self.btnReject.clicked.connect(self.reject)

        gridLay = QGridLayout()
        gridLay.addWidget(lbl1, 0, 1, 1, 2, Qt.AlignCenter)
        gridLay.addWidget(lbl12, 0, 3, 1, 2, Qt.AlignCenter)
        gridLay.addWidget(lbl13, 0, 5, 1, 2, Qt.AlignCenter)
        gridLay.addWidget(lbl14, 0, 7, 1, 2, Qt.AlignCenter)
        gridLay.addWidget(lbl2, 1, 1, 1, 1, Qt.AlignCenter)
        gridLay.addWidget(lbl3, 1, 2, 1, 1, Qt.AlignCenter)
        gridLay.addWidget(lbl4, 1, 3, 1, 1, Qt.AlignCenter)
        gridLay.addWidget(lbl5, 1, 4, 1, 1, Qt.AlignCenter)
        gridLay.addWidget(lbl6, 1, 5, 1, 1, Qt.AlignCenter)
        gridLay.addWidget(lbl7, 1, 6, 1, 1, Qt.AlignCenter)
        gridLay.addWidget(lbl8, 1, 7, 1, 1, Qt.AlignCenter)
        gridLay.addWidget(lbl9, 1, 8, 1, 1, Qt.AlignCenter)
        gridLay.addWidget(lbl10, 2, 0, Qt.AlignCenter)
        gridLay.addWidget(self.LFMax, 2, 1, Qt.AlignCenter)
        gridLay.addWidget(self.LFMaxCm, 2, 2, Qt.AlignCenter)
        gridLay.addWidget(self.RFMax, 2, 3, Qt.AlignCenter)
        gridLay.addWidget(self.RFMaxCm, 2, 4, Qt.AlignCenter)
        gridLay.addWidget(self.LRMax, 2, 5, Qt.AlignCenter)
        gridLay.addWidget(self.LRMaxCm, 2, 6, Qt.AlignCenter)
        gridLay.addWidget(self.RRMax, 2, 7, Qt.AlignCenter)
        gridLay.addWidget(self.RRMaxCm, 2, 8, Qt.AlignCenter)
        gridLay.addWidget(lbl11, 3, 0, Qt.AlignCenter)
        gridLay.addWidget(self.LFRef, 3, 1, Qt.AlignCenter)
        gridLay.addWidget(self.LFRefCm, 3, 2, Qt.AlignCenter)
        gridLay.addWidget(self.RFRef, 3, 3, Qt.AlignCenter)
        gridLay.addWidget(self.RFRefCm, 3, 4, Qt.AlignCenter)
        gridLay.addWidget(self.LRRef, 3, 5, Qt.AlignCenter)
        gridLay.addWidget(self.LRRefCm, 3, 6, Qt.AlignCenter)
        gridLay.addWidget(self.RRRef, 3, 7, Qt.AlignCenter)
        gridLay.addWidget(self.RRRefCm, 3, 8, Qt.AlignCenter)
        gridLay.addWidget(self.btnAccept, 4, 3, 1, 2, Qt.AlignCenter)
        gridLay.addWidget(self.btnReject, 4, 5, 1, 2, Qt.AlignCenter)

        self.setLayout(gridLay)
        self.show()

    def get_val(self):
        self.returnVal = []
        try:

            self.vLFMaxCm = float(self.LFMaxCm.text())
            ConfigStorage.update_setting('suspension_config.ini', 'Suspension', 'LFMax', str(self.vLFMaxCm))
            self.vLFRefCm = float(self.LFRefCm.text())
            ConfigStorage.update_setting('suspension_config.ini', 'Suspension', 'LFRef', str(self.vLFRefCm))
            self.vRFMaxCm = float(self.RFMaxCm.text())
            ConfigStorage.update_setting('suspension_config.ini', 'Suspension', 'RFMax', str(self.vRFMaxCm))
            self.vRFRefCm = float(self.RFRefCm.text())
            ConfigStorage.update_setting('suspension_config.ini', 'Suspension', 'RFRef', str(self.vRFRefCm))

            self.vLRMaxCm = float(self.LRMaxCm.text())
            ConfigStorage.update_setting('suspension_config.ini', 'Suspension', 'LRMax', str(self.vLRMaxCm))
            self.vLRRefCm = float(self.LRRefCm.text())
            ConfigStorage.update_setting('suspension_config.ini', 'Suspension', 'LRRef', str(self.vLRRefCm))
            self.vRRMaxCm = float(self.RRMaxCm.text())
            ConfigStorage.update_setting('suspension_config.ini', 'Suspension', 'RRMax', str(self.vRRMaxCm))
            self.vRRRefCm = float(self.RRRefCm.text())
            ConfigStorage.update_setting('suspension_config.ini', 'Suspension', 'RRRef', str(self.vRRRefCm))

            self.returnVal.append(float(self.LFMaxCm.text()))
            self.returnVal.append(float(self.LFRefCm.text()))
            self.returnVal.append(float(self.RFMaxCm.text()))
            self.returnVal.append(float(self.RFRefCm.text()))

            self.returnVal.append(float(self.LRMaxCm.text()))
            self.returnVal.append(float(self.LRRefCm.text()))
            self.returnVal.append(float(self.RRMaxCm.text()))
            self.returnVal.append(float(self.RRRefCm.text()))
        except:
            QMessageBox.warning(self, "Внимание!", "Проверьте корректность ввода данных")
            return
        self.accept()

    def exec_(self):
        super(ConfigDialog, self).exec_()
        return self.returnVal

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ConfigDialog([])
    val = w.exec_()
    print(val)
    sys.exit(app.exec_())