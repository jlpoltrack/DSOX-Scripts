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
## This script shows the two best synchronization methods for all InfiniiVision and InfiniiVision-X scopes. Benefits and drawbacks of each method are described.
## Only trivial error handling is provided except in the actual synchronization methods, where it is exactly as needed, though modifiable.
## This script should work for all InfiniiVision and InfiniiVision-X oscilloscopes:
## DSO5000A, DSO/MSO6000A/L, DSO/MSO7000A/B, EDU/DSOX1000A/G, DSO/MSO-X2000A, DSO/MSO-X3000A/T, DSO/MSO-X4000A, DSO/MSO-X6000A, M924xA (PXIe scope)

##############################################################################################################################################################################
##############################################################################################################################################################################
## DEFINE CONSTANTS
##############################################################################################################################################################################
##############################################################################################################################################################################

## Initialization constants
SCOPE_VISA_ADDRESS = "USB0::0x0957::0x1783::MY47050006::0::INSTR" # Get this from Keysight IO Libraries Connection Expert
    ## Note: Sockets will not work for the blocking_method as there is now way to do a device clear over a socket. They are otherwise not tested in this script.
    ## Video: Connecting to Instruments Over LAN, USB, and GPIB in Keysight Connection Expert: https://youtu.be/sZz8bNHX5u4
GLOBAL_TOUT =  10000 # IO time out in milliseconds

TIME_TO_TRIGGER = 10 # Time in seconds
    ## This is the time until the FIRST trigger event.
    ## While the script calculates a general time out for the given setup, it cannot know when a trigger event will occur.  Thus, the user must still set this value.
    ## This time is in addition to the calculated minimum timeout... so, if a scope might take say, 1 us to arm and acquire data,
        ## the signal might take 100 seconds before it occurs... this accounts for that.
    ## The SCOPE_ACQUISITION_TIME_OUT calculation pads this by 1.1

TIME_BETWEEN_TRIGGERS = 0.025 # Time in seconds - for Average, Segmented, and Equivalent Time types/modes, else set to 0
    ## In Average and Segmented Acq. Types, and Equivalent Time mode, the scope makes repeated acquisitions.  This is similar to
        ## the above TIME_TO_TRIGGER, but it is the time BETWEEN triggers.  For example, it might take 10 seconds
        ## for the first trigger event, and then they might start occurring regularly at say, 1 ms intervals.  In
        ## that scenario, 15 seconds (a conservative number for 10s) would be good for TIME_TO_TRIGGER,
        ## and 2 ms (again conservative) would be good for TIME_BETWEEN_TRIGGERS.
    ## The default in this sample script is 0.025 seconds. This is to make the sample script work for the LINE trigger
        ## used in this script when the scope is in Average Acq. Type and Segmented mode, or Equivalent Time mode, to force a
        ## trigger off of the AC input line (:TRIGger:EDGE:SOURce LINE) which runs at 50 or 60 Hz in most
        ## of the world (1/50 Hz -> 20 ms, so use 25 ms to be conservative).
    ## The SCOPE_ACQUISITION_TIME_OUT calculation pads this by 1.1

##############################################################################################################################################################################
##############################################################################################################################################################################
## Define 2 functions to synchronize InfiiVision Oscilloscopes
##############################################################################################################################################################################
##############################################################################################################################################################################

