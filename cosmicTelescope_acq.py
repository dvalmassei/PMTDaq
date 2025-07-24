#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 13:36:31 2025

@author: danielvalmassei
"""

from CAENpy.CAENDigitizer import CAEN_DT5742_Digitizer
from CAENpy.CAENDesktopHighVoltagePowerSupply import CAENDesktopHighVoltagePowerSupply
from ctypes import CDLL
import pandas as pd
import numpy as np
import time
from HV_scan_smaller_data import edit_bit, configure_digitizer
import matplotlib.pyplot as plt


def check_error_code(code):
    if code != 0:
        raise RuntimeError(f'libCAENDigitizer has returned error code {code}.')
    
def convert_dicitonaries_to_data_frame(waveforms:dict,channels):
    data = []
    for n_event,event_waveforms in enumerate(waveforms):
        for n_channel in channels:
            df = pd.DataFrame(event_waveforms[f'CH{n_channel}'])
            df['n_event'] = n_event
            df['n_channel'] = n_channel
            df.set_index(['n_event','n_channel'], inplace=True)
            data.append(df)
            
            return pd.concat(data)
        
def main():
    channels = [0,1]
    dc_offset = [-0.3,-0.3]
    n_events = 10000

    #libCAENDigitizer = CDLL('/usr/lib/libCAENDigitizer.so')
    
    ########## setup ##########
    digitizer = CAEN_DT5742_Digitizer(LinkNum=0)
    configure_digitizer(digitizer)
    digitizer.set_fast_trigger_mode(enabled=True)
    digitizer.set_fast_trigger_threshold(22222)
    digitizer.set_fast_trigger_DC_offset(V=0)
    for i in range(len(channels)):
        digitizer.set_channel_DC_offset(channel=channels[i],V=dc_offset[i])

    
    ########## Output Mode ##########
    old_0x8000_value = digitizer.read_register(0X8000)
    print(f'Old value of register 0x8000: {old_0x8000_value:08X}')
    new_0x8000_value = edit_bit(old_0x8000_value, 13, set_bit=False)
    print(f'Writing {new_0x8000_value:08X} at register 0x8000.')
    digitizer.write_register(0x8000, new_0x8000_value)
    print(f'0x8000 now: {digitizer.read_register(0x8000):08X} ')
    print('Ready for externally triggered acquisition in Output Mode')
    digitizer.set_max_num_events_BLT(1024) # Override the maximum number of events to be stored in the digitizer's self buffer.


    ########## Acquisition ##########
    collected_events = 0
    data = pd.DataFrame() #Pandas DataFrame
    
    
    time.sleep(0.1)
    data = []
    
    temp_data = [] #List of dict
    start_time = time.time()
    print(f'Start: {start_time}')
    collected_events = 0
    try:
        with digitizer:
            print('Digitizer is enabled!')
            while collected_events < n_events:
                time.sleep(0.5) #ask for data every ~500 ms
                wf = digitizer.get_waveforms()
                collected_events += len(wf)
                print(f'acquired {collected_events} of {n_events}...')
                temp_data += wf
                
        print(f'Stop: {time.time()}')
        print('Digitizer Closed. Now converting dictionaries to DataFrame...')
        temp_data = convert_dicitonaries_to_data_frame(temp_data,channels)
        print('Appending lists...')
        data.append(temp_data)
    
    finally:
        ########## Save the data to a file ##########
        print('Saving df as .csv')
        
        data.to_csv('out.csv')
        
if __name__ =='__main__':
    main()
