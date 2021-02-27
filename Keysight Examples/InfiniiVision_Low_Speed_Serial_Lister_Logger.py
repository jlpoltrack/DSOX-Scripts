# -*- coding: utf-8 -*-

## DO NOT CHANGE ABOVE LINE

# Python for Test and Measurement
#
# Requires VISA installed on Control PC
# 'keysight.com/find/iosuite'
# Requires PyVISA to use VISA in Python
# 'http://pyvisa.sourceforge.net/pyvisa/'

## Keysight IO Libraries 17.1.19xxx
## Anaconda Python 3.5.2 64 bit
## pyvisa 1.8
## Windows 7 Enterprise, 64 bit

##"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
## Copyright © 2017 Keysight Technologies Inc. All rights reserved.
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
import csv


##############################################################################################################################################################################
##############################################################################################################################################################################
## Intro, general comments, and instructions
##############################################################################################################################################################################
##############################################################################################################################################################################

## HiSlip and Socket connections not supported

## DESCRIPTION OF FUNCTIONALITY
## This script is a reference and starting point for automating lister data capture over USB.
## LAN can also be used for connection.
## A license is required for SPI and I2C triggering and decode.  
## The connections and settings in this script are based on the user's guide for the InfiniiVision serial 
## decode demo board: http://literature.cdn.keysight.com/litweb/pdf/N2918-97004.pdf
## The user must make some edits as per below instructions.
## The script configures the scope depending on the low speed serial protocol selected.  
## Lister data is saved to a csv file once the script is stopped.  
## Saves results to a csv file, which is operable in Microsoft Excel and just about any other software…

## Tested against:
## MSOX3104A w/ Firmware System Version 02.41.2015102200
## MSOX3104T w/ Firmware System Version 04.08.2016071801
## MSOX4154A w/ Firmware System Version 04.08.2016071800
## MSOX6004A w/ Firmware System Version 06.12.2016010702

## Refer to Keysight Command Expert for more details on accepted SCPI statements and arguments.

## NO ERROR CHECKING IS INCLUDED

## NOTE: The InfiniiVision 2K, 1K, and PXIe scopes require an analog channel to be used as a signal
## source for serial decode.  The 1K scopes cannot do 4 wire SPI.  

## INSTRUCTIONS
## 1. Connect digital or analog channels to DUT
## The following applies to this script:
## 2. Modify VISA address; Get VISA address of oscilloscope from Keysight IO Libraries Connection Expert
## 3. Settings will need to be changed based on the DUT.  For example, the clock, data line, and CS signal sources
##    will most likely be connected to different channels.  
## 4. Edit BASE_FILE_NAME and BASE_DIRECTORY under Data Save constants as needed
    ## IMPORTANT NOTE:  This script WILL overwrite previously saved files!

## ALWAYS DO SOME TEST RUNS!!!!! and ensure you are getting what you want and it is later usable!!!!!

##############################################################################################################################################################################
##############################################################################################################################################################################
## DEFINE CONSTANTS
##############################################################################################################################################################################
##############################################################################################################################################################################

## Initialization constants
VISA_ADDRESS = "TCPIP0::156.140.158.156::inst0::INSTR" # Get this from Keysight IO Libraries Connection Expert #Note: sockets are not supported in this revision of the script, and pyVisa 1.6.3 does not support HiSlip
GLOBAL_TOUT = 10000 # IO time out in milliseconds

## Data Save constants
#N_MEASUREMENTS = 5 # number of measurements to make per segment, an integer
BASE_FILE_NAME = "my_data"
BASE_DIRECTORY = "C:\\Users\\Public\\"
    ## IMPORTANT NOTE:  This script WILL overwrite previously saved files!
filename = BASE_DIRECTORY + BASE_FILE_NAME + "Test.csv"

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
## Define & open the scope by the VISA address ; # this uses pyvisa
KsInfiniiVisionX = rm.open_resource(VISA_ADDRESS)

## Set Global Timeout
## This can be used wherever, but local timeouts are used for Arming, Triggering, and Finishing the acquisition... Thus it mostly handles IO timeouts
KsInfiniiVisionX.timeout = GLOBAL_TOUT

#clear the instrument bus
KsInfiniiVisionX.clear()

KsInfiniiVisionX.query(":SYSTem:PRESet; *OPC?") ##Equivalent to pressing Default Setup button

LSS_sel= input("Please select a serial protocol: 1 for SPI, 2 for I2C: ") 
print("To stop script press ctrl-c or esc when Python console is active window")


#The below settings will most likely need to be changed.  These settings are based on a Keysight Demo Board.  
#Changing the order of statements is NOT recommended.  The *OPC? statement is used to ensure that each command completes execution.  
#Removal of *OPC? is optional.  If you do remove the *OPC?, be sure to change the .query to .write

SPI_patt = "'0x05XX'"  ##data pattern to trigger on in hexadecimal
I2C_patt = "'0x10'"    ##data pattern to trigger on in hexadecimal
I2C_addr = "'0x50'"    ##address for I2C data

