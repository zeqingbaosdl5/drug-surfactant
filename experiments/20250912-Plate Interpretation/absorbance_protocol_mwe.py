from opentrons import protocol_api

metadata = {
    "description": "Written in 2025.05",
    "author": "Zeqing Bao and Yunhee Hwang",
}

requirements = {"robotType": "Flex", "apiLevel": "2.23"}


def run(protocol: protocol_api.ProtocolContext):

    # Add runtime parameter for wavelength
    wavelength = protocol.add_parameter("wavelength", type=int, default=600)

    pr_mod = protocol.load_module(module_name="absorbanceReaderV1", location="C3")

    pr_mod.close_lid()
    pr_mod.initialize(
        mode="single", wavelengths=[wavelength]
    )  # can add (reference_wavelength=) for normalization (reference wavelenth data will be subtracted from wavelength indicated)
    pr_data = pr_mod.read()
    print(pr_data)
    pr_data[wavelength]["A1"]
    pr_data = pr_mod.read(export_filename="raw_absorbance_in")  # CSV file
    pr_mod.open_lid()
