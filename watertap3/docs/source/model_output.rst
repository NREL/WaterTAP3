.. _model_output:

Model Output for WaterTAP3
============================================================

This section describes the model results files and directory.

|


Directory Structure
-----------------------------

Directory Structure for baseline analyses::

    Source Water/
    | -- baseline/
    |     | -- Case study_baseline.csv (Case study specific baseline full results. Multiple files)
    |     | -- Source water_baseline.csv (Combined case study baseline full results)
    |     | -- Summary table_Source Water_baseline.csv (Key baseline results for source water)
    |     | -- figures/  (Treatment category level results)
    |     |	| -- Annual O&M Costs_baseline
    |     |	| -- Electricity Intensity System Treated_baseline
    |     |	| -- LCOW_Cost_Category
    |     |	| -- Total Capital Investment (TCI)_baseline
    |     |	| -- Treatment Category LCOW_baseline
    |     | -- csvs/
    |     |	| -- CSV files used to create figures in “figures” directory
    |     | -- by_unit/
    |     |	| -- CSV and figures for key cost results by unit process within the treatment train
    | -- baseline_and_whatifs/
    |     | -- Same structure as baseline folder but includes what-if scenarios
    | -- sensitivities/
    |     | -- Figure of LCOW ($/m3), electricity intensity (kwh/m3) and water recovery (%) for each sensitivity scenario (20 runs per scenario).
    |     | -- CSV of results used to create the figure.





Results File
----------------------------------

Flow rates, constituent levels, and key cost attributes are reported for each unit process in a treatment train. System-level metrics including aggregate costs, energy use, recovery rate, and Levelized Cost of Water (LCOW) are also included.

The results table is arranged into the following columns (bold):

**Case Study**:  The treatment facility name

**Metric**:  The category for what is being measured. Examples are:

•	Electricity
•	Cost
•	Annual Cost
•	Water Flow
•	Inlet Constituent Density
•	Outlet Constituent Density
•	Waste Constituent Density
•	Inlet Constituent Total Mass
•	Outlet Constituent Total Mass
•	Waste Constituent Total Mass


**Scenario**:  The name of the scenario that the values correspond with
ex. baseline or what-if scenarios

**Unit Process Name**:  The unit process name or “System”.

**Unit**:  The units used for the results value. Examples are:

•	Electricity intensity: kWh/m3
•	Total costs: $MM
•	Annual costs: $MM/yr
•	Flow rates: m3/s
•	Water constituents: kg, kg/m3

**Value**: The outlet result at the end of a unit process or the entire treatment train.

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
•	Names of constituents in the source water	[kg] and [kg/m3]


The results for an entire treatment train are:

•	System Total Capital Investment (TCI)			[$MM]
•	System Catalysts and Chemicals				    [$MM]
•	System Electricity						        [$MM]
•	System Catalysts and Chemicals				    [$MM/yr]
•	System Electricity						        [$MM/yr]
•	System Total Operating Cost				        [$MM/yr]
•	System LCOW					        [$/m3]
•	Electricity Intensity					        [kWh/m3]
•	Water Recovery 						               [%]

**Unit kind**: Intake, treatment process, or end-use as represented in the model

**Treatment Category**:  Influent Storage and Pumping, Pre-treatment, Principal treatment, Product
Storage, Product Distribution, Waste Treatment and Valorization, Waste Product Storage and Disposal, Post-treatment



..  raw:: pdf

    PageBreak


