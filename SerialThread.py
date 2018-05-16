import queue
import threading
import serial
import serial.tools.list_ports_windows
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# import sys
# from io import BytesIO


class ComMonitorThread(threading.Thread):
    def __init__(self,
                 bytesIO,  # Объект типа Bytes IO
                 error_q,
                 port_num,
                 port_baud,
                 port_stopbits=serial.STOPBITS_ONE,
                 port_parity=serial.PARITY_NONE,
                 port_timeout=0.01):
        print("init")
        threading.Thread.__init__(self)
        print("1")
        self.serial_port = None
        self.serial_arg = dict(port=port_num,
                               baudrate=port_baud,
                               stopbits=port_stopbits,
                               parity=port_parity,
                               timeout=port_timeout)
        print("2")
        self.bytesIO = bytesIO
        self.error_q = error_q

        self.running = True

        self.rec_packet_size = 28;
        self.serialData = [[], [], [], []]

        self.plotTimer = 0
        self.previousTimer = 0
        self.data = [deque(maxlen=200), deque(maxlen=200),
                     deque(maxlen=200), deque(maxlen=200)]
        for i in range(4):
            for j in range(200):
                self.data[i].append(0)

    def open_port(self):
        self.running = True
        try:
            if self.serial_port:
                self.serial_port.close()

            print("trying to connect")
            self.serial_port = serial.Serial(**self.serial_arg)

            print("got object: ", self.serial_port)
            self.error_q.put("connected")
        except:
            print("error")
            self.error_q.put("port error")
            return

    def run(self):
        print("Starting listening to port")
        while self.running:
            if self.serial_port:
                if self.serial_port.inWaiting() > 27:
                    new_data = self.serial_port.read(28)
                    self.bytesIO.write(new_data)
                    if len(new_data) == 28:
                        l_pos = int.from_bytes(new_data[19:21], byteorder='big')
                        l_press = int.from_bytes(new_data[21:23], byteorder='big')
                        r_pos = int.from_bytes(new_data[23:25], byteorder='big')
                        r_press = int.from_bytes(new_data[25:27], byteorder='big')
                        self.serialData[0].append(l_pos)
                        self.serialData[1].append(l_press)
                        self.serialData[2].append(r_pos)
                        self.serialData[3].append(r_press)
        print("Stop listening port")

    """
    отправляем b'a' для запуска записи
    отправляем b'b' для остановки записи
    """

    def send_byte(self, s):
        print("Sending byte:", s)
        if self.serial_port:
            self.serial_port.write(s)

    def stop(self):
        self.running = False
        if self.serial_port:
            self.serial_port.close()
            print('Disconnected...')

    def getSerialData(self, frame, lines, lineValueText, lineLabel, timeText):
        currentTimer = time.clock()
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)  # the first reading will be erroneous
        self.previousTimer = currentTimer
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')

        for i in range(4):
            self.data[i].extend(self.serialData[i])  # we get the latest data point and append it to our array
            self.serialData[i].clear()
            lines[i].set_data(range(200), list(self.data[i]))
            lineValueText[i].set_text('[' + lineLabel[i] + '] = ' + str(self.data[i][-1]))

    def start_rec(self):
        self.send_byte(b'a')
        time.sleep(1.0)
        numPlots = 4
        pltInterval = 100  # Period at which the plot animation updates [ms]
        xmin = 0
        xmax = 200
        ymin = 0
        ymax = 1023
        # fig = plt.figure(figsize=(10, 8))
        fig = plt.figure(111)
        ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
        ax.set_title('Data from suspension')
        ax.set_xlabel("Time")
        ax.set_ylabel("ADC output")

        lineLabel = ['X', 'Y', 'Z', 'J']
        style = ['r-', 'g-', 'b-', 'c-']  # linestyles for the different plots
        timeText = ax.text(0.70, 0.95, '', transform=ax.transAxes)
        lines = []
        lineValueText = []
        for i in range(numPlots):
            lines.append(ax.plot([], [], style[i], label=lineLabel[i])[0])
            lineValueText.append(ax.text(0.70, 0.90 - i * 0.05, '', transform=ax.transAxes))
        anim = animation.FuncAnimation(fig, self.getSerialData,
                                       fargs=(lines, lineValueText, lineLabel, timeText),
                                       interval=pltInterval)  # fargs has to be a tuple

        plt.legend(loc="upper left")
        plt.show()