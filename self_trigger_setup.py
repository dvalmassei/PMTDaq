#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 23 08:24:07 2025

@author: danielvalmassei
"""

from CAENpy.CAENDigitizer import CAEN_DT5742_Digitizer
from CAENpy.CAENDesktopHighVoltagePowerSupply import CAENDesktopHighVoltagePowerSupply
from ctypes import CDLL
import pandas as pd
import numpy
import time
from HV_scan import configure_digitizer, convert_dicitonaries_to_data_frame
import matplotlib.pyplot as plt

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

def main():
    try:
        libCAENDigitizer = CDLL('/usr/lib/libCAENDigitizer.so')
        
        HV = CAENDesktopHighVoltagePowerSupply(port='/dev/ttyACM1') # Open the connection.
        print('HV connected with:',HV.idn)
        digitizer = CAEN_DT5742_Digitizer(LinkNum=0)
        configure_digitizer(digitizer)
        digitizer.set_max_num_events_BLT(1024) # Override the maximum number of events to be stored in the digitizer's self buffer.
    
    
        ########## Turn on HV ##########
        print('Ramping voltage. This will take a moment...')
        HV.send_command('SET','ON',CH=0)
        HV.channels[0].ramp_voltage(900, ramp_speed_VperSec=20, timeout = (900/20 + 30)) #Ramp voltage to 800 V and wait for HV to finish
        print('HV ready.')
        
        v = HV.get_single_channel_parameter('VMON', 0) #read output voltage from HV supply
        i = HV.get_single_channel_parameter('IMON', 0) #read output current from HV supply
        print(f'Voltage measured at {v} V and is drawing {i} uA and and reset event count...')
        
        ########## Acquisition in Output Mode (default) w/ software trigger ##########
        dc_offset = 0
        
        keep_going = True
        while keep_going:
            digitizer.set_channel_DC_offset(channel=0,V=dc_offset) #set the DC offset to 0 V
            with digitizer:
                time.sleep(1) # wait one second
                libCAENDigitizer.CAEN_DGTZ_SendSWtrigger(digitizer._get_handle()) #trigger the digitizer with the software
                time.sleep(0.1)
                
            data = digitizer.get_waveforms()
            
            ########## Data analysis and plotting ##########
            if len(data) == 0:
                raise RuntimeError('Could not acquire any event. The reason may be that you dont have anything connected to the inputs of the digitizer, or a wrong trigger threshold and/or offset setting.')
            
            data = convert_dicitonaries_to_data_frame(data, 900)
            print(data)
            
            plt.plot(data['Time (s)'],data['Amplitude (V)'])
            plt.show()
        
            ##### Check if the baseline looks good #####
            while True:
                response = input('Is the baseline within the upper 25% of the ADC range? (Y/n)')
                if (response == 'Y'):
                    keep_going = False #All is good! We will move on
                    break
                elif (response == 'n'):
                    dc_offset = int(input(f'The current DC offset is {dc_offset}. Please enter the new DC offset:'))
                    keep_going = True #We need to change the DC offset and check again
                    break
                else:
                    print('Incorrect input. Please type "Y" or "n".')
            
        ########## Acquisition in Transparent Mode ##########
        old_0x8000_value = digitizer.read_register(0x8000) #get the current register config
        print(f'Old value of register 0x8000: {old_0x8000_value:08X}')
        new_0x8000_value = edit_bit(old_0x8000_value, 13, set_bit=True) #edit the bit[13]=1 for Transparent mode
        digitizer.write_register(0x8000,new_0x8000_value) #write the new value to the register
        print(f'Set Transparent mode. Wrote {new_0x8000_value:08X} at register 0x8000' )
        
        with digitizer:
            time.sleep(1) # wait one second
            digitizer.libCAENDigitizer.CAEN_DGTZ_SendSWtrigger() #trigger the digitizer with the software
            time.sleep(0.1)
        
        data = digitizer.get_waveforms()
        
        ########## Data analysis and plotting ##########
        if len(data) == 0:
            raise RuntimeError('Could not acquire any event. The reason may be that you dont have anything connected to the inputs of the digitizer, or a wrong trigger threshold and/or offset setting.')
        
        data = convert_dicitonaries_to_data_frame(data, 900)
        print(data)
        
        plt.plot(data['Time (s)'],data['Amplitude (V)'])
        plt.show()
        
        ########## Set Self Trigger Threshold ##########
        old_0x1080_value = digitizer.read_register(0x1080)
        print(f'Old value of register 0x1080: {old_0x1080_value:08X}')
        self_trigger_threashold = input('Please input the threshold value in decimal [0:4095]:')
        digitizer.write_register(0x1080, self_trigger_threashold) #NOTE: this is a quick trick that we can use right now because we are only working with Ch.0 read register descriptions for more info
        
        
        ########## Enable Self Trigger ##########
        old_0x10A8_value = digitizer.read_register(0x10A8)
        print(f'Old value of register 0x10A8: {old_0x10A8_value:08X}')
        new_0x10A8_value = edit_bit(old_0x10A8_value, 0, set_bit=True)
        print(f'Writing {new_0x10A8_value:08X} at register 0x10A8.')
        digitizer.write(new_0x10A8_value,0x10A8)
        print('Self trigger enabled for Ch.0')
        
        ########## Revert to Output Mode ##########
        old_0x8000_value = digitizer.read_register(0X8000)
        print(f'Old value of register 0x8000: {old_0x8000_value:08X}')
        new_0x8000_value = edit_bit(old_0x8000_value, 13, set_bit=False)
        print(f'Writing {new_0x8000_value:08X} at register 0x8000.')
        digitizer.write_register(0x8000, new_0x8000_value)
        print('Ready for Self-Triggered acquisition in Output Mode')
    
    except Exception as e:
        print('An error occured:', e)
        
    finally:
        ########## Turn off HV ##########
        HV.send_command('SET', 'VSET', CH=0, VAL=0) #set HV to 0V, but don't wait
        HV.send_command('SET','OFF',CH=0) #HV will now disable after it ramps down, but we can keep working
        print('HV turning off...')
    
    
if __name__ == '__main__':
    main()