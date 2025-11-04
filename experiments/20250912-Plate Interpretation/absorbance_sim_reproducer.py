import re
import os
from distutils.util import strtobool

SIMULATION_MODE = bool(strtobool(os.getenv("SIMULATION_MODE", "true")))

if SIMULATION_MODE:
    print("Running in simulation mode.")
    import opentrons.simulate

    protocol = opentrons.simulate.get_protocol_api("2.21")
else:
    print("WARNING: Running on physical hardware.")
    import opentrons.execute

    protocol = opentrons.execute.get_protocol_api("2.21")

print(f"Protocol API {protocol.api_version} loaded.")

# NOTE: 2.16 tested with https://github.com/AccelerationConsortium/ac-training-lab/blob/3988313d80d3d9b1f2a795ceb8701194af00d8e3/src/ac_training_lab/ot-2/_scripts/OT2mqtt.py # noqa: E501
# protocol = opentrons.execute.get_protocol_api("2.16")

pr_mod = protocol.load_module(module_name="absorbanceReaderV1", location="C3")

pr_mod.close_lid()
pr_mod.initialize(
    mode="single", wavelengths=[600]
)  # can add (reference_wavelength=) for normalization (reference wavelenth data will be subtracted from wavelength indicated)
pr_data = pr_mod.read()
print(pr_data)
pr_data[600]["A1"]
pr_data = pr_mod.read(export_filename="raw_absorbance_in")  # CSV file
