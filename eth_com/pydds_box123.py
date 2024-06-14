from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# "Atom Chips" Team
# Laboratoire Kastler Brossel, Paris

# Last version 30/11/2018

# This code allows you to send instructions to an Arduino Due for communicating with a AD9959/PCBZ DDS.

# Before using this code you have to load on the Arduino the code in the folder "Arduino_DDS".

# You can find some examples in the section "Make ramps" at the bottom of this page. Contact the authors for any question. Ask them for some examples.
# Original code form Francesco Ferri changed by Mathieu Bertrand 

import struct
import socket
import numpy as np

#----------------------------------------------------------------------------------
#ADDRESSES FOR THE ETHERNET COMMUNICATION WITH THE ARDUINO
#----------------------------------------------------------------------------------

arduino_IP_address_Box1 = '10.118.16.10';
arduino_IP_address_Box2 = '10.118.16.13';
arduino_IP_address_Box3 = '10.118.16.14';
arduino_IP_address_Box4 = '10.118.16.15';
arduino_port = 7777;

#----------------------------------------------------------------------------------
#FREQUENCY OF THE SYSTEM CLOCK
#----------------------------------------------------------------------------------
##Default system clock frequency 25MHz
input_clock = 25.
multiplier = 20

clock = input_clock*multiplier

# Conversion of binary multiplier into binary decimal for register 1 of AD9959
#2**23 sets VCO gain control to 1 and multiplier*2**18 fills the PLL divider ratio bits 22 to 18
reg1 = 2**23+multiplier*2**18

####Set a different value for the system clock
#def set_syst_clock(self, sys_clock):
#    clock = sys_clock
    
#----------------------------------------------------------------------------------
#CONVERSION FROM REAL VALUES TO TUNING WORDS FOR THE DDS (internal use)
#----------------------------------------------------------------------------------
def convert_freq(freq):
    return np.uint32( float(freq) / clock*0x100000000 ) # Rising Delta Word (RDW)                               # Python2->3, long->np.uint32
    
def convert_time(time):
    return np.uint8( time*clock/4 ) # Rising/Falling Sweep Ramp Rate Word (LSRR)                                
    
def convert_amplitude(fac): #fac is the multiplier for the amplitude. It must be fac<1
    f = 0
    b = 0
    for n in range (1,10):
        if (fac >= f + 1./(2.**n)):
            f +=  1./(2.**n)
            b += 2**(10-n)
    return np.uint32(b)


#----------------------------------------------------------------------------------
#HOW TO WRITE AN INSTRUCTION FOR THE DDS
#----------------------------------------------------------------------------------
###Different types of instructions: definition
type ={ ###Instructions for writing on some registers
        'channel' : (0x00 , 1),
        'set freq' : (0x04 , 4),
        'set freq ramp bottom': (0x04 , 4),
        'set freq ramp top' : (0x0A , 4),
        'set freq step up' :   (0x08 , 4),
        'set freq step down' : (0x09 , 4),
        'set time step' : (0x07 , 2),
        'load freq' : (0x04 , 4),
        'load freq ramp bottom': (0x04 , 4),
        'load freq ramp top' : (0x0A , 4),
        'load freq step up' : (0x08 , 4),
        'load freq step down' : (0x09 , 4),
        'load time step' : (0x07 , 2),
        'do Freq ramp' : (0x03, 3),
        'set amplitude' : (0x06, 3),
        'load amplitude' : (0x06, 3),  
        
#        'do Amp ramp' : (0x03, 3), # Added by Mathieu on 06/03/2019
#        'RU/RD' : (0x01, 3), # Added by Mathieu on 18/03/2019
#        'set amplitude ramp bottom' : (0x06 , 3), # Added by Mathieu on 06/03/2019
#        'set amplitude ramp top' : (0x0A , 4),  # Added by Mathieu on 06/03/2019
#        'set amplitude step up' :   (0x08 , 4), # Added by Mathieu on 06/03/2019
#        'set amplitude step down' : (0x09 , 4), # Added by Mathieu on 06/03/2019
#        'load amplitude ramp bottom' : (0x06 , 3), # Added by Mathieu on 06/03/2019
#        'load amplitude ramp top' : (0x0A , 4),  # Added by Mathieu on 06/03/2019
#        'load amplitude step up' :   (0x08 , 4), # Added by Mathieu on 06/03/2019
#        'load amplitude step down' : (0x09 , 4), # Added by Mathieu on 06/03/2019
        
        ###Instructions for controlling some pins
        'ioupdate' : (0 , 0),
        'reset' : (0 , 0),
        'profile pin P0' : (0 , 0),
        'profile pin P1' : (0 , 0),
        'profile pin P2' : (0 , 0),
        'profile pin P3' : (0 , 0),
        'free output' : (0 , 0),
        ###Instruction to set the single / cycling operation
        'repeat' : (0 , 0)
    }
        
