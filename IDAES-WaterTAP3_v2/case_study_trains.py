import pandas as pd
import ast

import numpy as np
import pandas as pd
from pyomo.network import Arc

import watertap as wt
from mixer_example import Mixer1
from split_test2 import Separator1

global train
global source_water
global pfd_dict  # this is set in function so not global.


from water_props import WaterParameterBlock

from pyomo.environ import (
    Block)

case_study_library = pd.read_csv("data/case_study_library.csv") #TODO EDIT THIS TO READ EXCEL FILE - ARIEL


def get_def_source(reference, water_type, case_study, scenario):

    df = wt.importfile.feedwater(
        input_file="data/case_study_water_sources.csv",
        reference = reference, 
        water_type = water_type, 
        case_study = case_study,
        scenario = scenario)
    
    return df
    
def get_case_study(flow = None, m = None):    
    
        
    # get source water information that will be used to get the flow in if not specified
    flow = {}
    if isinstance(source_water['water_type'], list) and not flow:
        for water_type in source_water['water_type']:
            df = get_def_source(source_water['reference'], water_type, source_water['case_study'], source_water['scenario'])
            flow[water_type] = df.loc['flow'].value
    elif not flow:
        df = get_def_source(source_water['reference'], source_water['water_type'], 
                            source_water['case_study'], source_water['scenario'])
        flow[source_water['water_type']] = df.loc['flow'].value
    m.fs.flow_in_dict = flow
    #set the flow based on the case study if not specified.
#     if flow is None: fow = df_source.loc["flow"].value
        
    case_study_library = "data/case_study_train_input_test.xlsx"

    # set up tables of design (how units are connected) and units (list of all units needed for the train)
    #df_design = pd.read_excel(case_study_library, sheet_name='design')
    df_units = pd.read_excel(case_study_library, sheet_name='units')
    df_units.CaseStudy = df_units.CaseStudy.str.lower()
    df_units.Reference = df_units.Reference.str.lower()
    df_units.Scenario = df_units.Scenario.str.lower()
    df_units = filter_df(df_units)

    ### create pfd_dictionary for treatment train
    m.fs.pfd_dict = get_pfd_dict(df_units)
    pfd_dict = m.fs.pfd_dict
    
    # create the constituent list for the train that is automatically used to edit the water property package.
    import generate_constituent_list
    import financials
    generate_constituent_list.train = train
    generate_constituent_list.source_water = source_water
    generate_constituent_list.pfd_dict = pfd_dict
    
    financials.train = train
    financials.source_water = source_water
    financials.pfd_dict = pfd_dict
    financials.get_system_specs(m.fs, train)
    
    #train_constituent_list = generate_constituent_list.run()
    
    # add the water parameter block to generate the list of constituent variables in the model
    m.fs.water = WaterParameterBlock()

    # add units to model
    print("------- Adding Unit Processes -------")
    for key in pfd_dict.keys():
        print(key)
        m = wt.design.add_unit_process(m = m, 
                                       unit_process_name = key, 
                                       unit_process_type = pfd_dict[key]['Unit'])
    print("-------------------------------------")

    # create a dictionary with all the arcs in the network based on the pfd_dict
    m, arc_dict, arc_i = create_arc_dict(m, pfd_dict, flow)
    m.fs.arc_dict = arc_dict
        
    # gets list of unit processes and ports that need either a splitter or mixer 
    splitter_list, mixer_list = check_split_mixer_need(arc_dict)
    
    # add the mixers if needed, and add the arcs around the mixers to the arc dictionary
    m, arc_dict, mixer_i, arc_i = create_mixers(m, mixer_list, arc_dict, arc_i)
    
    # add the splitters if needed, and add the arcs around the splitters to the arc dictionary
    m, arc_dict, splitter_i, arc_i = create_splitters(m, splitter_list, arc_dict, arc_i)
    
    # add the arcs to the model
    m = create_arcs(m, arc_dict) 
    
    # add the waste arcs to the model
    m, arc_i, mixer_i = add_waste_streams(m, arc_i, pfd_dict, mixer_i)

    return m
    
