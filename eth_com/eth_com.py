 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 08 10:22:13 2019

@author: jp

Module for ethernet communication from PC to Arduino via Ethernet Shield

"""


def dac_output(channel, voltage, output):

    import socket
    import struct
    
    IP_adr_lockbox = '10.118.16.29'    
        
    arduino_port = 7777
        
    msg_channel = struct.pack('B',channel)
    
    msg_voltage = struct.pack('H',voltage)
    
    msg_output = struct.pack('?',output)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    s.connect((IP_adr_lockbox, arduino_port))
    
    s.sendall(msg_channel)

    s.sendall(msg_voltage)
    
    s.sendall(msg_output)

if __name__ == '__main__':
    
    dac_output(1, 4095, output=False)