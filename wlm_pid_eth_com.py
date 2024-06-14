# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 14:55:20 2019

@author: JP Bureik

A PID-loop for the 679 nm laser using the High Finesse WS/7 wavemeter.
"""

"""
Revised on Thu Jun 13 17:10:20 2024

@author: G Dupuy

A PID-loop for the Raman 1083 nm laser using the High Finesse WS/6 wavemeter.
"""

from pylablib.aux_libs.devices.HighFinesse import WS
from datetime import datetime, timedelta
from time import sleep
from sys import stdout
import numpy as np
import socket
import struct
from matplotlib import pyplot as plt

#%% INPUT

# Measurement frequency of the WS/7:
MEAS_FREQ = 500 # in Hz, effectively limited to ca. 100 Hz by loop execution
# Desired PID-loop bandwidth:
PID_BW = 1 # in Hz
# Setpoint frequency:
FREQ_SCAN_START = 441.33238e12 # in Hz
FREQ_SCAN_STOP = 441.33224e12 # in Hz
# Conversion rate 1bit DAC -> df:
DF = 41.09e6 # Hz / bit

#%% INITIALIZE FUNCTIONS

def init_eth_com():
    
    IP_adr_lockbox = '10.118.16.29'    
        
    arduino_port = 7777
                    
    socket_ard = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    socket_ard.connect((IP_adr_lockbox, arduino_port))
    
    return socket_ard


def meas(LIB_PATH, MEAS_FREQ, PID_BW):
    """ Continously measure the laser frequency and return it as a list."""
    def print_freq_time(freq_wlm, meas_time):

        # Clear line so as to overwrite continously in IPython console
        last_lenght = 100 # Make this sufficiently large
        stdout.write('\b' * last_lenght)    # Go back
        stdout.write(' ' * last_lenght)     # Clear last dynamic output
        stdout.write('\b' * last_lenght)    # Reposition

        """ Display values in THz:
        Dividing by 1e12 is inconsistent (loses up to 4 digits)
        -> manipulate strings instead
        -> only loses 1 digit
        However, raw data from wlm loses 1 digit about 60% of the time
        -> in serial communication or w/ python loop??? """
        outText = str(freq_wlm)
        if len(outText) == 18:    # 100 THz + .123 -> 18 characters
            outText = outText[:3] + '.' + outText[3:outText.find('.')] +\
                outText[outText.find('.') + 1:] + ' THz    '
        elif len(outText) == 17:    # add additional space before unit
            outText = outText[:3] + '.' + outText[3:outText.find('.')] +\
                outText[outText.find('.') + 1:] + '  THz    '

        """ Display measurement time in seconds:
        Microseconds aren't padded w/ zeros (01.00500 s displays as 1.5 s)
        -> manipulate strings """
        if len(str(meas_time.microseconds)) == 6:
            time_str = str(meas_time.seconds) + '.' +\
                str(meas_time.microseconds)[:1] + ' s'
        else:
            time_str = str(meas_time.seconds) + '.' +\
                '0'*(6-len(str(meas_time.microseconds))) +\
                str(meas_time.microseconds)[:1] + ' s'

        # Combine into one line for easy carriage return
        outText = 'Frequency: ' + outText + 'Measurement time: ' + time_str
        stdout.write(outText)
        stdout.flush()

    freq_wlm = []

    with WS(lib_path=LIB_PATH, idx=2, hide_app=True) as wlm:

        wlm.start_measurement()
        start_time = datetime.now()
        meas_time = datetime.now() - start_time

        while meas_time < timedelta(seconds=1/PID_BW):

            freq_wlm.append(wlm.get_frequency())
            meas_time = datetime.now() - start_time

            # Print freauency and time:
            print_freq_time(freq_wlm[-1], meas_time)

            # Match loop speed to measurement frequency of wlm:
            sleep(1/MEAS_FREQ)

        wlm.stop_measurement()
        print('\nMean frequency: ' + str(np.mean(freq_wlm)/1e12) + ' THz')

    freq_wlm = np.asarray(freq_wlm)

    return freq_wlm, meas_time


# Filter out high frequency jumps that can occur at beginning or end of meas:


def filter_ends(freq_wlm):


    # Set filter limit:
    delta_freq_max = 5e7

    counter = []

    for k in range(1,len(freq_wlm)):

        if abs(freq_wlm[k-1] - freq_wlm[k]) > delta_freq_max:

            counter.append(k)

            # Filter beginning:
            if k < int(len(freq_wlm)/2):

                filtered = freq_wlm[k:]

            # Filter end
            else:

                filtered = freq_wlm[:k-1]

    # If no filter is necessary, return original array:
    if len(counter) == 0:

        filtered = freq_wlm

    else:

        print(str(len(counter)*2) + ' data points filtered out')

    return filtered


def create_error_signal(freq_wlm, FREQ_SCAN_START, FREQ_SCAN_STOP, DF):

    # Use mean value of ramp as setpoint:
    freq_sp = (FREQ_SCAN_START + FREQ_SCAN_STOP) / 2 # in Hz

    # Error on mean:
    err = np.mean(freq_wlm) - freq_sp
    
    # Calculate voltage:
    voltage = err/DF

    return voltage, freq_sp

def dac_output(socket_ard, channel, voltage, output):
                        
    msg_channel = struct.pack('B',channel)
    
    msg_voltage = struct.pack('H',voltage)
    
    msg_output = struct.pack('?',output)
            
    socket_ard.sendall(msg_channel)

    socket_ard.sendall(msg_voltage)
    
    socket_ard.sendall(msg_output)


def plot_wlm_signal(freq_wlm, meas_time, freq_sp):


    # Create time axis
    end_time = int(meas_time.seconds*1e6 + meas_time.microseconds) # in ms
    time_axis = np.linspace(0, end_time, num=len(freq_wlm))

    # Plot
    plt.figure()
    plt.plot(time_axis/1e6, freq_wlm/1e9, 'b', label = 'WLM')
    plt.plot(time_axis/1e6, freq_sp/1e9*np.ones(len(freq_wlm)), 'r',\
             label = 'Setpoint')
    plt.xlabel('Time [s]')
    plt.ylabel('Frequency [GHz]')
    plt.legend()
    plt.show()
    
def end_eth_com(socket_ard):
    
    socket_ard.close()

#%% EXECUTE

if __name__ == '__main__':
    
    socket_ard = init_eth_com()
    while True:
        freq_wlm, meas_time = meas(LIB_PATH, MEAS_FREQ, PID_BW)
        freq_wlm = filter_ends(freq_wlm)
        voltage, freq_sp = create_error_signal(freq_wlm, FREQ_SCAN_START,\
                                           FREQ_SCAN_STOP, DF)
        dac_output(socket_ard, channel=0, voltage, output=True)
        #plot_wlm_signal(freq_wlm, meas_time, freq_sp)
    end_eth_com(socket_ard)