### create pfd_dictionary for treatment train
def get_pfd_dict(df_units):
    ### create pfd_dictionary for treatment train
    pfd_dict = df_units.set_index('UnitName').T.to_dict()
    #print(pfd_dict)
    for key in pfd_dict.keys():
        # parameter from string to dict
        if pfd_dict[key]['Parameter'] is not np.nan:
            pfd_dict[key]['Parameter'] = ast.literal_eval(pfd_dict[key]['Parameter'])

        if pfd_dict[key]['ToUnitName'] is not np.nan:
            if "," in pfd_dict[key]['ToUnitName']:
                pfd_dict[key]['ToUnitName'] = pfd_dict[key]['ToUnitName'].split(",")
                pfd_dict[key]['FromPort'] = pfd_dict[key]['FromPort'].split(",")

    return pfd_dict



# adjust data for particular case study
def filter_df(df):
    df = df[df.Reference == train["reference"]]
    #df = df[df.WaterType == train["water_type"]]
    df = df[df.Scenario == train["scenario"]]
    df = df[df.CaseStudy ==  train["case_study"]]
    del df["CaseStudy"]; del df["Scenario"]; del df["Reference"];
    return df
    
    
# ADDING ARCS TO MODEL
def create_arcs(m, arc_dict):
    print("----- Connecting Unit Processes -----")

    for key in arc_dict.keys():
        source = arc_dict[key][0]
        source_port = arc_dict[key][1]
        outlet = arc_dict[key][2]
        outlet_port = arc_dict[key][3]
        
        print(source, "ToUnitName -->", outlet)

        setattr(m.fs, ("arc%s" % key), Arc(source = getattr(getattr(m.fs, source), source_port),  
                                           destination = getattr(getattr(m.fs, outlet), outlet_port))) 
        
    print("-------------------------------------")
    return m    
    
    
# create arc dictionary, add sources, add source to inlet arcs
def create_arc_dict(m, pfd_dict, flow):
    arc_dict = {}
    arc_i = 1


    for key in pfd_dict.keys():
        #print(key)
        # if the unit is an intake process
        if pfd_dict[key]["Type"] == "intake":
            source_exists = False
            num_sources = len(pfd_dict[key]["Parameter"]["water_type"])
            num_unique_sources = len(np.unique(pfd_dict[key]["Parameter"]["water_type"]))

            ### check if multiple sources with same name for 1 intake
            if num_sources != num_unique_sources:
                print("error: multiple sources with same name for 1 intake")

            for water_type in pfd_dict[key]["Parameter"]["water_type"]:
                    source_name = water_type
                    water_type = water_type
                    reference = source_water["reference"]
                    case_study = source_water["case_study"]
                    source_flow = flow[source_name]

                    m = wt.design.add_water_source(m = m, source_name = source_name, 
                                                   reference = reference, water_type = water_type, 
                                         case_study = case_study, flow = source_flow)

                    arc_dict[arc_i] = [source_name, "outlet", key, "inlet"] 
                    arc_i = arc_i + 1   
    
    
    # create arcs *for single streams* from .csv table.
    for key in pfd_dict.keys():
        if pfd_dict[key]["FromPort"] is not np.nan:
            if isinstance(pfd_dict[key]["FromPort"], list):
                for port_i in range(0, len(pfd_dict[key]["FromPort"])):
                    arc_dict[arc_i] = [key, pfd_dict[key]["FromPort"][port_i],
                                       pfd_dict[key]["ToUnitName"][port_i], "inlet"]
                    arc_i = arc_i + 1
            else:
                arc_dict[arc_i] = [key, pfd_dict[key]["FromPort"], pfd_dict[key]["ToUnitName"], "inlet"]
                arc_i = arc_i + 1
    
    return m, arc_dict, arc_i
    
    

# check if a mixer or splitter is needed
def check_split_mixer_need(arc_dict):
    mixer_list = []
    splitter_list = []
    unique_name_list1 = []
    unique_name_list2 = []

    for key in arc_dict.keys():
        # FOR SPLITTER
        if [arc_dict[key][0], arc_dict[key][1]] not in unique_name_list1: 
            unique_name_list1.append([arc_dict[key][0], arc_dict[key][1]])
        else:
            if [arc_dict[key][0], arc_dict[key][1]] not in splitter_list: 
                splitter_list.append([arc_dict[key][0], arc_dict[key][1]])

        # FOR MIXER    
        if [arc_dict[key][2], arc_dict[key][3]] not in unique_name_list2: 
            unique_name_list2.append([arc_dict[key][2], arc_dict[key][3]])
        else:
            if [arc_dict[key][2], arc_dict[key][3]] not in mixer_list: 
                mixer_list.append([arc_dict[key][2], arc_dict[key][3]])
    #print(mixer_list)
    return splitter_list, mixer_list


