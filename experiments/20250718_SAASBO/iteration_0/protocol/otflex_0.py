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
    ibp = surfactant_drug_dmso_stock_2['B1']
    lov = surfactant_drug_dmso_stock_2['B2']
    dcf = surfactant_drug_dmso_stock_2['B3']
    glv = surfactant_drug_dmso_stock_2['B4']

#    dmso = surfactant_drug_dmso_stock_2['B2']

    # load water in deck slot C3
    water_res = protocol.load_labware('nest_1_reservoir_290ml','C3')
    water = water_res['A1']
    
    # load well plate in deck slot D1
    plate = protocol.load_labware(load_name="corning_96_wellplate_360ul_flat", location='D1')
    #plate = hs_adapter.load_labware("corning_96_wellplate_360ul_flat") #use this if the plate is already loaded on the shaker
    next_plate_well = 'A1'

    # load deep well plate in deck slot D2
    #deepplate = protocol.load_labware('allenlabresevoir_96_wellplate_2200ul', location = 'D2')
    deepplate = hs_adapter.load_labware("corning_96_wellplate_360ul_flat")
    next_deepplate_well = 'A1'

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
        'IBP': ibp,
        'LOV': lov,
        'DCF': dcf,
        'GLV': glv,
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
            # if row == 'H':
            #     raise ValueError("Plate overflow: no more wells after H12")
            row = chr(ord(row) + 1)
        return f"{row}{col}"
        
        
    surfactant_list = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8','water']#, 'S9','s10', 's11', 's12'] add this if more than 9 surfactants
    drug_list = ['IBP', 'LOV', 'DCF', 'GLV']
    

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

    
    def hs(labware_to_shake, time, speed, new_location, original_location):  #only use when plate is not already on hs_adapter

        protocol.move_labware(labware=labware_to_shake, new_location=new_location, pick_up_offset={'x': 0, 'y': 0, 'z':-2}, drop_offset={'x': 0, 'y': 0, 'z': -5}, use_gripper=True)
        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_shake_speed(speed)
        protocol.delay(minutes=time)
        hs_mod.deactivate_shaker()
        hs_mod.open_labware_latch()
        protocol.move_labware(labware=labware_to_shake, new_location=original_location, pick_up_offset={'x': 0, 'y': 0, 'z':-2}, use_gripper=True)
    
    def plate_on_hs(labware_to_shake, new_location, speed, time):
        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_shake_speed(speed)
        protocol.delay(minutes=time)
        hs_mod.deactivate_shaker()
        hs_mod.open_labware_latch()
        protocol.move_labware(labware=labware_to_shake, new_location= new_location, pick_up_offset={'x': 0, 'y': 0, 'z':-2}, use_gripper=True)



    # to be rewritten according to the exp design
