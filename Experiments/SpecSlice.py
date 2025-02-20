class SpecSlice():
    def __init__(self, soccfg, cfg):
        super().__init__(soccfg, cfg)

    def initialize(self):
       print("test")

    ### define the template config
    ################################## code for running qubit spec on repeat
    config_template = {
        ##### define attenuators
        "yokoVoltage": 0.25,
        ###### cavity
        "read_pulse_style": "const",  # --Fixed
        "read_length": 5,  # us
        "read_pulse_gain": 10000,  # [DAC units]
        "read_pulse_freq": 6425.3,
        ##### spec parameters for finding the qubit frequency
        "qubit_freq_start": 2869 - 20,
        "qubit_freq_stop": 2869 + 20,
        "qubit_freq_expts": 81,  ### number of points
        "qubit_pulse_style": "flat_top",
        "sigma": 0.050,  ### units us
        "qubit_length": 1,  ### units us, doesnt really get used though
        "flat_top_length": 0.300,  ### in us
        "relax_delay": 500,  ### turned into us inside the run function
        "qubit_gain": 20000,  # Constant gain to use
        # "qubit_gain_start": 18500, # shouldn't need this...
        "reps": 100,
        "sets": 5,
    }