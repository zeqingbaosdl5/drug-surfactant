from opentrons import protocol_api
import re

metadata = {
    "description": "Written in 2025.05",
    "author": "Zeqing Bao and Yunhee Hwang",
}

requirements = {"robotType": "Flex", "apiLevel": "2.23"}

#parameters are needed to tell the expected values to Optentons
def add_parameters(parameters: protocol_api.Parameters):
    parameters.add_float(
        display_name="drug",
        variable_name="drug",
        default=180.0,
        minimum=180.0,
        maximum=180.0,
    )
    parameters.add_float(
        display_name="s1",
        variable_name="s1",
        default=300.0,
        minimum=0.0,
        maximum=1200.0,
    )
    parameters.add_float(
        display_name="s2",
        variable_name="s2",
        default=0.0,
        minimum=0.0,
        maximum=1200.0,
    )
    parameters.add_float(
        display_name="s3",
        variable_name="s3",
        default=0.0,
        minimum=0.0,
        maximum=1200.0,
    )
    parameters.add_float(
        display_name="s4",
        variable_name="s4",
        default=300.0,
        minimum=0.0,
        maximum=1200.0,
    )
    parameters.add_float(
        display_name="s5",
        variable_name="s5",
        default=0.0,
        minimum=0.0,
        maximum=1200.0,
    )
    parameters.add_float(
        display_name="s6",
        variable_name="s6",
        default=0.0,
        minimum=0.0,
        maximum=1200.0,
    )
    parameters.add_float(
        display_name="s7",
        variable_name="s7",
        default=0.0,
        minimum=0.0,
        maximum=1200.0,
    )
    parameters.add_float(
        display_name="s8",
        variable_name="s8",
        default=0.0,
        minimum=0.0,
        maximum=1200.0,
    )
    parameters.add_float(
        display_name="dmso",
        variable_name="dmso",
        default=0.0,
        minimum=0.0,
        maximum=0.0,# 0 as we are using maxium drug concentration
    )
    parameters.add_float(
        display_name="water",
        variable_name="water",
        default=550.0,
        minimum=0.0,
        maximum=1200.0,
    )
    parameters.add_float(
        display_name="IBP",
        variable_name="IBP",
        default=180.0,
        minimum=180.0,
        maximum=180.0,
    )
    parameters.add_float(
        display_name="LOV",
        variable_name="LOV",
        default=0.0,
        minimum=0.0,
        maximum=180.0,
    )
    parameters.add_float(
        display_name="DCF",
        variable_name="DCF",
        default=0.0,
        minimum=0.0,
        maximum=180.0,
    )
    parameters.add_float(
        display_name="GLV",
        variable_name="GLV",
        default=0.0,
        minimum=0.0,
        maximum=180.0,
    )
    parameters.add_int(
        display_name="replicates",
        variable_name="replicates",
        default=3,
        minimum=1,
        maximum=12,
    )
    parameters.add_int(
    variable_name="iteration",
    display_name="Iteration",
    default=0,
    minimum=0,
    maximum=10000,
    )
    well_choices = [
        {"display_name": well, "value": well}
        for well in [f"{row}{col}" for row in "ABCDEFGH" for col in range(1, 13)]
    ]
    parameters.add_str(
        variable_name="next_plate_well",
        display_name="Next Plate Well",
        choices=well_choices,
        default="A1",
    )
    parameters.add_str(
        variable_name="next_deepplate_well",
        display_name="Next Deepplate Well",
        choices=well_choices,
        default="A1",
    )


