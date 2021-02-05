import pandas as pd
import numpy as np
from case_study_trains import get_unit_processes

global case_study
global reference
global water_type
global unit_process_list
global scenario

import module_import

def run():
    
    df = pd.read_csv("Data/constituent_removal.csv")
    df = df[df.case_study == case_study]
    list1 = df[df.fractional_constituent_removal >=0].constituent.unique()
    
    import importfile
    
    df = importfile.feedwater(
        input_file="data/case_study_water_sources_and_uses.csv",
        reference = reference, water_type = water_type, 
        case_study = case_study)
        
    list2 = df.index
    
    final_list = [x for x in list1 if x in list2]
    
    #TODO ACTIVATE ONCE WE KNOW WE NEED TO ADD CHEM ADDITIONS!! 
    chem_addition_list = []
    
    for unit_process in get_unit_processes(case_study, scenario):
        up_module = module_import.get_module(unit_process)
        if hasattr(up_module, 'chem_dic'): 
            for chem in up_module.chem_dic.keys():
                chem_addition_list.append(chem)
    
    final_list = final_list + chem_addition_list
    
    return final_list

def get_removal_factors(unit_process):

    df = pd.read_csv("Data/constituent_removal.csv")
    df = df[df.case_study == 'Carlsbad']
    df = df[df.unit_process == unit_process]
    
    removal_dict = {}
    for constituent in df.constituent.unique():
        removal_dict[constituent] = df[df.constituent == constituent].fractional_constituent_removal.max()
    
    return removal_dict