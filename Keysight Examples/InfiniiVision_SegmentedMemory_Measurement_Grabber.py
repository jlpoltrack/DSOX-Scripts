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
#import pylab
import h5py


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
## Windows 7 Enterprise, 64 bit (has implications for time.clock if ported to unix type machine, use time.time instead)

## HiSlip and Socket connections not supported

## DESCRIPTION OF FUNCTIONALITY
## This script assumes the user has already acquired segments manually on an InfiniiVision or InfiniiVision-X oscilloscope.  A license may be needed for segmented memory.
## The user must make some trivial edits as per below instructions.
## The script figures out how many segments were actually acquired, flips through them, gathers the time tags and desired measurement results that the user has edited in.
## Saves results to a csv file, which is operable in Microsoft XL and just about any other software…
## Script defaults should work for any 4 channel InfiniiVision or InfiniiVision-X oscilloscope with:
    ## Channels 1 & 3 hooked to the probe compensation port with a passive probe
    ## Channels 1 & 3 on, and AutoScaled
    ## Results placed in C:\Users\Public\ w/ file name my_data.csv (editable)
## User enables segmented memory and acquires a few segments
## Tested against MSOX3104A w/ Firmware System Version 2.39.
## segmented memory video: https://www.youtube.com/watch?v=riYGdiNG2PU
## NO ERROR CHECKING IS INCLUDED

## INSTRUCTIONS
## 1. Setup oscilloscope and acquire segments manually, wait until acquisition is done
## The following applies to this script:
## 2. Modify VISA address; Get VISA address of oscilloscope from Keysight IO Libraries Connection Expert
## 3. Enter number of measurements to take per segment under ## Data Save constants: N_MEASUREMENTS
    ## At least 1 measurement MUST be enabled.
## 4. Edit BASE_FILE_NAME and BASE_DIRECTORY under Data Save constants as needed
    ## IMPORTANT NOTE:  This script WILL overwrite previously saved files!
## 5. Edit/add/remove measurements to retrieve at ## Flip through segments – refer to oscilloscope programmer's guide as needed
## 6. Edit header info at ## create header info
## ALWAYS DO SOME TEST RUNS!!!!! and ensure you are getting what you want and it is later usable!!!!!

##############################################################################################################################################################################
##############################################################################################################################################################################
## DEFINE CONSTANTS
##############################################################################################################################################################################
##############################################################################################################################################################################

## Initialization constants
VISA_ADDRESS = "USB0::0x0957::0x17A0::MY51500437::0::INSTR" # Get this from Keysight IO Libraries Connection Expert #Note: sockets are not supported in this revision of the script, and pyVisa 1.6.3 does not support HiSlip
GLOBAL_TOUT =  10000 # IO time out in milliseconds

## Data Save constants
N_MEASUREMENTS = 4 # number of measurements to make per segment, an integer
BASE_FILE_NAME = "my_data"
BASE_DIRECTORY = "C:\\Users\\Public\\"
    ## IMPORTANT NOTE:  This script WILL overwrite previously saved files!

##############################################################################################################################################################################
##############################################################################################################################################################################
## Main code
##############################################################################################################################################################################
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

#clear the instrument bus
KsInfiniiVisionX.clear()

## DO NOT RESET THE SCOPE!

##############################################################################################################################################################################
##############################################################################################################################################################################
## Flip through segments, get time tags and make measurements
##############################################################################################################################################################################
##############################################################################################################################################################################

## Find number of segments actually acquired
NSEG = int(KsInfiniiVisionX.query(":WAVeform:SEGMented:COUNt?"))
## compare with :ACQuire:SEGMented:COUNt?
## :ACQuire:SEGMented:COUNt? is how many segments the scope was set to acquire
## :WAVeform:SEGMented:COUNt? is how many were actually acquired
## KEY POINT:
    ## Using fewer segments can result in a higher sample rate.
    ## If the user sets the scope to acquire the maximum number for segments, and STOPS it before it is done,
    ## it is likely that a higher sample rate could have been achieved.

## pre-allocate data array
Data = np.zeros([NSEG,N_MEASUREMENTS+2])