def run(protocol: protocol_api.ProtocolContext):

    # robot setup
    protocol.comment("Setting up robot: loading tip racks, modules, and instruments.")
    # load 1000 uL tip rack in deck slot D2
    tip1000_1 = protocol.load_labware(
        load_name="opentrons_flex_96_filtertiprack_1000ul", location="B1"
    )
    tip1000_2 = protocol.load_labware(
        load_name="opentrons_flex_96_filtertiprack_1000ul", location="A1"
    )
    tip50 = protocol.load_labware(
        load_name="opentrons_flex_96_filtertiprack_50ul", location="B2"
    )

    hs_mod = protocol.load_module(module_name="heaterShakerModuleV1", location="D3")
    hs_adapter = hs_mod.load_adapter("opentrons_universal_flat_adapter")

    pr_mod = protocol.load_module(module_name="absorbanceReaderV1", location="C3")

    # attach pipette
    pipette_low = protocol.load_instrument(
        instrument_name="flex_1channel_50", mount="right", tip_racks=[tip50]
    )
    pipette_high = protocol.load_instrument(
        instrument_name="flex_1channel_1000",
        mount="left",
        tip_racks=[tip1000_1, tip1000_2],
    )

    surfactant_stock_1 = protocol.load_labware(
        load_name="allenlab_8_wellplate_20000ul", location="C1"
    )
    s1 = surfactant_stock_1["A1"]
    s2 = surfactant_stock_1["A2"]
    s3 = surfactant_stock_1["A3"]
    s4 = surfactant_stock_1["A4"]
    s5 = surfactant_stock_1["B1"]
    s6 = surfactant_stock_1["B2"]
    s7 = surfactant_stock_1["B3"]
    s8 = surfactant_stock_1["B4"]

    # load second stock plate with 4 surfactants + pyrene in deck slot C2
    surfactant_drug_dmso_stock_2 = protocol.load_labware(
        load_name="allenlab_8_wellplate_20000ul", location="C2"
    )
    #    s9 = surfactant_drug_dmso_stock_2['A1']
    #    s10 = surfactant_drug_dmso_stock_2['A2']
    #    s11 = surfactant_drug_dmso_stock_2['A3']
    #    s12 = surfactant_drug_dmso_stock_2['A4']
    ibp = surfactant_drug_dmso_stock_2["B1"]
    lov = surfactant_drug_dmso_stock_2["B2"]
    dcf = surfactant_drug_dmso_stock_2["B3"]
    glv = surfactant_drug_dmso_stock_2["B4"]

    #    dmso = surfactant_drug_dmso_stock_2['B2']

    # load water in deck slot C3
    # water_res = protocol.load_labware('nest_1_reservoir_290ml','C3')
    water = surfactant_drug_dmso_stock_2["A1"]

    # load well plate in deck slot D1
    plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat_new", location="D1"
    )
    # plate = hs_adapter.load_labware("corning_96_wellplate_360ul_flat") #use this if the plate is already loaded on the shaker
    next_plate_well = protocol.params.next_plate_well

    # load deep well plate in deck slot D2
    # deepplate = protocol.load_labware('allenlabresevoir_96_wellplate_2200ul', location = 'D2')
    deepplate = hs_adapter.load_labware("corning_96_wellplate_360ul_flat_new")
    next_deepplate_well = protocol.params.next_deepplate_well

    # trash bin
    trash = protocol.load_trash_bin(location="A3")

    sources = {
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "s4": s4,
        "s5": s5,
        "s6": s6,
        "s7": s7,
        "s8": s8,
        #   's9': s9,
        #   's10': s10,
        #   's11': s11,
        #   's12': s12,
        "water": water,
        "IBP": ibp,
        "LOV": lov,
        "DCF": dcf,
        "GLV": glv,
    }

    protocol.comment("Labware loaded. Starting experiment preparation.")

    def next_well(well):
        match = re.match(r"([A-H])(\d+)", well)
        if not match:
            raise ValueError(f"Invalid well format: {well}")

        row, col = match.groups()
        col = int(col)

        if col < 12:
            col += 1
        else:
            col = 1
            # if row == 'H':
            #     raise ValueError("Plate overflow: no more wells after H12")
            row = chr(ord(row) + 1)
        return f"{row}{col}"

    surfactant_list = [
        "s1",
        "s2",
        "s3",
        "s4",
        "s5",
        "s6",
        "s7",
        "s8",
        "water",
    ]  # , 'S9','s10', 's11', 's12'] add this if more than 9 surfactants
    drug_list = ["IBP", "LOV", "DCF", "GLV"]

    def pipette_selection(vol):
        if vol <= 40:
            return pipette_low
        else:
            return pipette_high

    def plate_on_hs(labware_to_shake, new_location, speed, time):
        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_shake_speed(speed)
        protocol.delay(minutes=time)
        hs_mod.deactivate_shaker()
        hs_mod.open_labware_latch()
        protocol.move_labware(
            labware=labware_to_shake,
            new_location=new_location,
            pick_up_offset={"x": 0, "y": 0, "z": -2},
            use_gripper=True,
        )

    def plate_on_hs_to_reader(labware_to_shake, speed, time):
        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_shake_speed(speed)
        protocol.delay(minutes=time)
        hs_mod.deactivate_shaker()
        hs_mod.open_labware_latch()

    def plate_on_pr(labware_to_read, new_location):
        pr_mod.close_lid()
        pr_mod.initialize(
            mode="single", wavelengths=[600]
        )  # can add (reference_wavelength=) for normalization (reference wavelenth data will be subtracted from wavelength indicated)
        pr_mod.open_lid()
        protocol.move_labware(
            labware=labware_to_read, new_location=pr_mod, use_gripper=True
        )
        pr_mod.close_lid()
        pr_data = pr_mod.read()
        pr_data[600]["A1"]
        pr_data = pr_mod.read(export_filename=f"raw_absorbance_i{protocol.params.iteration}")  # CSV file
        pr_mod.open_lid()
        protocol.move_labware(
            labware=labware_to_read, new_location=new_location, use_gripper=True
        )

    # to be rewritten according to the exp design
    ################################################################################################################################################
    data = [
        {
            "": "0",
            "trial_index": "0",
            "drug_name": "IBP",
            "drug": str(protocol.params.drug),
            "s1": str(protocol.params.s1),
            "s2": str(protocol.params.s2),
            "s3": str(protocol.params.s3),
            "s4": str(protocol.params.s4),
            "s5": str(protocol.params.s5),
            "s6": str(protocol.params.s6),
            "s7": str(protocol.params.s7),
            "s8": str(protocol.params.s8),
            "dmso": str(protocol.params.dmso),
            "water": str(protocol.params.water),
            "IBP": str(protocol.params.IBP),
            "LOV": str(protocol.params.LOV),
            "DCF": str(protocol.params.DCF),
            "GLV": str(protocol.params.GLV),
        },
    ]

    ################################################################################################################################################

    def make_drug_or_surfactant(a_list, next_deepplate_well, row_of_data):

        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 25
            pipette.well_bottom_clearance.aspirate = 2

        for n, item in enumerate(a_list):
            vol = float(row_of_data[item])
            pipette = pipette_selection(vol)
            if vol > 0:
                pipette.pick_up_tip()
                pipette_high.flow_rate.dispense = 50
                air_gap_vol = (
                    55 if pipette == pipette_high else 10
                )  # do air gap 50 for 1000uL tip
                hs_mod.close_labware_latch()
                pipette.transfer(
                    vol,
                    sources[item],
                    deepplate[next_deepplate_well],
                    new_tip="never",
                    air_gap=air_gap_vol,
                )
                pipette.blow_out(deepplate[next_deepplate_well].bottom(z=25))
                pipette.touch_tip(deepplate[next_deepplate_well], v_offset=15)
                pipette.drop_tip()

        current_deepplate_well = next_deepplate_well
        next_deepplate_well = next_well(next_deepplate_well)

        return current_deepplate_well, next_deepplate_well

    def make_exp(current_drug_well, current_surfactant_well, next_plate_well):

        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 13
            pipette.well_bottom_clearance.aspirate = 2

        replicate_wells = []
        for _ in range(protocol.params.replicates):
            replicate_wells.append(next_plate_well)
            next_plate_well = next_well(next_plate_well)

        pipette_high.pick_up_tip()
        pipette_high.flow_rate.dispense = 50
        for well in replicate_wells:
            pipette_high.transfer(
                270,
                deepplate[current_surfactant_well],
                plate[well],
                new_tip="never",
                air_gap=60,
            )  # do air gap 60 for 1000uL tip
            pipette_high.touch_tip(plate[well], v_offset=-3)
        pipette_high.drop_tip()

        pipette_low.pick_up_tip()
        for well in replicate_wells:
            pipette_low.transfer(
                30,
                deepplate[current_drug_well],
                plate[well],
                new_tip="never",
                air_gap=10,
            )
            pipette_low.flow_rate.dispense = 25
            pipette_low.blow_out(plate[well])
            pipette_low.touch_tip(plate[well], v_offset=-3)
        pipette_low.drop_tip()

        return next_plate_well

    ################################################################################################################################################

    protocol.comment("Preparing drug and surfactant mixtures in deep well plate.")
    well_pairs = []
    for i in range(len(data)):
        # for i in [8,9,10]:
        # use either the first or 2nd line, 1st line does range to first 8, 2nd line does the ones only listed in the brackets
        row_of_data = data[i]

        current_surfactant_well, next_deepplate_well = make_drug_or_surfactant(
            surfactant_list, next_deepplate_well, row_of_data
        )
        current_drug_well, next_deepplate_well = make_drug_or_surfactant(
            drug_list, next_deepplate_well, row_of_data
        )
        well_pairs.append((current_drug_well, current_surfactant_well))

    protocol.comment("Shaking deep well plate to mix components.")
    plate_on_hs(
        labware_to_shake=deepplate, new_location="D2", speed=1000, time=0.25
    )  # Changed to 5 mins of shaking
    protocol.move_labware(
        labware=plate,
        new_location=hs_adapter,
        pick_up_offset={"x": 0, "y": 0, "z": -2},
        drop_offset={"x": 0, "y": 0, "z": -5},
        use_gripper=True,
    )
    hs_mod.close_labware_latch()

    protocol.comment("Pipetting mixtures to experimental plate.")
    for i in range(len(data)):
        row_of_data = data[i]
        current_drug_well, current_surfactant_well = well_pairs[i]

        next_plate_well = make_exp(
            current_drug_well, current_surfactant_well, next_plate_well
        )

    protocol.comment("Shaking experimental plate before measurement.")
    plate_on_hs_to_reader(
        labware_to_shake=plate, time=0.25, speed=1000
    )  # time in minutes, speed in rpm
    protocol.comment("Measuring absorbance.")
    plate_on_pr(labware_to_read=plate, new_location="D1")
    protocol.move_labware(
            labware=deepplate, new_location=hs_adapter, use_gripper=True
        )
    pr_mod.close_lid()

