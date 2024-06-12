#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri June 14 18:14:07 2019

@author: jp
"""

import numpy as np
from scipy.signal import periodogram
from matplotlib import pyplot as plt

#%% INPUT

FILEPATH = {
        'Constant': {
                'data': '/Users/jp/Stage LKB/exp/wlm_pid/arduino_dac/'\
                    + '20190619/RefCurve_2019-06-19_0.Wfm.csv',
                'info': '/Users/jp/Stage LKB/exp/wlm_pid/arduino_dac/'\
                    + '20190619/RefCurve_2019-06-19_0.csv',
                },
        'Modulated': {
                'data': '/Users/jp/Stage LKB/exp/wlm_pid/arduino_dac/'\
                    + '20190614/RefCurve_2019-06-14_0.Wfm.csv',
                'info': '/Users/jp/Stage LKB/exp/wlm_pid/arduino_dac/'\
                    + '20190614/RefCurve_2019-06-14_0.csv'
                }
        }

#%% INITIALIZE FUNCTIONS

# Import data

def import_file(FILEPATH_DATA, FILEPATH_INFO):

    data = np.loadtxt(FILEPATH_DATA)

    info = np.loadtxt(FILEPATH_INFO, delimiter=':', dtype=str, usecols=(0,1))

    # Signal length = RecordLength, not SignalHardwareRecordLength:

    signal_length = int(info[np.where(info[:,0] == 'RecordLength'),1])

    data = data[:signal_length]

    return data, info

def create_time_axis(info, data):

    time_resolution = float(info[np.where(info[:,0] == 'Resolution'),1]) # seconds

    time_start = float(info[np.where(info[:,0] == 'XStart'),1]) # seconds

    time_stop = float(info[np.where(info[:,0] == 'XStop'),1]) # seconds

    time_axis = np.arange(time_start, time_stop-time_resolution/2,\
                          time_resolution)

    # Shift origin to zero

    time_axis = time_axis - time_start

    return time_resolution, time_axis

# Calculate PSD:

def psd(data, meas_series, time_resolution):

    fs = 1/time_resolution

    # For modulated, limit data to 1s of contiunous output:
    # if meas_series == 'Modulated':
    #
    #     data = data[int(np.where(time_axis==0.37)[0])+664:\
    #                 int(np.where(time_axis==0.37)[0]+1/time_resolution)]

    psd_x, psd_y = periodogram(data, fs)

    return psd_x, psd_y

# Plot data

def plot_data(time_axis, data, time_resolution, meas_series):

    plt.figure()
    plt.plot(time_axis, (data - np.mean(data)) * 1e3)
    plt.xlabel('Time [s]')
    plt.ylabel('Signal - mean [mV]')
    plt.title('Data: ' + str(meas_series))
    plt.show()

# Plot PSD

def plot_psd(psd_x, psd_y, meas_series):

    plt.figure()
    plt.plot(psd_x[1:2000], 1e6 * np.sqrt(psd_y[1:2000]))
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('PSD ' + r'$\left[\frac{\mu V}{\sqrt{Hz}}\right]$')
    plt.grid(True)
    plt.title('PSD: ' + str(meas_series))
    plt.show()

#%% EXECUTE

if __name__ == '__main__':

    for meas_series in FILEPATH.keys():

        data, info = import_file(FILEPATH[meas_series]['data'],\
                                 FILEPATH[meas_series]['info'])
        time_resolution, time_axis = create_time_axis(info, data)
        psd_x, psd_y = psd(data, meas_series, time_resolution)
        plot_data(time_axis, data, time_resolution, meas_series)
        plot_psd(psd_x, psd_y, meas_series)
