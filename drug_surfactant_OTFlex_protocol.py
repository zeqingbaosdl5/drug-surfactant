from opentrons import protocol_api

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

    # load well plate in deck slot D1
    plate = protocol.load_labware(load_name="corning_96_wellplate_360ul_flat", location="D1")

    # load deep well plate in deck slot D2
    deepplate = protocol.load_labware('allenlabresevoir_96_wellplate_2200ul', location = 'D2')


    # load first stock plate with 8 surfactants in deck slot C1
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
    

    # to be rewritten according to the exp design
################################################################################################################################################

    exp_list = {'exp1': {'surfactant_mix_stock_vols': {'T80': 195.52909090909085, 'CHAPS': 83.7981818181818, 'None_3': 0, 'water': 1520.6727272727273}, 'solvent_mix_vol': [32.67, 46.2, 65.34, 73.51, 83.31, 93.11, 102.91, 112.71, 122.51, 147.02, 207.91, 294.03], 'water_vol': [264.33, 250.8, 231.66, 223.49, 213.69, 203.89, 194.09, 184.29, 174.49, 149.98, 89.09, 2.97], 'pyrene_vol': [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]}, 'exp2': {'surfactant_mix_stock_vols': {'NaC': 1200.0, 'None_2': 0, 'None_3': 0, 'water': 600.0}, 'solvent_mix_vol': [32.67, 46.2, 65.34, 73.51, 83.31, 93.11, 102.91, 112.71, 122.51, 147.01, 207.91, 294.03], 'water_vol': [264.33, 250.8, 231.66, 223.49, 213.69, 203.89, 194.09, 184.29, 174.49, 149.99, 89.09, 2.97], 'pyrene_vol': [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]}, 'exp3': {'surfactant_mix_stock_vols': {'BAC': 146.70545454545453, 'SDS': 586.8218181818181, 'None_3': 0, 'water': 1066.4727272727273}, 'solvent_mix_vol': [32.67, 46.2, 65.34, 73.51, 83.31, 93.11, 102.91, 112.71, 122.51, 147.01, 207.91, 294.03], 'water_vol': [264.33, 250.8, 231.66, 223.49, 213.69, 203.89, 194.09, 184.29, 174.49, 149.99, 89.09, 2.97], 'pyrene_vol': [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]}}

    solvent_mix_loc = 'C1'
    row = 'A'

################################################################################################################################################


    def CMC_surfactant_combo (exp, solvent_mix_loc):

        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 40
            pipette.well_bottom_clearance.aspirate = 3        

        for key in exp['surfactant_mix_stock_vols'].keys():
            vol = exp['surfactant_mix_stock_vols'][key]
            
            if 0 < vol < 40:
                pipette = pipette_low
            else:
                pipette = pipette_high

            pipette.flow_rate.aspirate = max(1, vol)
            pipette.flow_rate.dispense = max(1, vol)

            
            if vol > 0:
                pipette.pick_up_tip()
                pipette.transfer(vol,
                    sources[key], deepplate[solvent_mix_loc], new_tip='never', air_gap= vol/20,
                    # blow_out=True,
                    # blow_out_location='destination well',
                )
                
#                pipette.touch_tip(deepplate[solvent_mix_loc])
                pipette.drop_tip()

    def CMC_surfactant_combo_mix (solvent_mix_loc):

        pipette_high.flow_rate.aspirate = 100
        pipette_high.flow_rate.dispense = 100
        pipette_high.well_bottom_clearance.dispense = 12
        pipette_high.well_bottom_clearance.aspirate = 12

        pipette_high.pick_up_tip(tip1000)

        pipette_high.mix(10, 100, deepplate[solvent_mix_loc])
#        pipette_high.blow_out(deepplate[solvent_mix_loc])
        pipette_high.drop_tip()



    def process_a_row(row, vols, source, destination, touch_tip):

        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 15
            pipette.well_bottom_clearance.aspirate = 3

        def pipette_selection (vol):
            if vol <= 40:
                return pipette_low
            else:
                return pipette_high
    
        last_pipette = None
        for i, vol in enumerate(vols):
            new_pipette = pipette_selection(vol)

            if new_pipette != last_pipette:
                if last_pipette and last_pipette.has_tip:
                    last_pipette.drop_tip()
                new_pipette.pick_up_tip()

            if vol>0:
                new_pipette.flow_rate.aspirate = max(1, vol)
                new_pipette.flow_rate.dispense = max(1, vol)
                new_pipette.flow_rate.blow_out = max(5, vol * 5)


            transfer_repeat = int((vol // 200) + 1)

            for _ in range(transfer_repeat):
                new_pipette.transfer(vol/transfer_repeat, source, destination[row + str(i+1)], new_tip='never', air_gap=(vol/transfer_repeat)/10, 
            #                         blow_out=True, blow_out_location='destination well'
                                     )
                if touch_tip:
                    new_pipette.touch_tip(destination[row + str(i+1)])

            last_pipette = new_pipette

        if last_pipette and last_pipette.has_tip:
            last_pipette.drop_tip()


    def CMC (exp, row, solvent_mix_loc):
        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 11
            pipette.well_bottom_clearance.aspirate = 3
        process_a_row(row, exp['water_vol'], water, plate, touch_tip=1)
        process_a_row(row, exp['pyrene_vol'], pyrene, plate, touch_tip=1)
        process_a_row(row, exp['solvent_mix_vol'], deepplate[solvent_mix_loc], plate, touch_tip=1)


    def next_well(well):
        import re
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


    ##########################################  no pipette change just for test  #############################################
    def CMC_mix_row(row):

        pipette_high.flow_rate.aspirate = 100
        pipette_high.flow_rate.dispense = 100

        pipette_high.pick_up_tip(tip1000)
        for col in range(1, 13):
            pipette_high.mix(5, 50, plate[row + str(col)])
        pipette_high.drop_tip()


    # Run the exps
    for exp_key in exp_list.keys():
        exp = exp_list[exp_key]

        # prepare surfactant combo
        CMC_surfactant_combo(exp, solvent_mix_loc)

        # mix the surfactant combo
        CMC_surfactant_combo_mix(solvent_mix_loc)

        # prepare cmc dilutions
        CMC(exp, row, solvent_mix_loc)

        # mix the cmc dilutions
        CMC_mix_row(row)

        # move to next well for solvent mix
        solvent_mix_loc = next_well(solvent_mix_loc)

        # move to next row for cmc dilutions
        row = chr(ord(row) + 1)

