# -*- coding: utf-8 -*-

## DO NOT CHANGE ABOVE LINE

# Python for Test and Measurement
#
# Requires VISA installed on Control PC
# 'keysight.com/find/iosuite'
# Requires PyVisa to use VISA in Python
# 'http://PyVisa.sourceforge.net/PyVisa/'

## Keysight IO Libraries 17.1.19xxx
## Anaconda Python 2.7.7 64 bit
## PyVisa 1.6.3
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
import visa # PyVisa info @ http://PyVisa.readthedocs.io/en/stable/
import time
import struct
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import pickle # Specifically needed for this script

##############################################################################################################################################################################
##############################################################################################################################################################################
## Intro, general comments, and instructions
##############################################################################################################################################################################
##############################################################################################################################################################################

## This example program is provided as is and without support. Keysight is not responsible for modifications.
## Standard Python style is not followed to allow for easier reading by non-Python programmers.

## Keysight IO Libraries 17.1.19xxx was used.
## Anaconda Python 2.7.7 64 bit is used - 64 bit is strongly recommended for all scope applications that can create lots of data.
## PyVisa 1.8 is used
## Windows 7 Enterprise, 64 bit (has implications for time.clock if ported to unix type machine, use time.time instead)

## HiSlip and Socket connections not supported

## DESCRIPTION OF FUNCTIONALITY
## This script shows how to query the scope setup, save it to disk, recall it form disk, and use it to setup the scope again.
    ## Doing the same for just the trigger setup is also shown.
    ## Doing the same but using the *LRN? query

## This script should work for all InfiniiVision and InfiniiVision-X oscilloscopes:
## DSO5000A, DSO/MSO6000A/L, DSO/MSO7000A/B, DSO/MSO-X2000A, DSO/MSO-X3000A/T, DSO/MSO-X4000A, DSO/MSO-X6000A

##############################################################################################################################################################################
##############################################################################################################################################################################
## DEFINE CONSTANTS
##############################################################################################################################################################################
##############################################################################################################################################################################

## Initialization constants
SCOPE_VISA_ADDRESS = "USB0::0x0957::0x17A0::MY51500439::0::INSTR" # Get this from Keysight IO Libraries Connection Expert
    ## Note: Sockets will not work for the blocking_method as there is now way to do a device clear over a socket. They are otherwise not tested in this script.
    ## Video: Connecting to Instruments Over LAN, USB, and GPIB in Keysight Connection Expert: https://youtu.be/sZz8bNHX5u4
GLOBAL_TOUT =  10000 # IO time out in milliseconds

## Setup base file name
SETUP_BASE_FILE_NAME = "my_setup"
## Save Location
BASE_DIRECTORY = "C:\\Users\\Public\\"

##############################################################################################################################################################################
##############################################################################################################################################################################
## Connect and initialize scope
##############################################################################################################################################################################
##############################################################################################################################################################################

## Define VISA Resource Manager & Install directory
## This directory will need to be changed if VISA was installed somewhere else.
rm = visa.ResourceManager('C:\\Windows\\System32\\visa32.dll') # this uses PyVisa
## This is more or less ok too: rm = visa.ResourceManager('C:\\Program Files (x86)\\IVI Foundation\\VISA\\WinNT\\agvisa\\agbin\\visa32.dll')
## In fact, it is generally not needed to call it explicitly: rm = visa.ResourceManager()

## Open Connection
## Define & open the scope by the VISA address ; # This uses PyVisa
try:
    KsInfiniiVisionX = rm.open_resource(SCOPE_VISA_ADDRESS)
except Exception:
    print "Unable to connect to oscilloscope  at " + str(SCOPE_VISA_ADDRESS) + ". Aborting script.\n"
    sys.exit()

## Set Global Timeout
## This can be used wherever, but local timeouts are used for Arming, Triggering, and Finishing the acquisition... Thus it mostly handles IO timeouts
KsInfiniiVisionX.timeout = GLOBAL_TOUT

## Clear the instrument bus
KsInfiniiVisionX.clear()

