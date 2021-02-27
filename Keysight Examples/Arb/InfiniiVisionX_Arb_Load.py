# -*- coding: utf-8 -*-

## DO NOT CHANGE ABOVE LINE

# Python for Test and Measurement
#
# Requires VISA installed on Control PC
# 'keysight.com/find/iosuite'
# Requires PyVISA to use VISA in Python
# 'http://pyvisa.sourceforge.net/pyvisa/'

## Keysight IO Libraries 17.1.19xxx
## Anaconda Python 2.7.7 64 bit
## pyvisa 1.8
## Windows 7 Enterprise, 64 bit

##"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
## Copyright © 2015 Keysight Technologies Inc. All rights reserved.
##
## You have a royalty-free right to use, modify, reproduce and distribute this
## example files (and/or any modified version) in any way you find useful, provided
## that you agree that Keysight has no warranty, obligations or liability for any
## Sample Application Files.
##
##"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

##############################################################################################################################################################################
##############################################################################################################################################################################
## Import Python modules
##############################################################################################################################################################################
##############################################################################################################################################################################

## Import python modules - Not all of these are used in this program; provided for reference
import sys
import visa
import time
import struct
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

##############################################################################################################################################################################
##############################################################################################################################################################################
## Intro, general comments, and instructions
##############################################################################################################################################################################
##############################################################################################################################################################################

## This example program is provided as is and without support. Keysight is not responsible for modifications.
## Standard Python style is not followed to allow for easier reading by non-Python programmers.

## Keysight IO Libraries 17.1.19xxx was used.
## Anaconda Python 2.7.7 64 bit is used
## pyvisa 1.8 is used
## Windows 7 Enterprise, 64 bit (has implications for time.clock if ported to unix type machine, use timw.time instead)

## HiSlip and Socket connections not supported

## This example shows several method for getting data into the arbitrary waveform generators on Keysight InfiniiVision-X scopes where applicable.  This requires the wavegen license on the oscilloscopes.

## Stick the included csv file, sample_arb_data.csv, in this directory C:\Users\Public\
## Change oscilloscope VISA address
## Run

##############################################################################################################################################################################
##############################################################################################################################################################################
## DEFINE CONSTANTS
##############################################################################################################################################################################
##############################################################################################################################################################################

## Initialization constants
VISA_ADDRESS = "TCPIP0::A-MX4154A-40345::inst0::INSTR" # Get this from Keysight IO Libraries Connection Expert #Note: sockets are not supported in this revision of the script, and pyVisa 1.6.3 does not support HiSlip
GLOBAL_TOUT =  10000 # IO time out in milliseconds

##############################################################################################################################################################################

##############################################################################################################################################################################
##############################################################################################################################################################################
## Connect and initialize scope
##############################################################################################################################################################################
##############################################################################################################################################################################

## Define VISA Resource Manager & Install directory
## This directory will need to be changed if VISA was installed somewhere else.
rm = visa.ResourceManager('C:\\Windows\\System32\\visa32.dll') # this uses pyvisa
## This is more or less ok too: rm = visa.ResourceManager('C:\\Program Files (x86)\\IVI Foundation\\VISA\\WinNT\\agvisa\\agbin\\visa32.dll')
## In fact, it is generally not needed to call it explicitly
## rm = visa.ResourceManager()

## Open Connection
## Define & open the scope by the VISA address ; # This uses PyVisa
try:
    KsInfiniiVisionX = rm.open_resource(SCOPE_VISA_ADDRESS)
except Exception:
    print "Unable to connect to oscilloscope at " + str(SCOPE_VISA_ADDRESS) + ". Aborting script.\n"
    sys.exit()

## Set Global Timeout
## This can be used wherever, but local timeouts are used for Arming, Triggering, and Finishing the acquisition... Thus it mostly handles IO timeouts
KsInfiniiVisionX.timeout = GLOBAL_TOUT

## Clear the instrument bus
KsInfiniiVisionX.clear()

## reset the scope
KsInfiniiVisionX.write("*RST")

## always stop scope when making changes
KsInfiniiVisionX.query("*CLS;:STOP;*OPC?")

##############################################################################################################################################################################
##############################################################################################################################################################################
## Main Script
##############################################################################################################################################################################
##############################################################################################################################################################################

## scale analog ch1
KsInfiniiVisionX.write(":CHANnel1:SCALe 0.2")

## somwe wavegen initial stuff
KsInfiniiVisionX.write(":WGEN:RST") # since it is reset, it will default to a sine wave
KsInfiniiVisionX.write(":WGEN:OUTPut ON")
KsInfiniiVisionX.write(":WGEN:ARBitrary:INTerpolate 0")
KsInfiniiVisionX.write(":WGEN:ARBitrary:BYTeorder LSBF")
KsInfiniiVisionX.write(":WGEN:VOLTage 1")

## force an acquisition
KsInfiniiVisionX.query(":SINGle;:TRIGger:FORCe;*OPC?") ## this is a terrible way to do this, but fine for this example
## Should see a sinewave (from wgen default)

## Above, the *OPC?is really only needed because the method used to acqurie the signal is actually insufficient.
    ## It DOES NOT synchronize the acquistion in a meaningful way, but, for this smmple, it DOES provide enough delay to cause the next step to work,
    ## otherwise, the scope is trying to load no signal into the arb (no signal acquired that quickly)

