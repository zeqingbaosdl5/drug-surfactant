from opentrons import protocol_api
import re

metadata = {
    "description": "Written on 2025.04.29",
    "author": "Zeqing Bao"
}

requirements = {"robotType": "Flex", "apiLevel": "2.19"}


def run(protocol: protocol_api.ProtocolContext):


    # robot setup
    # load 1000 uL tip rack in deck slot D2
    tip1000 = protocol.load_labware(load_name="opentrons_flex_96_filtertiprack_1000ul", location="B1")
    tip50 = protocol.load_labware(load_name="opentrons_flex_96_filtertiprack_50ul", location="B2")
    
    # attach pipette 
    pipette_low = protocol.load_instrument(instrument_name="flex_1channel_50", mount="right", tip_racks=[tip50])
    pipette_high = protocol.load_instrument(instrument_name="flex_1channel_1000", mount="left", tip_racks=[tip1000])

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
    next_deepplate_well = 'A2'

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
    

    # to be rewritten according to the exp design
################################################################################################################################################
    data = [{'': '0',
                'trial_index': '0',
                'drug': '103.2',
                's1': '53.868613138686136',
                's2': '71.82481751824818',
                's3': '0.0',
                's4': '35.91240875912409',
                's5': '119.70802919708028',
                's6': '11.970802919708028',
                's7': '5.985401459854014',
                's8': '41.89781021897811',
                's9': '107.73722627737227',
                's10': '95.76642335766422',
                's11': '107.73722627737227',
                's12': '107.73722627737227',
                'dmso': '16.799999999999997',
                'water': '179.99999999999994'},
                {'': '1',
                'trial_index': '1000',
                'drug': '2.4',
                's1': '48.71794871794872',
                's2': '17.948717948717952',
                's3': '25.641025641025642',
                's4': '43.58974358974359',
                's5': '25.641025641025642',
                's6': '33.333333333333336',
                's7': '38.46153846153846',
                's8': '25.641025641025642',
                's9': '12.820512820512821',
                's10': '7.692307692307692',
                's11': '20.512820512820515',
                's12': '0.0',
                'dmso': '117.6',
                'water': '700.0'},
                {'': '2',
                'trial_index': '2000',
                'drug': '64.8',
                's1': '64.51612903225806',
                's2': '96.77419354838709',
                's3': '12.903225806451614',
                's4': '32.25806451612903',
                's5': '19.35483870967742',
                's6': '122.58064516129035',
                's7': '38.70967741935484',
                's8': '122.58064516129035',
                's9': '0.0',
                's10': '32.25806451612903',
                's11': '19.35483870967742',
                's12': '38.70967741935484',
                'dmso': '55.199999999999996',
                'water': '400.0'},]

################################################################################################################################################

    def make_drug_or_surfactant(a_list, next_deepplate_well, row_of_data):

        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 35
            pipette.well_bottom_clearance.aspirate = 3     

        for n, item in enumerate(a_list):
            vol = float(row_of_data[item])
            pipette = pipette_selection(vol)
            pipette.pick_up_tip()
            if vol > 0:
                pipette = pipette_selection(vol)
                pipette.transfer(vol, sources[item], deepplate[next_deepplate_well], new_tip='never', air_gap= 10)
                pipette.blow_out(deepplate[next_deepplate_well])
            pipette.drop_tip()
        current_deepplate_well = next_deepplate_well
        next_deepplate_well = next_well(next_deepplate_well)

        if n == len(surfactant_list) - 1:
            pipette_high.pick_up_tip()
            pipette_high.mix(5, 100, deepplate[next_deepplate_well])
            pipette_high.drop_tip()

        return current_deepplate_well, next_deepplate_well


    def make_exp(current_drug_well, current_surfactant_well, next_plate_well):

        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 15
            pipette.well_bottom_clearance.aspirate = 3     

        pipette_low.pick_up_tip()
        pipette_low.transfer(30, deepplate[current_drug_well], plate[next_plate_well], new_tip='never', air_gap= 10)
        pipette_low.blow_out(plate[next_plate_well])
        pipette_low.drop_tip()

        pipette_high.pick_up_tip()
        pipette_high.transfer(270, deepplate[current_surfactant_well], plate[next_plate_well], new_tip='never', air_gap= 10)
        pipette_high.blow_out(plate[next_plate_well])

        pipette_high.mix(5, 100, plate[next_plate_well])
        pipette_high.drop_tip()

        current_exp_well = next_plate_well
        next_plate_well = next_well(next_plate_well)

        return current_exp_well, next_plate_well


    for i in range(len(data)):

        row_of_data = data[i]

        current_surfactant_well, next_deepplate_well = make_drug_or_surfactant(surfactant_list, next_deepplate_well, row_of_data)
        current_drug_well, next_deepplate_well = make_drug_or_surfactant(drug_list, next_deepplate_well, row_of_data)

        #n=1
        current_exp_well, next_plate_well = make_exp(current_drug_well, current_surfactant_well, next_plate_well)

        #n=2
        current_exp_well, next_plate_well = make_exp(current_drug_well, current_surfactant_well, next_plate_well)

        #n=3
        current_exp_well, next_plate_well = make_exp(current_drug_well, current_surfactant_well, next_plate_well)
