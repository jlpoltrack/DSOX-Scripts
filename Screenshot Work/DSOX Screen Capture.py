# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
#https://github.com/twam/scpi-scripts
#https://pyvisa.readthedocs.io/en/1.8/index.html
import pyvisa
import time

startTime = time.time()

#Open the resource manager
rm = pyvisa.ResourceManager()

#Iterate through the resource list, get all the IDN responses
for device in rm.list_resources():
    deviceIDNs = {}
    _device = rm.open_resource(device)
    _IDN = _device.query('*IDN?')
    deviceIDNs[device] = _IDN

#Look for 'SO-X' in the IDN response, this is likely a DSOX oscilloscope
for key,value in deviceIDNs.items():                                            
    if 'SO-X' in value:
        scopeResource = key
        break                                                                   #Break when Oscilloscope Found

# %%
#Connect to the cscilloscope and set the timeout
scope = rm.open_resource(scopeResource)
scope.timeout = 10000
idnResponse = scope.query('*IDN?')
print(f'Connected to: {idnResponse}')

# %%
#Create a timestamp for the filename, process takes ~2-3 seconds therefore will never overwrite
from datetime import datetime

fileDate = str(datetime.now()).replace(':','_').replace('-','_').replace(' ','_')[0:19]

#Get the screen data from the oscilloscope and write it to the file
scope.write(':HARDcopy:INKSaver 0')                                             #Black Background
data = scope.query_binary_values(':DISPlay:DATA? PNG, COLOR', datatype='B')
newfile=open(f'Capture_{fileDate}.png','wb')
newfile.write(bytearray(data))

print(f'Image Saved.  Took: {round(time.time() - startTime, 1)} Seconds')