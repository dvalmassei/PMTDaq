#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  7 13:46:20 2025

@author: danielvalmassei
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
#import mplhep as hep



def main(filename='out.csv'):
    #plt.style.use(hep.style.LHCb2)
    gain = 1 #additional gain provided by base or circuit
    data = pd.read_csv(filename)
    
    data = data[data['n_channel'] == 'CH0']
    plt.plot(data['Amplitude (V)'])
    plt.show()
    
    #print(data[data['n_channel'] == 'CH0'])
    
    pedestal_corrected_amps = -(data['Amplitude (V)'] - np.mean(np.mean(data['Amplitude (V)'][10:210])))
    
    plt.plot(pedestal_corrected_amps[:1023])
    plt.ylabel('Voltage (V)')
    plt.xlabel('Sample No.')
    plt.show()
    
    voltages = data['voltage'].unique()
    
    mean_charge = np.zeros(len(voltages))
    std_charge = np.zeros(len(voltages))
    err_charge = np.zeros(len(voltages))
    
    for voltage in range(len(voltages)):
        voltage_events = data[data['voltage']==voltages[voltage]]
        n_events = len(voltage_events['n_event'].unique())
        charge = np.zeros(n_events)
        for i in range(n_events):
            event = voltage_events[voltage_events['n_event'] == i].fillna(1.0)
            pedestal_corrected_amps = -(event['Amplitude (V)'] - np.mean(event['Amplitude (V)'][10:210]))
            charge[i] = np.trapz(pedestal_corrected_amps,event['Time (s)'])/(50*1.602*10**(-19))

                
        counts,bins = np.histogram(charge/gain,bins=64,range=(-0.1E8,7E8))
        plt.stairs(counts,bins,label=f'{voltages[voltage]:.5}V')
        
        
        mean_charge[voltage] = np.mean(charge)
        std_charge[voltage] = np.std(charge)
        err_charge[voltage] = std_charge[voltage]/np.sqrt(n_events)
        
    #print(voltages,mean_charge,std_charge,err_charge)
    
    plt.legend()
    #plt.yscale('log')
    plt.grid(True,which='both',axis='both')
    plt.ylabel('Events')
    plt.xlabel('Gain')
    plt.show()
        
    plt.errorbar(voltages, mean_charge/gain, yerr = err_charge,marker = '.',capsize=5,color='Maroon')
    #plt.yscale('log')
    plt.grid(True,which='both',axis='both')
    plt.ylabel('Gain')
    plt.xlabel('Voltage (V)')
    plt.show()
    
    plt.errorbar(voltages, mean_charge/gain, yerr = err_charge,marker = '.',capsize=5,color='Maroon')
    plt.yscale('log')
    plt.grid(True,which='both',axis='both')
    plt.ylabel('Gain')
    plt.xlabel('Voltage (V)')
    plt.show()
    
    df = pd.DataFrame(np.array([voltages,mean_charge,std_charge,err_charge]).T,columns = ['voltage','gain','std','err'])
    df.to_csv('gain_table.txt',sep='|',float_format='%.6g',index=False)
        
if __name__ == '__main__':
    if len(sys.argv) < 2:
        main()
    elif len(sys.argv) == 2:
        args = sys.argv[1:]
        main(str(args[0]))
    else:
        print('Too many arguments.')
        