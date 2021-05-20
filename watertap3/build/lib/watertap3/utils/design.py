#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import properties and units from 'WaterTAP Library'

from pyomo.network import Arc

from . import importfile, module_import
from .constituent_removal_water_recovery import create
from .mixer_example import Mixer
from .source_example import Source
from .split_test2 import Separator

__all__ = ['add_unit_process',
           'add_water_source',
           'add_splitter',
           'add_mixer']


def add_unit_process(m=None, unit_process_name=None, unit_process_type=None, with_connection=False, from_splitter=False, splitter_tream=None, link_to=None, link_from=None, connection_type='series',
                     stream_name=None):  # in design

    up_module = module_import.get_module(unit_process_type)

    unit_params = m.fs.pfd_dict[unit_process_name]['Parameter']

    if 'basic' in unit_process_type:
        setattr(m.fs, unit_process_name, up_module.UnitProcess(default={
                'property_package':
                    m.fs.water
                }))
        basic_unit_name = unit_params['unit_process_name']
        m = create(m, basic_unit_name, unit_process_name)

    else:
        setattr(m.fs, unit_process_name, up_module.UnitProcess(default={'property_package': m.fs.water}))
        m = create(m, unit_process_type, unit_process_name)

    ### SET PARAMS HERE FOR UP ###
    getattr(m.fs, unit_process_name).get_costing(unit_params=unit_params)

    if with_connection == True:

        if from_splitter == True:

            setattr(m.fs, splitter_tream,
                    Arc(source=getattr(m.fs, link_from).outlet1,
                        destination=getattr(m.fs, link_to).inlet))

        if from_splitter == False:
            m = connect_blocks(m=m, up1=link_from, up2=link_to,
                               connection_type=connection_type,
                               stream_name=stream_name)

    return m


def add_water_source(m=None, source_name=None, link_to=None,
                     reference=None, water_type=None, case_study=None, flow=None):  # in design

    df = importfile.feedwater(
            input_file='data/case_study_water_sources.csv',
            reference=reference, water_type=water_type,
            case_study=case_study)

    setattr(m.fs, source_name, Source(default={'property_package': m.fs.water}))
    getattr(m.fs, source_name).set_source()
    getattr(m.fs, source_name).flow_vol_in.fix(flow)

    train_constituent_list = list(getattr(m.fs, source_name).config.property_package.component_list)

    for constituent_name in train_constituent_list:
        if constituent_name in df.index:
            getattr(m.fs, source_name).conc_mass_in[:, constituent_name].fix(df.loc[constituent_name].value)
        else:
            getattr(m.fs, source_name).conc_mass_in[:, constituent_name].fix(0)

    getattr(m.fs, source_name).pressure_in.fix(1)
    return m


def add_splitter(m=None, split_name=None, with_connection=False, outlet_list=None, outlet_fractions=None,
                 link_to=None, link_from=None, stream_name=None, unfix=False):  # in design

    setattr(m.fs, split_name, Separator(default={
            'property_package': m.fs.water,
            'ideal_separation': False,
            'outlet_list': outlet_list
            }))

    if unfix == True:
        getattr(m.fs, split_name).split_fraction[0, key].unfix()
    else:
        for key in outlet_fractions.keys():
            getattr(m.fs, split_name).split_fraction[0, key].fix(outlet_fractions[key])
    return m


# TO DO MAKE THE FRACTION A DICTIONARY
def add_mixer(m=None, mixer_name=None, with_connection=False, inlet_list=None,
              link_to=None, link_from=None, stream_name=None):  # in design

    setattr(m.fs, mixer_name, Mixer(default={
            'property_package': m.fs.water,
            'inlet_list': inlet_list
            }))
    return m


def main():
    print('importing something')
    # need to define anything here?


if __name__ == '__main__':
    main()