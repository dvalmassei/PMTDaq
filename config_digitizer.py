#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 22 13:00:10 2025

@author: danielvalmassei
"""

from CAENpy.CAENDigitizer import CAEN_DT5742_Digitizer

def configure_digitizer(digitizer:CAEN_DT5742_Digitizer):
   	digitizer.set_sampling_frequency(MHz=2500)
   	digitizer.set_record_length(512)
   	digitizer.set_max_num_events_BLT(1024)
   	digitizer.set_acquisition_mode('sw_controlled')
   	digitizer.set_ext_trigger_input_mode('disabled')
   	digitizer.write_register(0x811C, 0x000D0001) # Enable busy signal on GPO.
   	digitizer.set_fast_trigger_mode(enabled=True)
   	digitizer.set_fast_trigger_digitizing(enabled=True)
   	digitizer.enable_channels(group_1=True, group_2=False)
   	digitizer.set_fast_trigger_threshold(22222)
   	digitizer.set_fast_trigger_DC_offset(V=0)
   	digitizer.set_post_trigger_size(0)
   	for ch in [0]:
   		digitizer.set_trigger_polarity(channel=ch, edge='falling')
   	print('Digitizer connected with:',digitizer.idn)