if LSS_sel == '1':
    KsInfiniiVisionX.query(":TIMebase:SCALe 0.001; *OPC?") ##Sets the t/div to 1 ms.  This may need to be changed depending on the frequency of bus activity
    KsInfiniiVisionX.query(":SBUS1:MODE SPI; *OPC?") ##Selects the serial protocol to use
    KsInfiniiVisionX.query(":SBUS1:SPI:SOURce:CLOCk DIGital1; *OPC?") ##Designates Digital channel 1 as the clock 
    KsInfiniiVisionX.query(":SBUS1:SPI:WIDTh 16; *OPC?") ##Defines the word size of the SPI packets
    KsInfiniiVisionX.query(":SBUS1:SPI:FRAMing1 NCHipselect; *OPC?")  ##Sets the chip select as active low
    KsInfiniiVisionX.query(":SBUS1:SPI:SOURce:FRAMe DIGital0; *OPC?") ##Designates Digital channel 0 as the chip select 
    KsInfiniiVisionX.query(":SBUS1:SPI:SOURce:MOSI DIGital3; *OPC?") ##Designates Digital channel 3 as the data line    
    KsInfiniiVisionX.query(":SBUS1:SPI:TRIGger:TYPE MOSI; *OPC?") ##Tells the trigger circuitry to watch the MISO
    KsInfiniiVisionX.query(":TRIGger:MODE SBUS1; *OPC?") ##Identifies the serial bus where a trigger event will occur
    KsInfiniiVisionX.query(":SBUS1:SPI:TRIGger:PATTern:MOSI:DATA "+SPI_patt+"; *OPC?") ##Defines a MISO data pattern to trigger on (in Hex format)
    ##NOTE: X = don't cares 
    KsInfiniiVisionX.query(":SBUS1:SPI:TRIGger:PATTern:MOSI:WIDTh 16; *OPC?") ##Tell trigger circuitry the width of the MISO word
    KsInfiniiVisionX.query(":TRIGger:SWEep NORMal; *OPC?") ##Sets the scope to normal trigger mode
    KsInfiniiVisionX.query(":SBUS1:DISPlay 1; *OPC?") ##Displays the serial decode bus
    KsInfiniiVisionX.query(":LISTer:DISPlay 1; *OPC?") ##Displays the lister
elif LSS_sel == '2':
    KsInfiniiVisionX.query(":TIMebase:SCALe 0.0005; *OPC?") ##Sets the t/div to 5 ms.  This may need to be changed depending on the frequency of bus activity
    KsInfiniiVisionX.query(":SBUS1:MODE IIC; *OPC?")
    KsInfiniiVisionX.query(":SBUS1:IIC:SOURce:CLOCk DIGital15; *OPC?")
    KsInfiniiVisionX.query(":SBUS1:IIC:SOURce:DATA DIGital14; *OPC?")
    KsInfiniiVisionX.query(":TRIGger:MODE SBUS1; *OPC?")
    KsInfiniiVisionX.query(":SBUS1:IIC:TRIGger:TYPE WRITe7; *OPC?") ##Sets the IIC trigger type. 
    ##WRITe7 is a 7 bit address frame in the following format (Start:Address7:Write:Ack:Data).
    ##For a complete list of accepted IIC trigger types refer to Keysight Command Expert.
    KsInfiniiVisionX.query(":SBUS1:IIC:TRIGger:PATTern:ADDRess "+I2C_addr+"; *OPC?") ##Sets the address for IIC data.
    KsInfiniiVisionX.query(":SBUS1:IIC:TRIGger:PATTern:DATA "+I2C_patt+"; *OPC?") ##Specifies data value to search for
    KsInfiniiVisionX.query(":TRIGger:SWEep NORMal; *OPC?")
    KsInfiniiVisionX.query(":SBUS1:DISPlay 1; *OPC?") ##Displays the serial decode bus
    KsInfiniiVisionX.query(":LISTer:DISPlay 1; *OPC?")
## DO NOT RESET THE SCOPE!


Master_List=[]
#Initialize an empty list where lister data will be stored
  

try: 
##The following while loop tells the scope to acquire lister data and then append it to Master_List.  
##NOTE: Digitize is a special run command that prevents scope operations from being interrupted.
##Digitize is useful when performing decode or intensive calculations because it ensures that all processing is complete
##before results are available.  When digitize is complete acquistion is stopped.  
    while(1): 
        KsInfiniiVisionX.write(":DIGitize") 
        Master_List.append(KsInfiniiVisionX.query(":LISTer:DATA?"))

##This loop can be exited by pressing any key.  The contents of Master_List are then written to a CSV file.
except KeyboardInterrupt: ##When the python console is selected, pressing ctrl-C or 
##escape will stop the script.
    KsInfiniiVisionX.clear() ##Clears the instrument bus
    KsInfiniiVisionX.query(":STOP;*OPC?") ##Stops acquistion
    KsInfiniiVisionX.close() ##Closes the USB connection to the scope
##The following with statement and for loop formats the data from Master_List
    with open(filename, 'w', newline='') as csvfile: 
        Serial_Data = csv.writer(csvfile, delimiter='\n')
        for x in Master_List:
            Serial_Data.writerow(x.split('\n')) ##split entries based on new line character
            ##note that each acquisition is separated by a new line and new header.  
    sys.exit("User Interupt.  Properly closing scope and aborting script.")
##NOTE: question marks under the "time" column in the CSV file indicate that a portion of a
##data packet is offscreen 
except Exception: 
##If an exception occurs the instrument bus is cleared, acqusition is stopped, and the connection closed.
    KsInfiniiVisionX.clear()
    KsInfiniiVisionX.query(":STOP;*OPC?")
    KsInfiniiVisionX.clear()
    KsInfiniiVisionX.close()
    sys.exit("Something went wrong.  Properly closing scope and aborting script.")

print ("Done.")