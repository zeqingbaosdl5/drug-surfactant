import re
import os

SIMULATION_MODE = os.getenv("SIMULATION_MODE", "true").lower() == "true"

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

protocol.home()

pr_mod = protocol.load_module(module_name="absorbanceReaderV1", location="C3")


pr_mod.close_lid()
pr_mod.initialize(
    mode="single", wavelengths=[600]
)  # can add (reference_wavelength=) for normalization (reference wavelenth data will be subtracted from wavelength indicated)
pr_mod.open_lid()
protocol.move_labware(labware=labware_to_read, new_location=pr_mod, use_gripper=True)
pr_mod.close_lid()
pr_data = pr_mod.read()
pr_data[600]["A1"]
pr_data = pr_mod.read(export_filename="raw_absorbance_in")  # CSV file
pr_mod.open_lid()
protocol.move_labware(
    labware=labware_to_read, new_location=new_location, use_gripper=True
)


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
    for _ in range(3):  # Change this number to control the amount of replicates
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
            air_gap=50,
        )  # do air gap 50 for 1000uL tip
        pipette_high.touch_tip(plate[well], v_offset=-3)
    pipette_high.drop_tip()

    pipette_low.pick_up_tip()
    for well in replicate_wells:
        pipette_low.transfer(
            30, deepplate[current_drug_well], plate[well], new_tip="never", air_gap=10
        )
        pipette_low.flow_rate.dispense = 25
        pipette_low.blow_out(plate[well])
        pipette_low.touch_tip(plate[well], v_offset=-3)
    pipette_low.drop_tip()

    return next_plate_well


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


for i in range(len(data)):
    row_of_data = data[i]
    current_drug_well, current_surfactant_well = well_pairs[i]

    next_plate_well = make_exp(
        current_drug_well, current_surfactant_well, next_plate_well
    )


plate_on_hs_to_reader(
    labware_to_shake=plate, time=0.25, speed=1000
)  # time in minutes, speed in rpm
plate_on_pr(labware_to_read=plate, new_location="D1")
