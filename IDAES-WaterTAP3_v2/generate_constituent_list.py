import pandas as pd
import numpy as np
#from case_study_trains import get_unit_processes

#global case_study
#global reference
#global water_type
global unit_process_list
#global scenario

global train
global source_water
global pfd_dict

import module_import

def get_def_source(reference, water_type, case_study, scenario):
    import importfile
    df = importfile.feedwater(
        input_file="data/case_study_water_sources.csv",
        reference = reference, 
        water_type = water_type, 
        case_study = case_study,
        scenario = scenario)
    
    return df

def run():
    import case_study_trains
    train = case_study_trains.train 
    source_water = case_study_trains.source_water 
    
    # getting the list of consituents with removal factors that are bigger than 0
    df = pd.read_csv("data/constituent_removal.csv")
    df.case_study = np.where(df.case_study == "default", train["case_study"], df.case_study)
    df = df[df.reference == train["reference"]]
    df = df[df.case_study == train["case_study"]]
    df = df[df.scenario == train["scenario"]]
    
#     list1a = df[df.value == "calculated"].constituent.unique()
#     df = df[df.value != "calculated"]
#     df.value = df.value.astype(float)
    list1 = df[df.value >=0].constituent.unique()
#     list1 = list(list1b) + list(list1a)

    # grabs inlet water information
    if isinstance(source_water['water_type'], list):
        list2 = []
        for water_type in source_water['water_type']:
            df = get_def_source(source_water['reference'], water_type, source_water['case_study'], source_water['scenario'])
            list2 = list(df.index) + list2
        list2 = list(set(list2))
    else:
        df = get_def_source(source_water['reference'], source_water['water_type'], 
                            source_water['case_study'], source_water['scenario'])
        list2 = df.index
    
    
    # gets list of consituents in inlet water --> REMOVE?
    #list2 = df.index
    
    # combines list
    final_list = [x for x in list1 if x in list2]
    
    #TODO ACTIVATE ONCE WE KNOW WE NEED TO ADD CHEM ADDITIONS!! 
#     chem_addition_list = []
    
#     for unit_process in pfd_dict.keys():
#         up_module = module_import.get_module(pfd_dict[unit_process]["Unit"])
#         if hasattr(up_module, 'chem_dic'): 
#             for chem in up_module.chem_dic.keys():
#                 chem_addition_list.append(chem)
    
#    final_list = final_list + chem_addition_list
    
    return final_list

def get_removal_factors(unit_process):
    import case_study_trains
    train = case_study_trains.train 
    source_water = case_study_trains.source_water
       
    df = pd.read_csv("data/constituent_removal.csv")
    df.case_study = np.where(df.case_study == "default", train["case_study"], df.case_study)
    df = df[df.reference == train["reference"]]
    df = df[df.case_study == train["case_study"]]
    df = df[df.scenario == train["scenario"]]
    df = df[df.unit_process == unit_process]
    
    removal_dict = {}
    for constituent in df.constituent.unique():
        removal_dict[constituent] = df[df.constituent == constituent].value.max()
    
    return removal_dict
