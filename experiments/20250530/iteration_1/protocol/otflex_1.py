from opentrons import protocol_api
import re

metadata = {
    "description": "Written in 2025.05",
    "author": "Zeqing Bao and Yunhee Hwang"
}

requirements = {"robotType": "Flex", "apiLevel": "2.19"}


def run(protocol: protocol_api.ProtocolContext):


    # robot setup
    # load 1000 uL tip rack in deck slot D2
    tip1000_1 = protocol.load_labware(load_name="opentrons_flex_96_filtertiprack_1000ul", location="B1")
    tip1000_2 = protocol.load_labware(load_name="opentrons_flex_96_filtertiprack_1000ul", location="A1")
    tip50 = protocol.load_labware(load_name="opentrons_flex_96_filtertiprack_50ul", location="B2")
    
    # attach pipette 
    pipette_low = protocol.load_instrument(instrument_name="flex_1channel_50", mount="right", tip_racks=[tip50])
    pipette_high = protocol.load_instrument(instrument_name="flex_1channel_1000", mount="left", tip_racks=[tip1000_1, tip1000_2])

    surfactant_stock_1 = protocol.load_labware(load_name="allenlab_8_wellplate_20000ul", location="C1")
    s1 = surfactant_stock_1['A1']
    s2 = surfactant_stock_1['A2']
    s3 = surfactant_stock_1['A3']
    s4 = surfactant_stock_1['A4']
    s5 = surfactant_stock_1['B1']
    s6 = surfactant_stock_1['B2']
    s7 = surfactant_stock_1['B3']
    s8 = surfactant_stock_1['B4']

    # load second stock plate with 4 surfactants + pyrene in deck slot C2
    surfactant_drug_dmso_stock_2 = protocol.load_labware(load_name="allenlab_8_wellplate_20000ul", location="C2")
    s9 = surfactant_drug_dmso_stock_2['A1']
    s10 = surfactant_drug_dmso_stock_2['A2']
    s11 = surfactant_drug_dmso_stock_2['A3']
    s12 = surfactant_drug_dmso_stock_2['A4']
    drug = surfactant_drug_dmso_stock_2['B1']
    dmso = surfactant_drug_dmso_stock_2['B2']

    # load water in deck slot C3
    water_res = protocol.load_labware('nest_1_reservoir_290ml','C3')
    water = water_res['A1']
    
    # load well plate in deck slot D1
    plate = protocol.load_labware(load_name="corning_96_wellplate_360ul_flat", location="D1")
    next_plate_well = 'B1'

    # load deep well plate in deck slot D2
    deepplate = protocol.load_labware('allenlabresevoir_96_wellplate_2200ul', location = 'D2')
    next_deepplate_well = 'B1'

    # trash bin
    trash = protocol.load_trash_bin(location="A3")

    sources = {
        's1': s1,
        's2': s2,
        's3': s3,
        's4': s4,
        's5': s5,
        's6': s6,
        's7': s7,
        's8': s8,
        's9': s9,
        's10': s10,
        's11': s11,
        's12': s12,
        'water': water,
        'drug': drug,
        'dmso': dmso,
    }
    

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
            if row == 'H':
                raise ValueError("Plate overflow: no more wells after H12")
            row = chr(ord(row) + 1)
        return f"{row}{col}"
        
        
    surfactant_list = ['water', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']
    drug_list = ['dmso', 'drug']
    

    def pipette_selection (vol):
        if vol <= 40:
            return pipette_low
        else:
            return pipette_high

    def modified_transfer(vol, pipette_selection, source_well, transfered_well, trash):
        buffer= 0.3 # buffer can be modified to change buffer volume
        m_vol= vol*(1+ buffer)
        pipette_selection.aspirate(m_vol, source_well)
        pipette_selection.flow_rate.dispense = 50 #can change rate if it is too fast
        pipette_selection.dispense(vol, transfered_well)
        pipette_selection.dispense (m_vol-vol, trash) 

    def run(protocol: protocol_api.ProtocolContext):
        labware = labware
        new_location =new_location
        protocol.move_labware(labware, new_location, use_gripper=True)
    
    def run(protocol: protocol_api.ProtocolContext):
     hs_mod = protocol.load_module('heaterShakerModuleV1', 1)



    # to be rewritten according to the exp design
########################################################################################################################################
    data = [
    {
        "": "0",
        "trial_index": "6.0",
        "drug": "93.6",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "1.6",
        "s4": "1.6",
        "s5": "0.912",
        "s6": "1.6",
        "s7": "1.088",
        "s8": "1.6",
        "s9": "1.6",
        "dmso": "26.400000000000006",
        "water": "990.0"
    },
    {
        "": "1",
        "trial_index": "7.0",
        "drug": "1.2",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "2.0",
        "s5": "0.0",
        "s6": "2.0",
        "s7": "2.0",
        "s8": "2.0",
        "s9": "2.0",
        "dmso": "118.79999999999998",
        "water": "990.0"
    },
    {
        "": "2",
        "trial_index": "8.0",
        "drug": "120.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "2.3980815347721824",
        "s4": "2.3980815347721824",
        "s5": "1.4148681055155876",
        "s6": "2.3980815347721824",
        "s7": "1.3908872901678655",
        "s8": "0.0",
        "s9": "0.0",
        "dmso": "0.0",
        "water": "990.0"
    },
    {
        "": "3",
        "trial_index": "9.0",
        "drug": "1.2",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "2.5",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "2.5",
        "s8": "2.5",
        "s9": "2.5",
        "dmso": "118.79999999999998",
        "water": "990.0"
    },
    {
        "": "4",
        "trial_index": "10.0",
        "drug": "120.0",
        "s1": "0.0",
        "s2": "1.4285714285714286",
        "s3": "1.4285714285714286",
        "s4": "1.4285714285714286",
        "s5": "0.0",
        "s6": "1.4285714285714286",
        "s7": "1.4285714285714286",
        "s8": "1.4285714285714286",
        "s9": "1.4285714285714286",
        "dmso": "0.0",
        "water": "990.0"
    },
    {
        "": "5",
        "trial_index": "11.0",
        "drug": "120.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "1.6897506925207757",
        "s6": "2.770083102493075",
        "s7": "2.770083102493075",
        "s8": "2.770083102493075",
        "s9": "0.0",
        "dmso": "0.0",
        "water": "990.0"
    }
]
########################################################################################################################################
################################################################################################################################################

    def make_drug_or_surfactant(a_list, next_deepplate_well, row_of_data):

        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 25
            pipette.well_bottom_clearance.aspirate = 3     

        for n, item in enumerate(a_list):
            vol = float(row_of_data[item])
            pipette = pipette_selection(vol)
            if vol > 0:
                pipette.pick_up_tip()
                pipette_high.flow_rate.dispense= 50
                ##modified_transfer(vol, pipette_selection=pipette, source_well=sources[item], transfered_well=deepplate[next_deepplate_well], trash=trash)
                air_gap_vol = 50 if pipette == pipette_high else 10
                pipette.transfer(vol, sources[item], deepplate[next_deepplate_well], new_tip='never', air_gap= air_gap_vol)
                pipette.blow_out(deepplate[next_deepplate_well])
                pipette.touch_tip(deepplate[next_deepplate_well], v_offset=-11)
                pipette.drop_tip()
        current_deepplate_well = next_deepplate_well
        next_deepplate_well = next_well(next_deepplate_well)

        if n == len(surfactant_list)-1:
            pipette_high.pick_up_tip()
            pipette_high.flow_rate.dispense = 50
            pipette_high.mix(5, 50, deepplate[current_deepplate_well].bottom(3))
            pipette_high.blow_out(deepplate[current_deepplate_well])
            pipette_high.touch_tip(deepplate[current_deepplate_well], v_offset=-7)
            pipette_high.drop_tip()
            #protocol.move_labware(labware=deepplate, new_location= "D3", use_gripper=True)#added speed don't know if it will work
        
        if n == len(drug_list)-1:
            pipette_high.pick_up_tip()
            pipette_high.flow_rate.dispense = 50
            pipette_high.mix(5, 50, deepplate[current_deepplate_well].bottom(3))
            pipette_high.blow_out(deepplate[current_deepplate_well])
            pipette_high.touch_tip(deepplate[current_deepplate_well], v_offset=-7)
            pipette_high.drop_tip()
            #protocol.move_labware(labware=deepplate, new_location= "D2", use_gripper=True)

        return current_deepplate_well, next_deepplate_well


        
    def make_exp(current_drug_well, current_surfactant_well, next_plate_well):

        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 13
            pipette.well_bottom_clearance.aspirate = 3     


        pipette_high.pick_up_tip()
        #modified_transfer(vol=270, pipette_selection=pipette_high, source_well=deepplate[current_surfactant_well], transfered_well=plate[next_plate_well], trash=trash)
        pipette_high.flow_rate.dispense = 50
        pipette_high.transfer(270, deepplate[current_surfactant_well], plate[next_plate_well], new_tip='never', air_gap= 40)
        pipette_high.drop_tip()

        pipette_low.pick_up_tip()
        #modified_transfer(vol=30, pipette_selection=pipette_low, source_well=deepplate[current_drug_well], transfered_well=plate[next_plate_well], trash=trash)
        pipette_low.transfer(30, deepplate[current_drug_well], plate[next_plate_well], new_tip='never', air_gap= 10)

        pipette_low.flow_rate.aspiration = 25 #the system keeps aspirating at 35 
        pipette_low.flow_rate.dispense = 25
        pipette_low.mix(5, 40, plate[next_plate_well].bottom(1))
        pipette_low.blow_out(plate[next_plate_well])
        pipette_low.touch_tip(plate[next_plate_well], v_offset=0)
        pipette_low.drop_tip()
        #protocol.move_labware(labware=plate, new_location= "D3", use_gripper=True)
        #protocol.move_labware(labware=plate, new_location= "D1", use_gripper=True)

        current_exp_well = next_plate_well
        next_plate_well = next_well(next_plate_well)

        return current_exp_well, next_plate_well


    for i in range(len(data)):
    #for i in [8,9,10]: 
    #use either the first or 2nd line, 1st line does range to first 8, 2nd line does the ones only listed in the brackets
        row_of_data = data[i]

        current_surfactant_well, next_deepplate_well = make_drug_or_surfactant(surfactant_list, next_deepplate_well, row_of_data)
        current_drug_well, next_deepplate_well = make_drug_or_surfactant(drug_list, next_deepplate_well, row_of_data)

        #n=1
        current_exp_well, next_plate_well = make_exp(current_drug_well, current_surfactant_well, next_plate_well)

        #n=2
        current_exp_well, next_plate_well = make_exp(current_drug_well, current_surfactant_well, next_plate_well)

        #n=3
        #current_exp_well, next_plate_well = make_exp(current_drug_well, current_surfactant_well, next_plate_well)
