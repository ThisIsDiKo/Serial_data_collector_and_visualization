import sys

from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QApplication, QFileDialog, QCheckBox, \
    QMainWindow, QLabel, QLineEdit, QSizePolicy, QMessageBox, QComboBox
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.QtCore import  QObject, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from SerialThreadV2 import ComMonitorThread
import serial.tools.list_ports_windows as comPortList
import queue
import io

from ConfigDialog import ConfigDialog

from statistics import mean

import struct
import numpy as np

class ComboBox(QComboBox):
    popUpSignal = pyqtSignal()

    def showPopup(self):
        self.popUpSignal.emit()
        super(ComboBox, self).showPopup()

class Window(QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        #------------------------------------------------------------
        self.comPort = ComboBox()
        self.update_port_list()
        self.comPort.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.comPort.popUpSignal.connect(self.update_port_list)

        self.comBaud = QComboBox()
        self.comBaud.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.comBaud.addItems(["115200", "9600"])

        self.btnConnect = QPushButton("Подключить")
        self.btnConnect.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnConnect.clicked.connect(self.onclick_connect)

        self.btnStart = QPushButton("Start")
        self.btnStart.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnStart.clicked.connect(self.onclick_start)

        self.btnStop = QPushButton("Stop")
        self.btnStop.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnStop.clicked.connect(self.onclick_stop)

        self.lblInd = QLabel("Not Connected")
        self.lblInd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lblInd.setStyleSheet("background-color: red")

        self.error_q = queue.Queue()
        self.monitor = None
        self.bytesIO = io.BytesIO()
        #------------------------------------------------------------
        self.figSensors = Figure(dpi=80)
        self.figAccel = Figure(dpi=50)

        self.canvasSensors = FigureCanvas(self.figSensors)
        self.canvasSensors.setMinimumSize(600, 200)
        self.canvasAccel = FigureCanvas(self.figAccel)
        self.canvasAccel.setFixedSize(200, 400)

        self.toolbarSensors = NavigationToolbar(self.canvasSensors, self)

        self.axesSensors = self.figSensors.add_subplot(111)
        self.axesSensors.set_title("Графики сигнала")
        self.axesSensors.set_ylabel("Сигнал (отн. ед)")
        self.axesSensors.set_xlabel("Время, с")

        self.axesXYAccel = self.figAccel.add_subplot(211)
        self.axesZAccel = self.figAccel.add_subplot(212)

        self.btnOpenTxt1 = QPushButton("Открыть первый файл")
        self.btnOpenTxt1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnOpenTxt1.clicked.connect(lambda: self.onclick_open_txt(0))

        self.btnOpenTxt2 = QPushButton("Открыть второй файл")
        self.btnOpenTxt2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnOpenTxt2.clicked.connect(lambda: self.onclick_open_txt(1))

        self.lblYMax = QLabel("Маскимальная высота")
        self.tYMax = QLineEdit("20")
        self.lblYMin = QLabel("Минимальная высота")
        self.tYmin = QLineEdit("0")
        self.lblOffset = QLabel("Смещение во времени")
        self.tOffset = QLineEdit("0")
        self.btnAccept = QPushButton("Применить")
        self.btnAccept.clicked.connect(self.onclick_accept)
        self.lblYMin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lblYMax.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.tYmin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.tYMax.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lblOffset.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.tOffset.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnAccept.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.lblChBox1 = QLabel("Первый файл")
        self.chbox1 = QCheckBox("LF (R)")
        self.chbox1.setChecked(True)
        self.chbox1.clicked.connect(self.chbox_draw_plots)
        self.chbox2 = QCheckBox("RF (G)")
        self.chbox2.clicked.connect(self.chbox_draw_plots)
        self.chbox3 = QCheckBox("LR (B)")
        self.chbox3.clicked.connect(self.chbox_draw_plots)
        self.chbox4 = QCheckBox("RR (C)")
        self.chbox4.clicked.connect(self.chbox_draw_plots)

        self.lblChBox2 = QLabel("Второй файл")
        self.chbox5 = QCheckBox("LF (M)")
        self.chbox5.clicked.connect(self.chbox_draw_plots)
        self.chbox6 = QCheckBox("RF (Y)")
        self.chbox6.clicked.connect(self.chbox_draw_plots)
        self.chbox7 = QCheckBox("LR (K)")
        self.chbox7.clicked.connect(self.chbox_draw_plots)
        self.chbox8 = QCheckBox("RR (W)")
        self.chbox8.clicked.connect(self.chbox_draw_plots)

        self.tableVel = QTableWidget(self)
        self.tableVel.setColumnCount(4)
        self.tableVel.setRowCount(2)
        self.tableVel.setHorizontalHeaderLabels(["LF", "RF", "LR", "RR"])
        self.tableVel.setVerticalHeaderLabels(["Файл 1 [м / с]", "Файл 2 [м / с]"])

        self.tableVel.setItem(0, 0, QTableWidgetItem("---------------"))
        self.tableVel.setItem(0, 1, QTableWidgetItem("---------------"))
        self.tableVel.setItem(0, 2, QTableWidgetItem("---------------"))
        self.tableVel.setItem(0, 3, QTableWidgetItem("---------------"))
        self.tableVel.setItem(1, 0, QTableWidgetItem("---------------"))
        self.tableVel.setItem(1, 1, QTableWidgetItem("---------------"))
        self.tableVel.setItem(1, 2, QTableWidgetItem("---------------"))
        self.tableVel.setItem(1, 3, QTableWidgetItem("---------------"))
        self.tableVel.setFixedSize(400, 75)

        self.tableVel.resizeColumnsToContents()
        self.tableVel.resizeRowsToContents()

        self.hbox = QHBoxLayout()
        self.vboxBtn = QVBoxLayout()

        self.hboxComPort = QHBoxLayout()
        self.hboxComPort.addWidget(self.comPort)
        self.hboxComPort.addWidget(self.comBaud)
        self.hboxComPort.addWidget(self.btnConnect)

        self.hboxControl = QHBoxLayout()
        self.hboxControl.addWidget(self.btnStart)
        self.hboxControl.addWidget(self.btnStop)

        self.vboxBtn.addLayout(self.hboxComPort)
        self.vboxBtn.addLayout(self.hboxControl)
        self.vboxBtn.addWidget(self.lblInd)
        self.vboxBtn.addWidget(self.btnOpenTxt1)
        self.vboxBtn.addWidget(self.btnOpenTxt2)
        self.vboxBtn.addWidget(self.lblYMax)
        self.vboxBtn.addWidget(self.tYMax)
        self.vboxBtn.addWidget(self.lblYMin)
        self.vboxBtn.addWidget(self.tYmin)
        self.vboxBtn.addWidget(self.lblOffset)
        self.vboxBtn.addWidget(self.tOffset)
        self.vboxBtn.addWidget(self.btnAccept)
        self.hbox.addLayout(self.vboxBtn)
        self.vbox = QVBoxLayout()
        self.hboxNav = QHBoxLayout()
        self.hboxNav.addWidget(self.toolbarSensors)
        self.hboxNav.addWidget(self.tableVel)
        self.vbox.addLayout(self.hboxNav)
        self.vbox.addWidget(self.canvasSensors)

        self.hboxChbox1 = QHBoxLayout()
        self.hboxChbox1.addWidget(self.lblChBox1)
        self.hboxChbox1.addWidget(self.chbox1)
        self.hboxChbox1.addWidget(self.chbox2)
        self.hboxChbox1.addWidget(self.chbox3)
        self.hboxChbox1.addWidget(self.chbox4)

        self.hboxChbox2 = QHBoxLayout()
        self.hboxChbox2.addWidget(self.lblChBox2)
        self.hboxChbox2.addWidget(self.chbox5)
        self.hboxChbox2.addWidget(self.chbox6)
        self.hboxChbox2.addWidget(self.chbox7)
        self.hboxChbox2.addWidget(self.chbox8)

        self.hboxChbox = QVBoxLayout()
        self.hboxChbox.addLayout(self.hboxChbox1)
        self.hboxChbox.addLayout(self.hboxChbox2)

        self.vbox.addLayout(self.hboxChbox)
        self.hbox.addLayout(self.vbox)
        self.hbox.addWidget(self.canvasAccel)

        self.setLayout(self.hbox)
        # self.setMinimumSize(1000, 700)

        self.data = [
            dict.fromkeys(['timings', 'accX', 'accY', 'accZ', 'LF', 'RF', 'LR', 'RR', 'vLF', 'vRF', 'vLR', 'vRR'], []),
            dict.fromkeys(['timings', 'accX', 'accY', 'accZ', 'LF', 'RF', 'LR', 'RR', 'vLF', 'vRF', 'vLR', 'vRR'], [])]

        self.messageLength = 28

    def onclick_open_txt(self, list_num):
        print("num of list", list_num)
        fname = QFileDialog.getOpenFileName(self, 'Open File', '', 'Data File (*.txt)')[0]
        try:
            f = open(fname, 'rb')
        except:
            print("error reading file")
            return
        rawData = bytearray()
        byte = f.read(1)
        while byte != b'':
            rawData.append(int.from_bytes(byte, byteorder='big'))
            byte = f.read(1)
        f.close()
        print("Len of file:", len(rawData))

        self.data[list_num] = dict(timings=[], accX=[], accY=[], accZ=[], LF=[], RF=[],
                                   LR=[], RR=[], vLF=[], vRF=[], vLR=[], vRR=[],
                                   LFMax='0', LFRef='0', RFMax='0', RFRef='0',
                                   LRMax='0', LRRef='0', RRMax='0', RRRef='0')

        rawData = rawData[rawData.index(127):]
        if rawData[17] == 10:
            print("Найдена калибровочная позиция")
            self.data[list_num]['LFMax'] = struct.unpack(">H", rawData[1:3])[0]
            self.data[list_num]['LFRef'] = struct.unpack(">H", rawData[3:5])[0]
            self.data[list_num]['RFMax'] = struct.unpack(">H", rawData[5:7])[0]
            self.data[list_num]['RFRef'] = struct.unpack(">H", rawData[7:9])[0]
            self.data[list_num]['LRMax'] = struct.unpack(">H", rawData[9:11])[0]
            self.data[list_num]['LRRef'] = struct.unpack(">H", rawData[11:13])[0]
            self.data[list_num]['RRMax'] = struct.unpack(">H", rawData[13:15])[0]
            self.data[list_num]['RRRef'] = struct.unpack(">H", rawData[15:17])[0]

            print("Калибровка:", self.data[list_num]['LFMax'],
                  self.data[list_num]['LFRef'],
                  self.data[list_num]['RFMax'],
                  self.data[list_num]['RFRef'],
                  self.data[list_num]['LRMax'],
                  self.data[list_num]['LRRef'],
                  self.data[list_num]['RRMax'],
                  self.data[list_num]['RRRef'])

        rawData = rawData[18:]
        progressList = [i for i in range(1, len(rawData), int(len(rawData) / 100))]
        intData = []
        curProgressBar = 0
        for i in range(0, len(rawData), self.messageLength):
            tempStruct = []
            for j in range(1, self.messageLength - 1, 2):
                if j < 5:
                    tempStruct.append(struct.unpack(">H", rawData[i + j:i + j + 2])[0])
                else:
                    tempStruct.append(struct.unpack(">h", rawData[i + j:i + j + 2])[0])
            intData.append(tempStruct)

            if i > progressList[curProgressBar] and curProgressBar < (len(progressList) - 1):
                curProgressBar += 1
                print(curProgressBar, '%')

        del rawData

        for slice in intData:
            self.data[list_num]['timings'].append(slice[0] * 65536 + slice[1])
            self.data[list_num]['accX'].append(slice[2])
            self.data[list_num]['accY'].append(slice[3])
            self.data[list_num]['accZ'].append(slice[4])
            self.data[list_num]['LF'].append(slice[9])
            self.data[list_num]['RF'].append(slice[10])
            self.data[list_num]['LR'].append(slice[11])
            self.data[list_num]['RR'].append(slice[12])

        del intData

        dotsInCm = ConfigDialog([self.data[list_num]['LFMax'],
                                 self.data[list_num]['LFRef'],
                                 self.data[list_num]['RFMax'],
                                 self.data[list_num]['RFRef'],
                                 self.data[list_num]['LRMax'],
                                 self.data[list_num]['LRRef'],
                                 self.data[list_num]['RRMax'],
                                 self.data[list_num]['RRRef']
                                 ]).exec_()
        print("Entered values:", dotsInCm)
        if len(dotsInCm) == 8:
            self.data[list_num]['LF'] = self.approx_data_to_cm(self.data[list_num]['LF'],
                                                               self.data[list_num]['LFMax'],
                                                               self.data[list_num]['LFRef'],
                                                               dotsInCm[0],
                                                               dotsInCm[1])
            self.data[list_num]['RF'] = self.approx_data_to_cm(self.data[list_num]['RF'],
                                                               self.data[list_num]['RFMax'],
                                                               self.data[list_num]['RFRef'],
                                                               dotsInCm[2],
                                                               dotsInCm[3])
            self.data[list_num]['LR'] = self.approx_data_to_cm(self.data[list_num]['LR'],
                                                               self.data[list_num]['LRMax'],
                                                               self.data[list_num]['LRRef'],
                                                               dotsInCm[4],
                                                               dotsInCm[5])
            self.data[list_num]['RR'] = self.approx_data_to_cm(self.data[list_num]['RR'],
                                                               self.data[list_num]['RRMax'],
                                                               self.data[list_num]['RRRef'],
                                                               dotsInCm[6],
                                                               dotsInCm[7])
            print("RR:", self.data[list_num]['RR'][20:50])
            min_val = min([min(self.data[list_num]['LF']), min(self.data[list_num]['RF']), min(self.data[list_num]['LR']), min(self.data[list_num]['RR'])])
            max_val = max(
                [max(self.data[list_num]['LF']), max(self.data[list_num]['RF']), max(self.data[list_num]['LR']),
                 max(self.data[list_num]['RR'])])
            self.tYMax.setText('{:.2f}'.format(max_val))
            self.tYmin.setText('{:.2f}'.format(min_val))

        # self.data[list_num]['LF'] = self.simple_filter(self.data[list_num]['LF'], 2)
        # self.data[list_num]['RF'] = self.simple_filter(self.data[list_num]['RF'], 2)
        # self.data[list_num]['LR'] = self.simple_filter(self.data[list_num]['LR'], 2)
        # self.data[list_num]['RR'] = self.simple_filter(self.data[list_num]['RR'], 2)

        min_timing = min(self.data[list_num]['timings'])
        print("Min timings is: ", min_timing, self.data[list_num]['timings'][:10])
        for i in range(len(self.data[list_num]['timings'])):
            self.data[list_num]['timings'][i] = (self.data[list_num]['timings'][i] - min_timing) / 1000
            self.data[list_num]['accX'][i] = self.data[list_num]['accX'][i] / 16384
            self.data[list_num]['accY'][i] = self.data[list_num]['accY'][i] / 16384
            self.data[list_num]['accZ'][i] = self.data[list_num]['accZ'][i] / 16384

        self.data[list_num]['vLF'] = self.calc_vel(self.data[list_num]['timings'], self.data[list_num]['LF'])
        self.data[list_num]['vRF'] = self.calc_vel(self.data[list_num]['timings'], self.data[list_num]['RF'])
        self.data[list_num]['vLR'] = self.calc_vel(self.data[list_num]['timings'], self.data[list_num]['LR'])
        self.data[list_num]['vRR'] = self.calc_vel(self.data[list_num]['timings'], self.data[list_num]['RR'])

        self.chbox_draw_plots()
        self.draw_accel_plots(0, 0)

    def chbox_draw_plots(self):
        draw1_LF = self.chbox1.isChecked()
        draw1_RF = self.chbox2.isChecked()
        draw1_LR = self.chbox3.isChecked()
        draw1_RR = self.chbox4.isChecked()

        draw2_LF = self.chbox5.isChecked()
        draw2_RF = self.chbox6.isChecked()
        draw2_LR = self.chbox7.isChecked()
        draw2_RR = self.chbox8.isChecked()

        if self.data[0]['timings'] or self.data[1]['timings']:
            self.draw_plots(draw1_LF, draw1_RF, draw1_LR, draw1_RR,
                            draw2_LF, draw2_RF, draw2_LR, draw2_RR)

    def draw_plots(self, draw1_LF, draw1_RF, draw1_LR, draw1_RR, draw2_LF, draw2_RF, draw2_LR, draw2_RR):
        self.axesSensors.clear()
        self.axesSensors.grid()
        self.axesSensors.set_title("Графики сигнала")
        self.axesSensors.set_ylabel("Позиция, см")
        self.axesSensors.set_xlabel("Время, с")
        ylim_max = self.tYMax.text()
        ylim_min = self.tYmin.text()
        try:
            self.axesSensors.set_ylim(float(ylim_min), float(ylim_max))
        except:
            print("Wrong number")
        # self.axesSensors.set_xlim([min(self.timings), max(self.timings)])

        if self.data[0]['timings']:
            if draw1_LF:
                self.axesSensors.plot(self.data[0]['timings'], self.data[0]['LF'], 'r')
            if draw1_RF:
                self.axesSensors.plot(self.data[0]['timings'], self.data[0]['RF'], 'g')
            if draw1_LR:
                self.axesSensors.plot(self.data[0]['timings'], self.data[0]['LR'], 'b')
            if draw1_RR:
                self.axesSensors.plot(self.data[0]['timings'], self.data[0]['RR'], 'c')

        if self.data[1]['timings']:
            if draw2_LF:
                self.axesSensors.plot(self.data[1]['timings'], self.data[1]['LF'], 'm')
            if draw2_RF:
                self.axesSensors.plot(self.data[1]['timings'], self.data[1]['RF'], 'y')
            if draw2_LR:
                self.axesSensors.plot(self.data[1]['timings'], self.data[1]['LR'], 'k')
            if draw2_RR:
                self.axesSensors.plot(self.data[1]['timings'], self.data[1]['RR'], 'k--')

        self.canvasSensors.draw()

        self.canvasSensors.mpl_connect('button_press_event', self.canvas_sensors_onclick)
        self.canvasSensors.mpl_connect('motion_notify_event', self.canvas_sensors_onmove)

    def draw_accel_plots(self, indx1, indx2):
        self.axesXYAccel.clear()
        self.axesXYAccel.grid()
        self.axesXYAccel.set_xlim([-2, 2])
        self.axesXYAccel.set_ylim([-2, 2])
        self.axesXYAccel.set_title("Ускорения (R-1, B-2)")
        self.axesXYAccel.axhline(color='k').set_ydata(0)
        self.axesXYAccel.axvline(color='k').set_xdata(0)
        if self.data[0]['timings']:
            self.axesXYAccel.plot(self.data[0]['accX'][indx1], self.data[0]['accY'][indx1], 'ro')
        if self.data[1]['timings']:
            self.axesXYAccel.plot(self.data[1]['accX'][indx2], self.data[1]['accY'][indx2], 'bo')

        self.axesZAccel.clear()
        self.axesZAccel.grid()
        self.axesZAccel.set_xlim([-2, 2])
        self.axesZAccel.set_ylim([-2, 2])
        self.axesZAccel.axhline(color='k').set_ydata(0)
        self.axesZAccel.axvline(color='k').set_xdata(0)
        if self.data[0]['timings']:
            self.axesZAccel.plot(0, self.data[0]['accZ'][indx1], 'ro')
        if self.data[1]['timings']:
            self.axesZAccel.plot(0, self.data[1]['accZ'][indx2], 'bo')

        self.canvasAccel.draw()

    def canvas_sensors_onmove(self, event):
        if event.button == 1:
            if event.xdata is not None:
                if event.xdata > 0:
                    print(event.xdata, event.ydata)
                    self.canvas_onclicked_left(event)

    def canvas_sensors_onclick(self, event):
        if event.button == 1:
            if event.xdata is not None:
                if event.xdata > 0:
                    print("clicked", event.xdata, event.ydata)
                    self.canvas_onclicked_left(event)

    def canvas_onclicked_left(self, event):
        try:
            if self.data[0]['timings']:
                indx1 = np.searchsorted(self.data[0]['timings'], [event.xdata])[0]
                print('indx1 =', indx1)
                self.tableVel.setItem(0, 0, QTableWidgetItem(str(self.data[0]['vLF'][indx1])))
                self.tableVel.setItem(0, 1, QTableWidgetItem(str(self.data[0]['vRF'][indx1])))
                self.tableVel.setItem(0, 2, QTableWidgetItem(str(self.data[0]['vLR'][indx1])))
                self.tableVel.setItem(0, 3, QTableWidgetItem(str(self.data[0]['vRR'][indx1])))
            else:
                indx1 = 0
            if self.data[1]['timings']:
                indx2 = np.searchsorted(self.data[1]['timings'], [event.xdata])[0]
                self.tableVel.setItem(1, 0, QTableWidgetItem(str(self.data[1]['vLF'][indx2])))
                self.tableVel.setItem(1, 1, QTableWidgetItem(str(self.data[1]['vRF'][indx2])))
                self.tableVel.setItem(1, 2, QTableWidgetItem(str(self.data[1]['vLR'][indx2])))
                self.tableVel.setItem(1, 3, QTableWidgetItem(str(self.data[1]['vRR'][indx2])))
            else:
                indx2 = 0
            self.draw_accel_plots(indx1, indx2)

        except:
            print("Out of index")

    def calc_vel(self, timings, pos):
        vel = [0]
        for i in range(1, len(timings)):
            vel.append((pos[i] - pos[i - 1]) / (timings[i] - timings[i - 1]) / 100)  # Тк метры
        return vel

    def onclick_accept(self):
        try:
            offset = float(self.tOffset.text())
            for i in range(len(self.data[1]['timings'])):
                self.data[1]['timings'][i] = self.data[1]['timings'][i] + offset
        except:
            QMessageBox.warning(self, "Внимание!", "Проверьте корректность ввода данных")
        self.chbox_draw_plots()

    # def approx_data_to_cm(self, data, DMax, DRef, DMaxCm, DRefCm):
    #     k = (DMaxCm - DRefCm) / (DMax - DRef)
    #     b = DRefCm - k * DRef
    #     print("k =", k, "b =", b)
    #
    #     returnData = []
    #     for val in data:
    #         returnData.append(val * k + b)
    #
    #     return returnData

    def approx_data_to_cm(self, data, DMax, DRef, DMaxCm, DRefCm):
        MaxCm = DMaxCm - DRefCm
        RefCm = 0

        k = (MaxCm - RefCm) / (DMax - DRef)
        b = RefCm - k * DRef
        print("k =", k, "b =", b)

        returnData = []
        for val in data:
            returnData.append(val * k + b)

        return returnData

    def simple_filter(self, data, window_size):
        return_list = data[:]
        for i in range(len(data) - window_size):
            return_list[i] = mean(data[0 + i:(window_size - 1) + i])
        return return_list

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
                self.lblInd.setText("Port Connected")
                return

            self.monitor = None
            self.btnStart.setEnabled(False)
            self.btnStop.setEnabled(False)
            self.lblInd.setText("Connection error")

    def onclick_start(self):
        if self.monitor:
            self.bytesIO.truncate(0)
            self.bytesIO.seek(0)
            self.lblInd.setStyleSheet("background-color: green")
            self.monitor.start_rec()

    def onclick_stop(self):
        if self.monitor:
            self.monitor.send_byte(b'b')
            self.lblInd.setStyleSheet("background-color: red")

    def update_port_list(self):
        l = list()
        self.comPort.clear()
        for p in comPortList.comports():
            l.append(p.device)
        self.comPort.addItems(l)

    def closeEvent(self, QCloseEvent):
        try:
            if self.monitor:
                print("finishing monitor")
                self.monitor.stop()
        except:
            print("exit error")

        print("exit by btn")
        QCloseEvent.accept()
if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())
