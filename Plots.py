import sys

from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QApplication, QFileDialog

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import struct
import numpy as np


class Window(QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.figSensors = Figure()
        self.figAccel = Figure(figsize=(3, 3))

        self.canvasSensors = FigureCanvas(self.figSensors)
        self.canvasAccel = FigureCanvas(self.figAccel)

        self.toolbarSensors = NavigationToolbar(self.canvasSensors, self)

        self.axesSensors = self.figSensors.add_subplot(211)
        self.axesVelocity = self.figSensors.add_subplot(212)

        self.axesXYAccel = self.figAccel.add_subplot(211)
        self.axesZAccel = self.figAccel.add_subplot(212)

        self.btnOpenTxt = QPushButton("Open .txt file")
        self.btnOpenTxt.clicked.connect(self.onclick_open_txt)

        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.btnOpenTxt)
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.toolbarSensors)
        self.vbox.addWidget(self.canvasSensors)
        self.hbox.addLayout(self.vbox)
        self.hbox.addWidget(self.canvasAccel)

        self.setLayout(self.hbox)
        self.setMinimumSize(1000, 500)

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

        self.messageLength = 28

    def onclick_open_txt(self):
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

        rawData = rawData[rawData.index(127):]
        progressList = [i for i in range(1, len(rawData), int(len(rawData) / 100))]
        intData = []
        curProgressBar = 0
        for i in range(0, len(rawData), self.messageLength):
            tempStruct = []
            for j in range(1, self.messageLength - 1, 2):
                if j < 5:
                    tempStruct.append(struct.unpack(">H", rawData[i + j: i + j + 2])[0])
                else:
                    tempStruct.append(struct.unpack(">h", rawData[i + j : i + j + 2])[0])
            intData.append(tempStruct)

            if i > progressList[curProgressBar] and curProgressBar < (len(progressList) - 1):
                curProgressBar += 1
                print(curProgressBar, '%')
        for i in range(29):
            print(rawData[i], end=' ')
        print()
        del rawData
        print("Размер целочисленных данных:", len(intData), len(intData[0]), intData[0])
        for slice in intData:
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
        del intData

        min_timing = min(self.timings)
        for i in range(len(self.timings)):
            self.timings[i] = (self.timings[i] - min_timing) / 1000;
            self.accX[i] = self.accX[i] / 16384
            self.accY[i] = self.accY[i] / 16384
            self.accZ[i] = self.accZ[i] / 16384

        print("timings:", self.timings[:20])

        self.draw_plots(True, True, True, True)
        self.draw_accel_plots(0)

    def draw_plots(self, draw_1, draw_2, draw_3, draw_4):
        self.axesSensors.clear()
        self.axesSensors.grid()

        if draw_1:
            self.axesSensors.plot(self.timings, self.l_pos, 'r')
        if draw_2:
            self.axesSensors.plot(self.timings, self.l_press, 'g')
        if draw_3:
            self.axesSensors.plot(self.timings, self.r_pos, 'b')
        if draw_4:
            self.axesSensors.plot(self.timings, self.r_press, 'c')

        self.canvasSensors.draw()

        self.canvasSensors.mpl_connect('button_press_event', self.canvas_sensors_onclick)
        self.canvasSensors.mpl_connect('motion_notify_event', self.canvas_sensors_onmove)

    def draw_accel_plots(self, indx):
        self.axesXYAccel.clear()
        self.axesXYAccel.grid()
        self.axesXYAccel.set_xlim([-1, 1])
        self.axesXYAccel.set_ylim([-1, 1])
        self.axesXYAccel.axhline(color='k').set_ydata(0)
        self.axesXYAccel.axvline(color='k').set_xdata(0)
        self.axesXYAccel.plot(self.accX[indx], self.accY[indx], 'ro')

        self.axesZAccel.clear()
        self.axesZAccel.grid()
        self.axesZAccel.set_xlim([-2, 2])
        self.axesZAccel.set_ylim([-2, 2])
        self.axesZAccel.axhline(color='k').set_ydata(0)
        self.axesZAccel.axvline(color='k').set_xdata(0)
        self.axesZAccel.plot(0, self.accZ[indx], 'ro')
        self.canvasAccel.draw()

    def canvas_sensors_onmove(self, event):
        if event.button == 1:
            if event.xdata > 0:
                self.canvas_onclicked_left(event)

    def canvas_sensors_onclick(self, event):
        if event.button == 1:
            if event.xdata > 0:
                self.canvas_onclicked_left(event)

    def canvas_onclicked_left(self, event):
        indx = np.searchsorted(self.timings, [event.xdata])[0]
        self.draw_accel_plots(indx)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())