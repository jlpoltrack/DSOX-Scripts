# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
#https://github.com/twam/scpi-scripts
import pyvisa
import time

startTime = time.time()

rm = pyvisa.ResourceManager()

for device in rm.list_resources():
    deviceIDNs = {}
    _device = rm.open_resource(device)
    _IDN = _device.query('*IDN?')
    deviceIDNs[device] = _IDN

for key,value in deviceIDNs.items():                                            #Look for 'SO-X' in IDN Response
    if 'SO-X' in value:
        scopeResource = key

# %%
scope = rm.open_resource(scopeResource)
scope.read_termination = '\n'
scope.write_termination = '\n'
scope.timeout = 5000
idnResponse = scope.query('*IDN?')
print(f'Connected to: {idnResponse}')

# %%
from datetime import datetime

fileDate = str(datetime.now()).replace(':','_').replace(' ',' ')[0:19]          #Timestamp

scope.write(':HARDcopy:INKSaver 0')                                             #Black Background
data = scope.query_binary_values(':DISPlay:DATA? PNG, COLOR', datatype='B')     #Request Image Data

newfile=open(f'Capture_{fileDate}.png','wb')
newfile.write(bytearray(data))

print(f'Image Saved.  Took: {round(time.time() - startTime, 1)} Seconds')