########################################################################################################################################
    data = [
    {
        "": "0",
        "trial_index": "0",
        "drug_name": "IBP",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "468.0",
        "s7": "240.0",
        "s8": "144.0",
        "dmso": "0.0",
        "water": "348.0",
        "IBP": "180.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "1",
        "trial_index": "1",
        "drug_name": "IBP",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "48.0",
        "s3": "612.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "480.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "59.99999999999983",
        "IBP": "180.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "2",
        "trial_index": "2",
        "drug_name": "LOV",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "12.0",
        "s6": "0.0",
        "s7": "672.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "515.9999999999999",
        "IBP": "0.0",
        "LOV": "180.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "3",
        "trial_index": "3",
        "drug_name": "LOV",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "408.00000000000006",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "168.0",
        "dmso": "0.0",
        "water": "623.9999999999999",
        "IBP": "0.0",
        "LOV": "180.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "4",
        "trial_index": "4",
        "drug_name": "DCF",
        "drug": "180.0",
        "s1": "324.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "755.9999999999999",
        "s5": "36.0",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "84.00000000000007",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "180.0",
        "GLV": "0.0"
    },
    {
        "": "5",
        "trial_index": "5",
        "drug_name": "DCF",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "480.0",
        "s7": "264.0",
        "s8": "348.0",
        "dmso": "0.0",
        "water": "107.99999999999987",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "180.0",
        "GLV": "0.0"
    },
    {
        "": "6",
        "trial_index": "6",
        "drug_name": "GLV",
        "drug": "180.0",
        "s1": "348.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "215.99999999999997",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "636.0",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "180.0"
    },
    {
        "": "7",
        "trial_index": "7",
        "drug_name": "GLV",
        "drug": "180.0",
        "s1": "431.99999999999994",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "12.0",
        "s6": "120.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "636.0",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "180.0"
    },
    {
        "": "8",
        "trial_index": "8",
        "drug_name": "IBP",
        "drug": "180.0",
        "s1": "600.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "227.99999999999997",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "372.0",
        "IBP": "180.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "9",
        "trial_index": "9",
        "drug_name": "IBP",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "444.0",
        "s4": "204.0",
        "s5": "384.0",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "167.99999999999991",
        "IBP": "180.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "10",
        "trial_index": "10",
        "drug_name": "LOV",
        "drug": "180.0",
        "s1": "360.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "684.0",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "155.99999999999991",
        "IBP": "0.0",
        "LOV": "180.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "11",
        "trial_index": "11",
        "drug_name": "LOV",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "324.0",
        "s4": "264.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "444.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "167.99999999999991",
        "IBP": "0.0",
        "LOV": "180.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "12",
        "trial_index": "12",
        "drug_name": "DCF",
        "drug": "180.0",
        "s1": "252.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "708.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "72.0",
        "dmso": "0.0",
        "water": "167.99999999999991",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "180.0",
        "GLV": "0.0"
    },
    {
        "": "13",
        "trial_index": "13",
        "drug_name": "DCF",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "120.0",
        "s3": "107.99999999999999",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "936.0",
        "dmso": "0.0",
        "water": "36.00000000000003",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "180.0",
        "GLV": "0.0"
    },
    {
        "": "14",
        "trial_index": "14",
        "drug_name": "GLV",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "192.0",
        "s4": "0.0",
        "s5": "264.0",
        "s6": "0.0",
        "s7": "204.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "539.9999999999999",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "180.0"
    },
    {
        "": "15",
        "trial_index": "15",
        "drug_name": "GLV",
        "drug": "180.0",
        "s1": "288.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "420.0",
        "s5": "371.99999999999994",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "120.00000000000011",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "180.0"
    },
    {
        "": "16",
        "trial_index": "16",
        "drug_name": "IBP",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "756.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "443.99999999999994",
        "IBP": "180.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "17",
        "trial_index": "17",
        "drug_name": "IBP",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "240.0",
        "s5": "0.0",
        "s6": "551.9999999999999",
        "s7": "0.0",
        "s8": "96.0",
        "dmso": "0.0",
        "water": "312.00000000000006",
        "IBP": "180.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "18",
        "trial_index": "18",
        "drug_name": "LOV",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "12.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "240.0",
        "s7": "0.0",
        "s8": "743.9999999999999",
        "dmso": "0.0",
        "water": "204.00000000000006",
        "IBP": "0.0",
        "LOV": "180.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "19",
        "trial_index": "19",
        "drug_name": "LOV",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "300.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "360.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "540.0",
        "IBP": "0.0",
        "LOV": "180.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "20",
        "trial_index": "20",
        "drug_name": "DCF",
        "drug": "180.0",
        "s1": "107.99999999999999",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "923.9999999999999",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "167.99999999999991",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "180.0",
        "GLV": "0.0"
    },
    {
        "": "21",
        "trial_index": "21",
        "drug_name": "DCF",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "491.99999999999994",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "671.9999999999999",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "36.00000000000003",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "180.0",
        "GLV": "0.0"
    },
    {
        "": "22",
        "trial_index": "22",
        "drug_name": "GLV",
        "drug": "180.0",
        "s1": "348.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "336.0",
        "s6": "468.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "48.00000000000004",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "180.0"
    },
    {
        "": "23",
        "trial_index": "23",
        "drug_name": "GLV",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "516.0",
        "s5": "635.9999999999999",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "48.00000000000004",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "180.0"
    },
    {
        "": "24",
        "trial_index": "24",
        "drug_name": "IBP",
        "drug": "180.0",
        "s1": "539.9999999999999",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "215.99999999999997",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "444.00000000000006",
        "IBP": "180.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "25",
        "trial_index": "25",
        "drug_name": "IBP",
        "drug": "180.0",
        "s1": "288.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "144.0",
        "s7": "0.0",
        "s8": "156.0",
        "dmso": "0.0",
        "water": "612.0",
        "IBP": "180.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "26",
        "trial_index": "26",
        "drug_name": "LOV",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "491.99999999999994",
        "s3": "252.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "396.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "59.99999999999983",
        "IBP": "0.0",
        "LOV": "180.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "27",
        "trial_index": "27",
        "drug_name": "LOV",
        "drug": "180.0",
        "s1": "564.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "12.0",
        "s7": "0.0",
        "s8": "612.0",
        "dmso": "0.0",
        "water": "12.00000000000001",
        "IBP": "0.0",
        "LOV": "180.0",
        "DCF": "0.0",
        "GLV": "0.0"
    },
    {
        "": "28",
        "trial_index": "28",
        "drug_name": "DCF",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "408.00000000000006",
        "s3": "0.0",
        "s4": "576.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "215.99999999999997",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "180.0",
        "GLV": "0.0"
    },
    {
        "": "29",
        "trial_index": "29",
        "drug_name": "DCF",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "228.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "60.0",
        "s6": "816.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "95.99999999999986",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "180.0",
        "GLV": "0.0"
    },
    {
        "": "30",
        "trial_index": "30",
        "drug_name": "GLV",
        "drug": "180.0",
        "s1": "384.0",
        "s2": "324.0",
        "s3": "0.0",
        "s4": "0.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "0.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "492.0",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "180.0"
    },
    {
        "": "31",
        "trial_index": "31",
        "drug_name": "GLV",
        "drug": "180.0",
        "s1": "0.0",
        "s2": "0.0",
        "s3": "0.0",
        "s4": "240.0",
        "s5": "0.0",
        "s6": "0.0",
        "s7": "780.0",
        "s8": "0.0",
        "dmso": "0.0",
        "water": "179.99999999999994",
        "IBP": "0.0",
        "LOV": "0.0",
        "DCF": "0.0",
        "GLV": "180.0"
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
                air_gap_vol = 50 if pipette == pipette_high else 10 #do air gap 50 for 1000uL tip
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
        
        replicate_wells = []
        for _ in range(3):  #Change this number to control the amount of replicates
            replicate_wells.append(next_plate_well)
            next_plate_well = next_well(next_plate_well)

        pipette_high.pick_up_tip()
        pipette_high.flow_rate.dispense = 50
        for well in replicate_wells:
            pipette_high.transfer(270, deepplate[current_surfactant_well], plate[well], new_tip='never', air_gap= 50) #do air gap 50 for 1000uL tip
            pipette_high.touch_tip(plate[well], v_offset=-3)
        pipette_high.drop_tip()


        pipette_low.pick_up_tip()
        for well in replicate_wells:
            pipette_low.transfer(30, deepplate[current_drug_well], plate[well], new_tip='never', air_gap= 10) 
            pipette_low.flow_rate.dispense = 25
            pipette_low.blow_out(plate[well])
            pipette_low.touch_tip(plate[well], v_offset=-3)
        pipette_low.drop_tip()
        

        return next_plate_well
    

    well_pairs = []
    for i in range(len(data)):
    #for i in [8,9,10]: 
    #use either the first or 2nd line, 1st line does range to first 8, 2nd line does the ones only listed in the brackets
        row_of_data = data[i]

        current_surfactant_well, next_deepplate_well = make_drug_or_surfactant(surfactant_list, next_deepplate_well, row_of_data)
        current_drug_well, next_deepplate_well = make_drug_or_surfactant(drug_list, next_deepplate_well, row_of_data)
        well_pairs.append((current_drug_well, current_surfactant_well))  

    
    plate_on_hs(labware_to_shake = deepplate, new_location = 'D2', speed= 1000, time = 1)  # Changed to 5 mins of shaking
    protocol.move_labware(labware= plate, new_location=hs_adapter, pick_up_offset={'x': 0, 'y': 0, 'z':-2}, drop_offset={'x': 0, 'y': 0, 'z': -5}, use_gripper=True)
    hs_mod.close_labware_latch()


    for i in range(len(data)):
        row_of_data = data[i]
        current_drug_well, current_surfactant_well = well_pairs[i]

        next_plate_well = make_exp(current_drug_well, current_surfactant_well, next_plate_well)
        

    plate_on_hs(labware_to_shake=plate, new_location='D1', time=5, speed=1000) # time in minutes, speed in rpm
