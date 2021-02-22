import pandas as pd
import generate_constituent_list
import case_study_trains

def create(m, module_name):
    
    # Get get water recovery
    df = pd.read_csv("data/water_recovery.csv")
    case_study_name = case_study_trains.train["case_study"]
    
    if case_study_name in df[df.unit_process == module_name].case_study:
        if "calculated" not in df[((df.unit_process == module_name) & (df.case_study == case_study_name))].recovery.max():
            flow_recovery_factor = float(df[((df.unit_process == module_name) & (df.case_study == case_study_name))].recovery)
            getattr(m.fs, module_name).water_recovery.fix(flow_recovery_factor)
    else:
        if "calculated" not in df[((df.unit_process == module_name) & (df.case_study == "Default"))].recovery.max():
            flow_recovery_factor = float(df[((df.unit_process == module_name) & (df.case_study == "Default"))].recovery)
            getattr(m.fs, module_name).water_recovery.fix(flow_recovery_factor)
    
    # Get constituent list and removal rates for this unit process
    train_constituent_removal_factors = generate_constituent_list.get_removal_factors(module_name)
        
    for constituent_name in getattr(m.fs, module_name).config.property_package.component_list:
        
        if constituent_name in train_constituent_removal_factors.keys():
            getattr(m.fs, module_name).removal_fraction[:, constituent_name].fix(train_constituent_removal_factors[constituent_name])
        else:
            getattr(m.fs, module_name).removal_fraction[:, constituent_name].fix(0)
    # Also set pressure drops - for now I will set these to zero
    getattr(m.fs, module_name).deltaP_outlet.fix(1e-4)
    getattr(m.fs, module_name).deltaP_waste.fix(1e-4)

    # Adding costing for units - this is very basic for now so use default settings
    #getattr(m.fs, module_name).get_costing(module=financials)

    return m  