.. _data_input:

Data Input for WaterTAP3
============================================================

This section describes the data input .csv files contained in the ``data`` folder located in the
``watertap3`` directory. Many of these files applications and uses in WaterTAP3 are fully discussed
in other sections, but their headings and a basic descriptions are presented here.

|

.. _data_basic_unit:

``basic_unit.csv``
-----------------------------

This .csv file provides the inputs for unit process models that are initiated with the
``basic_unit`` module (fully discussed in the unit process section of this document).

Capital costs for basic units based on water or mass flow are calculated with the general form:

    .. math::

        C_{basic} = B f ^ {x}
|
The ratio of the unit water flow (or mass flow) to the basis water flow (or mass flow) is the
scaling factor `f` used to scale the unit costs to the basis costs:

    .. math::

        f = \frac{Q_{in}}{Q_{basis}}
|

More detail is available in the :ref:`basic_unit_unit` unit process documentation.

The headings for ``basic_unit.csv`` are:

* **unit_process**:  The unit process name provided by user input.

* **flow_basis**: The flow basis for the unit process costing curve. This is either volume
  [m3/hr] or mass [kg/hr] based.

* **cap_basis**: The capital basis for the unit process costing curve.

* **cap_exp**: The exponent `x` for the costing curve.

* **elect**: Electricity intensity for the unit [kWh/m3]. This value is fixed.

* **year**: Costing year for the unit.

* **kind**: Indicates whether the unit is based on volumetric or mass flow.
|

.. _data_case_study_basis:

``case_study_basis.csv``
----------------------------------

This .csv contains the foundational technoeconomic assumptions for the entire treatment train.
This input is also discussed in the :ref:`financials_financial_basis_inputs` section of this
documentation and inputs from this data file are used throughout the :ref:`financials` section of
this documentation.

The file is arranged into the following columns:

* **case_study**: The treatment facility name.

* **scenario**: The name of the scenario that the TEA values correspond with

* **value**: The number or name of the variable of interest

* **reference**: The name of the project that is using the model

* **variable**: The name of the variable of interest

    * *analysis_year*: The first year of the plant is/was in operation
    * *location_basis*: The country or U.S. state where the plant is located. Used for assigning the
      electricity cost [$/kwh]. Electricity costs are provided in the data folder.
    * *plant_life_yrs*: The initial design basis for plant-life and used for life cycle analysis
      calculations. The default plant-life is 20 years.
    * *land_cost_percent*: The assumed cost of land as a percentage of total fixed capital
      investment. This is a part of the total capital investment.
    * *working_capital_percent*: The assumed cost of working capital as a percentage of total fixed
      capital investment. This is a part of the total capital investment.
    * *salaries_percent*: The assumed cost of salaries as a percentage of total fixed capital
      investment. This is a part of the fixed operating costs.
    * *employee_benefits_percent*: The assumed cost of employee benefits as a percentage of total
      salary cost. This is a part of the fixed operating costs.
    * *maintenance_cost_percent*: The assumed cost of maintenance as a percentage of total fixed
      capital investment. This is a part of the fixed operating costs.
    * *laboratory_fees_percent*: The assumed cost of laboratory fees as a percentage of total fixed
      capital investment. This is a part of the fixed operating costs.
    * *insurance_and_taxes_percent*: The assumed cost of insurance and taxes as a percentage of
      total fixed capital investment. This is a part of the fixed operating costs.
    * *default_cap_scaling_exp*: The typical value for economy-of-scale for capital equipment.
      This is a part of the total and fixed capital investment.
    * *default_opex_scaling_exp*: The typical value for economy-of-scale for fixed plant costs.
      This is a part of the fixed operating costs.
    * *cap_by_equity*: The percent of the capital that is financed by equity rather than debt.
      This is a part of the capital recovery factor and LCOW calculations.
    * *debt_interest_rate*: The rate for loan financing of capital. This is a part of the capital
      recovery factor and LCOW calculations.
    * *exp_return_on_equity*: The expected return, interest rate, or cost of capital associated
      with the portion of capital financed with equity.
    * *default_tpec_multiplier*: The Total Purchased Equipment Cost (TPEC) to fixed capital
      investment. This is is a part of the total and fixed capital investment calculations.
    * *default_tic_multiplier*: The Total Installed Cost (TIC) to fixed capital investment. This
      is a part of the total and fixed capital investment calculations.

|

.. _data_case_study_water_sources:

``case_study_water_sources.csv``
-------------------------------------

Source water information is required to run the model. It can be selected from a list of
pre-existing case studies or entered manually using Jupyter Notebook or the input data tables in
this .csv file. There is no limit on the number of source water nodes for the model and the
treatment train design section details how to connect source waters to the treatment train.
Water flow rates (volumetric) and any constituent information required to calculate a unit
process performance or cost must exist in the source water information.

