# NAWI-WaterTAP3

A repo for the working version of WaterTAP3-Python and introductory tutorials to learn the basic functionalities of the model.

#### NEEDS TO BE UPDATED FOR NEW MODEL UPDATES. INFORMATION BELOW RELATES TO OLD MODEL AND IS STILL FUNCTIONAL.



### Table of Contents
- [Requirements](https://github.com/NREL/NAWI-WaterTAP3#requirements)
- [Data](https://github.com/NREL/NAWI-WaterTAP3#data)
- [Tutorials](https://github.com/NREL/NAWI-WaterTAP3#tutorials)
- [ModelStructure](https://github.com/NREL/NAWI-WaterTAP3#modelstructure)

### Requirements
We recommend you to use `conda` to manage WaterTAP3 environment. A YAML file `environment.yml` is provided for your convenience to build a `watertap3` environment.

### Data
Input data to run the model includes financial tables and assumptions on specific unit processes. Global data inputs are stored in `Data/` and unit-specific
assumptions are stored in the `.py` file of the unit process.

### Tutorials
These tutorials are meant to demonstrate the building blocks of creating a treatment train and basic simulation capabilities.
1. `WaterTAP3_DesignTrain_Tutorial.ipynb` Build, save, and load a treatment train from scratch (~10 mins)
2. `WaterTAP3_RunTrain_Tutorial.ipynb` Load a pre-existing treatment train, build the model, and run a simulation. Visualize total cost and levelized cost for each unit process. Compare cost calculation methods (~10 mins)
3. `WaterTAP3_RunTrain_Optimization_Tutorial.ipynb` Load a pre-existing treatment train and simulate an optimization example that selects the optimal membrane for an example RO process (~10 mins)

The following steps describe how to setup and execute WaterTAP3 tutorials in Jupyter Notebook:
1. Clone this repo
```
$ git clone https://github.com/NREL/NAWI-WaterTAP3.git
```
2. Load the WaterTAP3 environment and activate
```
$ conda env create --file environment.yml
$ conda activate watertap3
```
3. Navigate to the repo folder in a terminal and open the Jupyter Notebook dashboard
```
(watertap3) YOUR\PATH\TO\NAWI-WaterTAP3> $ jupyter notebook
```
4. Open the desired `TUTORIALNAME.ipynb` notebook and follow the steps as listed
