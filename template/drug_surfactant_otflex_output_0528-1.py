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
    next_plate_well = 'D1'

    # load deep well plate in deck slot D2
    deepplate = protocol.load_labware('allenlabresevoir_96_wellplate_2200ul', location = 'D2')
    next_deepplate_well = 'C3'

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
        'dmso': '67.2',
        'drug': '52.79999999999999',
        's1': '60.294117647058826',
        's10': '90.44117647058822',
        's11': '108.52941176470588',
        's12': '108.52941176470588',
        's2': '66.32352941176471',
        's3': '60.294117647058826',
        's4': '42.205882352941174',
        's5': '120.58823529411765',
        's6': '12.058823529411764',
        's7': '6.029411764705882',
        's8': '42.205882352941174',
        's9': '102.5',
        'trial_index': '0.0',
        'water': '179.99999999999994'},
    {   '': '1',
        'dmso': '117.6',
        'drug': '2.4',
        's1': '48.305084745762706',
        's10': '7.627118644067798',
        's11': '17.796610169491526',
        's12': '0.0',
        's2': '20.338983050847457',
        's3': '25.423728813559322',
        's4': '43.220338983050844',
        's5': '25.423728813559322',
        's6': '33.05084745762712',
        's7': '40.67796610169491',
        's8': '27.966101694915253',
        's9': '10.169491525423728',
        'trial_index': '1.0',
        'water': '700.0'},
    {   '': '2',
        'dmso': '86.4',
        'drug': '33.6',
        's1': '66.66666666666667',
        's10': '33.333333333333336',
        's11': '20.0',
        's12': '40.0',
        's2': '100.0',
        's3': '20.0',
        's4': '26.666666666666668',
        's5': '26.666666666666668',
        's6': '126.66666666666667',
        's7': '33.333333333333336',
        's8': '126.66666666666667',
        's9': '0.0',
        'trial_index': '2.0',
        'water': '379.9999999999999'},
    {   '': '3',
        'dmso': '96.0',
        'drug': '24.0',
        's1': '1.8604651162790697',
        's10': '13.953488372093023',
        's11': '11.162790697674419',
        's12': '12.093023255813954',
        's2': '3.7209302325581395',
        's3': '16.744186046511626',
        's4': '13.953488372093023',
        's5': '13.953488372093023',
        's6': '6.511627906976744',
        's7': '11.162790697674419',
        's8': '3.7209302325581395',
        's9': '11.162790697674419',
        'trial_index': '3.0',
        'water': '880.0'},
    {   '': '4',
        'dmso': '108.0',
        'drug': '12.0',
        's1': '33.64485981308411',
        's10': '6.728971962616822',
        's11': '6.728971962616822',
        's12': '74.01869158878505',
        's2': '127.8504672897196',
        's3': '100.93457943925233',
        's4': '67.28971962616822',
        's5': '74.01869158878505',
        's6': '26.91588785046729',
        's7': '67.28971962616822',
        's8': '107.66355140186916',
        's9': '26.91588785046729',
        'trial_index': '4.0',
        'water': '280.0000000000001'},
    {   '': '5',
        'dmso': '62.4',
        'drug': '57.6',
        's1': '28.282828282828284',
        's10': '40.40404040404041',
        's11': '26.262626262626263',
        's12': '14.141414141414142',
        's2': '4.0404040404040416',
        's3': '10.101010101010102',
        's4': '0.0',
        's5': '0.0',
        's6': '22.22222222222222',
        's7': '24.242424242424242',
        's8': '4.0404040404040416',
        's9': '26.262626262626263',
        'trial_index': '5.0',
        'water': '800.0'},
    {   '': '6',
        'dmso': '91.2',
        'drug': '28.8',
        's1': '90.60402684563758',
        's10': '66.44295302013424',
        's11': '102.68456375838926',
        's12': '18.120805369127513',
        's2': '90.60402684563758',
        's3': '108.7248322147651',
        's4': '114.76510067114094',
        's5': '36.24161073825503',
        's6': '96.64429530201342',
        's7': '12.080536912751677',
        's8': '54.36241610738255',
        's9': '108.7248322147651',
        'trial_index': '6.0',
        'water': '99.99999999999987'},
    {   '': '7',
        'dmso': '79.19999999999999',
        'drug': '40.800000000000004',
        's1': '19.35483870967742',
        's10': '29.03225806451613',
        's11': '25.806451612903224',
        's12': '51.61290322580645',
        's2': '19.35483870967742',
        's3': '6.451612903225806',
        's4': '25.806451612903224',
        's5': '51.61290322580645',
        's6': '29.03225806451613',
        's7': '64.51612903225806',
        's8': '45.16129032258064',
        's9': '32.25806451612903',
        'trial_index': '7.0',
        'water': '599.9999999999999'},
    {   '': '8',
        'dmso': '96.0',
        'drug': '24.0',
        's1': '6.299212598425196',
        's10': '17.637795275590552',
        's11': '11.338582677165356',
        's12': '23.937007874015748',
        's2': '21.41732283464567',
        's3': '25.196850393700785',
        's4': '2.5196850393700787',
        's5': '8.818897637795276',
        's6': '7.559055118110236',
        's7': '10.078740157480315',
        's8': '22.67716535433071',
        's9': '2.5196850393700787',
        'trial_index': '8.0',
        'water': '840.0'},
    {   '': '9',
        'dmso': '76.8',
        'drug': '43.2',
        's1': '81.92',
        's10': '35.84',
        's11': '81.92',
        's12': '10.24',
        's2': '15.360000000000001',
        's3': '0.0',
        's4': '66.55999999999999',
        's5': '97.27999999999999',
        's6': '102.4',
        's7': '71.68',
        's8': '0.0',
        's9': '76.8',
        'trial_index': '9.0',
        'water': '360.0'},
    {   '': '10',
        'dmso': '103.2',
        'drug': '16.8',
        's1': '49.62406015037594',
        's10': '9.924812030075188',
        's11': '46.31578947368421',
        's12': '23.157894736842106',
        's2': '36.390977443609025',
        's3': '43.00751879699247',
        's4': '29.77443609022556',
        's5': '43.00751879699247',
        's6': '49.62406015037594',
        's7': '16.541353383458645',
        's8': '26.466165413533833',
        's9': '66.16541353383458',
        'trial_index': '10.0',
        'water': '560.0'},
    {   '': '11',
        'dmso': '64.8',
        'drug': '55.199999999999996',
        's1': '26.01769911504425',
        's10': '147.43362831858408',
        's11': '0.0',
        's12': '121.41592920353983',
        's2': '78.05309734513274',
        's3': '60.707964601769916',
        's4': '164.7787610619469',
        's5': '26.01769911504425',
        's6': '0.0',
        's7': '164.7787610619469',
        's8': '130.08849557522126',
        's9': '60.707964601769916',
        'trial_index': '11.0',
        'water': '20.000000000000018'},
    {   '': '12',
        'dmso': '83.99999999999999',
        'drug': '36.0',
        's1': '0.0',
        's10': '31.34020618556701',
        's11': '43.092783505154635',
        's12': '47.01030927835052',
        's2': '54.84536082474226',
        's3': '19.587628865979383',
        's4': '62.68041237113402',
        's5': '11.75257731958763',
        's6': '27.42268041237113',
        's7': '0.0',
        's8': '23.50515463917526',
        's9': '58.76288659793815',
        'trial_index': '12.0',
        'water': '620.0000000000001'},
    {   '': '13',
        'dmso': '100.8',
        'drug': '19.2',
        's1': '80.0',
        's10': '80.0',
        's11': '20.0',
        's12': '60.0',
        's2': '46.66666666666667',
        's3': '100.0',
        's4': '33.333333333333336',
        's5': '80.0',
        's6': '113.33333333333334',
        's7': '120.0',
        's8': '80.0',
        's9': '46.66666666666667',
        'trial_index': '13.0',
        'water': '140.0000000000001'},
    {   '': '14',
        'dmso': '72.0',
        'drug': '48.0',
        's1': '8.21917808219178',
        's10': '7.397260273972602',
        's11': '2.054794520547945',
        's12': '1.643835616438356',
        's2': '8.21917808219178',
        's3': '2.876712328767123',
        's4': '5.342465753424657',
        's5': '7.397260273972602',
        's6': '4.931506849315069',
        's7': '2.876712328767123',
        's8': '8.21917808219178',
        's9': '0.821917808219178',
        'trial_index': '14.0',
        'water': '940.0'},
    {   '': '15',
        'dmso': '115.2',
        'drug': '4.8',
        's1': '47.1578947368421',
        's10': '11.789473684210526',
        's11': '117.89473684210526',
        's12': '100.21052631578947',
        's2': '5.894736842105263',
        's3': '70.73684210526316',
        's4': '17.68421052631579',
        's5': '35.36842105263158',
        's6': '17.68421052631579',
        's7': '58.94736842105263',
        's8': '17.68421052631579',
        's9': '58.94736842105263',
        'trial_index': '15.0',
        'water': '439.99999999999994'}]
