import pydds_box123
import frequency_plot as frplt
import Switch_Off as SwOff

dds1 = pydds_box123.DDS(1)
dds2 = pydds_box123.DDS(2)
dds3 = pydds_box123.DDS(3)

#------------------------------------------
###########################################
#Frequencies and amplitudes
###########################################

# Master AOM parameters
f_Simple = 340
faom_Simple = f_Simple/2
Amp_Simple = 900/1024

f_Double = 355
faom_Double = f_Double/2
Amp_Double = 600/1024

# MOT AOM parameters
f_BlueMOT = 342
faom_BlueMOT = f_BlueMOT/2
Amp_BlueMOT = 850/1024

# Zeeman slower AOM parameters
faom_Zee = 175
Amp_Zee = 850/1024

# Imaging pulse AOM parameters
f_Im = 380
faom_Im = f_Im/2
Amp_Im = 1000/1024

# 679nm repumper AOM parameters
faom_679nm = 92
Amp_679nm = 1000/1024

# 707nm repumper splitted for both AOM parameters
faom_707nm = 89
Amp_707nm = 400/1024

# 689nm Master AOM parameters
f_Red_Master = 110
faom_Red_Master = f_Red_Master/2
Amp_Red_Master = 300/1024

# 689nm Slave AOM parameters
f_Red_Slave = 220
faom_Red_Slave = f_Red_Slave/2
Amp_Red_Slave = 550/1024

#------------------------------------------
###########################################
#DDS Box 1 Channels
###########################################

#CH0 =  Master double, 3350-199, f = 177.5*2 = 355MHz, Amp = 600./1024
#CH1 = Master simple, 3350-125, f = 170*2 = 340MHz, Amp = 900./1024 
#CH2 = Slave MOT, 3350-125, f = 171*2 = 342MHz, Amp = 850./1024
#CH3 = Slave Zeeman Slower, 3350-125, f = 175MHz, Amp = 850./1024

#------------------------------------------

#Basic commands

#CH0 =  Master double, 3350-199, f = 177.5*2 = 355MHz, Amp = 600./1024
dds1.select_channel(0)
print('Box 1 CH0 selected')
dds1.setfrequency(faom_Double)
dds1.setamplitude(Amp_Double)

#CH1 = Master simple, 3350-125, f = 170*2 = 340MHz, Amp = 900./1024 
dds1.select_channel(1) 
print('Box 1 CH1 selected')
dds1.setfrequency(faom_Simple)
dds1.setamplitude(Amp_Simple)

# the arm to (MOT & Zeeman & Imaging) is at detuning = 2*170 - 4*177.5 = -370 MHz

#CH2 = Slave MOT, 3350-125, f = 171*2 = 342MHz, Amp = 850./1024
# MOT detuning is -370 + 342 = -28 MHz
dds1.select_channel(2) 
print('Box 1 CH2 selected')
dds1.setfrequency(faom_BlueMOT)
dds1.setamplitude(Amp_BlueMOT)

#CH3 = Slave Zeeman Slower, 3350-125, f = 175MHz, Amp = 850./1024
# Zeeman detuning is -370 - 175 = -545 MHz
dds1.select_channel(3) 
print('Box 1 CH3 selected')
dds1.setfrequency(faom_Zee)
dds1.setamplitude(Amp_Zee)

#------------------------------------------
###########################################
#DDS Box 2 Channels
###########################################
#CH0 = imaging 461nm, 3200-125, f = 380MHz, Amp = 1000./1024 

#------------------------------------------
#Basic commands

# the arm to (MOT & Zeeman & Imaging) is at detuning = 2*170 - 4*177.5 = -370 MHz

#CH0 = imaging 461nm, 3350-199, f = 380MHz, Amp = 1000./1024
dds2.select_channel(0) 
print('Box 2 CH1 selected')
dds2.setfrequency(faom_Im) #Imaging
dds2.setamplitude(Amp_Im)

#dds2.select_channel(2) 
#print('Box 2 CH2 selected')
#dds2.setfrequency()
#dds2.setamplitude(./1024)  
#                                    
#dds2.select_channel(3) 
#print('Box 2 CH3 selected')
#dds2.setfrequency()
#dds2.setamplitude(./1024)

#------------------------------------------
###########################################
#DDS Box 3 Channels
########################################### 
#CH0 = 707nm splitted for AOM spectro and AOM fiber at the same time, f = 89 MHz, Amp = 270./1024
#CH1 = 679nm, f = 92 MHz, Amp = 900./1024
#CH2 =  Red Slave 698nm, 3110-120, f = 220, Amp = 550./1024
#CH3 = Red Master 689nm, 3200-125, f = 55*2 = 110MHz, Amp = 700./1024 

#------------------------------------------
#Basic commands

#CH0 = 707nm splitted for AOM spectro and AOM fiber at the same time, f = 89 MHz, Amp = 270./1024
dds3.initialize_channel(0)
dds3.select_channel(0)
print('Box 3 CH0 selected')
dds3.setfrequency(faom_707nm)
dds3.setamplitude(Amp_707nm)

#CH1 = 679nm, f = 92 MHz, Amp = 900./1024
dds3.select_channel(1) 
print('Box 3 CH1 selected')
dds3.setfrequency(faom_679nm) 
dds3.setamplitude(Amp_679nm) 

#CH2 =  Red Slave 698nm, 3110-120, f = 220, Amp = 500./1024
dds3.select_channel(2) 
print('Box 3 CH2 selected')
dds3.setfrequency(faom_Red_Slave)
dds3.setamplitude(Amp_Red_Slave)   

#CH3 = Master 689nm, 3110-120, f = 55*2 = 110MHz, Amp = 300./1024     
dds3.select_channel(3) 
print('Box 3 CH3 selected')
dds3.setfrequency(faom_Red_Master) 
dds3.setamplitude(Amp_Red_Master)

#------------------------------------------
###########################################
##Switch off

#SwOff.switch_off()

#------------------------------------------
###########################################


#------------------------------------------
###########################################
#Frequency plot
###########################################

frplt.plot_freqs(faom_Simple,faom_Double,faom_BlueMOT,faom_Zee,faom_Im)