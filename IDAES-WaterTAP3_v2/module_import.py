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
        import sw_onshore_intake as up  
        
    if module_name == "holding_tank":
        import holding_tank as up 
        
    if module_name == "tri_media_filtration":
        import tri_media_filtration as up
        
    if module_name == "cartridge_filtration":
        import cartridge_filtration as up 
        
        
        
        
     
        
    return up


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
