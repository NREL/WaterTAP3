import pandas as pd
import numpy as np

__all__ = ['run',
           'get_removal_factors']


def get_source_constituents(reference, water_type, case_study, scenario):
    input_file = 'data/case_study_water_sources.csv'
    source_df = pd.read_csv(input_file, index_col='variable')
    source_df = source_df[((source_df.case_study == case_study) & (source_df.water_type == water_type) & (source_df.reference == reference) & (source_df.scenario == scenario))]
    source_df.set_index(source_df.index, inplace=True)
    return source_df

def run(m_fs):
    train = m_fs.train
    # getting the list of consituents with removal factors that are bigger than 0
    df = pd.read_csv('data/constituent_removal_factors.csv')
    df.case_study = np.where(df.case_study == 'default', train['case_study'], df.case_study)
    df = df[df.reference == train['reference']]
    df = df[df.case_study == train['case_study']]
    df = df[df.scenario == 'baseline']
    list1 = df[df.value >= 0].constituent.unique()
    list2 = m_fs.source_df.index.unique().to_list()

    m_fs.source_constituents = source_constituents = [x for x in list1 if x in list2]

    return source_constituents


def get_removal_factors(m, unit_process_type, unit_process_name):

    train = m.fs.train
    df = pd.read_csv('data/constituent_removal_factors.csv')
    const_df = df[((df.unit_process == unit_process_type) & (df.scenario == 'baseline') & (df.reference == train['reference']))].copy()
    const_df = const_df[(const_df.case_study == train['case_study']) | (const_df.case_study == 'default')].copy()
    constituent_list = getattr(m.fs, unit_process_name).config.property_package.component_list
    removal_dict = {}
    for constituent in constituent_list:
        if constituent not in const_df.constituent.unique():
            continue
        if const_df[((const_df.case_study == train['case_study']) & (const_df.constituent == constituent))].empty:
            rf = const_df[((const_df.case_study == 'default') & (const_df.constituent == constituent))].value.iloc[0]
            removal_dict[constituent] = rf
        else:
            rf = const_df[((const_df.case_study == train['case_study']) & (const_df.constituent == constituent))].value.iloc[0]
            removal_dict[constituent] = rf

    return removal_dict