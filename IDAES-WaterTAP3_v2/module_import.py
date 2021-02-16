from pylab import *
import shutil
import sys
import os.path
import pandas as pd
import numpy as np
import networkx as nx

# TODO FIX IMPORTS
# black
def get_module(module_name):

    if module_name == "media_filtration_twb":
        import media_filtration_twb as up

    if module_name == "media_filtration_twb2":
        import media_filtration_twb2 as up

    if module_name == "microfiltration_twb":
        import microfiltration_twb as up

    if module_name == "ultrafiltration_twb":
        import ultrafiltration_twb as up

    if module_name == "uv_twb":
        import uv_twb as up

    if module_name == "chlorination_twb":
        import chlorination_twb as up

    if module_name == "ro_twb":
        import ro_twb as up

    if module_name == "nanofiltration_twb":
        import nanofiltration_twb as up

    if module_name == "ro_bor":
        import ro_bor as up

    if module_name == "uvozone_twb":
        import uvozone_twb as up

    if module_name == "mbr":
        import mbr as up
    
    if module_name == "coag_and_floc":
        import coag_and_floc as up
    
    if module_name == "water_pumping_station":
        import water_pumping_station as up
        
    if module_name == "media_filtration":
        import media_filtration as up
        
    if module_name == "coag_and_floc":
        import coag_and_floc as up    
     
    if module_name == "lime_softening":
        import lime_softening as up 
     
    if module_name == "ro_deep":
        import ro_deep as up 
    
    if module_name == "ro_deep_scnd_pass":
        import ro_deep_scnd_pass as up
        
    if module_name == "treated_storage_24_hr":
        import treated_storage_24_hr as up 
    
    if module_name == "sedimentation":
        import sedimentation as up 
        
    if module_name == "water_pumping_station":
        import water_pumping_station as up 
        
    if module_name == "sulfuric_acid_addition":
        import sulfuric_acid_addition as up 
        
    if module_name == "sodium_bisulfite_addition":
        import sodium_bisulfite_addition as up 
    
    if module_name == "co2_addition":
        import co2_addition as up 
    
    if module_name == "ammonia_addition":
        import ammonia_addition as up 
    
    if module_name == "municipal_drinking":
        import municipal_drinking as up 
        
    if module_name == "sw_onshore_intake":
        #print("goes in", module_name)
        import sw_onshore_intake as up  
        
    if module_name == "holding_tank":
        import holding_tank as up 
        
    if module_name == "tri_media_filtration":
        import tri_media_filtration as up
        
    if module_name == "cartridge_filtration":
        import cartridge_filtration as up 
        
    if module_name == "backwash_solids_handling":
        import backwash_solids_handling as up
    
    if module_name == "surface_discharge":
        import surface_discharge as up
        
    if module_name == "landfill":
        import landfill as up
        
    if module_name == "coagulant_addition":
        import coagulant_addition as up
    
    if module_name == "fecl3_addition":
        import fecl3_addition as up
    
    if module_name == "caustic_soda_addition":
        import caustic_soda_addition as up
    
    if module_name == "static_mix":
        import static_mix as up

    if module_name == 'uv_aop':
        import uv_aop as up

    if module_name == "anti_scalant_addition":
        import anti_scalant_addition as up 
       
    if module_name == "fe_mn_removal":
        import fe_mn_removal as up 

        
    if module_name == "well_field":
        import well_field as up 
        
        
     
        
    return up


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