###Size of the information to write on registers.
#The DDS registers have a specific size, which depends on the register itself. It is important to write  
#numbers with the correct size, otherwise you will have cuts. In the table below there`s a list of the sizes
#of the main numbers you have to specify for producing frequencies and ramps.
#--- `freq`: unsigned 32bit
#--- `ramp bottom`: unsigned 32bit
#--- `ramp top`: unsigned 32bit
#--- `freq step up`: unsigned 32bit
#--- `freq step down`: unsigned 32bit
#--- `time step`: unsigned 8bit !!!

###Write a generic instruction for the DDS

class Instruction:
    def __init__(self, name, value=0, wait=0, wait_for_trigger=False, convert=True ): 
#`name` is the name of the instruction (see definitions above).
#`value` is the mean content of the instrucion. See how it is used below.
#`wait` is the time (in ms) you want to wait before implementing the next operation (it corresponds to a delay in the arduino software). The precision is 1us.
#`instr` is the flag for distinguish the different ways of playing the instruction.
#`wait for trigger=True` connects the execution of the instruction to a trigger signal.
#`convert=True` enables the conversion of frequencie and time values to the tuning words for the DDS registers.
        self.type = type[name]
        self.name = name
        self.value = value
        self.wait = wait
        self.wait_for_trigger = wait_for_trigger       
        self.convert = convert
        self.val = 0
        self.instr = 0
#Make different operations depending on the type of the instruction:
    #If the instruction is "set a value", then issue an IOUpdate after have sent it; if the instruction is "load a value", don't send any IOUpdate.
        if ('set' in self.name):
            self.instr = 1
        elif ('load' in self.name):
            self.instr = 0
    #Instructions about frequency values
        if  ('freq' in self.name):
                #value is the frequency
                self.val = convert_freq(self.value) if self.convert else self.value
    #Instructions about time values
        elif ('time' in self.name):
                #value is the time step in microsec. It can be also a list of two values: 
                #value[0] is the falling time step, value[1] is the rising time step.
                #If you set a single value for the time step, it will be applied both to falling and to rising.
            if isinstance(self.value, list) :
                #self.value.__class__ == 'list':
                if self.convert: self.value[0] = convert_time(self.value[0])
                else: self.value[0]
                if self.convert: self.value[1] = convert_time(self.value[1])
                else: self.value[1]
                self.value[0] = np.uint16(self.value[0])
                self.value[1] = np.uint16(self.value[1])
                self.value[0] = self.value[0] << 8
                self.value[0] = self.value[0] | self.value[1]
                self.val = self.value[0]
            else:
                self.value = convert_time(self.value) if self.convert else self.value
                self.value += self.value << 8
                self.val = self.value
            #Choose the channel
        elif self.name=='channel':
            if(value == 0): self.value=16
            elif(value == 1): self.value=32
            elif(value == 2): self.value=64
            elif(value == 3): self.value=128
            self.val=self.value
            self.instr = 0 # no IOupdate
    #Instruction to enable the `Linear Sweep Mode` of the DDS in Frequency Sweep
        elif self.name == 'do Freq ramp':
            if (self.value):   self.val = 0x00806300 #value=True enables the linear sweep freq mode
            else: self.val = 0x00006300 #value=False enables the single frequency mode
            self.instr = 1 # IOupdate
#    #Instruction to enable the `Linear Sweep Mode` of the DDS in Amplitude Sweep # Added by Mathieu on 06/03/2019
#        elif self.name == 'do Amp ramp':
#            if (self.value):   self.val = 0x00406300 #value=True enables the linear sweep amplitude mode
#            else: self.val = 0x00006300 #value=False enables the single mode
#            self.instr = 1 # IOupdate
    #Instruction for modulating the amplitude
        elif ('amplitude' in self.name):
            #value is the multiplier for the amplitude of the output signal. The multiplier must be <1. The resolution is 1/(2**10).
            if ('ramp top' in self.name):
                self.val = convert_amplitude(value)*2**22
            else: 
                self.val = convert_amplitude(value)
                self.val += 4096 #enable the amplitude multiplier