## Clear all registers and errors
## Always stop scope when making any changes.
KsInfiniiVisionX.query(":STOP;*CLS;*OPC?")

##############################################################################################################################################################################
##############################################################################################################################################################################
## Main: Get & save setup, default the scope, recall & load setup, check for errors.
##############################################################################################################################################################################
##############################################################################################################################################################################

## Get setup
Setup = KsInfiniiVisionX.query_binary_values(":SYStem:SETup?","B",False)

## Save the setup to disk
filename = BASE_DIRECTORY + SETUP_BASE_FILE_NAME  + ".KsIv_ scope_setup"
with open(filename, 'w') as filehandle:
    pickle.dump(Setup, filehandle)

## Default the scope
KsInfiniiVisionX.write("*RST")

### Recall the setup form disk
with open(filename, 'r') as filehandle:
    recalled_Setup = pickle.load(filehandle)

## Stop the scope before making any setup changes, and clear any existing errors
KsInfiniiVisionX.query(":STOP;*CLS;*OPC?")

## Write the recalled setup to the scope
KsInfiniiVisionX.write_binary_values(":SYStem:SETup ",recalled_Setup,"B",False)
    ## Note, this will  not put the scope into Run mode or Single

## Check for errors
Setup_Err = []
ErrorList = KsInfiniiVisionX.query(":SYSTem:ERRor?").split(',')
Error = ErrorList[0]
while int(Error)!=0: ## Basically this reads all errors in the error queue until the error queue is empty
    print "Error #: " + ErrorList[0]
    print "Error Description: " + ErrorList[1]
    Setup_Err.append(ErrorList[0])
    Setup_Err.append(ErrorList[1])
    ErrorList = KsInfiniiVisionX.query(":SYSTem:ERRor?").split(',')
    Error = ErrorList[0]
    Setup_Err = list(Setup_Err)

if len(Setup_Err) == 0:
    print "Setup loaded without error.\n"
    del Setup_Err
else:
    print "Setup has scope specific errors.\n"

##############################################################################################################################################################################
##############################################################################################################################################################################
## Just the trigger setup
##############################################################################################################################################################################
##############################################################################################################################################################################

## Note that this general method can be used with the other "subsystems" (e.g. :WAVegen?, :CHANnel1?) to the same effect.

## Get the trigger setup
Trigger_Setup = str(KsInfiniiVisionX.query(":TRIGger?")).strip("\n")

## Save the trigger setup
filename = BASE_DIRECTORY + SETUP_BASE_FILE_NAME  + ".KsIv_ scope_trigger_setup"
with open(filename, 'w') as filehandle:
    file.write(filehandle,Trigger_Setup)

## Change the trigger setup
KsInfiniiVisionX.query(":TRIGger:MODE EDGE;EDGE:SOURce LINE;*OPC?")

## Recall the trigger setup
with open(filename, 'r') as filehandle:
    Recalled_Trigger_Setup = file.read(filehandle)

## Stop the scope before making any setup changes, and clear any existing errors
KsInfiniiVisionX.query(":STOP;*CLS;*OPC?")

## Load the trigger setup
KsInfiniiVisionX.write(Recalled_Trigger_Setup)

## Check for errors
Trig_Setup_Err = []
ErrorList = KsInfiniiVisionX.query(":SYSTem:ERRor?").split(',')
Error = ErrorList[0]
while int(Error)!=0: ## Basically this reads all errors in the error queue until the error queue is empty
    print "Error #: " + ErrorList[0]
    print "Error Description: " + ErrorList[1]
    Trig_Setup_Err.append(ErrorList[0])
    Trig_Setup_Err.append(ErrorList[1])
    ErrorList = KsInfiniiVisionX.query(":SYSTem:ERRor?").split(',')
    Error = ErrorList[0]
    Trig_Setup_Err = list(Trig_Setup_Err)

if len(Trig_Setup_Err) == 0:
    print "Load trigger setup completed without error.\n"
    del Trig_Setup_Err
