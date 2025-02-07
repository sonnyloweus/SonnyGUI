###### define default configuration
BaseConfig = {
    "res_ch": 0, # --Fixed
    "qubit_ch": 1,  # --Fixed
    "mixer_freq":0.0, # MHz
    "ro_chs":[0] , # --Fixed
    "reps":1000, # --Fixed
    "nqz": 2, #### refers to cavity
    "qubit_nqz": 2,
    "relax_delay":10, # us
    "res_phase":0, # --Fixed
    "pulse_style": "const", # --Fixed
    "read_length": 5, # units us, previously this was just names "length"
    # Try varying length from 10-100 clock ticks
    "pulse_gain":30000, # [DAC units]
    # Try varying pulse_gain from 500 to 30000 DAC units
    "pulse_freq": 0.0, # [MHz]
    # In this program the signal is up and downconverted digitally so you won't see any frequency
    # components in the I/Q traces below. But since the signal gain depends on frequency,
    # if you lower pulse_freq you will see an increased gain.
    "adc_trig_offset": 0.468+0.02, #+ 1, #soc.us2cycles(0.468-0.02), # [Clock ticks]
    # Try varying adc_trig_offset from 100 to 220 clock ticks
    "cavity_LO": 0.0,
}