## Flip through segments
for n in range(1,NSEG+1,1): ## Python indices start at 0, segments start at 1
    KsInfiniiVisionX.write(":ACQuire:SEGMented:INDex " + str(n)) ## go to segment n
    time_tag = KsInfiniiVisionX.query(":WAVeform:SEGMented:TTAG?") ## get time tag of segment n

    ## As an alternate method to the below method of explicitly defining each measurement, one could setup measurements on the scope,
        ## and just grab and parse the results with results = KsInfiniiVisionX.query(":MEASure:RESults?”).split(,).  Refer to programmer’s guide for more details.
        ## Also requires user to let the oscilloscope “analyze” the segments.
        ## However, the oscilloscope may not allow for more than so many measurements (up to 10, depending on oscilloscope), and using more than
        ## 1 custom threshold per channel does not work on the oscilloscope itself.  The below method has no such limitations.

    M1 = KsInfiniiVisionX.query(":MEASure:VMIN? CHANnel1") ## with the question mark after the meausrement, the scope makes a measurement and returns it, but it does not show up on screen
    M2 = KsInfiniiVisionX.query(":MEASure:VPP? CHANnel3")
    M3 = KsInfiniiVisionX.query(":MEASure:DEFine THResholds,ABSolute,2,1.15,0.25,CHANnel1;:MEASure:FREQuency? CHANnel1;:MEASure:DEFine THResholds,STANdard,CHANnel1") # shows how to change thresholds and make a measurement with them.
            ## Note the threshold definition code and measurement is split with a semi-colon ;
            ## IMPORTANT NOTE:
                ## When the loop starts over it will now have perhaps wrong thresholds for some other timing measurement on ch1 because of the above threshold definition.
                ## Thus, one may need to adjust/reset thresholds... for example: :MEASure:DEFine THResholds,STANdard,CHANnel1 is used (with a ;) to rese the thresholds

    ## This next line shows how to use the ZOOM WINDOW to gate a measurement
    M4 = KsInfiniiVisionX.query(":TIMebase:MODE WINDow;:TIMebase:WINDow:Range 20.00E-06;:TIMebase:WINDow:POSition -250E-06;:MEASure:WINDow ZOOM;:MEASure:VAVerage?;:MEASure:WINDow MAIN;:TIMebase:MODE MAIN")
    ## It is performed like this:
        ##  Note everything was concatenated with semi-colons, as this speeds things up
        ## 1. Turn on zoom window with :TIMebase:MODE WINDow
        ## 2. Adjust width and range (total width) and then position of zoom window with :TIMebase:WINDow:Range 20.00E-06 and :TIMebase:WINDow:POSition -250E-06
            ## Note, for the ZOOM window, a negative position moves the window to the left, which is opposite the MAIN window behavior
            ## Need to adjust width (RANGe) before the POSition as POSition can change when the RANGE is adjusted
        ## 3. Tell oscilloscope to apply measurements to Zoom window with :MEASure:WINDow ZOOM
        ## 4. Make measurement (adjust thresholds as needed)
        ## 5. Tell oscilloscope to go back to making measurements on main time window with :MEASure:WINDow MAIN
        ## 6. Turn off zoom window (really, turning of the zoom window takes care of step 5, but is left in for clarity and robustness) with :TIMebase:MODE MAIN
        ## On the X4000A, X3000T, and X6000A, it is possible to gate measurements with the cursors: use :MEASure:WINDow GATE instead of :MEASure:WINDow ZOOM, and setup the marker X1 and X2 positions

    ## Note: M3 and M4 are rather likely to cuase "Data out of Range Errors" for a generic setup...

    ## Add additional measurements here and modify Data and Header as needed
    ## M5 = KsInfiniiVisionX.query(":MEASure:VPP? CHANnel1")

    ## This next measurement shows how to do a delay measurement on 2 channels with custom threhsolds for each
    ## M6: = KsInfiniiVisionX.query(":MEASure:DEFine THResholds,ABSolute,2.6,1,0.3,CHANnel1;:MEASure:DEFine THResholds,ABSolute,2,0.5,.3,CHANnel3;:MEASure:DEFine DELay,3,-1;:MEASure:DELay? CHANNEL1,CHANNEL3;:MEASure:DEFine THResholds,STANdard,CHANnel1")
        ## Defines absolute upper, middle, then lower thershold voltages (in that order) on channels 1 and then different ones on channel 3
            ## :MEASure:DEFine THResholds,ABSolute,2.6,1,0.3,CHAN1
            ## :MEASure:DEFine THResholds,ABSolute,2,0.5,.3,CHAN2
        ## Defines the edges for the delay mesurement as the 3rd rising edge on the first channel, and the first falling edge on the second channel
            ## :MEASure:DEFine DELay,3,-1
            ## NOTE: If there is an edge close to the left side of the screen, it may not count it…. So do some tests first, of course
        ## Actually measure dealy with: :MEASure:DELay? CHANNEL1,CHANNEL3
        ## Reset thresholds... (reset delay definition if needed)

    ## Assign results to Data array
    Data[n-1,0] = n ## segment index
    Data[n-1,1] = time_tag ## segment time tag
    Data[n-1,2] = M1 ## first measurement
    Data[n-1,3] = M2 ## second measurement
    Data[n-1,4] = M3 ## third measurement
    Data[n-1,5] = M4 ## third measurement
    ## Add more measurements to Data as needed
    ## Data[n-1,6] = M5 ## fourth measurement

## Close Connection to scope properly
KsInfiniiVisionX.clear()
KsInfiniiVisionX.close()

## Save Data to local disk

## create header info
## example Header = "Segment Index, Segment Time Tag (s), M1 (units), M2 (units), M3 (units)"
Header = "Segment Index, Segment Time Tag (s),VMin CH1 (V),Vpeak-peak CH3 (V),Frequency CH1 (Hz),Vavg Ch1 (V)"

## Actually save data in csv format - openable in Microsoft XL and most other software...
filename = BASE_DIRECTORY + BASE_FILE_NAME + "_Measurements.csv"
with open(filename, 'w') as filehandle:
    filehandle.write(str(Header) + "\n")
    np.savetxt(filehandle, Data, delimiter=',')
del filehandle

print "Done."