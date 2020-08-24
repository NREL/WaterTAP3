from pylab import *
import shutil
import sys
import os.path
import pandas as pd
import numpy as np
import networkx as nx

def get_module(module_name):
        
    if module_name == 'media_filtration_twb':
        import media_filtration_twb as up
    
    if module_name == 'media_filtration_twb2':
        import media_filtration_twb2 as up    
    
    if module_name == 'microfiltration_twb':
        import microfiltration_twb as up
    
    if module_name == 'ultrafiltration_twb':
        import ultrafiltration_twb as up
    
    if module_name == 'uv_twb':
        import uv_twb as up
        
    if module_name == 'chlorination_twb':
        import chlorination_twb as up      

    if module_name == 'ro_twb':
        import ro_twb as up   
        
    if module_name == 'nanofiltration_twb':
        import nanofiltration_twb as up    
        
    if module_name == 'ro_bor':
        import ro_bor as up 
    
    if module_name == 'uvozone_twb':
        import uvozone_twb as up 
    
    if module_name == 'mbr':
        import mbr as up   
        
        
    return up


def main():
    print("importing something")
    # need to define anything here?

if __name__ == "__main__":
    main()














