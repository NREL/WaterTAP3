import ast

import numpy as np
import pandas as pd
from pyomo.environ import Block
from pyomo.network import Arc

from watertap3.utils import Mixer, Splitter, SplitterBinary, design, financials
from .water_props import WaterParameterBlock

__all__ = [
           'get_case_study',
           'get_pfd_dict',
           'create_arcs',
           'create_arc_dict',
           'check_split_mixer_need',
           'create_mixers',
           'create_splitters',
           'add_waste_streams'
           ]

def get_case_study(m=None, new_df_units=None):
    '''
    Function to add constituents and unit processes to flowsheet and connect 
    all ports.
    '''
    if new_df_units is not None:
        m.fs.df_units = new_df_units
        m.fs.pfd_dict = get_pfd_dict(new_df_units)
        m.fs.new_case_study = True
    else:
        m.fs.pfd_dict = get_pfd_dict(m.fs.df_units)
        m.fs.new_case_study = False

    pfd_dict = m.fs.pfd_dict
    financials.get_system_specs(m.fs)

    # add the water parameter block to generate the list of constituent variables in the model
    m.fs.water = WaterParameterBlock()

    # add units to model
    print('\n=========================ADDING UNIT PROCESSES=========================')
    for unit_process_name in pfd_dict.keys():
        unit = unit_process_name.replace('_', ' ').swapcase()
        unit_process_type = pfd_dict[unit_process_name]['Unit']
        unit_process_kind = pfd_dict[unit_process_name]['Type']
        print(f'{unit}')
        m = design.add_unit_process(m=m,
                                    unit_process_name=unit_process_name,
                                    unit_process_type=unit_process_type,
                                    unit_process_kind=unit_process_kind)
    print('=======================================================================\n')

    # create a dictionary with all the arcs in the network based on the pfd_dict
    m, arc_dict, arc_i = create_arc_dict(m, pfd_dict, m.fs.flow_in_dict)
    m.fs.arc_dict = arc_dict

    # gets list of unit processes and ports that need either a splitter or mixer 
    splitter_list, mixer_list = check_split_mixer_need(arc_dict)
    m.fs.splitter_list = splitter_list
    m.fs.mixer_list = mixer_list
    # add the mixers if needed, and add the arcs around the mixers to the arc dictionary
    m, arc_dict, mixer_i, arc_i = create_mixers(m, mixer_list, arc_dict, arc_i)

    # add the splitters if needed, and add the arcs around the splitters to the arc dictionary
    m, arc_dict, splitter_i, arc_i = create_splitters(m, splitter_list, arc_dict, arc_i)
    m.fs.splitter_i = splitter_i
    # add the arcs to the model
    m = create_arcs(m, arc_dict)
    # add the waste arcs to the model
    m, arc_i, mixer_i = add_waste_streams(m, arc_i, pfd_dict, mixer_i)

    return m


### create pfd_dictionary for treatment train
def get_pfd_dict(df_units):
    ### create pfd_dictionary for treatment train
    pfd_dict = df_units.set_index('UnitName').T.to_dict()
    for key in pfd_dict.keys():
        # parameter from string to dict
        if pfd_dict[key]['Parameter'] is not np.nan:
            pfd_dict[key]['Parameter'] = ast.literal_eval(pfd_dict[key]['Parameter'])
        if pfd_dict[key]['ToUnitName'] is not np.nan:
            if ',' in pfd_dict[key]['ToUnitName']:
                pfd_dict[key]['ToUnitName'] = pfd_dict[key]['ToUnitName'].split(',')
                pfd_dict[key]['FromPort'] = pfd_dict[key]['FromPort'].split(',')

    return pfd_dict


# ADDING ARCS TO MODEL
def create_arcs(m, arc_dict):
    for key in arc_dict.keys():
        source = arc_dict[key][0]
        source_port = arc_dict[key][1]
        outlet = arc_dict[key][2]
        outlet_port = arc_dict[key][3]
        setattr(m.fs, (f'arc{key}'), Arc(source=getattr(getattr(m.fs, source), source_port),
                                         destination=getattr(getattr(m.fs, outlet), outlet_port)))
    return m


