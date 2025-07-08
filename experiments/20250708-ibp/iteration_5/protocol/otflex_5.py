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

    hs_mod = protocol.load_module(module_name="heaterShakerModuleV1", location="D3")
    hs_adapter = hs_mod.load_adapter("opentrons_universal_flat_adapter")
    
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
    plate = protocol.load_labware(load_name="corning_96_wellplate_360ul_flat", location='D1')
    #plate = hs_adapter.load_labware("corning_96_wellplate_360ul_flat") #use this if the plate is already loaded on the shaker
    next_plate_well = 'B1'

    # load deep well plate in deck slot D2
    #deepplate = protocol.load_labware('allenlabresevoir_96_wellplate_2200ul', location = 'D2')
    deepplate = hs_adapter.load_labware("corning_96_wellplate_360ul_flat")
    next_deepplate_well = 'D2'

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
        
        
    surfactant_list = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8','water']#, 'S9','s10', 's11', 's12'] add this if more than 9 surfactants
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

    
    def hs(labware_to_shake, time, speed, orignial_location):  #only use when plate is not already on hs_adapter
    #def hs(time, speed):

        hs_mod.open_labware_latch()
        protocol.move_labware(labware=labware_to_shake, new_location=hs_adapter, use_gripper=True)
        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_shake_speed(speed)
        protocol.delay(minutes=time)
        hs_mod.deactivate_shaker()
        hs_mod.open_labware_latch()
        protocol.move_labware(labware=labware_to_shake, new_location=orignial_location, use_gripper=True)
    
    def plate_on_hs(labware_to_shake, new_location, speed, time):
        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_shake_speed(speed)
        protocol.delay(minutes=time)
        hs_mod.deactivate_shaker()
        hs_mod.open_labware_latch()
        protocol.move_labware(labware=labware_to_shake, new_location= new_location, use_gripper=True)



    # to be rewritten according to the exp design
########################################################################################################################################
    data = [
    {
        "": "0",
        "trial_index": "15.0",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "303.33333333333337",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "303.33333333333337",
        "s7": "0.0",
        "s8": "303.33333333333337",
        "dmso": "0.0",
        "water": "89.99999999999997"
    },
    {
        "": "1",
        "trial_index": "16.0",
        "drug": "180.0",
        "s1": "230.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "230.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "230.0",
        "s8": "230.0",
        "dmso": "0.0",
        "water": "79.99999999999996"
    },
    {
        "": "2",
        "trial_index": "17.0",
        "drug": "180.0",
        "s1": "225.0",
        "s2": "0.0",
        "s3": "225.0",
        "s4": "225.0",
        "s5": "0.0",
        "s6": "225.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "99.99999999999997"
    }
]
########################################################################################################################################
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
                pipette_high.flow_rate.dispense= 50
                air_gap_vol = 50 if pipette == pipette_high else 10
                hs_mod.close_labware_latch()
                pipette.transfer(vol, sources[item], deepplate[next_deepplate_well], new_tip='never', air_gap= air_gap_vol)
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
        
        pipette_high.pick_up_tip()
        pipette_high.flow_rate.dispense = 50
        pipette_high.transfer(270, deepplate[current_surfactant_well], plate[next_plate_well], new_tip='never', air_gap= 40)
        pipette_high.drop_tip()

        pipette_low.pick_up_tip()
        pipette_low.transfer(30, deepplate[current_drug_well], plate[next_plate_well], new_tip='never', air_gap= 10) 
        pipette_low.flow_rate.dispense = 25
        pipette_low.blow_out(plate[next_plate_well])
        pipette_low.touch_tip(plate[next_plate_well], v_offset=-3)
        pipette_low.drop_tip()

        current_exp_well = next_plate_well
        next_plate_well = next_well(next_plate_well)

        return current_exp_well, next_plate_well
    

    well_pairs = []
    for i in range(len(data)):
    #for i in [8,9,10]: 
    #use either the first or 2nd line, 1st line does range to first 8, 2nd line does the ones only listed in the brackets
        row_of_data = data[i]

        current_surfactant_well, next_deepplate_well = make_drug_or_surfactant(surfactant_list, next_deepplate_well, row_of_data)
        current_drug_well, next_deepplate_well = make_drug_or_surfactant(drug_list, next_deepplate_well, row_of_data)
        well_pairs.append((current_drug_well, current_surfactant_well))  

    
    plate_on_hs(labware_to_shake = deepplate, new_location = 'D2', speed= 1000, time = 1)
    protocol.move_labware(labware= plate, new_location=hs_adapter, use_gripper=True)
    hs_mod.close_labware_latch()


    for i in range(len(data)):
        row_of_data = data[i]
        
        current_drug_well, current_surfactant_well = well_pairs[i]

        #n=1
        current_exp_well, next_plate_well = make_exp(current_drug_well, current_surfactant_well, next_plate_well)

        #n=2
        current_exp_well, next_plate_well = make_exp(current_drug_well, current_surfactant_well, next_plate_well)

        #n=3
        #current_exp_well, next_plate_well = make_exp(current_drug_well, current_surfactant_well, next_plate_well)

    plate_on_hs(labware_to_shake=plate, time=1, speed=1000, new_location='D1') # time in minutes, speed in rpm
