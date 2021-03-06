from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from SerialThread import ComMonitorThread
import serial.tools.list_ports_windows as comPortList
import queue
import io
import matplotlib.pyplot as plt
import pickle
from statistics import median
import time
import matplotlib.animation as animation


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
        self.btnOpenFile.clicked.connect(self.onclick_open_file)
        self.btnOpenTxtFile = QPushButton("Open TXT File")
        self.btnOpenTxtFile.clicked.connect(self.onclick_open_txt_file)

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
        self.hboxFile.addWidget(self.btnOpenTxtFile)

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
            self.monitor.start_rec()
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

    def onclick_open_txt_file(self):
        fname = QFileDialog.getOpenFileName(self, 'Open File', '', 'Data File (*.txt)')[0]
        try:
            f = open(fname, 'rb')
        except:
            print("error reading file")
            return
        raw_data = []
        byte = f.read(1)
        while byte != b'':
            raw_data.append(int.from_bytes(byte, byteorder='big'))
            byte = f.read(1)
        f.close()
        print("Len of file:", len(raw_data))

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
        print("hello")
        print(raw_data[:20])
        print(type(raw_data[0]))
        print("1st index:", raw_data.index(127))
        raw_data = raw_data[raw_data.index(127):]
        int_data = []
        print("raw_data[message_len - 1]:", raw_data[message_len - 1])
        while len(raw_data) > (message_len - 1) and raw_data[message_len - 1] == 10:
            temp_struct = []
            for i in range(message_len):
                temp_struct.append(raw_data.pop(0))
            print('.')
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
        plt.plot(self.timings, self.l_pos, self.timings, self.r_pos, self.timings, self.l_press, self.timings,
                 self.r_press)
        plt.show()


    def onclick_open_file(self):
        fname = QFileDialog.getOpenFileName(self, 'Open File', '', 'Data File (*.pickle)')[0]

        try:
            f = open(fname, 'rb')
        except:
            print("error reading file")
            return

        with f:
            data = pickle.load(f)

            if len(data) == 12:
                self.timings = data[0][:]
                self.accX = data[1][:]
                self.accY = data[2][:]
                self.accZ = data[3][:]
                self.temp = data[4][:]
                self.gyroX = data[5][:]
                self.gyroY = data[6][:]
                self.gyroZ = data[7][:]
                self.l_pos = data[8][:]
                self.l_press = data[9][:]
                self.r_pos = data[10][:]
                self.r_press = data[11][:]
                del data
                print("Size of loaded data:", len(self.timings))

        f.close()
        plt.figure(12)
        plt.plot(self.timings, self.l_pos)
        plt.show()

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

        print("processing data")
        raw_data = list(self.bytesIO.getbuffer())[:]
        self.bytesIO.truncate(0)
        self.bytesIO.seek(0)
        print("got buffer")
        '''
        print("1st index:", raw_data.index(127))
        raw_data = raw_data[raw_data.index(127):]
        int_data = []
        while len(raw_data) > (message_len - 1) and raw_data[message_len-1] is 10:
            temp_struct = []
            for i in range(message_len):
                temp_struct.append(raw_data.pop(0))
            temp_struct_2 = []
            for i in range(int(message_len / 2) - 1):
                temp_struct_2.append(temp_struct[i * 2 + 1] * 256 + temp_struct[i * 2 + 2])

            int_data.append(temp_struct_2)
        '''
        raw_data = raw_data[raw_data.index(127):]
        int_data = []
        progress_list = [i for i in range(1, len(raw_data), int(len(raw_data)/100))]
        cur_bar = 0
        print("Starting cycle")
        print("raw: ", raw_data[:56])
        for i in range(0, len(raw_data), message_len):
            temp_str = []
            for j in range(1, message_len-1, 2):
                temp_str.append(int.from_bytes(raw_data[i + j : i + j + 2], byteorder='big'))
            int_data.append(temp_str)
            #Процесс вычисления
            if i > progress_list[cur_bar] and cur_bar < (len(progress_list) - 1):
                cur_bar += 1
                print(cur_bar, '%')

        print("int data:", int_data[:2])

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
        del int_data
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