# create arc dictionary, add sources, add source to inlet arcs
def create_arc_dict(m, pfd_dict, flow):
    arc_dict = {}
    arc_i = 1
    for key in pfd_dict.keys():
        # if the unit is an intake process
        if pfd_dict[key]['Type'] == 'intake':
            num_sources = len(pfd_dict[key]['Parameter']['water_type'])
            num_unique_sources = len(np.unique(pfd_dict[key]['Parameter']['water_type']))

            ### check if multiple sources with same name for 1 intake
            if num_sources != num_unique_sources:
                print('error: multiple sources with same name for 1 intake')

            for water_type in pfd_dict[key]['Parameter']['water_type']:
                source_name = water_type
                water_type = water_type
                source_flow = flow[source_name]

                m = design.add_water_source(m=m, source_name=source_name, water_type=water_type, flow=source_flow)

                arc_dict[arc_i] = [source_name, 'outlet', key, 'inlet']
                arc_i += 1

                # create arcs *for single streams* from .csv table.
    for key in pfd_dict.keys():
        if pfd_dict[key]['FromPort'] is not np.nan:
            if isinstance(pfd_dict[key]['FromPort'], list):
                for port_i in range(0, len(pfd_dict[key]['FromPort'])):
                    arc_dict[arc_i] = [key, pfd_dict[key]['FromPort'][port_i],
                                       pfd_dict[key]['ToUnitName'][port_i], 'inlet']
                    arc_i += 1
            else:
                arc_dict[arc_i] = [key, pfd_dict[key]['FromPort'], pfd_dict[key]['ToUnitName'], 'inlet']
                arc_i += 1

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
    return splitter_list, mixer_list


def create_mixers(m, mixer_list, arc_dict, arc_i):
    mixer_i = 1
    inlet_i = 1
    for j in mixer_list:
        inlet_list = []
        mixer_name = f'mixer{mixer_i}'
        for key in list(arc_dict.keys()):
            if ((arc_dict[key][2] == j[0]) & (arc_dict[key][3] == j[1])):

                # inlet list for when mixer is added to model
                inlet_name = f'inlet{inlet_i}'
                inlet_list.append(inlet_name)
                inlet_i += 1

                # add new arc to arc dict
                arc_dict[arc_i] = [arc_dict[key][0], arc_dict[key][1], mixer_name, inlet_name]
                arc_i += 1

                # delete from arc dict
                del arc_dict[key]

        # add mixer to model with inlet list
        setattr(m.fs, mixer_name,
                Mixer(default={'property_package': m.fs.water, 'inlet_list': inlet_list}))

        # arc from mixer outlet to node
        arc_dict[arc_i] = [mixer_name, 'outlet', j[0], j[1]]
        arc_i += 1
        mixer_i += 1

    return m, arc_dict, mixer_i, arc_i


