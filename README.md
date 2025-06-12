# PMTDaq
Python scripts for control of the CAEN DT1470 HV Supply and CAEN 5742 Digitzer for self triggered gain measurements

## Special Dependencies
-[pySerial](https://pypi.org/project/pyserial/)
```
pip install pyserial
```

-[CAENpy](https://github.com/SengerM/CAENpy)
- this is a python wrapper for the CAEN Digitizer library and communication with CAEN power supplies. You will also need to install libraries and driver necessary for the power supplies and digitzers.
```
pip install git+https://github.com/SengerM/CAENpy
```

## Usage
See [CAENpy](https://github.com/SengerM/CAENpy) for examples of how to interact with the HV Supply and Digitizer.

1. When setting up the digitizer to self tirgger, run
```
python self_trigger_setup.py
```

This script sets up the digitizer in a default configuration, then supplies 1000V with the HV Supply. 1 event is then aquired with the software trigger and is plotted, so the user may see the offset for each channel. The user is then queried to change the DC offset for Ch. 0 in a loop until a satisfactory offset is achieved. Finally, the acquisition mode is changed to the "transparent" mode and another acquisition is made. The user can then determine the proper trigger threshold for their application. It is useful to make note of the DC offset and trigger threshold. You will use these values when calling `HV_scan.py`.

2. Now the user is ready to call
```
python HV_scan.py <dc_offset> <trigger_threshold> <n_events> <low_HV> <high_hv> <n_steps>
```

or

```
python HV_scan_smaller_data.py <dc_offset> <trigger_threshold> <n_events> <low_HV> <high_hv> <n_steps>
```

In either case the inputs are optional, though all inouts are required if the user wants to change any. `HV_scan.py` will produce a .csv called 'out.csv' with all 8 channels in the first register shown. This is often unnecessary for a gain measurement, so I also provide `HV_smaller_data.py` which only prints Ch.0 to the .csv.

Variables:
- dc_offset: DC_offset for Ch.0 in V. Default: -0.3
- self_trigger_threshold: trigger threshold in ADC units. Default: 2870
- n_events: number of events per voltage. Default: 100
- low_HV: minimun voltage for the scan. Default: 800
- high_HV: maximum voltage for the scan. Default: 1200
- n_steps: number of divisions between low_HV and high_HV. Default: 10

```
python analysis.py <filename>
```

3. Offline analysis of the .csv created by `HV_scan.py`. Provides plots of 'Amplitude (V)' vs. index, pedestal corrected voltage of first event, histogram of the gain on an event-by-event basis, gain vs. HV in both linear and log, and 'gain_table.csv' ready for integration as a table in ELOG.

Variables:
- filename: name of .csv for analysis. Default: 'out.csv'
