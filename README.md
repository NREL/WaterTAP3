# NAWI-WaterTAP3

A repo for the working version of WaterTAP3-Python and introductory tutorials to learn the basic functionalities of the model.

# NEEDS TO BE UPDATED FOR NEW MODEL UPDATES. INFORMATION BELOW RELATES TO OLD MODEL AND IS STILL FUNCTIONAL.



### Table of Contents
- [Requirements](https://github.com/NREL/HiPerFEWS#requirements)
- [Data](https://github.com/NREL/HiPerFEWS#data)
- [Tutorials](https://github.com/NREL/HiPerFEWS#tutorials)
- [ModelStructure](https://github.com/NREL/HiPerFEWS#modelstructure)

### Requirements; update these

### Data
Input data to run the model includes financial tables and assumptions on specific unit processes. Global data inputs are stored in `Data/` and unit-specific
assumptions are stored in the `.py` file of the unit process.

### Tutorials
These tutorials are meant to demonstrate the building blocks of creating a treatment train and basic simulation capabilities.
1. `WaterTAP3_DesignTrain_Tutorial.ipynb` Build, save, and load a treatment train from scratch (~10 mins)
2. `WaterTAP3_RunTrain_Tutorial.ipynb` Load a pre-existing treatment train, build the model, and run a simulation. Visualize total cost and levelized cost for each unit process. Compare cost calculation methods (~10 mins)
3. `WaterTAP3_RunTrain_Optimization_Tutorial.ipynb` Load a pre-existing treatment train and simulate an optimization example that selects the optimal membrane for an example RO process (~10 mins)

### Setup and execution of WaterTAP3 tutorials in Jupyter Notebook
1. Clone this repo
```
git clone https://github.com/NREL/NAWI-WaterTAP3.git
```
2. Load the WaterTAP3 environment.
3. Navigate to the repo folder in a terminal and open the Jupyter Notebook notebook dashboard.
4. In the notebook dashboard, open the desired *TUTORIALNAME*.ipynb notebook and follow the steps in the notebook. Execute cells by selecting them and pressing shift+enter.