def create_splitters(m, splitter_list, arc_dict, arc_i):
    splitter_i = 1
    outlet_i = 1
    m.fs.unit_options = unit_options = {}
    m.fs.all_splitters = all_splitters = {}
    if not splitter_list:
        m.fs.choose = False
    for j in splitter_list:
        splitter_unit = j[0]
        splitter_port = j[1]
        outlet_i = 1
        outlet_list = []
        outlet_list_up = m.fs.outlet_list_up = {}
        splitter_name = f'splitter{splitter_i}'
        all_splitters[splitter_name] = {'from_unit': splitter_unit, 
                                        'to_units': list(zip(m.fs.pfd_dict[splitter_unit]['ToUnitName'], m.fs.pfd_dict[splitter_unit]['FromPort'])), 
                                        # 'split_fraction': m.fs.pfd_dict[splitter_unit]['Parameter']['split_fraction'], 
                                        'indicator': False}
        for key in list(arc_dict.keys()):
            if ((arc_dict[key][0] == splitter_unit) & (arc_dict[key][1] == splitter_port)):
                split_dict = m.fs.split_dict = {}
                w = 0
                for uname in m.fs.pfd_dict[splitter_unit]['ToUnitName']:
                    if m.fs.pfd_dict[splitter_unit]['FromPort'][w] == 'outlet':
                        if 'split_fraction' in m.fs.pfd_dict[splitter_unit]['Parameter']:
                            all_splitters[splitter_name]['split_fraction']  = m.fs.pfd_dict[splitter_unit]['Parameter']['split_fraction']
                            split_dict[uname] = m.fs.pfd_dict[splitter_unit]['Parameter']['split_fraction'][w]
                            w += 1
                            split_fractions = m.fs.pfd_dict[splitter_unit]['Parameter']['split_fraction']
                            if all(split == 1 for split in split_fractions):
                                m.fs.choose = True
                                unit_options[splitter_i] = {splitter_unit: list(split_dict.keys())}
                            else:
                                m.fs.choose = False

                            # outlet list for when splitter is added to model
                outlet_name = f'outlet_{outlet_i}'
                outlet_list.append(outlet_name)
                outlet_i += 1

                # add new arc to arc dict
                arc_dict[arc_i] = [splitter_name, outlet_name, arc_dict[key][2], arc_dict[key][3]]
                arc_i += 1

                unit_hold = arc_dict[key][2]

                if arc_dict[key][2] not in split_dict.keys():
                    for l in m.fs.arc_dict.keys():
                        if arc_dict[key][2] == m.fs.arc_dict[l][0]:
                            unit_hold = m.fs.arc_dict[l][2]

                if len(split_dict) > 0:
                    outlet_list_up[outlet_name] = split_dict[unit_hold]
                else:
                    outlet_list_up[outlet_name] = "NA"
                # delete from arc dict
                del arc_dict[key]

        # add splitter to model with outlet list
        if m.fs.choose:
            all_splitters[splitter_name]['indicator'] = True
            setattr(m.fs, splitter_name, SplitterBinary(default={'property_package': m.fs.water}))
            this_splitter = getattr(m.fs, splitter_name)
            this_splitter.split_dict = split_dict
            this_splitter._split_from_unit = splitter_unit
            this_splitter.get_split(split_dict=split_dict)
            # setattr(this_splitter, f'unit_list', unit_options[splitter_i])
        else:
            setattr(m.fs, splitter_name, Splitter(default={'property_package': m.fs.water}))
            setattr(m.fs, f'{splitter_name}_outlet_list', outlet_list_up)
            unit_params = m.fs.pfd_dict[splitter_unit]['Parameter']
            getattr(m.fs, splitter_name).outlet_list = outlet_list_up
            # could just have self call the split list directly without reading in unit params. same for all 
            getattr(m.fs, splitter_name).get_split(outlet_list_up=outlet_list_up, unit_params=unit_params)

        # arc from mixer outlet to node
        arc_dict[arc_i] = [splitter_unit, splitter_port, splitter_name, 'inlet']
        arc_i += 1
        splitter_i += 1

    return m, arc_dict, splitter_i, arc_i

def add_waste_streams(m, arc_i, pfd_dict, mixer_i):
    # get number of units going to automatic waste disposal units
    i = 0
    waste_inlet_list = []
    unit_list = []
    for key in m.fs.pfd_dict.keys():
        unit_list.append(m.fs.pfd_dict[key]['Unit'])
        if 'surface_discharge' == m.fs.pfd_dict[key]['Unit']:
            sd_name = key
    if 'surface_discharge' in unit_list:
        for b_unit in m.fs.component_objects(Block, descend_into=False):
            if hasattr(b_unit, 'waste'):
                if len(getattr(b_unit, 'waste').arcs()) == 0:
                    if str(b_unit)[3:] in list(pfd_dict.keys()):  #
                        if pfd_dict[str(b_unit)[3:]]['Type'] == 'treatment':
                            i += 1
                            waste_inlet_list.append((f'inlet{i}'))

        if len(waste_inlet_list) > 1:
            i = 0
            waste_mixer = f'mixer{mixer_i}'
            m.fs.water_mixer_name = waste_mixer  # used for displaying train. not used for model
            setattr(m.fs, waste_mixer,
                    Mixer(default={'property_package': m.fs.water, 'inlet_list': waste_inlet_list}))
            for b_unit in m.fs.component_objects(Block, descend_into=False):
                if hasattr(b_unit, 'waste'):
                    if len(getattr(b_unit, 'waste').arcs()) == 0:
                        if str(b_unit)[3:] in list(pfd_dict.keys()):
                            if pfd_dict[str(b_unit)[3:]]['Type'] == 'treatment':
                                i += 1
                                setattr(m.fs, (f'arc{arc_i}'), Arc(source=getattr(b_unit, 'waste'),
                                                                     destination=getattr(getattr(m.fs, waste_mixer),
                                                                                         f'inlet{i}')))
                                arc_i += 1

            # add connection for waste mixer to surface discharge -->
            if 'surface_discharge' in unit_list:
                setattr(m.fs, (f'arc{arc_i}'), Arc(source=getattr(m.fs, waste_mixer).outlet,
                                                     destination=getattr(m.fs, sd_name).inlet))
                arc_i += 1
        return m, arc_i, mixer_i

    else:
        return m, arc_i, mixer_i