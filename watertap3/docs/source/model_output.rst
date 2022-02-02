.. _model_output:

Model Output for WaterTAP3
============================================================

This section describes the model results files and directory.

|


Directory Structure
-----------------------------

Directory structure for results::

    source/
    | -- baseline/
    |     | -- casestudy_baseline.csv (Case study specific baseline full results.)
    |     | -- source_baseline_results.csv (Combined results for all case studies.)
    |     | -- summary_table_source_baseline.csv (Key baseline results for source water.)
    |     | -- figures/  (Treatment category level results)
    |     |	| -- Annual O&M Costs_baseline
    |     |	| -- Electricity Intensity System Treated_baseline
    |     |	| -- LCOW_Cost_Category
    |     |	| -- Total Capital Investment (TCI)_baseline
    |     |	| -- Treatment Category LCOW_baseline
    |     | -- csvs/
    |     |	| -- CSV files used to create figures in “figures” directory
    |     | -- by_unit/
    |     |	| -- CSV and figures for key cost results by unit process.
    | -- baseline_and_whatifs/
    |     | -- Same structure as baseline folder but for both baseline and what-if scenarios.
    | -- sensitivities/
    |     | -- source_sensitivities.csv (Combined results of all sensitivity analysis.)
    |     | -- casestudy_scenario_sensitivity.csv (Sensitivity results.)



|
|

Results File
----------------------------------

Flow rates, constituent levels, and key cost attributes are reported for each unit process in a treatment train. System-level metrics including aggregate costs, energy use, recovery rate, and Levelized Cost of Water (LCOW) are also included.

The results table is arranged into the following columns (bold):

**Unit Process Name**:  The unit process name or “System”.

**Variable**: The variable name that corresponds to the value. Examples are:

•	Electricity Intensity 					    [kWh/m3]
•	Total Capital Investment (TCI)				[$MM]
•	Catalysts and Chemicals					    [$MM/yr]
•	Electricity							        [$MM/yr]
•	Other Variable Operating 				    [$MM/yr]
•	Fixed Operation						        [$MM/yr]
•	Annual O&M Costs					        [$MM/yr]
•	Inlet Water						            [m3/s]
•	Outlet Water						        [m3/s]
•	Waste Water						            [m3/s]
•	Names of constituents in the source water	[kg/s] and [kg/m3]


Example results for the entire treatment train are:

•	System Total Capital Investment (TCI)			[$MM]
•	System Catalyst and Chemical Cost			    [$MM]
•	System Electricity Cost					        [$MM]
•	System Catalyst and Chemical Cost (Annual)	    [$MM/yr]
•	System Electricity Cost (Annual)					        [$MM/yr]
•	System Total Operating Cost	(Annual)			        [$MM/yr]
•	System LCOW					                [$/m3]
•	System Electricity Intensity					        [kWh/m3]
•	Water Recovery 						               [%]

**Value**: The model result for the Variable in that row

**Metric**:  The category for what is being measured. Examples are:

•	Electricity
•	Cost
•	Annual Cost
•	Water Flow
•	Inlet Concentration
•	Outlet Concentration
•	Waste Concentration
•	Inlet Mass Flow
•	Outlet Mass Flow
•	Waste Mass Flow

**Unit**:  The units used for the results value. Examples are:

•	LCOW: $/m3
•	Electricity intensity: kWh/m3
•	Total costs: $MM
•	Annual costs: $MM/yr
•	Flow rates: m3/s
•	Water constituents: kg/s, kg/m3

**Unit Kind**: Intake, treatment process, or end-use as represented in the model

**Treatment Category**:  Influent Storage and Pumping, Pre-treatment, Principal treatment, Product
Storage, Product Distribution, Waste Treatment and Valorization, Waste Product Storage and Disposal, Post-treatment

**Case Study**:  The treatment facility name

**Scenario**:  The name of the scenario that the values correspond with ex. baseline or what-if scenarios

Note: the **python_var** and **python_param** columns are presented for ease of access if the user wants to access these results programatically. If the Unit Process Name is "System," 
the **python_param** column is the name of the Variable in the model. The **python_var** is the name of the unit on the flowsheet and is also the name of the unit from the input sheet.

Sensitivity Analysis File
----------------------------------

Results files for sensitivity analysis are arranged into the following columns
Sensitivity results columns:

*	**sensitivity_var** – indicates the variable around which sensitivity was done:

        * plant_cap = Plant Capacity Utilization
        * wacc = Weighted Average Cost of Capital (WACC) 
        * tds_in = TDS concentration into treatment train
        * flow_in = volumetric flowrate into treatment train
        * plant_life = plant lifetime
        * elect_price = electricity price
        * component_replacement = maintenance cost as a percentage of FCI 
        * If there was sensitivity around a reverse osmosis unit, an entry in this column is:
            
            * [RO unit name from input sheet]_[sensitivity variable]
            * e.g. if the RO is named “ro_first_pass” and sensitivity was around the pressure, the entry would be “ro_first_pass_pressure”
            * RO sensitivity variables:
            
                * membrane_area = area for the RO unit
                * pressure = feed pressure for RO unit
                * factor_membrane_replacement = membrane replacement factor for RO unit
|
*	**baseline_sens_value** – the value of the sensitivity variable specified in “sensitivity_var” column used in the baseline model
*	**scenario_value** – the value of the sensitivity variable specified in “sensitivity_var” column used in the sensitivity analysis used to generate results for that row
*	**sensitivity_var_norm** – the value of the sensitivity variable in the sensitivity analysis relative to the value in the baseline analysis
*	**lcow** – system LCOW for the sensitivity analysis
*	**lcow_norm** – system LCOW for the sensitivity analysis normalized to the LCOW for the baseline case (LCOWsens / LCOWbaseline)
*	**lcow_diff** – difference between sensitivity LCOW and baseline LCOW (LCOWsens - LCOWbaseline)
*	**baseline_lcow** – LCOW for the baseline analysis
*	**water_recovery** – system water recovery for the sensitivity analysis
*	**water_recovery_difference** – difference between water recovery in the sensitivity analysis and in the baseline analysis
*	**treated_water_vol** – treated water flow [m3/s] for the sensitivity analysis
*	**baseline_treated_water** – treated water flow for the baseline analysis
*	**treated_water_norm** – treated water flow for sensitivity analysis relative to the treated water flow for the baseline analysis (Qsens / Qbaseline)
*	**elec_lcow** – electricity LCOW for the sensitivity analysis
*	**elec_lcow_difference** – difference between electricity LCOW for the sensitivity analysis and the baseline analysis
*	**baseline_elect_int** – system electricity intensity for the baseline analysis
*	**elec_int** – system electricity intensity for the sensitivity analysis
*	**elect_int_norm** – system electricity intensity for the sensitivity analysis relative to the system electricity intensity for the baseline analysis (Esens / Ebaseline)
*	**scenario_name** – the name of the sensitivity analysis scenario in a more human-readable form
*	If there was sensitivity around a reverse osmosis unit:

            * **ro_pressure** – feed pressure for the RO unit for sensitivity analysis
            * **ro_press_norm** – feed pressure for the RO unit for sensitivity analysis relative to feed pressure for the RO unit for the baseline analysis
            * **ro_area** – membrane area for the RO unit for sensitivity analysis
            * **ro_area_norm** – membrane area for the RO unit for sensitivity analysis relative to membrane area for the RO unit for the baseline analysis
            * **mem_replacement** – membrane replacement factor used in sensitivity analysis
            * **Note**: these columns are empty if the sensitivity analysis was not done around an RO unit



..  raw:: pdf

    PageBreak


