import numpy as np

R1 = 20000
R2 = 20000
R3 = 50
R4 = 50

IBP_EXCITATION_VOLTAGE_V = 5
IBP_SENSITIVITY_UV_V_MM_HG = 5
IBP_SENSITIVITY_UV_MM_HG = IBP_SENSITIVITY_UV_V_MM_HG * IBP_EXCITATION_VOLTAGE_V

def mm_hg_to_volts(data_mm_hg):
    attenuation_factor = ((R3 + R4) / (R1 + R2 + R3 + R4))
    # Step 1, Convert pressure mmHG float to voltage uV
    pressure_mm_hg = np.divide(data_mm_hg, 1)
    # Step 2, Convert pressure mmHG float to voltage uV
    pressure_uV = np.multiply(pressure_mm_hg, IBP_SENSITIVITY_UV_MM_HG)
    # Step 3, Apply Attenuation Factor
    pressure_gain_uV = np.divide(pressure_uV, attenuation_factor)
    # Step 4, Convert Voltage uV to Voltage V
    out_dac_values_volt = np.divide(pressure_gain_uV, 1000000)

    return out_dac_values_volt