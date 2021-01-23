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
        from src import media_filtration_twb as up

    if module_name == "media_filtration_twb2":
        from src import media_filtration_twb2 as up

    if module_name == "microfiltration_twb":
        from src import microfiltration_twb as up

    if module_name == "ultrafiltration_twb":
        from src import ultrafiltration_twb as up

    if module_name == "uv_twb":
        from src import uv_twb as up

    if module_name == "chlorination_twb":
        from src import chlorination_twb as up

    if module_name == "ro_twb":
        from src import ro_twb as up

    if module_name == "nanofiltration_twb":
        from src import nanofiltration_twb as up

    if module_name == "ro_bor":
        from src import ro_bor as up

    if module_name == "uvozone_twb":
        from src import uvozone_twb as up

    if module_name == "mbr":
        from src import mbr as up
    
    if module_name == "coag_and_floc":
        from src import coag_and_floc as up
    
    if module_name == "water_pumping_station":
        from src import water_pumping_station as up
    
    return up


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
