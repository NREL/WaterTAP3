#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyomo.environ import ConcreteModel, SolverFactory, TransformationFactory
from pyomo.network import Arc

from idaes.core import FlowsheetBlock

# Import properties and units from "WaterTAP Library"
from water_props import WaterParameterBlock

import financials

from pyomo.environ import Block, Constraint, Var, units as pyunits
import module_import
from source_example import Source
from mixer_example import Mixer1
from split_test2 import Separator1
from pyomo.network import Arc, SequentialDecomposition

import pandas as pd

import generate_constituent_list

def connect_blocks(m = None, 
                    stream_name = None,
                    from_node = None,
                    outlet_name = "outlet",
                    to_node = None,
                    inlet_name = "inlet"):
    
    '''default is outlet and inlet. if different - for example for mixer or splitter - need to specify the names'''
    
    f1 = getattr(m.fs, from_node)
    f2 = getattr(f1, outlet_name)
    t1 = getattr(m.fs, to_node)
    t2 = getattr(t1, inlet_name)

    setattr(m.fs, stream_name, Arc(source=f2, destination=t2))
    
    return m


def add_unit_process(m = None, unit_process_name = None, unit_process_type = None, with_connection = False,
                     from_splitter = False, splitter_tream = None,
                    link_to = None, link_from = None, connection_type = "series", stream_name = None): # in design
             
    
    up_module = module_import.get_module(unit_process_type)
    
    setattr(m.fs, unit_process_name, up_module.UnitProcess(default={"property_package": m.fs.water}))
    
    m = up_module.create(m, unit_process_name)
    
    if with_connection == True:
        
        if from_splitter == True:
            
            setattr(m.fs, splitter_tream, 
                    Arc(source=getattr(m.fs, link_from).outlet1, 
                                           destination=getattr(m.fs, link_to).inlet))            
            
        if from_splitter == False:
            m = connect_blocks(m = m, up1 = link_from, up2 = link_to, 
                               connection_type = connection_type, 
                               stream_name = stream_name)
    
    return m




def add_water_source(m = None, source_name = None, link_to = None, 
                     reference = None, water_type = None, case_study = None, flow = 0): # in design
    
    import importfile
    
    df = importfile.feedwater(
        input_file="data/case_study_water_sources_and_uses.csv",
        reference = reference, water_type = water_type, 
        case_study = case_study)
    
    
    train_constituent_list = generate_constituent_list.run()
    
    setattr(m.fs, source_name, Source(default={"property_package": m.fs.water}))
    
    getattr(m.fs, source_name).inlet.flow_vol.fix(flow)
        
    for constituent_name in train_constituent_list:
        
        if constituent_name in df.index:
            getattr(m.fs, source_name).inlet.conc_mass[:, constituent_name].fix(df.loc[constituent_name].Value)        
        
        else:
            getattr(m.fs, source_name).inlet.conc_mass[:, constituent_name].fix(1e-4)
            
    #getattr(m.fs, source_name).inlet.conc_mass[:, "TOC"].fix(df.loc["TOC"].Value)
    #getattr(m.fs, source_name).inlet.conc_mass[:, "nitrates"].fix(df.loc["Nitrate"].Value) #TODO ChangeNitrate
    #getattr(m.fs, source_name).inlet.conc_mass[:, "TDS"].fix(df.loc["TDS"].Value)
    
    
    getattr(m.fs, source_name).inlet.temperature.fix(300)
    getattr(m.fs, source_name).inlet.pressure.fix(2e5)
    
    
    # Set removal and recovery fractions -> CAN WE JUST SET OUTLETS AND THAT'S IT? OR CLEANER WITH THE SAME FORMAT?
    getattr(m.fs, source_name).water_recovery.fix(1.0)
    getattr(m.fs, source_name).removal_fraction[:, "TDS"].fix(1e-4)
    # I took these values from the WaterTAP3 nf model
    getattr(m.fs, source_name).removal_fraction[:, "TOC"].fix(1e-4)
    getattr(m.fs, source_name).removal_fraction[:, "nitrates"].fix(1e-4)
    # Also set pressure drops - for now I will set these to zero
    getattr(m.fs, source_name).deltaP_outlet.fix(1e-4)
    getattr(m.fs, source_name).deltaP_waste.fix(1e-4)
    
    if link_to is not None: # TODO - potential for multiple streams
        connect_blocks(m = m, up1 = source_name, up2 = link_to, connection_type = None, 
                               stream_name = ("%s_stream" % source_name))
        
    return m

# NOT USED:
def add_water_use(m = None, use_name = None, with_connection = False, inlet_list = ["inlet"],
                    link_to = None, link_from = None, stream_name = None, end_use_constraint = False): # in design
    
    setattr(m.fs, use_name, Mixer1(default={
        "property_package": m.fs.water,
        "inlet_list": inlet_list}))


    if end_use_constraint == True: 
    
        # Set removal and recovery fractions -> CAN WE JUST SET OUTLETS AND THAT'S IT? OR CLEANER WITH THE SAME FORMAT?
        getattr(m.fs, split_name).water_recovery.fix(1)
        getattr(m.fs, split_name).removal_fraction[:, "TDS"].fix(0.5)
        # I took these values from the WaterTAP3 nf model
        getattr(m.fs, split_name).removal_fraction[:, "TOC"].fix(0.5)
        getattr(m.fs, split_name).removal_fraction[:, "nitrates"].fix(0.5)
        # Also set pressure drops - for now I will set these to zero
        getattr(m.fs, split_name).deltaP_outlet1.fix(1e-4)
        getattr(m.fs, split_name).deltaP_outlet2.fix(1e-4)
    
    if link_to is not None: # TODO - potential for multiple streams
        connect_blocks(m = m, up1 = link_from, up2 = link_to, connection_type = None, 
                               stream_name = stream_name)
        
    return m

def add_splitter(m = None, split_name = None, with_connection = False, outlet_list = None, outlet_fractions = None,
                    link_to = None, link_from = None, stream_name = None, unfix = False): # in design
    
    
    setattr(m.fs, split_name, Separator1(default={
        "property_package": m.fs.water,
        "ideal_separation": False,
        "outlet_list": outlet_list}))
    
    if unfix == True:
        getattr(m.fs, split_name).split_fraction[0, key].unfix()    
    else:
        for key in outlet_fractions.keys():
            getattr(m.fs, split_name).split_fraction[0, key].fix(outlet_fractions[key])     
    
    return m

# TO DO MAKE THE FRACTION A DICTIONARY
def add_mixer(m = None, mixer_name = None, with_connection = False, inlet_list = None,
                    link_to = None, link_from = None, stream_name = None): # in design
    
    setattr(m.fs, mixer_name, Mixer1(default={
        "property_package": m.fs.water,
        "inlet_list": inlet_list}))
    
    return m






def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()