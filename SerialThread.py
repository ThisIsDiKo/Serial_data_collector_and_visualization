# import queue
import threading
import serial
import serial.tools.list_ports_windows


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
        threading.Thread.__init__(self)

        self.serial_port = None
        self.serial_arg = dict(port=port_num,
                               baudrate=port_baud,
                               stopbits=port_stopbits,
                               parity=port_parity,
                               timeout=port_timeout)
        self.bytesIO = bytesIO
        self.error_q = error_q

        self.running = True

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
                new_data = self.serial_port.read(1)
                new_data += self.serial_port.read(self.serial_port.inWaiting())
                if len(new_data) > 0:
                    self.bytesIO.write(new_data)
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