####################################################
####################################################
## METHOD1, load from actual channel
## get analog ch1 into arb memory
KsInfiniiVisionX.query(":WGEN:ARBitrary:STORe CHAN1;*OPC?") # Interestingly, if this actually fails and it's not just a command error, it does not generate a scope error, tho an error is displayed on screen (not a typical error)
##  When we do this, it has the side effect of changing the ampltiude and offset of the wgen

KsInfiniiVisionX.query("*OPC?") # puase to allow it to load
KsInfiniiVisionX.write(":WGEN:VOLTage 1")
KsInfiniiVisionX.write(":SINGle;:TRIGger:FORCe")
time.sleep(2) # pause soley so user can see signal
## Should see another sine wave

err = str(KsInfiniiVisionX.query(":SYSTem:ERRor?"))
print err

## OR

## The below methods use an IEEE488.2 compliant definite length binary block transfer.
## ASCII trasnfers are also possible, but MUCH slower.  Method 2 shows this as well, though it is commented out.
## See also: https://docs.python.org/2/library/struct.html#format-characters and https://pyvisa.readthedocs.io/en/stable/rvalues.html#writing-binary-values

####################################################
####################################################
## METHOD2, load values scaled to -1 to 1 - offset and ampltiude set the scale - scope automatically adjusts it to fit into the 10 bit DAC
KsInfiniiVisionX.write_binary_values(':WGEN:ARBitrary:DATA ',[-1,-.5,0,0.5,1], datatype = 'f', is_big_endian = False ) # floating point values between -1 and +1; can be is CSV/ASCII or Binary
## One could use a csv or a binary file here
## f means float

## As an ASCII transfer:
##KsInfiniiVisionX.write(':WGEN:ARBitrary:DATA %s' % ('-1,-.5,0,0.5,1'))
## or
##KsInfiniiVisionX.write(":WGEN:ARBitrary:DATA -1,-.5,0,0.5,1")

KsInfiniiVisionX.query("*OPC?") # puase to allow it to load
KsInfiniiVisionX.write(":WGEN:VOLTage 1")
KsInfiniiVisionX.write(":SINGle;:TRIGger:FORCe")
time.sleep(2) # pause soley so user can see signal
## Should see a positive going step waveform

err = str(KsInfiniiVisionX.query(":SYSTem:ERRor?"))
print err

## OR

####################################################
####################################################
## METHOD3, load values scaled to the 10 bit DAC - offset and ampltiude set the scale
KsInfiniiVisionX.write_binary_values(':WGEN:ARBitrary:DATA:DAC ',[0,-100,-200,-300,-400,-500], datatype = 'h', is_big_endian = False ) # decimal 16-bit integer values between -512 to +511,  can be is CSV/ASCII or Binar
## One could use a csv or a binary file here
## h means signed short integer

KsInfiniiVisionX.query("*OPC?") # puase to allow it to load
KsInfiniiVisionX.write(":SINGle;:TRIGger:FORCe")
##  ## Should see a negative going step waveform

err = str(KsInfiniiVisionX.query(":SYSTem:ERRor?"))
print err

## OR

####################################################
####################################################
## METHOD4, load a csv or binary file
file_to_load = "C:\\Users\\Public\\sample_arb_data.csv"
with open(file_to_load, 'r') as filehandle: # r means open for reading
    recalled_data = np.loadtxt(file_to_load,delimiter=',')
    ## This data must be between -1 and +1 or -512 TO +511, so it needs to be normalized!
    ## This should be done unless you have already scaled it or u do not want to for some reason.

## Normalize
recalled_max = np.max(recalled_data)
recalled_min = np.min(recalled_data)
recalled_range = recalled_max - recalled_min

## Normalize to -1 to +1 range (use  y = mx + b)
scale_adjust  = 2.0 / recalled_range # in Python, either the dividend or the divisor must be a float, else it returns zero
norm_offset   = -1 - recalled_min * scale_adjust
norm_recalled = (recalled_data * scale_adjust) + norm_offset

## Normalize to 10 bit DAC range - Must still be from -512 to +511
scale_adjust_DAC  = 1023.0 / recalled_range
norm_offset_DAC   = -512 - recalled_min * scale_adjust_DAC
norm_recalled_DAC = (recalled_data * scale_adjust_DAC) + norm_offset_DAC
## These may not be integers, so round them per whatever method you like
norm_recalled_DAC = np.round(norm_recalled_DAC)

KsInfiniiVisionX.write_binary_values(':WGEN:ARBitrary:DATA ', norm_recalled, datatype = 'f', is_big_endian = False )
## OR for the DAC KsInfiniiVisionX.write_binary_values(':WGEN:ARBitrary:DATA:DAC ', norm_recalled_DAC, datatype = 'h', is_big_endian = False )
## Adjust output to real voltage as needed
KsInfiniiVisionX.query("*OPC?") # puase to allow it to load
KsInfiniiVisionX.write(":SINGle;:TRIGger:FORCe")

err = str(KsInfiniiVisionX.query(":SYSTem:ERRor?"))
print err

####################################################
####################################################
## done - properly close scope
KsInfiniiVisionX.clear()
KsInfiniiVisionX.close()