The source water input dataset is arranged into the following columns:

* **case_study**: The treatment facility name.

* **scenario**: The name of the scenario that the values correspond with, otherwise the default value will be used.

* **water_type**: The type/source of the water. This is where the intake unit water_type names must match the train input water_type process parameter in the treatment train design.

* **variable**: The name of the constituent or property of interest, such as ‘flow’ (required) or
  ‘tds’.

* **value**: The number of the variable of interest

* **unit**: The units used for the constituent, such as kg/m3 (constituent concentration)

* **reference**: The name of the project.

.. _data_catalyst_chemicals:

``catalyst_chemicals.csv``
--------------------------------

This .csv contains the price data used to calculate chemical and catalyst costs. WaterTAP3 uses
the unit per volume (typically a dose as kg/m3) and the price in this .csv to calculate costs.
More information on how this file is used is in the :ref:`financials_variable_operating_costs`
section of this documentation.

The columns are:

* **Material**: Name of the material, catalyst, or chemical used in the unit process. Note that
  when user input is required for a catalyst or chemical (e.g. in the :ref:`chlorination_unit` unit
  module), the input must match *exactly* with the name in this column.

* **Price_Units**: The units associated with the Price column. Typically $/kg.

* **Price**: The price per unit used to calculate costs.

* **Price_Year**: The pricing year. Used to calculate a chemical index factor.

* **Purity**: The purity of the chemical used for pricing.

.. _data_chemical_addition:

``chemical_addition.csv``
---------------------------------------------

This .csv contains data used to construct costing curves for different chemicals in the
``chemical_addition`` unit module. A user could add an entry to this .csv if there is a chemical
that is not represented here if they have a value for each column. More information on how this
unit works is provided in the ``chemical_addition`` unit module.

The columns are:

* **chem_name**: Name of the material, catalyst, or chemical used in the unit process. Note that
  the chemical name provided by user input must match *exactly* with the entry in this column.

* **base**: The costing basis for the chemical addition used to construct the costing curve.

* **exp**: The exponent for the chemical addition used to construct the costing curve.

* **ratio**: The ratio of the chemical in the solution used in the source costing data.

* **density**: The density [kg/m3] of the chemical in the solution used in the source costing data.


.. _data_chlorine_dose_cost:

``chlorine_dose_cost.csv``
---------------------------------------------

This .csv contains costing data used in the ``chlorination`` unit module. This data is used as
the basis to calculate the capital costs for chlorination based on unit flow and chlorine dose.
The data in this file comes from the `User's Manual for Integrated Treatment Train Toolbox -
Potable Reuse (IT3PR) Version 2.0 <https://www.twdb.texas
.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf>`_.

The columns are:

* **Cost**: The cost associated with the dose and flow [$1000].

* **Dose**: The chlorine dose used for costing [mg/L].

* **Flow_mgd**: The flow used for costing [MGD].

.. _data_constituent_removal:

``constituent_removal.csv``
---------------------------------------------

This .csv contains default and case specific constituent removal factors. More information on how
these factors are used is discussed in the :ref:`constituent_removal` section of this
documentation.

The columns are:

* **case_study**: The treatment facility name.

* **scenario**: The name of the scenario associated with the removal fraction.

* **units**: The units used for the constituent, such as kg/m3 (constituent concentration).

* **unit_process**: The unit process with the associated removal.

* **value**: The fraction or percent of the constituent in the source water that will be removed.

* **constituent**: The constituent being removed as named in the model.

* **calculation_type**: How the model will handle the values when the unit process changes the
  constituent level, ultraviolet transmittance, or pH.

    * *fractional_constituent_removal*: fractional removal
    * *absolute_value*: percent removal for ultraviolet transmittance
    * *delta_constituent_or_property*: when the pH is changed
|
* **reference**: The name of the project that is using the model.

* **data_reference**: The source of the data values and how values were calculated. Not used in
  the model but presented for user reference.

* **constituent_longform**: The longform name of the constituent. Not used in the model but
  presented for user reference.

.. _data_cost_curves:

``cost_curves.csv``
---------------------------------------------

This .csv contains summary outputs for different EPA model runs at different flow rates. The EPA
models can be found at https://www.epa.gov/sdwa/drinking-water-treatment-technology-unit-cost-models

Outputs from these EPA models is used for the following WaterTAP3 unit modules:

* :ref:`cation_exchange_unit`
* :ref:`anion_exchange_unit`
* :ref:`fixed_bed_pressure_vessel_unit`
* :ref:`fixed_bed_gravity_basin_unit`
* :ref:`multi_stage_bubble_aeration_unit`
* :ref:`packed_tower_aeration_unit`
* :ref:`gac_pressure_vessel_unit`
* :ref:`gac_gravity_unit`