def create_mixers(m, mixer_list, arc_dict, arc_i):
    mixer_i = 1
    inlet_i = 1
    for j in mixer_list:
        inlet_list = []
        mixer_name = "mixer%s" % mixer_i
        for key in list(arc_dict.keys()):
            if ((arc_dict[key][2] == j[0]) & (arc_dict[key][3] == j[1])):

                # inlet list for when mixer is added to model
                inlet_name = "inlet%s" % inlet_i
                inlet_list.append(inlet_name)
                inlet_i = inlet_i + 1

                # add new arc to arc dict
                arc_dict[arc_i] = [arc_dict[key][0], arc_dict[key][1], mixer_name, inlet_name]
                arc_i = arc_i + 1 

                # delete from arc dict
                del arc_dict[key]

        # add mixer to model with inlet list
        setattr(m.fs, mixer_name, 
            Mixer1(default={"property_package": m.fs.water, "inlet_list": inlet_list}))

        # arc from mixer outlet to node
        arc_dict[arc_i] = [mixer_name, "outlet", j[0], j[1]]
        arc_i = arc_i + 1
        mixer_i = mixer_i + 1
    
    return m, arc_dict, mixer_i, arc_i

def create_splitters(m, splitter_list, arc_dict, arc_i):
    splitter_i = 1
    outlet_i = 1
    for j in splitter_list:
        outlet_list = []
        splitter_name = "splitter%s" % splitter_i
        for key in list(arc_dict.keys()):
            if ((arc_dict[key][0] == j[0]) & (arc_dict[key][1] == j[1])):

                # outlet list for when splitter is added to model
                outlet_name = "outlet%s" % outlet_i
                outlet_list.append(outlet_name)
                outlet_i = outlet_i + 1

                # add new arc to arc dict
                arc_dict[arc_i] = [splitter_name, outlet_name, arc_dict[key][2], arc_dict[key][3]]
                arc_i = arc_i + 1 

                # delete from arc dict
                del arc_dict[key]

        # add splitter to model with outlet list  
        import splitter_mar1
         
        setattr(m.fs, splitter_name, splitter_mar1.UnitProcess(default={"property_package": m.fs.water}))
        unit_params = m.fs.pfd_dict[j[0]]["Parameter"]   
        getattr(m.fs, splitter_name).outlet_list = outlet_list
        if "split_fraction" in unit_params:
            print("params into splitter -->", unit_params["split_fraction"])
        # could just have self call the split list directly without reading in unit params. same for all 
        getattr(m.fs, splitter_name).get_split(outlet_list=outlet_list, unit_params=unit_params)
        
        
        # arc from mixer outlet to node
        arc_dict[arc_i] = [j[0], j[1], splitter_name, "inlet"]
        arc_i = arc_i + 1
        splitter_i = splitter_i + 1
    
    return m, arc_dict, splitter_i, arc_i