################################################################################################################################################

    def make_drug_or_surfactant(a_list, next_deepplate_well, row_of_data):

        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 20
            pipette.well_bottom_clearance.aspirate = 3     

        for n, item in enumerate(a_list):
            vol = float(row_of_data[item])
            pipette = pipette_selection(vol)
            if vol > 0:
                pipette.pick_up_tip()
                ##modified_transfer(vol, pipette_selection=pipette, source_well=sources[item], transfered_well=deepplate[next_deepplate_well], trash=trash)
                air_gap_vol = 50 if pipette == pipette_high else 10
                pipette_high.flow_rate.aspiration = 300
                pipette_low.flow_rate.aspiration = 300
                pipette_high.flow_rate.dispense = 50
                pipette_low.flow_rate.dispense = 300
                pipette.transfer(vol, sources[item], deepplate[next_deepplate_well], new_tip='never', air_gap= air_gap_vol)
                pipette.blow_out(deepplate[next_deepplate_well])
                pipette.touch_tip(deepplate[next_deepplate_well], v_offset=-11)
                pipette.drop_tip()
        current_deepplate_well = next_deepplate_well
        next_deepplate_well = next_well(next_deepplate_well)

        if n == len(surfactant_list)-1:
            pipette_high.pick_up_tip()
            #pipette_high.flow_rate.aspirate = 25
            pipette_high.flow_rate.dispense = 50
            pipette_high.mix(5, 50, deepplate[current_deepplate_well].bottom(3))
            pipette_high.blow_out(deepplate[current_deepplate_well])
            pipette_high.touch_tip(deepplate[current_deepplate_well], v_offset=-5)
            pipette_high.drop_tip()
            #protocol.move_labware(labware=deepplate, new_location= "D3", use_gripper=True)#added speed don't know if it will work
        
        if n == len(drug_list)-1:
            pipette_high.pick_up_tip()
            #pipette_high.flow_rate.aspirate = 25
            pipette_high.flow_rate.dispense = 50
            pipette_high.mix(5, 50, deepplate[current_deepplate_well].bottom(3))
            pipette_high.blow_out(deepplate[current_deepplate_well])
            pipette_high.touch_tip(deepplate[current_deepplate_well], v_offset=-5)
            pipette_high.drop_tip()
            #protocol.move_labware(labware=deepplate, new_location= "D2", use_gripper=True)

        return current_deepplate_well, next_deepplate_well


        
    def make_exp(current_drug_well, current_surfactant_well, next_plate_well):

        for pipette in [pipette_low, pipette_high]:
            pipette.well_bottom_clearance.dispense = 13
            pipette.well_bottom_clearance.aspirate = 3     


        pipette_high.pick_up_tip()
        #modified_transfer(vol=270, pipette_selection=pipette_high, source_well=deepplate[current_surfactant_well], transfered_well=plate[next_plate_well], trash=trash)
        pipette_high.flow_rate.aspirate = 25
        pipette_high.flow_rate.dispense = 25
        pipette_high.transfer(270, deepplate[current_surfactant_well], plate[next_plate_well], new_tip='never', air_gap= 40)
        #pipette_high.blow_out(plate[next_plate_well])
        pipette_high.drop_tip()

        pipette_low.pick_up_tip()
        #modified_transfer(vol=30, pipette_selection=pipette_low, source_well=deepplate[current_drug_well], transfered_well=plate[next_plate_well], trash=trash)
        pipette_low.flow_rate.aspiration = 300
        pipette_low.flow_rate.dispense = 300
        pipette_low.transfer(30, deepplate[current_drug_well], plate[next_plate_well], new_tip='never', air_gap= 10)
        pipette_low.blow_out(plate[next_plate_well])
        pipette_low.touch_tip(plate[next_plate_well], v_offset=-2)

        pipette_low.flow_rate.aspiration = 25
        pipette_low.flow_rate.dispense = 25
        pipette_low.mix(5, 40, plate[next_plate_well].bottom(1))
        #pipette_high.blow_out(plate[next_plate_well])
        pipette_low.touch_tip(plate[next_plate_well], v_offset=-1)
        pipette_low.drop_tip()
        protocol.move_labware(labware=plate, new_location= "D3", use_gripper=True)
        protocol.move_labware(labware=plate, new_location= "D1", use_gripper=True)

        current_exp_well = next_plate_well
        next_plate_well = next_well(next_plate_well)

        return current_exp_well, next_plate_well


    #for i in range(8):
    for i in [13,14,15]: 
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
