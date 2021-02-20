# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
#https://github.com/twam/scpi-scripts
import pyvisa

rm = pyvisa.ResourceManager()
print(rm.list_resources())

# %%
scope = rm.open_resource(rm.list_resources()[0])
scope.read_termination = '\n'
scope.write_termination = '\n'
scope.timeout = 5000
print(scope.query('*IDN?'))

# %%
from datetime import datetime

fileDate = str(datetime.now()).replace(':','_').replace(' ',' ')[0:19]          #Timestamp

scope.write(':HARDcopy:INKSaver 0')                                             #Black Background
data = scope.query_binary_values(':DISPlay:DATA? PNG, COLOR', datatype='B')     #Request Image Data

newfile=open(f'Capture_{fileDate}.png','wb')
newfile.write(bytearray(data))