################################################    
#### ADD CONNECTIONS TO SURFACE DISCHARGE ### TO DO --> CHECK WASTE DISPOSALS. IF NOT IN DESIGN, THEN INCLUDE HERE.
################################################    
def add_waste_streams(m, arc_i, pfd_dict, mixer_i):

    # get number of units going to automatic waste disposal units
    i = 0
    waste_inlet_list = []
    
    if "surface_discharge" in pfd_dict.keys():
    
        for b_unit in m.fs.component_objects(Block, descend_into=False):
            if hasattr(b_unit, 'waste'):

                if len(getattr(b_unit, "waste").arcs()) == 0:
                    if str(b_unit)[3:] in list(pfd_dict.keys()): #
                        if pfd_dict[str(b_unit)[3:]]["Type"] == "treatment":
                            i = i + 1
                            waste_inlet_list.append(("inlet%s" % i))

        if len(waste_inlet_list) > 1:
            i = 0
            waste_mixer = "mixer%s" % mixer_i
            m.fs.water_mixer_name = waste_mixer # used for displaying train. not used for model
            setattr(m.fs, waste_mixer,
                    Mixer1(default={"property_package": m.fs.water, "inlet_list": waste_inlet_list}))

            for b_unit in m.fs.component_objects(Block, descend_into=False):
                 if hasattr(b_unit, 'waste'):

                    if len(getattr(b_unit, "waste").arcs()) == 0:

                        if str(b_unit)[3:] in list(pfd_dict.keys()):
                            if pfd_dict[str(b_unit)[3:]]["Type"] == "treatment":
                                i = i + 1
                                setattr(m.fs, ("arc%s" % arc_i), Arc(source = getattr(b_unit, "waste"),  
                                                                   destination = getattr(getattr(m.fs, waste_mixer),
                                                                                         "inlet%s" % i)))
                                arc_i = arc_i + 1

            # add connection for waste mixer to surface dicharge -->
            if "surface_discharge" in list(pfd_dict.keys()):
                setattr(m.fs, ("arc%s" % arc_i), Arc(source = getattr(m.fs, waste_mixer).outlet,  
                                                                   destination = getattr(m.fs, "surface_discharge").inlet))
                arc_i = arc_i + 1
        return m, arc_i, mixer_i

    else:  
        return m, arc_i, mixer_i
        


























# def get_unit_processes(case_study, scenario):
#     unit_processes = []
    
#     if case_study == "Carlsbad":
#         if scenario == "Baseline":
#             unit_processes = ["sw_onshore_intake",
#                           "coag_and_floc",
#                           "tri_media_filtration",
#                           "sulfuric_acid_addition",
#                           "sodium_bisulfite_addition",
#                           "cartridge_filtration",
#                           "ro_deep",                 
#                           "lime_softening",                  
#                           "co2_addition",                  
#                           "chlorination_twb",                  
#                           "ammonia_addition",                  
#                           "treated_storage_24_hr",
#                           "municipal_drinking",
#                           "backwash_solids_handling",
#                           "surface_discharge",
#                           "landfill"]
    
#         if scenario == "TwoPassRO":
#             unit_processes = ["sw_onshore_intake",
#                           "coag_and_floc",
#                           "tri_media_filtration",
#                           "sulfuric_acid_addition",
#                           "sodium_bisulfite_addition",
#                           "cartridge_filtration",
#                           "ro_deep",
#                           "ro_deep_scnd_pass",
#                           "lime_softening",                  
#                           "co2_addition",                  
#                           "chlorination_twb",                  
#                           "ammonia_addition",                  
#                           "treated_storage_24_hr",
#                           "municipal_drinking",
#                           "backwash_solids_handling",
#                           "surface_discharge",
#                           "landfill"]
            
#     if len(unit_processes) == 0: 
#         print("potential error: no unit processes listed to build treatment train")
#         df_units = pd.read_excel(case_study_library, sheet_name='units')
#         df_units = filter_df(df_units)
#         unit_processes = list(df_units.Unit)
        
#     return unit_processes


# def check_waste_source_recovered(b_unit):
#     check = "no"
    
#     if "backwash_solids_handling" in str(b_unit): check = "yes"
    
#     if "landfill" in str(b_unit): check = "yes"
    
#     if "surface_discharge" in str(b_unit): check = "yes"
    
#     if "source1" in str(b_unit): check = "yes"
    
#     if "municipal_drinking" in str(b_unit): check = "yes"
    
#     return check
                          
def check_waste(b_unit):
    check = "no"
    
    if "backwash_solids_handling" in str(b_unit): check = "yes"
    
    if "landfill" in str(b_unit): check = "yes"
    
    if "surface_discharge" in str(b_unit): check = "yes"
    
    return check                          


# def check_intake(b_unit):
#     check = "no"
    
#     if "sw_onshore_intake" in str(b_unit): check = "yes"
       
#     return check   

# def check_product(b_unit):
#     check = "no"
    
#     if "municipal_drinking" in str(b_unit): check = "yes"
       
#     return check 

# def get_number_of_chemical_additions(case_study, scenario):
#     i = 0
#     for unit_process in get_unit_processes(case_study, scenario):
#         i = i + 1 if hasattr(module_import.get_module(unit_process), 'chem_dic') is True else i
    
#     return i




        


