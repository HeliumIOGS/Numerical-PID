# -*- coding: utf-8 -*-
# @Author: tc/gd
# @Date:   2024-05-31 11:01:16
# @Last Modified by:   Your name
# @Last Modified time: 2024-06-17 15:23:50

import sys
sys.path.append('py-ws7')
from wlm import WavelengthMeter as WM
from log_config import logging
import threading, queue
import time
import numpy as np
import traceback
from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM, SOCK_STREAM, SHUT_RDWR
import struct

wvm = WM()
wl = wvm.GetFrequency(channel=1)

class PID():
    """Takes care of getting the frequency from the wavemeter, computing the error to the setpoint, and sending the
    required output voltage to the Arduino.
    """
    def __init__(self):
        self.set_freq = 276.76492   # In THz
        self.Kp = .1
        self.Ki = 1
        self.Kd = 0
        self.Npts = 10000
        self.freq = np.zeros(self.Npts)
        self.tps = np.zeros(self.Npts)
        self.error = np.zeros(self.Npts)
        self.start_tps = time.time()
        self.conv_factor = 1/3.3/1000/(51e-6)*2**12*4
        self.offset = 1024

    def update_PID(self):
        
        self.freq = np.roll(self.freq,1)
        self.tps = np.roll(self.tps,1)
        self.error = np.roll(self.error,1)

        measure = wvm.GetFrequency(channel=1)

        self.freq[0] = measure
        self.tps[0] = time.time() - self.start_tps
        self.error[0] = measure - self.set_freq
        
        self.DAC_output = self.conv_factor*(self.Kp*(self.error[0]) + self.Ki*np.trapz(self.error,self.tps) + self.Kd*(self.error[0] - self.error[1])/(self.tps[0]-self.tps[1])) + self.offset

        if self.DAC_output < 0:
            self.DAC_output = 0
            logging.warning('Low saturation')

        if self.DAC_output > 2047:
            self.DAC_output = 2047
            logging.warning('High saturation')
        
        self.DAC_output = int(np.nan_to_num(self.DAC_output))
        logging.info(f'error = {self.error[0]*1e6:.1f} MHz, DAC output = {self.DAC_output:.0f}')
        return self.DAC_output

class ArduinoCom(threading.Thread):

    def __init__(self, port):

        threading.Thread.__init__(self)
        self.IP_adr_lockbox = '10.117.53.46'
        self.arduino_port = port
        self.pid = PID()
        
    def dac_output(self, channel, voltage, output):
                        
        msg_channel = struct.pack('B',channel)
        msg_voltage = struct.pack('H',voltage)
        msg_output = struct.pack('?',output)

        # print(msg_voltage)
                
        self.socket_ard.sendall(msg_channel)
        self.socket_ard.sendall(msg_voltage)
        self.socket_ard.sendall(msg_output)

    def run(self):
        while True:
            value = self.pid.update_PID()
            
            self.socket_ard = socket(AF_INET, SOCK_STREAM) 
            self.socket_ard.connect((self.IP_adr_lockbox, self.arduino_port))
            self.dac_output(0, value, True)
            self.socket_ard.shutdown(SHUT_RDWR)
            self.socket_ard.close()
            time.sleep(1)

class SockThread(threading.Thread):
    """Opens a socket and send wavemeter freauency.
    """
    def __init__(self, PORT):
        threading.Thread.__init__(self)
        self.IP = '0.0.0.0'
        self.PORT = PORT
        self.BUFFER_SIZE = 1024
    
    def run(self):
        while True:
            with socket() as soc:
                soc.bind((self.IP, self.PORT))
                soc.listen(1)
                client, addr = soc.accept()
                input = client.recv(self.BUFFER_SIZE).decode()
                wl = wvm.GetFrequency(channel=1)
                client.send(str(wl).encode())

if __name__ == '__main__':
    try:
        threadGrafana = SockThread(6666)
        threadArduinoPID = ArduinoCom(7777)
        threads = [threadGrafana, threadArduinoPID]

        for thread in threads:
            thread.daemon = True
            thread.start()

        while True:
            # In order to catch the keyboard interrupt
            time.sleep(100)

    except KeyboardInterrupt:
        logging.critical('Keyboard Interrupt -- closing all threads...')
        traceback.print_exc(file=sys.stdout)