#            self.val += 4096+2048+2**17 #enable the amplitude multiplier and the RU/RD
    #Instruction for sending an IOUpdate pulse 
        elif self.name == 'ioupdate':
            self.val = 0
            self.instr = 3
    #Instruction for sending an IOUpdate pulse 
        elif self.name == 'reset':
            self.val = 0
            self.instr = 4
    #Instruction for setting the state of the profile pin
        elif self.name == 'profile pin P0':
            self.instr = 2
            if (self.value): self.val = 1 #value=True set the profile pin to be high
            else: self.val = 0 #value=False set the profile pin to be low
    #Instruction for setting the state of the free output pin
        elif self.name == 'free output':
            self.instr = 5
            if (self.value): self.val = 1 #value=True set the free output pin to be high
            else: self.val = 0 #value=False set the profile pin to be low
    #Instruction for setting the cycling operation
        elif self.name == 'repeat':
            self.instr = 6
            if (self.value): self.val = 1 #value=True set the cycling operation: the instructions loaded on Arduino will be repeated continuously
            else: self.val = 0 #value=False: the instructions loaded on Arduino will be repeated only once
    #Instruction for setting the state of the profile pin P1
        elif self.name == 'profile pin P1':
            self.instr = 7
            if (self.value): self.val = 1 #value=True set the profile pin to be high
            else: self.val = 0 #value=False set the profile pin to be low
    #Instruction for setting the state of the profile pin P2
        elif self.name == 'profile pin P2':
            self.instr = 8
            if (self.value): self.val = 1 #value=True set the profile pin to be high
            else: self.val = 0 #value=False set the profile pin to be low
    #Instruction for setting the state of the profile pin P3
        elif self.name == 'profile pin P3':
            self.instr = 9
            if (self.value): self.val = 1 #value=True set the profile pin to be high
            else: self.val = 0 #value=False set the profile pin to be low
#    #Instruction for enabling/disabling the Ramp Up/Ramp Down (RU/RD) mode
#        elif self.name == 'RU/RD': 
#            self.instr = 0
#            if (self.value): self.val = reg1+0xC00 # Enable RU/RD pins
#            else: self.val = reg1 # Disable RU/RD pins
        else: 
            self.val = 0
        
            
#Build the `Instruction`. The properties correspond to the fields of the `Instruction` struct in the Arduino software. 
    #Flag for distinguish the different way of playing the instruction
    @property
    def instruction(self):
        return self.instr
    #If the instruction corresponds to writing on a register, `adress` is the register id.
    @property
    def address(self):
        return self.type[0]
    #Number of milliseconds you want to wait before playing the instruction. 
    @property
    def waitms(self):
        return int(self.wait)
    #Number of microseconds you want to wait before playing the instruction.
    @property
    def waitmics(self):
        return int( (self.wait-int(self.wait))*1000 )
    #Main information content of the instruction. It is not used for `ioupdate`.
    @property
    def data(self):
        return self.val
    #If the instruction corresponds to writing on a register, `number_of_bytes` is the size of the information that have to be stored on the register.
    @property
    def number_of_bytes(self):
        return self.type[1]
    #If wait_for_trigger=1 the instruction will be played after a trigger signal.
    @property
#    def wait_for_trigger(self):
    def wait_for_trigger_property(self): # Problem if it has the same name as input wait_for_trigger
        if (self.wait_for_trigger):
            return 1             
        else:
            return 0     
    
#----------------------------------------------------------------------------------
#HOW TO CONTROL THE DDS
#----------------------------------------------------------------------------------
class DDS:
    def __init__(self,box):
#        pass
        if box == 1:
            self.arduino_IP_address = arduino_IP_address_Box1
        elif box == 2:
            self.arduino_IP_address = arduino_IP_address_Box2
        elif box == 3:
            self.arduino_IP_address = arduino_IP_address_Box3
        elif box == 4:
            self.arduino_IP_address = arduino_IP_address_Box4
        else:
            print('PyDDS : Choose Box 1,2,3 or 4')
        self.box = box
        
###Send a message to the arduino through the Ethernet
    def send(self, msg):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((self.arduino_IP_address, arduino_port))
        s.sendall(msg)
##        l = s.sendall(msg)
##         m = 'Debug : '
##         while m:
##             print m
##             try:
##                 m = s.recv(1024)
##             except socket.timeout :
##                 m = ''
        try :
            m = int(s.recv(1024))
            if m != 0 :
                print('PyDDS : Error when writing to the DDS. Error code : ', m)
        except socket.timeout :
            print('PyDDS Box {} : Timeout'.format(str(self.box)))                        
        s.close()
        