#######################################################################################################
## Define a simple and fast function utilizing the blocking :DIGitize command in conjunction with *OPC?
def blocking_method():

    KsInfiniiVisionX.timeout =  SCOPE_ACQUISITION_TIME_OUT # Time in milliseconds (PyVisa uses ms) to wait for the scope to arm, trigger, finish acquisition, and finish any processing.
        ## Note that this is a property of the device interface, KsInfiniiVisionX.
	## If doing repeated acquisitions, this should be done BEFORE the loop, and changed again after the loop if the goal is to achieve best throughput.

    print "Acquiring signal(s)...\n"
    try: # Set up a try/except block to catch a possible timeout and exit.
        KsInfiniiVisionX.query(":DIGitize;*OPC?") # Acquire the signal(s) with :DIGItize (blocking) and wait until *OPC? comes back with a one. There is no need to issue a *CLS before issuing the :DIGitize command as :DIGitize actually takes care of this for you.
        print "Signal acquired.\n"
        KsInfiniiVisionX.timeout =  GLOBAL_TOUT # Reset timeout back to what it was, GLOBAL_TOUT.
    except Exception: # Catch a possible timeout and exit.
        print "The acquisition timed out, most likely due to no trigger, or improper setup causing no trigger. Properly closing scope connection and exiting script.\n"
        KsInfiniiVisionX.clear() # Clear scope communications interface; a device clear aborts a digitize and clears the scope's IO interface..
        ## Don't do a *CLS.  If you do, you won't be able to do a meaningful :SYSTem:ERRor? query as *CLS clears the error queue
        KsInfiniiVisionX.close() # Close communications interface to scope
        sys.exit("Exiting script.")

    ## Benefits of this method:
        ## Fastest, compact
        ## Only way for Average Acquisition type:
            ## The :SINGle command does not do a complete average.
            ## Counting triggers with :RUN is much too slow
        ## Allows for easy synchronization with math functions
        ## Don't have to deal with the status registers, which can be confusing
        ## Potentially faster than polling_method(), for better throughput
        ## Because it's faster one can retrieve more accurate acquisition times than with a polling method.
        ## Works best for segmented memory if any post processing is done on the scope, e.g. measurements, lister, math, as this does not come back until the processing is all done
            ## In this scenario, :DIGitize does not reduce the sample rate or memory depth.
    ## Drawbacks of this method:
        ## Usually does not fill acquisition memory tot eh maximum available, usually only on-screen data.
        ## May not be at the highest sample rate (compared with the polling_method)
        ## Requires a well-chosen, hard-set timeout that will cover the time to arm, trigger,
            ## and finish acquisition.
        ## Requires Exception handling and a device_clear() for a possible timeout (no trigger event).
            ## Socket connection cannot do device_clear()
        ## Since :DIGitize is a "specialized form of the :RUN" command, on these scope, that results in:
            ## the sample rate MAY be reduced from using :SINGle - usually at longer time scales -
            ## typically only acquires what is on screen, though at the fastest time scales, more than on screen data may be acquired
            ## Thus, for max memory and max sample rate, use the polling_method(), which uses :SINGle.
    ## How it works:
        ## The :DIGitize command is a blocking command, and thus, all other SCPI commands are blocked until
            ## :DIGitize is completely done.  This includes any subsequent processing that is already set up,
            ## such as math, jitter separation, and measurements.  Key Point: When the *OPC? query is appended to
            ## :DIGitize with a semi-colon (;), which essentially ties it to the same thread in the parser,
            ## it is immediately dealt with when :DIGitize finishes and gives a “1” back to the script, allowing the script to move on.
    ## Other Notes:
        ## If you DO NOT know when a trigger will occur, you will need to (should) set a very long time out.
        ## The timeout will need to be (should be) adjusted before and after the :DIGitize operation,
            ## though this is not absolutely required.
        ## A :DIGitize can be aborted with a device clear, whcih also stops the scope: KsInfiniiVisionX.clear()
        ## :DIGItize disables the anti-aliasing feature (sample rate dither) on all InfiniiVision and InfiniiVision-X scopes.
        ## :DIGitize temporarily blocks the front panel, and all front panel presses are queued until :DIGitize is done.  So if you change the vertical scale, it will not happen until the acquisition is done.
            ## The exception is that the Run/Stop button on the front panel is NOT blocked (unless the front panel is otherwise locked by :SYSTem:LOCK 1).

