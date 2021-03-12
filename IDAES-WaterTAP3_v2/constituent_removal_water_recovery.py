import pandas as pd
import generate_constituent_list
import case_study_trains

def create(m, unit_process_type, unit_process_name):
    # Get get water recovery
    df = pd.read_csv("data/water_recovery.csv")
    case_study_name = case_study_trains.train["case_study"]
    
    if unit_process_type == "reverse_osmosis": unit_process_type = "ro_deep" # until reverse osmosis is in table input
        
    if case_study_name in df[df.unit_process == unit_process_type].case_study:
        if "calculated" not in df[((df.unit_process == unit_process_type) & (df.case_study == case_study_name))].recovery.max():
            flow_recovery_factor = float(df[((df.unit_process == unit_process_type) & (df.case_study == case_study_name))].recovery)
            getattr(m.fs, unit_process_name).water_recovery.fix(flow_recovery_factor)
    else:
        if "calculated" not in df[((df.unit_process == unit_process_type) & (df.case_study == "default"))].recovery.max():
            flow_recovery_factor = float(df[((df.unit_process == unit_process_type) & (df.case_study == "default"))].recovery)
            getattr(m.fs, unit_process_name).water_recovery.fix(flow_recovery_factor)
    
    if unit_process_type != "ro_deep":
        #print(unit_process_type)
        if unit_process_type == "ro_deep": print("should not go here")
        getattr(m.fs, unit_process_name).deltaP_waste.fix(1e-6)
        getattr(m.fs, unit_process_name).deltaP_outlet.fix(1e-6)

    # Get constituent list and removal rates for this unit process
    train_constituent_removal_factors = generate_constituent_list.get_removal_factors(unit_process_type)
    #if unit_process_type == "ro_deep": print(train_constituent_removal_factors)
        
    for constituent_name in getattr(m.fs, unit_process_name).config.property_package.component_list:
        
        if constituent_name in train_constituent_removal_factors.keys():
            
            getattr(m.fs, unit_process_name).removal_fraction[:, constituent_name].fix(
                train_constituent_removal_factors[constituent_name])
        else:
            getattr(m.fs, unit_process_name).removal_fraction[:, constituent_name].fix(1e-6)


    return m
