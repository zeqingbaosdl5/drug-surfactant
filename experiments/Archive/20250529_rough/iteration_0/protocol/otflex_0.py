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
    next_plate_well = 'F1'

    # load deep well plate in deck slot D2
    deepplate = protocol.load_labware('allenlabresevoir_96_wellplate_2200ul', location = 'D2')
    next_deepplate_well = 'F1'

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
        
        
    surfactant_list = ['water', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 's12']
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
    data = [   {   '': '0',
        'dmso': '16.799999999999997',
        'drug': '103.2',
        's1': '56.65178571428571',
        's10': '91.60714285714286',
        's11': '107.27678571428571',
        's12': '106.07142857142858',
        's2': '71.11607142857142',
        's3': '59.0625',
        's4': '37.36607142857143',
        's5': '115.71428571428571',
        's6': '9.642857142857142',
        's7': '10.848214285714286',
        's8': '42.1875',
        's9': '102.45535714285714',
        'trial_index': '0.0',
        'water': '189.99999999999994'},
    {   '': '1',
        'dmso': '118.79999999999998',
        'drug': '1.2',
        's1': '45.10033444816054',
        's10': '9.698996655518393',
        's11': '17.458193979933107',
        's12': '2.424749163879598',
        's2': '18.428093645484946',
        's3': '24.24749163879598',
        's4': '40.735785953177256',
        's5': '24.24749163879598',
        's6': '31.521739130434774',
        's7': '37.826086956521735',
        's8': '25.702341137123742',
        's9': '12.608695652173912',
        'trial_index': '1.0',
        'water': '710.0000000000002'},
    {   '': '2',
        'dmso': '56.400000000000006',
        'drug': '63.59999999999999',
        's1': '64.69344608879491',
        's10': '35.51797040169133',
        's11': '20.29598308668076',
        's12': '38.05496828752642',
        's2': '97.67441860465118',
        's3': '16.49048625792812',
        's4': '30.443974630021142',
        's5': '24.1014799154334',
        's6': '119.23890063424946',
        's7': '34.24947145877378',
        's8': '116.70190274841438',
        's9': '2.536997885835095',
        'trial_index': '2.0',
        'water': '400.0'},
    {   '': '3',
        'dmso': '74.39999999999999',
        'drug': '45.599999999999994',
        's1': '1.509433962264151',
        's10': '14.150943396226413',
        's11': '10.943396226415095',
        's12': '11.88679245283019',
        's2': '3.773584905660378',
        's3': '16.60377358490566',
        's4': '13.58490566037736',
        's5': '13.773584905660377',
        's6': '6.79245283018868',
        's7': '11.320754716981135',
        's8': '3.9622641509433967',
        's9': '11.698113207547172',
        'trial_index': '3.0',
        'water': '880.0'},
    {   '': '4',
        'dmso': '97.19999999999999',
        'drug': '22.799999999999997',
        's1': '29.14179104477612',
        's10': '6.6231343283582085',
        's11': '9.272388059701491',
        's12': '74.17910447761193',
        's2': '123.19029850746269',
        's3': '99.34701492537312',
        's4': '68.88059701492537',
        's5': '71.52985074626866',
        's6': '31.791044776119403',
        's7': '64.90671641791045',
        's8': '101.99626865671642',
        's9': '29.14179104477612',
        'trial_index': '4.0',
        'water': '289.99999999999994'},
    {   '': '5',
        'dmso': '3.600000000000006',
        'drug': '116.39999999999999',
        's1': '25.94377510040161',
        's10': '37.00803212851406',
        's11': '25.18072289156627',
        's12': '14.497991967871487',
        's2': '3.8152610441767063',
        's3': '9.538152610441768',
        's4': '0.0',
        's5': '0.3815261044176706',
        's6': '21.365461847389557',
        's7': '24.41767068273092',
        's8': '3.8152610441767063',
        's9': '24.03614457831325',
        'trial_index': '5.0',
        'water': '810.0'}]
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