###Send an I/O update pulse to the DDS. The DDS will upload the new values.
    def ioupdate(self):
        self.send( struct.pack('B',1) ) #flag for the switch in the Arduino loop
        
 ###Send a reset pulse to the DDS. It sets all the registers to the default.   
    def reset(self):
        self.send( struct.pack('B',2) ) #flag for the switch in the Arduino loop
        
###Set the profile pin P0 state for controlling the ramp in the ramp mode.
    def profilepin0_high(self):
        self.send( struct.pack('B',5) ) #flag for the switch in the Arduino loop
        
    def profilepin0_low(self):
        self.send( struct.pack('B',6) ) #flag for the switch in the Arduino loop
        
###Set the profile pin P1 state for controlling the ramp in the ramp mode.
    def profilepin1_high(self):
        self.send( struct.pack('B',11) ) #flag for the switch in the Arduino loop
        
    def profilepin1_low(self):
        self.send( struct.pack('B',12) ) #flag for the switch in the Arduino loop
        
###Set the profile pin P2 state for controlling the ramp in the ramp mode.
    def profilepin2_high(self):
        self.send( struct.pack('B',13) ) #flag for the switch in the Arduino loop
        
    def profilepin2_low(self):
        self.send( struct.pack('B',14) ) #flag for the switch in the Arduino loop
        
###Set the profile pin P3 state for controlling the ramp in the ramp mode.
    def profilepin3_high(self):
        self.send( struct.pack('B',15) ) #flag for the switch in the Arduino loop
        
    def profilepin3_low(self):
        self.send( struct.pack('B',16) ) #flag for the switch in the Arduino loop

###Send a pulse from the free output pin.    
    def free_output(self):
        self.send( struct.pack('B',7) ) #flag for the switch in the Arduino loop
        
###Interrupt the .    
    def interrupt(self):
        self.send( struct.pack('B',10) ) #flag for the switch in the Arduino loop

###Set the single / cycling operation
    def repeat(self, val = True):
        if val: self.send( struct.pack('B',8) ) #flag for the switch in the Arduino loop
        else : self.send( struct.pack('B',9) ) #flag for the switch in the Arduino loop
       
###Send an information to be written on to a register. 
    #`writeregister` accepts three different numbers for address, data and number of bytes; 
    def writeregister(self, address, data, number_of_bytes, ioupdate=False):
        msg = struct.pack( 'B', 0) #flag for the switch in the Arduino loop
        msg += struct.pack( '<BBBBL', address, number_of_bytes, 0, 0, data )
        #print 'Data :',data
        #print 'Msg {0} bytes : {1}'.format(len(msg), ','.join( [ str(ord(x)) for x in msg ] ) )
        self.send(msg)
        if ioupdate : self.ioupdate()

###Send a single `Instruction` to Arduino
    #`sendinstruction` accepts an `Instruction` type information (see above).
    def sendinstruction(self, i):
        self.writeregister(i.address, i.data, i.number_of_bytes, i.instruction)
        
###Load a list Instruction` on the Arduino software (without writing on the chip).
    def loadinstructions(self, instructions):
        msg = struct.pack( 'B', 3) #flag for the switch in the Arduino loop
        msg += struct.pack( '<L', len(instructions) )
        for i in instructions :
#            msg += struct.pack( '<BBBBLLL', i.instruction, i.address, i.number_of_bytes, i.wait_for_trigger, i.data, i.waitms, i.waitmics )
            msg += struct.pack( '<BBBBLLL', i.instruction, i.address, i.number_of_bytes, i.wait_for_trigger_property, i.data, i.waitms, i.waitmics )
        self.send(msg)
        
###Write the instructions you have loaded on the Arduino chip.
    def playinstructions(self):
        self.send( struct.pack('B',4) ) #flag for the switch in the Arduino loop
        
#------------------------------------------------------------------------------------------------------
#Select channel and mode of operation
#------------------------------------------------------------------------------------------------------
#See the Register Map of the DDS AD9959 for more information about the settings

    def initialize_channel(self, channel):
        self.reset()
        if channel==0: 
            self.writeregister( 0x00, 16, 1)
        if channel==1:
            self.writeregister( 0x00, 32, 1)
        if channel==2:
            self.writeregister( 0x00, 64, 1)
        if channel==3:
            self.writeregister( 0x00, 128, 1)
        self.writeregister( 0x01, reg1, 3)
#        self.writeregister( 0x01, 9699328, 3)
        self.ioupdate()
        #self.writeregister( 0x04, 429496730, 4 )
        #self.ioupdate()