Further explanation of how this data is used in those unit models is provided in the
documentation for each respective unit. In short, data from the ``flow_in``, ``cap_total``, and
``electricity_intensity`` columns are used to construct cost curves as a function of flow [m3/hr]
to determine capital costs and electricity intensity for each of these units.

The columns are:

* **unit_process**: The name of the WaterTAP3 unit module.

* **flow_in**: The flow [m3/hr] used to construct the cost curve.

* **cap_total**: Summation of the direct, indirect, and add-on costs from the EPA model runs.

* **electricity_intensity**: Electricity intensity data from EPA model runs.

* **tds_in**: Used by the Cation Exchange and Anion Exchange unit model to select the proper cost
  curve to use for the given TDS into the unit. If the unit does not have an entry in this
  column, it is not a function of this variable.

* **num_stage**: Used by the Multi-Stage Bubble Aeration unit model to select the proper cost
  curve based on the number of stages in the unit (determined from user input). If the unit does
  not have an entry in this column, it is not a function of this variable.

* **radon_rem**: Used by the Packed Tower Aeration unit model to determine the proper cost curve
  based on the target amount of radon removal (determined from user input). If the unit does not
  have an entry in this column, it is not a function of this variable.

* **ebct**: Used by the GAC - Gravity and GAC - Pressure Vessel unit models to determine the
  proper cost curve to used based on the EBCT (determined from user input). If the unit does not
  have an entry in this column, it is not a function of this variable.

The columns to the right of ``ebct`` are materials names specific to each unit model that uses
this .csv. If there is no entry for the unit model under one of these columns, that unit model
does not use that chemical. For example, the Cation Exchange unit model uses Ion_Exchange_Resin,
but does not use Acetic_Acid. The values in each of these columns correspond to a dose for that
chemical. WaterTAP3 takes the average of the entire column as the dose for that material or
chemical which is then used to calculate chemical costs.


.. _data_electricity_costs:

``electricity_costs.csv``
---------------------------------------------

This .csv contains location specific electricity costs used to determine the electricity costs
for the model.

The columns are:

* **location**: The location for the case study determined from the ``case_study_basis.csv``.

* **cost**: The $/kWh price of electricity in that location.

.. _data_plant_cost_indices:

``plant_cost_indices.csv``
---------------------------------

This .csv contains costing indices data.

There are four types of cost indices applied in WaterTAP3 – Capital, Catalysts and Chemicals,
Labor and Consumer Price Index. WaterTAP3 calculates each of these indices for 1990-2050.
These factors are used to help account for the time-value of investments and are used in the capital
and operating cost calculations.

* **Year**:  The year for the costing index.
* **Capital_Index**: The capital index for the given year.
* **CatChem_Index**: The catalyst and chemical index for the given year.
* **Labor_Index**: The labor index for the given year.
* **CPI_Index**: The consumer price index (CPI) for the given year.

Further information on how these values are used in WaterTAP3 is available in the
:ref:`financials_costing_indices_and_factors` section of this documentation.

.. _data_treatment_train_setup:

``treatment_train_setup.csv``
---------------------------------

This .csv is how treatment trains are setup in WaterTAP3. Please refer to the
:ref:`treatment_train_setup` section of this document for an in-depth description of this file
and how it is used to create custom treatment trains in WaterTAP3.

.. _data_uv_cost_interp:

``uv_cost_interp.csv``
-------------------------------

Contains interpolated data from `User's Manual for Integrated Treatment Train Toolbox -
Potable Reuse (IT3PR) Version 2.0 <https://www.twdb.texas
.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf>`_ used to calculate the
capital costs of a UV/AOP system as a function of flow, dose, and UV transmittance.

The columns are:

* **dose**: The UV dose [mJ/cm2] (from user input) used to determine capital costs.

* **flow**: The flow [MGD] used to determine capital costs.

* **uvt**: The UV Transmittance (from user input) used to determine capital costs.

* **cost**: The cost [$1000] as a function of dose, flow, and UVT.

More information in the :ref:`uv_aop_unit` model documentation.


.. _data_water_recovery:

``water_recovery.csv``
---------------------------------

This .csv contains fractions of water recovery for each unit in WaterTAP3. More information on
how this data is used in WaterTAP3 is available in the :ref:`water_recovery` section of this
documentation.

The columns are:

* **case_study**: The treatment facility name or default

* **scenario**: The name of the scenario that the values correspond with

* **unit_process**: The name of the unit process corresponding to the recovery value.

* **recovery**: How much water is recovered by each unit process (%)

* **reference**: The source of the recovery data




..  raw:: pdf

    PageBreak