else:
    print "Trigger setup has scope specific errors.\n"

## This can produce trivial erro4s on occasion.  Take the below as an example, for loading in an edge trigger with the source as LINE.
    ## :TRIG:MODE EDGE;SWE NORM;NREJ 0;HFR 0;HOLD +60E-09;:TRIG:EDGE:SOUR LINE;LEV 0.0;SLOP POS;REJ OFF;COUP DC
    ## Here what happens is that, as it returns the general trigger settings, it also returns the trigger COUPling and noise REJect...
        ## neither of which apply to SOURce = LINE, and can thus be safely ignored.

## One place this can go wrong, though, is if you need to adjust the thresholds on multichannel triggers.  Most of the time, the :TRIG? query
    ## will not return the threshold level for edges in this scenario (e.g. the OR trigger). In this case, it would be best to first grab the
    ## general trigger setup, then set the type to line, and find the threshold for each channel...  and restore as needed.

## Another way to generate an error here is saving this file for use on a different scope with different channel count/abilities.  Probes with different
    ## attenuation ratios potential can also affect this.

##############################################################################################################################################################################
##############################################################################################################################################################################
## Setup file using *LRN?
##############################################################################################################################################################################
##############################################################################################################################################################################
    
## The *LRN method will retrieve all the setup information from the instrument. For some scopes the file looks like an XML file, for
##    others it is not readable. 
    
## Define the path to the new file.
filePath = BASE_DIRECTORY + SETUP_BASE_FILE_NAME + '.txt'

## Send the *LRN? query to get all the setup information.
try:
    KsInfiniiVisionX.write('*LRN?')

    # Read Raw needs to be used to work with all scopes. 
    #    If the read_raw command is not used, python will try to turn the unicode string into Ascii. Not all 
    #    character exist in ascii. Python will through an error and not allow the retrieval of data.
    # read_raw gets the exact data sent by the scope. read or query commands try to encode the data to ascii.
    data = KsInfiniiVisionX.read_raw()
except:
    print 'An Error Occurred reading the setup. Aborting. \n'
    KsInfiniiVisionX.clear()
    KsInfiniiVisionX.close()
    sys.exit()
  
## Save the setup data to a file. We will write in binary to prevent python from throwing a ascii conversion error.
f = open(filePath,'wb')
f.write(data)
f.close()    

print 'Setup information saved to ' + filePath
    
# Read the file back. We read in binary because we wrote in binary.
#    If we write in binary and read normally we will get the ascii conversion error.
f = open(filePath,'rb')
dataOut = f.read()
f.close()


## Stop the scope before making any setup changes, and clear any existing errors
KsInfiniiVisionX.query(":STOP;*CLS;*OPC?")

## Same as above.
## Write Raw needs to be used to avoid any errors from python. 
## write_raw allows us to write exactly what the scope sent out.
try:
    KsInfiniiVisionX.write_raw(dataOut)
except:
    print 'An Error Occurred reading the setup. Aborting. \n'
    KsInfiniiVisionX.clear()
    KsInfiniiVisionX.close()   
    sys.exit()
    
print 'Setup file sent to instrument.\n'


## Check for any errors caused by the setup file.
KsInfiniiVisionX.write('SYSTem:ERRor?')
errors = KsInfiniiVisionX.read()
print 'Errors: ', errors
while errors != u'+0,"No error"\n':
    KsInfiniiVisionX.write('SYSTem:ERRor?')
    errors = KsInfiniiVisionX.read()
    print 'Errors: ', errors   

# This method of getting the setup file will work differently for all scopes. 
# The InfiniiVisionX scopes, return what looks like an XML file. 
# The old InfiniiVision scopes return unreadable data. 
# Every instrument is different. 
# If the scope was in 'Stop'. The data might not show up when the setup file is sent back.
#    It might show up with, what looks to be, corrupt data.
#    A quick press of the single button shows the correct screen. 
##############################################################################################################################################################################


print "Done."

## Close connection to scope
KsInfiniiVisionX.clear()
KsInfiniiVisionX.close()
