from opentrons import protocol_api

metadata = {
    "description": "Minimal runtime param test",
    "author": "Copilot",
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
        description="Test wavelength parameter",
    )


def run(protocol: protocol_api.ProtocolContext):

    for variable_name, value in protocol.params.get_all().items():
        protocol.comment(f"variable {variable_name} has value {value}")

    # # Access runtime parameter
    # wavelength = protocol.params.wavelength
    # # Print to robot logs so we can verify via /logs/api.log
    # print(f"RUNTIME_PARAM_WAVELENGTH={wavelength}")
    # # do nothing else
    return
