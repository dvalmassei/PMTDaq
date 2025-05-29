#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 22 07:50:58 2025

@author: danielvalmassei
"""

from CAENpy.CAENDigitizer import CAEN_DT5742_Digitizer
from CAENpy.CAENDesktopHighVoltagePowerSupply import CAENDesktopHighVoltagePowerSupply
import pandas as pd
import numpy
import time


def configure_digitizer(digitizer:CAEN_DT5742_Digitizer):
   	digitizer.set_sampling_frequency(MHz=2500)
   	digitizer.set_record_length(1024)
   	digitizer.set_max_num_events_BLT(1024)
   	#digitizer.set_acquisition_mode('sw_controlled')
   	#digitizer.set_ext_trigger_input_mode('disabled')
   	digitizer.write_register(0x811C, 0x000D0001) # Enable busy signal on GPO.
   	#digitizer.set_fast_trigger_mode(enabled=True)
   	digitizer.set_fast_trigger_digitizing(enabled=True)
   	digitizer.enable_channels(group_1=True, group_2=False)
   	#digitizer.set_fast_trigger_threshold(22222)
   	#digitizer.set_fast_trigger_DC_offset(V=0)
   	#digitizer.set_post_trigger_size(0)
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
    
    
def main():
    ########## setup ##########
    HV = CAENDesktopHighVoltagePowerSupply(port='/dev/ttyACM0') # Open the connection.
    print('HV connected with:',HV.idn)
    digitizer = CAEN_DT5742_Digitizer(LinkNum=0)
    configure_digitizer(digitizer)
    digitizer.set_max_num_events_BLT(1024) # Override the maximum number of events to be stored in the digitizer's self buffer.


    ########## Turn on HV ##########
    print('Ramping voltage. This will take a moment...')
    HV.send_command('SET','ON',CH=0)
    HV.channels[0].ramp_voltage(800, ramp_speed_VperSec=50) #Ramp voltage to 800 V and wait for HV to finish
    print('HV ready.')
    
    
    ########## Acquisition ##########
    n_events = 0
    ACQUIRE_AT_LEAST_THIS_NUMBER_OF_EVENTS = 1000
    data = [] #Pandas DataFrame
    
    with digitizer:
        print('Digitizer is enabled!')
        for voltage in [800,1000,10]:
            temp_data = [] #List
            n_events = 0
            HV.channels[0].ramp_voltage(voltage,ramp_speed_VperSec=15)
            v = HV.get_single_channel_parameter('VMON', 0)
            i = HV.get_single_channel_parameter('IMON', 0)
            print(f'Voltage measured at {v} V and is drawing {i} uA and and reset event count...')
            while n_events < ACQUIRE_AT_LEAST_THIS_NUMBER_OF_EVENTS:
                time.sleep(.05) #ask for data every ~50 ms
                wf = digitizer.get_waveforms()
                n_events += len(wf)
                print(f'acquired {n_events} of {ACQUIRE_AT_LEAST_THIS_NUMBER_OF_EVENTS} at {voltage}...')
                temp_data.append(wf)
                
            print(f'Collected {n_events} at {voltage} V')
            print('Now appending to DataFrame...')
            data = pd.concat(data,convert_dicitonaries_to_data_frame(temp_data,voltage))
    
    print('Acquisition complete.')
    
    
    ########## Turn off HV ##########
    HV.send_command('SET', 'VSET', CH=0, VAL=0) #set HV to 0V, but don't wait
    HV.send_command('SET','OFF',CH=0) #HV will now disable after it ramps down, but we can keep working
    
    ########## Save the data to a file ##########
    print(data)
    
if __name__ == '__main__':
    main()