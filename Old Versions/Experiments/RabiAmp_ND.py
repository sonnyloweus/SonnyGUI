class RabiAmp_ND():

    def initialize(self):
        super().__init__()


    def body(self):
        print("hi")

    ### define the template config
    config_template = {
        ##### define attenuators
        "yokoVoltage": 0.25,
        ###### cavity
        "read_pulse_style": "const",  # --Fixed
        "read_length": 10,  # us
        "read_pulse_gain": 10000,  # [DAC units]
        "read_pulse_freq": 6425.3,
        ##### spec parameters for finding the qubit frequency
        "qubit_freq_start": 2869 - 10,
        "qubit_freq_stop": 2869 + 10,
        "qubit_freq_expts": 41,
        "qubit_pulse_style": "arb",
        "sigma": 0.300,  ### units us, define a 20ns sigma
        # "flat_top_length": 0.300, ### in us
        "relax_delay": 500,  ### turned into us inside the run function
        ##### amplitude rabi parameters
        "qubit_gain_start": 20000,
        "qubit_gain_stop": 30000,  ### stepping amount of the qubit gain
        "qubit_gain_expts": 3,  ### number of steps
        "reps": 50,  # number of averages for the experiment
        "sets": 1, # number of interations to loop over experiment
    }
