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
    deepplate = protocol.load_labware('corning_96_wellplate_360ul_flat', location = 'D2')
    #deepplate = hs_adapter.load_labware("corning_96_wellplate_360ul_flat")
    next_deepplate_well = 'G9'

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

    
    def plate_on_hs_2(labware_to_shake, time_1, speed_1, new_location):  #only use when plate is not already on hs_adapter
    #def hs(time, speed):

        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_shake_speed(speed_1)
        protocol.delay(minutes=time_1)
        #hs_mod.deactivate_shaker()
        #protocol.delay(minutes=time_2)
        #hs_mod.set_and_wait_for_shake_speed(speed_3)
        #protocol.delay(minutes=time_3)
        #hs_mod.deactivate_shaker()
        #protocol.delay(minutes=time_4)
        hs_mod.deactivate_shaker()
        hs_mod.open_labware_latch()
        protocol.move_labware(labware=labware_to_shake, new_location=new_location, use_gripper=True)
    
    def plate_on_hs(labware_to_shake, new_location, speed, time):
        hs_mod.close_labware_latch()
        hs_mod.set_and_wait_for_shake_speed(speed)
        protocol.delay(minutes=time)
        hs_mod.deactivate_shaker()
        hs_mod.open_labware_latch()
        protocol.move_labware(labware=labware_to_shake, new_location= new_location, use_gripper=True)



    # to be rewritten according to the exp design

########################################################################################################################################
################################################################################################################################################
    
    
    hs_mod.open_labware_latch()
    #z=-8 is max for pick up, z for drop should be -3 units less than z for pick up to place on hs surface
    protocol.move_labware(labware=plate, new_location=hs_adapter,pick_up_offset={'x': 0, 'y': 0, 'z':-2}, drop_offset={'x': 0, 'y': 0, 'z': -5}, use_gripper=True)
    hs_mod.close_labware_latch()

    hs_mod.open_labware_latch()
    protocol.move_labware(labware=plate, pick_up_offset={'x': 0, 'y': 0, 'z': -3}, new_location='D1', use_gripper=True)
    
    
   
    protocol.move_labware(labware=deepplate, new_location=hs_adapter, pick_up_offset={'x': 0, 'y': 0, 'z': -2}, drop_offset={'x': 0, 'y': 0, 'z': -5}, use_gripper=True)
    hs_mod.close_labware_latch()

    hs_mod.open_labware_latch()
    protocol.move_labware(labware=deepplate, new_location='D2', pick_up_offset={'x': 0, 'y': 0, 'z': -2}, use_gripper=True)
    
    

    #protocol.drop_offset (z=0)
    #protocol.pick_up_offset(z=0)
    
    
   