#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  7 13:46:20 2025

@author: danielvalmassei
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

data = pd.read_csv('out.csv')

data = data[data['n_channel'] == 'CH0']
plt.plot(data['Amplitude (V)'][:])
plt.show()

#print(data[data['n_channel'] == 'CH0'])

pedestal_corrected_amps = -(data['Amplitude (V)'] - np.mean(np.mean(data['Amplitude (V)'][10:210])))

plt.plot(pedestal_corrected_amps[1024*5:1024*6])
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
    
    mean_charge[voltage] = np.mean(charge)
    std_charge[voltage] = np.std(charge)
    err_charge[voltage] = std_charge[voltage]/np.sqrt(n_events)
    
plt.errorbar(voltages, mean_charge, yerr = err_charge)
plt.show()
        