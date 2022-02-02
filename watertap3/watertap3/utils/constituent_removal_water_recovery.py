import pandas as pd
from watertap3.utils import generate_constituent_list

__all__ = ['create']


def create(m, unit_process_type, unit_process_name):
    df = pd.read_csv('data/water_recovery.csv')
    case_study_name = m.fs.train['case_study']
    scenario = m.fs.train['scenario']

    cases = df[df.unit_process == unit_process_type].case_study.to_list()
    scenarios = df[df.unit_process == unit_process_type].scenario.to_list()
    default_df = df[((df.unit_process == unit_process_type) & (df.case_study == 'default'))].recovery
    tups = zip(cases, scenarios)

    if (case_study_name, scenario) in tups:
        case_study_df = df[((df.unit_process == unit_process_type) & (df.case_study == case_study_name) & (df.scenario == scenario))]
        if 'calculated' not in case_study_df.recovery.max():
            flow_recovery_factor = float(case_study_df.recovery)
            getattr(m.fs, unit_process_name).water_recovery.fix(flow_recovery_factor)
    else:
        if default_df.empty:
            raise TypeError(f'There is no default water recovery for {unit_process_type}.\nCheck that there is an entry for this unit in water_recovery.csv')
        if 'calculated' not in default_df.max():
            flow_recovery_factor = float(default_df)
            getattr(m.fs, unit_process_name).water_recovery.fix(flow_recovery_factor)

    train_constituent_removal_factors = generate_constituent_list.get_removal_factors(m, unit_process_type, unit_process_name)

    for constituent_name in getattr(m.fs, unit_process_name).config.property_package.component_list:
        if constituent_name in train_constituent_removal_factors.keys():
            getattr(m.fs, unit_process_name).removal_fraction[:, constituent_name].fix(train_constituent_removal_factors[constituent_name])
        else:
            getattr(m.fs, unit_process_name).removal_fraction[:, constituent_name].fix(1E-5)
    return m

