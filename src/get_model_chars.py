from pylab import *
import shutil
import sys
import os.path
import pandas as pd
import numpy as np
import networkx as nx


def get_link_variable(m, variable):
    if variable == "Flow":
        return m.FlowInLinkSegments
    if variable == "TOC":
        return m.TOCInLinkSegments
    if variable == "Nitrate":
        return m.NitrateInLinkSegments
    if variable == "Cost":
        return m.TotalCostInLinkSegments
    if variable == "TDS":
        return m.TDSInLinkSegments


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
