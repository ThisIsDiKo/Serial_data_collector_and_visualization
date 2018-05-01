from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from SerialThread import ComMonitorThread
import serial.tools.list_ports_windows as comPortList
import queue
import io
import matplotlib.pyplot as plt
import pickle
from statistics import median


class ComboBox(QComboBox):
    popUpSignal = pyqtSignal()

    def showPopup(self):
        self.popUpSignal.emit()
        super(ComboBox, self).showPopup()

class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.comPort = ComboBox()
        self.update_port_list()
        self.comPort.popUpSignal.connect(self.update_port_list)

        self.comBaud = QComboBox()
        self.comBaud.addItems(["9600", "19200"])

        self.btnConnect = QPushButton("Connect")
        self.btnConnect.clicked.connect(self.onclick_connect)

        self.lblFile = QLabel("FileName: ")

        self.lblFileName = QLabel()

        self.btnOpenFile = QPushButton("Open File")
        #self.btnOpenFile.clicked.connect(self.onclick_open_file)

        self.btnStart = QPushButton("Start")
        self.btnStart.clicked.connect(self.onclick_start)

        self.btnStop = QPushButton("Stop")
        self.btnStop.clicked.connect(self.onclick_stop)

        self.lblInd = QLabel("Receiving data")
        self.lblInd.setStyleSheet("background-color: red")

        self.chboxUseBoth = QCheckBox("Use both sens")
        self.btnPlotGraph = QPushButton("Plot Graphs")
        #self.btnPlotGraph.clicked.connect(self.onclick_plot_graph)

        self.lblFilterSize = QLabel("Filter buffer")
        self.txtFilterSize = QLineEdit("5")
        self.chboxFilter = QCheckBox("Floating")
        self.btnFilter = QPushButton("Use Filter and Plot Graph")
        #self.btnFilter.clicked.connect(self.onclick_filter)

        self.btnSave = QPushButton("Save to File")
        self.btnSave.clicked.connect(self.onclick_save_to_file)

        self.lblStatus = QLabel()

        self.hboxComPort = QHBoxLayout()
        self.hboxComPort.addWidget(self.comPort)
        self.hboxComPort.addWidget(self.comBaud)
        self.hboxComPort.addWidget(self.btnConnect)

        self.hboxFile = QHBoxLayout()
        self.hboxFile.addWidget(self.lblFile)
        self.hboxFile.addWidget(self.lblFileName)
        self.hboxFile.addWidget(self.btnOpenFile)

        self.hboxControl = QHBoxLayout()
        self.hboxControl.addWidget(self.btnStart)
        self.hboxControl.addWidget(self.btnStop)

        self.hboxPlot = QHBoxLayout()
        self.hboxPlot.addWidget(self.chboxUseBoth)
        self.hboxPlot.addWidget(self.btnPlotGraph)

        self.hboxFilter = QHBoxLayout()
        self.hboxFilter.addWidget(self.lblFilterSize)
        self.hboxFilter.addWidget(self.txtFilterSize)
        #self.hboxFilter.addWidget(self.chboxFilter)
        self.hboxFilter.addWidget(self.btnFilter)


        self.vboxMain = QVBoxLayout()
        self.vboxMain.addLayout(self.hboxComPort)
        self.vboxMain.addLayout(self.hboxFile)
        self.vboxMain.addLayout(self.hboxControl)
        self.vboxMain.addWidget(self.lblInd)
        self.vboxMain.addLayout(self.hboxPlot)
        self.vboxMain.addLayout(self.hboxFilter)
        self.vboxMain.addWidget(self.btnSave)
        self.vboxMain.addWidget(self.lblStatus)

        self.setLayout(self.vboxMain)
        self.resize(400, 200)

        self.error_q = queue.Queue()

        self.monitor = None
        self.fileToWrite = None

        self.bytesIO = io.BytesIO()

        self.figure_num = 1

        self.timings = []
        self.accX = []
        self.accY = []
        self.accZ = []
        self.temp = []
        self.gyroX = []
        self.gyroY = []
        self.gyroZ = []
        self.l_pos = []
        self.r_pos = []
        self.l_press = []
        self.r_press = []

    def update_port_list(self):
        l = list()
        self.comPort.clear()
        for p in comPortList.comports():
            l.append(p.device)
        self.comPort.addItems(l)

    def onclick_connect(self):
        portName = self.comPort.currentText()
        portBaud = int(self.comBaud.currentText())
        print("creating com port")
        if self.monitor is None:
            print("creating com port")
            self.monitor = ComMonitorThread(self.bytesIO,
                                            self.error_q,
                                            port_num=portName,
                                            port_baud=portBaud)
            print("monitor created")
            self.monitor.open_port()
            print("monitor started")
            com_error = self.error_q.get()[0]
            print("got status")
            self.monitor.start()
            if com_error is not "port error":
                self.btnStart.setEnabled(True)
                self.btnStop.setEnabled(True)
                self.lblStatus.setText("Port Connected")
                return

            self.monitor = None
            self.btnStart.setEnabled(False)
            self.btnStop.setEnabled(False)
            self.lblStatus.setText("Connection error")

    def closeEvent(self, QCloseEvent):
        try:
            if self.monitor:
                print("finishing monitor")
                self.monitor.stop()
            if self.fileToWrite:
                print("finishing file")
                self.fileToWrite.close()
        except:
            print("exit error")

        print("exit by btn")
        QCloseEvent.accept()

    def onclick_start(self):
        if self.monitor:
            self.bytesIO.truncate(0)
            self.bytesIO.seek(0)
            self.monitor.send_byte(b'a')
            self.lblInd.setStyleSheet("background-color: green")

    def onclick_stop(self):
        if self.monitor:
            self.monitor.send_byte(b'b')
            self.lblInd.setStyleSheet("background-color: red")
            self.process_data()

    def onclick_save_to_file(self):
        text, ok = QInputDialog.getText(self, 'File Name', 'Enter file name')
        if ok and self.timings:
            with open(str(text) + ".pickle", "wb") as f:
                pickle.dump((self.timings, self.accX, self.accY, self.accZ,
                             self.temp, self.gyroX, self.gyroY, self.gyroZ,
                             self.l_pos, self.l_press, self.r_pos, self.r_press), f)
                print("File saved")

    def process_data(self):
        message_len = 28
        self.timings = []
        self.accX = []
        self.accY = []
        self.accZ = []
        self.temp = []
        self.gyroX = []
        self.gyroY = []
        self.gyroZ = []
        self.l_pos = []
        self.r_pos = []
        self.l_press = []
        self.r_press = []

        raw_data = list(self.bytesIO.getbuffer())[:]
        print("1st index:", raw_data.index(127))
        raw_data = raw_data[raw_data.index(127):]
        int_data = []
        while len(raw_data) > (message_len - 1) and raw_data[message_len-1] is 10:
            temp_struct = []
            for i in range(message_len):
                print(raw_data[0], end=' ')
                temp_struct.append(raw_data.pop(0))
            print()
            temp_struct_2 = []
            for i in range(int(message_len / 2) - 1):
                temp_struct_2.append(temp_struct[i * 2 + 1] * 256 + temp_struct[i * 2 + 2])

            int_data.append(temp_struct_2)

        print("Размер целочисленных данных:", len(int_data), len(int_data[0]))

        for slice in int_data:
            self.timings.append(slice[0] * 65536 + slice[1])
            self.accX.append(slice[2])
            self.accY.append(slice[3])
            self.accZ.append(slice[4])
            self.temp.append(slice[5])
            self.gyroX.append(slice[6])
            self.gyroY.append(slice[7])
            self.gyroZ.append(slice[8])
            self.l_pos.append(slice[9])
            self.r_pos.append(slice[11])
            self.l_press.append(slice[10])
            self.r_press.append(slice[12])

        print("timings:", self.timings[:20])

        plt.figure(1)
        plt.plot(self.timings, self.l_pos, self.timings, self.r_pos, self.timings, self.l_press, self.timings, self.r_press)
        plt.show()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("Arduino 28 bytes")
    window.show()
    sys.exit(app.exec_())