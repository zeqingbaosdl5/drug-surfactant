from opentrons import protocol_api

metadata = {
    "description": "Written in 2025.05",
    "author": "Zeqing Bao and Yunhee Hwang",
}

requirements = {"robotType": "Flex", "apiLevel": "2.23"}


def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_int(
        display_name="Wavelength",
        variable_name="wavelength",
        default=450,
        minimum=300,
        maximum=1000,
        unit="nm",
        description="Absorbance wavelength for the plate reader.",
    )


def run(protocol: protocol_api.ProtocolContext):
    # Access runtime parameter for wavelength
    wavelength = protocol.params.wavelength
    protocol.comment(f"Using wavelength: {wavelength} nm")

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
