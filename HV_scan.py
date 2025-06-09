#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 22 07:50:58 2025

@author: danielvalmassei
"""

from CAENpy.CAENDigitizer import CAEN_DT5742_Digitizer
from CAENpy.CAENDesktopHighVoltagePowerSupply import CAENDesktopHighVoltagePowerSupply
import pandas as pd
import numpy as np
import time
#from ctypes import CDLL
import sys


def configure_digitizer(digitizer:CAEN_DT5742_Digitizer):
   	digitizer.set_sampling_frequency(MHz=2500)
   	digitizer.set_record_length(1024)
   	digitizer.set_max_num_events_BLT(1024)
   	digitizer.set_acquisition_mode('sw_controlled')
   	digitizer.set_ext_trigger_input_mode('disabled')
   	digitizer.write_register(0x811C, 0x000D0001) # Enable busy signal on GPO.
   	#digitizer.set_fast_trigger_mode(enabled=True)
   	digitizer.set_fast_trigger_digitizing(enabled=True)
   	digitizer.enable_channels(group_1=True, group_2=False)
   	#digitizer.set_fast_trigger_threshold(22222)
   	#digitizer.set_fast_trigger_DC_offset(V=0)
   	digitizer.set_post_trigger_size(0)
   	for ch in [0]:
           digitizer.set_trigger_polarity(channel=ch, edge='falling')
          
   	print('Digitizer connected with:',digitizer.idn)

        
def convert_dicitonaries_to_data_frame(waveforms:dict,voltage):
	data = []
	for n_event,event_waveforms in enumerate(waveforms):
		for n_channel in event_waveforms:
			df = pd.DataFrame(event_waveforms[n_channel])
			df['n_event'] = n_event
			df['voltage'] = voltage
			df['n_channel'] = n_channel
			df.set_index(['n_event','n_channel'], inplace=True)
			data.append(df)
            
	return pd.concat(data)

def edit_bit(hex_value, bit_position, set_bit=True):
    """
    Edit a single bit in a 32-bit hexadecimal value.

    Args:
        hex_value (str): A string representing the 32-bit hex value (e.g., '0x12345678').
        bit_position (int): Bit position to modify (0 = least significant bit, 31 = most significant).
        set_bit (bool): If True, set the bit to 1. If False, clear the bit to 0.

    Returns:
        str: New 32-bit hexadecimal value as a string (e.g., '0x123456F8').
    """
    if not (0 <= bit_position < 32):
        raise ValueError("bit_position must be between 0 and 31")

    value = hex_value

    if set_bit:
        value |= (1 << bit_position) #bitwise OR comparisson
    else:
        value &= ~(1 << bit_position) #bitwise AND comparisson

    return value

def check_error_code(code):
    if code != 0:
        raise RuntimeError(f'libCAENDigitizer has returned error code {code}.')
    
    
def main(dc_offset=-0.3, self_trigger_threshold=2870, n_events=100, low_HV=800, high_HV=1200, n_steps=10):
    
    #libCAENDigitizer = CDLL('/usr/lib/libCAENDigitizer.so')
    
    ########## setup ##########
    HV = CAENDesktopHighVoltagePowerSupply(port='/dev/ttyACM0') # Open the connection.
    print('HV connected with:',HV.idn)
    print('Ramping voltage. This will take a moment...')
    time.sleep(0.5)
    HV.send_command('SET', 'VSET', CH=0, VAL=low_HV)
    HV.send_command('SET','ON',CH=0)
    digitizer = CAEN_DT5742_Digitizer(LinkNum=0)
    configure_digitizer(digitizer)
    digitizer.set_channel_DC_offset(channel=0,V=dc_offset) #set the DC offset to 0 V
    
        ##### Set Self Trigger Threshold #####
    old_0x1080_value = digitizer.read_register(0x1080)
    print(f'Old value of register 0x1080: {old_0x1080_value:08X}')
    digitizer.write_register(0x1080, self_trigger_threshold) #NOTE: this is a quick trick that we can use right now because we are only working with Ch.0 read register descriptions for more info
    print(f'0x1080 now: {digitizer.read_register(0x1080):08X} ')
    
        ##### Enable Self Trigger #####
    old_0x10A8_value = digitizer.read_register(0x10A8)
    print(f'Old value of register 0x10A8: {old_0x10A8_value:08X}')
    new_0x10A8_value = edit_bit(old_0x10A8_value, 0, set_bit=True)
    print(f'Writing {new_0x10A8_value:08X} at register 0x10A8.')
    digitizer.write_register(0x80A8,new_0x10A8_value)
    print(f'0x10A8 now: {digitizer.read_register(0x10A8):08X} ')
    print('Self trigger enabled for Ch.0')
    
        ##### Revert to Output Mode #####
    old_0x8000_value = digitizer.read_register(0X8000)
    print(f'Old value of register 0x8000: {old_0x8000_value:08X}')
    new_0x8000_value = edit_bit(old_0x8000_value, 13, set_bit=False)
    print(f'Writing {new_0x8000_value:08X} at register 0x8000.')
    digitizer.write_register(0x8000, new_0x8000_value)
    print(f'0x8000 now: {digitizer.read_register(0x8000):08X} ')
    print('Ready for Self-Triggered acquisition in Output Mode')
    digitizer.set_max_num_events_BLT(1024) # Override the maximum number of events to be stored in the digitizer's self buffer.


    ########## Turn on HV ##########
    HV.channels[0].ramp_voltage(low_HV, ramp_speed_VperSec=50, timeout = low_HV/50 + 30) #Ramp voltage to 800 V and wait for HV to finish
    print('HV ready.')
    
    
    ########## Acquisition ##########
    collected_events = 0
    ACQUIRE_AT_LEAST_THIS_NUMBER_OF_EVENTS = n_events
    data = pd.DataFrame() #Pandas DataFrame
    timeout = n_events*0.5 #timeout if it is taking more than 0.5s/event
    
   
    
    time.sleep(0.1)
    voltages = np.linspace(low_HV,high_HV,n_steps,endpoint=True)
    data = []
    for i in range(len(voltages)):
        temp_data = [] #List
        start_time = time.time()
        collected_events = 0
        HV.channels[0].ramp_voltage(voltages[i],ramp_speed_VperSec=15)
        v = HV.get_single_channel_parameter('VMON', 0)
        current = HV.get_single_channel_parameter('IMON', 0)
        print(f'Voltage measured at {v} V and is drawing {current} uA and and reset event count...')
        with digitizer:
            print('Digitizer is enabled!')
            while collected_events < ACQUIRE_AT_LEAST_THIS_NUMBER_OF_EVENTS:
                if time.time()-start_time > timeout:
                    wf = digitizer.get_waveforms()
                    collected_events += len(wf)
                    print(f'Timeout: acquired {collected_events} of {ACQUIRE_AT_LEAST_THIS_NUMBER_OF_EVENTS} at {voltages[i]} V...')
                    temp_data += wf
                    break
                else:
                    time.sleep(0.5) #ask for data every ~500 ms
                    wf = digitizer.get_waveforms()
                    collected_events += len(wf)
                    print(f'acquired {collected_events} of {ACQUIRE_AT_LEAST_THIS_NUMBER_OF_EVENTS} at {voltages[i]} V...')
                    temp_data += wf
                
        print(f'Collected {collected_events} at {voltages[i]} V.')
        if len(temp_data) > 0:
            print('Digitizer Closed. Now converting dictionaries to DataFrame...')
            temp_data = convert_dicitonaries_to_data_frame(temp_data,voltages[i])
            print('merging dataframes...')
            data.append(temp_data)
            print('Increasing voltage...')
        else:
            print('No data. Increasing voltage...')
        
    print('Acquisition complete.')
    data = pd.concat(data)
    
    
    ########## Turn off HV ##########
    HV.send_command('SET', 'VSET', CH=0, VAL=0) #set HV to 0V, but don't wait
    HV.send_command('SET','OFF',CH=0) #HV will now disable after it ramps down, but we can keep working
    
    ########## Save the data to a file ##########
    print('Saving df as .csv')
    data.to_csv('out.csv')
    
    print('Ramping HV down...')
    HV.channels[0].ramp_voltage(0,ramp_speed_VperSec=50, timeout = high_HV/50 + 30)
    print('Done.')
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        main()
    elif len(sys.argv) == 7:
        args = sys.argv[1:]
        main(dc_offset=float(args[0]), self_trigger_threshold=int(args[1]), n_events=int(args[2]), low_HV=float(args[3]), high_HV=float(args[4]), n_steps=int(args[5]))
    else:
        print('Too many or too few arguments passed. Please pass dc offset, self trigger threshold, n_events per measurement, low HV, high HV, and n steps.')
        