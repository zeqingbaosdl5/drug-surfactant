from opentrons import protocol_api


def run(protocol: protocol_api.ProtocolContext):

    pr_mod = protocol.load_module(module_name="absorbanceReaderV1", location="C3")

    pr_mod.close_lid()
    pr_mod.initialize(
        mode="single", wavelengths=[600]
    )  # can add (reference_wavelength=) for normalization (reference wavelenth data will be subtracted from wavelength indicated)
    pr_data = pr_mod.read()
    print(pr_data)
    pr_data[600]["A1"]
    pr_data = pr_mod.read(export_filename="raw_absorbance_in")  # CSV file