#        self.setfrequency(94.)
#        self.setamplitude(0.)
        self.repeat(0)
        self.ioupdate()
        
        
    def select_channel(self, channel):
        #self.reset()
        if channel==0: 
            self.writeregister( 0x00, 16, 1)
        if channel==1:
            self.writeregister( 0x00, 32, 1)
        if channel==2:
            self.writeregister( 0x00, 64, 1)
        if channel==3:
            self.writeregister( 0x00, 128, 1)
        #self.repeat(0)
                        

    def start_ramp(self):
        #If you want to start a ramp with an Instruction that can be stored by Arduino, see the Instruction `ramp`.
        self.writeregister( 0x03, 0x00806300, 3)
        self.ioupdate()
        
#------------------------------------------------------------------------------------------------------
#Generate single frequencies
#------------------------------------------------------------------------------------------------------
#If you were using the DDS to generate a ramp, you have to do `initialize_channel(channel)` before setting the frequency and the amplitude 

    def setfrequency(self, freq, convert=True):
        self.sendinstruction( Instruction('set freq', freq, wait=0, convert=convert) )
        
    def setamplitude(self,amp):
        self.sendinstruction( Instruction('set amplitude', amp, wait=0, convert=True) )
        
#------------------------------------------------------------------------------------------------------
#Make ramps
#------------------------------------------------------------------------------------------------------
#See the details about the byte dimension of the values to write in section `How to write an instruction for the DDS` above.
    
###Make a linear ramp between two frequencies
#First you have to make a rising ramp, then you can play with the profile pin to go up and down
    def load_linear_ramp(self, channel, ramp_bottom, ramp_top, freq_step_up, freq_step_down, time_step_up, time_step_down):
        self.writeregister(0x00, 16, 1)
        self.writeregister( 0x01, reg1, 3)
#        self.writeregister(0x01, 9699328, 3)
        time_step = [time_step_down, time_step_up]
        instruction_list = []
#        instruction_list.append(Instruction('profile pin', value=True))
        instruction_list.append(Instruction('profile pin P0', value=True))
        instruction_list.append(Instruction('load freq ramp bottom', ramp_bottom))
        instruction_list.append(Instruction('load freq ramp top', ramp_top))
        instruction_list.append(Instruction('load time step', time_step))
        instruction_list.append(Instruction('load freq step up', freq_step_up))
        instruction_list.append(Instruction('load freq step down', freq_step_down))
        instruction_list.append(Instruction('do Freq ramp', value=True, wait=0))
#Then you have to do playinstructions() and eventually profilepin_low() and profilepin_high()
    
###Make a generic ramp between two frequencies.
#`ramp_bottom` is the value of the lowest frequency;
#`ramp_top` is the value of the highest frequency;
#`freq_step_up/down` are the list of the values of the frequency step;
#`time_step_up/down` are the list of the values of the time step;
#`wait_up/down` are the list of the values of the time you want to wait before updating again the slope (in ms).
    def load_generic_ramp(self, ramp_bottom, ramp_top, freq_step_up, freq_step_down, time_step_up, time_step_down, wait_up, wait_down, rest_time):
        self.writeregister(0x00, 16, 1)
        self.writeregister( 0x01, reg1, 3)
#        self.writeregister(0x01, 9699328, 3)
        N_up = len(freq_step_up)
        N_down = len(freq_step_down)
        instruction_list = []
#        instruction_list.append(Instruction('profile pin', value=True))
        instruction_list.append(Instruction('profile pin P0', value=True))
        instruction_list.append(Instruction('load freq ramp bottom', ramp_bottom))
        instruction_list.append(Instruction('load freq ramp top', ramp_top))
        instruction_list.append(Instruction('load time step', [time_step_down[0], time_step_up[0]]))
        instruction_list.append(Instruction('load freq step up', freq_step_up[0]))
        instruction_list.append(Instruction('load freq step down', freq_step_down[0]))
        instruction_list.append(Instruction('do Freq ramp', value=True, wait=0))
        for i in range(1, N_up):
            instruction_list.append(Instruction('load time step', [time_step_down[i], time_step_up[i]], wait_up[i]))
            instruction_list.append(Instruction('set freq step up', freq_step_up[i], wait=0))
        instruction_list.append(Instruction('profile pin', value=False, wait=rest_time))
        for i in range(0, N_down):
            instruction_list.append(Instruction('load time step', [time_step_down[i], time_step_up[i]], wait_down[i]))
            instruction_list.append(Instruction('set freq step down', freq_step_down[i], wait=0))
        self.loadinstructions(instruction_list)
#Then you have to do playinstructions()