##################################################################################################################
## Define a function using the non-blocking :SINGle command and polling on the Operation Status Condition Register
def polling_method():

    MAX_TIME_TO_WAIT = SCOPE_ACQUISITION_TIME_OUT/float(1000) # Time in seconds to wait for the scope to arm, trigger, and finish acquisition.
        ## Note that this is NOT a property of the device interface, KsInfiniiVisionX, but rather some constant in the script to be used later with
            ## the Python module "time," and will be used as time.clock().

    ## Define "mask" bits and completion criterion.
    ## Mask condition for Run state in the Operation Status Condition (and Event) Register
         ## This can be confusing.  In general, refer to Programmer's Guide chapters on Status Reporting, and Synchronizing Acquisitions
         ## Also see the annotated screenshots included with this sample script.
    RUN_BIT = 3 # The run bit is the 4th bit (see next set of comments @ Completion Criteria).
    RUN_MASK = 1<<RUN_BIT  # This basically means:  2^3 = 8, or rather, in Python 2**3 (<< is a left shift; left shift is fastest); this is used later to
        ## "unmask" the result of the Operation Status Event Register as there is no direct access to the RUN bit.

    ## Completion criteria
    ACQ_DONE = 0 # Means the scope is stopped
    ACQ_NOT_DONE = 1<<RUN_BIT # Means the scope is running; value is 8
        ## This is the 4th bit of the Operation Status Condition (and Event) Register.
        ## The registers are binary and start counting at zero, thus the 4th bit (4th position in a binary representation of decimal 8 = 2^3 = (1 left shift 3).
        ## This is either High (running = 8) or low (stopped and therefore done with acquisition = 0).

    print "Acquiring signal(s)...\n"
    StartTime = time.clock() # Define acquisition start time; This is in seconds.
    KsInfiniiVisionX.write("*CLS;:SINGle") # Beigin Acquisition with *CLS and the non-blocking :SINGle command, concatenated together. The *CLS clears all (non-mask) registers & sets them to 0;

    ## Initialize the loop entry condition (assume Acq. is not done).
    Acq_State = ACQ_NOT_DONE

    ## Poll the scope until Acq_State is a one. (This is NOT a "Serial Poll.")
    while Acq_State == ACQ_NOT_DONE and (time.clock() - StartTime <= MAX_TIME_TO_WAIT):
        Status = int(KsInfiniiVisionX.query(":OPERegister:CONDition?")) # Ask scope if it is done with the acquisition via the Operation Status Condition (not Event) Register.
            ## The Condition register reflects the CURRENT state, while the EVENT register reflects the first event that occurred since it was cleared or read, thus the CONDITION register is used.
            ## DO NOT do: KsInfiniiVisionX.query("*CLS;SINGle;OPERegister:CONDition?") as putting :OPERegister:CONDition? rigth after :SINgle doesn't work reliably
                ## The scope SHOULD trigger, but it sits there with the Single hard key on the scope lit yellow; hitting this key causes a trigger.
        Acq_State = (Status & RUN_MASK) # Bitwise AND of the Status and RUN_MASK.  This exposes ONLY the 4th bit, which is either High (running = 8) or low (stopped and therefore done with acquisition = 0)
        if Acq_State == ACQ_DONE:
            break # Break out of while loop so that the 100 ms pause below is not incurred if done.
        time.sleep(.1) # Pause 100 ms to prevent excessive queries
            ## This can actually be set a little faster, at 0.045.  The point here is that
                ## 1. if there are other things being controlled, going too fast can tie up the bus.
                ## 2. going faster does not work on all scopes.  The symptom of this not working is:
                    ## The scope SHOULD trigger, but it sits there with the Single hard key on the scope lit yellow; hitting this key causes a trigger.
            ## The pause should be at the end of the loop, so that the scope is immediately asked if it is done.
        ## Loop exits when Acq_State != NOT_DONE, that is, it exits the loop when it is DONE or if the max wait time is exceeded.

    if Acq_State == ACQ_DONE: # Acquisition fully completed
        print "Signal acquired.\n"
    else: # Acquisition failed for some reason
        print "Max wait time exceeded."
        print "This happens if there was no trigger event."
        print "Adjust settings accordingly.\n"
        print "Properly closing scope connection and exiting script.\n"
        KsInfiniiVisionX.clear() # Clear scope communications interface
        KsInfiniiVisionX.query(":STOP;*OPC?") # Stop the scope
        KsInfiniiVisionX.close() # Close communications interface to scope
        sys.exit("Exiting script.")
        ## Or do something else...

    ## Benefits of this method:
        ## Don't have to worry about interface timeouts
        ## Easy to expand to know when scope is armed, and triggered
        ## MAY result in a higher sample rate than the blocking method
        ## Always fills max available memory
        ## Can use with a socket connection if desired
    ## Drawbacks of this method:
        ## Slow
        ## Does NOT work for Average Acquisition type
            ## :SINGle does not do a complete average
                ## It does a single acquisition as if it were in NORMal acq. type
                ## Counting triggers in :RUN is much too slow
        ## Works for Segmented Memory, BUT if any post processing is done on the scope, e.g. measurements, lister, math, as this reprotsa that the acquisition is done,
            ## which is correct, BUT  the processing is NOT done, and it willt ake an indefintie amoutn of time to wiat for that, though there is no way to tell if it is done.
            ## Use the blcoking_mthod for Segmented Memory.
        ## Can't be used effectively for synchronizing math functions
            ## It can be done by applying an additional hard coded wait after the acquisition is done.  At least 200 ms is suggested, more may be required.
            ## However, as long as the time out is not excessively short, the math happens fast enough that once :OPERegister:CONDition? comes back as done
                ## that one can just wait for it when it is time to pull the math waveform.  The exception would be for eye or jitter mode on an X6000A, where the processing time can be long.
        ## Still need some maximum timeout (here MAX_TIME_TO_WAIT), ideally, or the script will sit in the while loop forever if there is no trigger event
            ## Max time out (here MAX_TIME_TO_WAIT) must also account for any processing done (see comments on math above)
            ## Max time out (here MAX_TIME_TO_WAIT) must also account for time to arm the scope and finish the acquisition
                ## This arm/trigger/finish part is accounted for in the main script.
    ## How it works:
        ## Pretty well explained in line; see annotated screenshots. Basically:
            ## What really matters is the RUN bit in the Operation Condition (not Event) Register.  This bit changes based on the scope state.
            ## If the scope is running, it is high (8), and low (0) if it is stopped.
            ## The only (best) way to get at this bit is with the :OPERation:CONDition? query.  The Operation Condition Register can reflect states
            ## for other scope properties, for example, if the scope is armed, thus it can produce values other than 0 (stopped) or 8 (running).
            ## To handle that, the result of :OPERation:Condition? is bitwise ANDed (& in Python) with an 8.  This is called "unmasking."
            ## Here, the "unmasking" is done in the script.  On the other hand, it is possible to "mask" which bits get passed to the
            ## summary bit to the next register below on the instrument itself.  However, this method it typically only used when working with the Status Byte,
            ## and not used here.
            ## Why 8 = running = not done?
                ## The Run bit is the 4th bit of the Operation Status Condition (and Event) Registers.
                ## The registers are binary and start counting at zero, thus the 4th bit is bit number 3, and 2^3 = 8, and thus it returns an 8 for high and a 0 for low.
            ## Why the CONDITION and NOT the EVENT register?
                ## The Condition register reflects the CURRENT state, while the EVENT register reflects the first event that occurred since it was cleared or read (as in: has it EVER happened?),
                ## thus the CONDITION register is used.
    ## Note that with this method using :SINGle, for InfiniiVision-X scopes only, :SINGle itself forces the trigger sweep mode into NORMal.
        ## This does not happen with the blocking method, using :DIGitize or on the InfiniiVsion notXs.

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
    print "Unable to connect to oscilloscope at " + str(SCOPE_VISA_ADDRESS) + ". Aborting script.\n"
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
## Main code
##############################################################################################################################################################################
##############################################################################################################################################################################

try:

    ###############################################################################
    ## Setup scope

    ## Note that one would normally perform a reset (default setup) if one were to create the setup from scratch...
        ## But here we will use the scope "as is" for the most part.
    ## KsInfiniiumScope.query("*RST;*OPC?") # resets the scope

    KsInfiniiVisionX.query(":STOP;*OPC?") # Scope always should be stopped when making changes.

    ## Whatever is needed

    ## For this example, the scope will be forced to trigger on the (power) LINE voltage so something happens
    KsInfiniiVisionX.write(":TRIGger:SWEep NORMal") # Always use normal trigger sweep, never auto.
    KsInfiniiVisionX.query(":TRIGger:EDGE:SOURce LINE;*OPC?") # This line simply gives the scope something to trigger on

    ## Clear the display (only so the user can see the waveform being acquired, otherwise this is not needed at all)
    KsInfiniiVisionX.write(":CDISplay")

    ###############################################################################
    ## Calculate acquisition timeout/wait time by short, overestimate method

    ## Create some default variables
    N_AVERAGES = 1
    N_SEGMENTS = 1

    ## Get some info about the scope time base setup
    HO         = float(KsInfiniiVisionX.query(":TRIGger:HOLDoff?"))
    T_RANGE    = float(KsInfiniiVisionX.query(":TIMebase:RANGe?"))
    T_POSITION = float(KsInfiniiVisionX.query(":TIMebase:POSition?"))

    ## Determine Acquisition Type and Mode:
    ACQ_TYPE = str(KsInfiniiVisionX.query(":ACQuire:TYPE?").strip("\n"))
    ACQ_MODE = str(KsInfiniiVisionX.query(":ACQuire:MODE?").strip("\n"))

    if ACQ_MODE == "SEGM":
        N_SEGMENTS= float(KsInfiniiVisionX.query(":ACQuire:SEGMented:COUNt?"))
        ## Note that if there is a lot of analysis associated segments, e.g. serial data decode, the timeout will likely need to be longer than calculated.
            ## The user is encouraged to manually set up the scope in this case, as it will be used, and time it, and use that, with a little overhead.
            ## Blocking method is recommended for Segmented Memory mode.
    elif ACQ_TYPE == "AVER":
        N_AVERAGES = float(KsInfiniiVisionX.query(":ACQuire:COUNt?"))

    ## Calculate acuisition timeout by overestimate method:
    SCOPE_ACQUISITION_TIME_OUT = (float(TIME_TO_TRIGGER)*1.1 + (T_RANGE*2.0 + abs(T_POSITION)*2.0 + HO*1.1 + float(TIME_BETWEEN_TRIGGERS)*1.1)*N_SEGMENTS*N_AVERAGES)*1000.0 # Recall that PyVisa timeouts are in ms, so multiply by 1000

    ## Ensure the timeout is no less than 10 seconds
    if SCOPE_ACQUISITION_TIME_OUT < 10000.0:
        SCOPE_ACQUISITION_TIME_OUT = 10000.0

    ## What about Equivalent Time Mode and other odd modes such as Jitter or Eye (the last two only being found on the X6000A), and math functions?
        ## In most cases, the padding and 10 second minimum timeout will take care of this.
        ## Equivalent Time Mode only has an effects at the fastest time scales, so it really doesn’t make a difference as long as a trigger signal is present. If trigger signal occurs rarely, adjust the TIME_BETWEEN_TRIGGERS constant accordingly.
        ## For math, the math will happen fast enough that the “padding” in the timeout calculation takes care of this.
        ## For jitter mode on the X6000A, the user can try this, method, and typically there is always s signal present, and the 10 second minimum should work out.  If not, make it bigger, or increase padding.
        ## For Eye mode on the X6000A, none of this works anyway, and you have to use :RUN (or :RTEYe:ACQuire) and :STOP.

    ###############################################################################
    ## Acquire Signal

    ## Choose blocking_method or polling_method
    ## There is no a-priori reason to do this as a Python function except that a user would probably want to use it repeatedly

    ## If Acquisition Type is Average, always use blocking_method() to get complete average
    polling_method()

    ###############################################################################
    ## Do Something with data... save, export, additional analysis...

    ## For example, make a peak-peak voltage measurement on channel 1:
    Vpp_Ch1 = str(KsInfiniiVisionX.query("MEASure:VPP? CHANnel1")).strip("\n") # The result comes back with a newline, so remove it with .strip("\n")
    print "Vpp Ch1 = " + Vpp_Ch1 + " V\n"

    ###############################################################################

    ##############################################################################################################################################################################
    ##############################################################################################################################################################################
    ## Done - cleanup
    ##############################################################################################################################################################################
    ##############################################################################################################################################################################

    KsInfiniiVisionX.clear() # Clear scope communications interface
    KsInfiniiVisionX.close() # Close communications interface to scope
except KeyboardInterrupt:
    KsInfiniiVisionX.clear()
    KsInfiniiVisionX.query(":STOP;*OPC?")
    KsInfiniiVisionX.write(":SYSTem:LOCK 0")
    KsInfiniiVisionX.clear()
    KsInfiniiVisionX.close()
    sys.exit("User Interupt.  Properly closing scope and aborting script.")
except Exception:
    KsInfiniiVisionX.clear()
    KsInfiniiVisionX.query(":STOP;*OPC?")
    KsInfiniiVisionX.write(":SYSTem:LOCK 0")
    KsInfiniiVisionX.clear()
    KsInfiniiVisionX.close()
    sys.exit("Something went wrong.  Properly closing scope and aborting script.")

print "Done."