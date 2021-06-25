Data Input Files
============================================================

There are several input files required to run WaterTAP3. All of these files are located in the
data subdirectory of the watertap3 directory, e.g. ``~/watertap3/watertap3/data``.

Treatment Train Setup
------------------------------

``data/treatment_train_setup.xlsx``

This is the input file used to arrange unit processes in the proper order and with the
proper flows according to the users design.

The columns are:

* **CaseStudy**: The treatment facility name

* **Reference**: The name of the project that is using the model

* **Scenario**: The name of the scenario that the values correspond with, used to match water
  recovery and constituent removal rates specific to the case study-scenario combination.

* **Unit**: The unit process to be added to the train. The unit name in this column must match the
  exact naming convention of the unit process in the WaterTAP3 model.

* **Type**: The role of the unit process along the treatment train.

    * Options are "intake", "treatment", "use", or "waste"

    * "intake" types are declared for units that begin the treatment train and have a source water.

    * "use" types are declared for units considered to have a treated water product. The volume
      of water that goes through these units is used to calculate LCOW. These units do not have
      an outlet or waste port connected to another unit (i.e. they are a terminal unit)

    * "treatment" types are declared for treatment units. These units can have any number of
      inlet and outlet ports, but have only one waste outlet.

    * "waste" types are declared for units that handle terminal waste streams for the facility.
      These units can have any number of inlet ports but don't have outlet or waste ports that
      connect to another unit (i.e. they are a terminal unit).

* **UnitName**: The unit process name specific to the train being built is defined by the user.

    * Each unit name must be unique. For example, if there are two of the same unit processes
      under the **Unit** column (e.g. ``chlorination``), the first chlorination unit name could be
      ``chlorination_a`` and the second could be ``chlorination_b``. The unit in this column is
      connected to the unit defined in the **ToUnitName** column.

* **ToUnitName**: The **UnitName** for a unit process in a different row that connects to the
  **UnitName** for the current row. The user can include any number of destination units by
  including them in this column separated by a column and with *no space in between*.

    * Example: If you wanted ``media_filtration`` to split outlet flow 50/50 to
      ``anti_scalant_addition`` and ``chlorination_b``, you would put
      ``anit_scalant_addition,chlorination_b`` in the **ToUnitName** column for the
      ``media_filtration`` row.

    * This is better explained in the example below.

* **FromPort**: For each unit process identified in the **ToUnitName** column, there needs to be a
  corresponding port, either “outlet” or “waste”, that tells the model how to connect the current
  unit to the next unit in the train. If there is more than one port, the types are separated by a
  comma and *no space in between*.

    * Example: If you wanted the treated flow from ``media_filtration`` to go to
      ``anti_scalant_addition`` and the waste flow to go to ``backwash_solids_handling``, put
      ``outlet,waste`` in the **FromPort** column for the ``media_filtration`` row.

* **Parameter**: Used to characterize each unit process. All parameter formats are provided as python dictionaries,
  meaning the cell text must be enclosed by curly braces ``{ }``, have quotation marks around
  parameter names, commas between each parameter, and a colon ``:`` separating the parameter name
  and the value for that parameter.

    * Example: If ``“chemical_name”``, ``“contact_time”``, ``“ct”``, ``“mass_transfer”``, and
      ``“aop”`` are the parameter names, the proper format is:

        * ``{'chemical_name': 'Hydrogen_Peroxide', 'contact_time': 1, 'ct': 1, 'mass_transfer': 0.8, 'aop': False}``

    * Specifics for required and optional unit parameters for each unit are provided in the
      documentation for each unit model.

Treatment Train Example
*****************************

Below is an example treatment train input file with various unit processes, flow splits, and
waste streams.

.. image:: images/example_treatment_train.png
   :scale: 90%
   :align: center

* Row 2: ``well_field`` is the "intake" unit for the treatment train. All the flow from the
  ``well_field`` flows to ``media_filtration``.

    * "intake" units must have a ``water_type`` in the **Parameter** column that corresponds to
      the proper source water found in ``case_study_water_sources.csv``

    * The source water name must be in quotes and enclosed in brackets ``[ ]`` even if there is
      only one source water for the treatment train. This is to facilitate the inclusion of
      multiple source waters for a single intake.

* Row 3: Outlets for ``media_filtration`` flows to both ``cartridge_filtration`` and
  ``ro_first_stage``. There is also a waste stream that flows to ``landfill``.

    * You can designate any split fraction you want in the **Parameter** column by using the
      ``"split_fraction"`` parameter.

    * Split fractions provided with ``"split_fraction"`` must be provided in brackets ``[ ]`` and
      the order of values in the split fraction correspond to the order of units in **ToUnitName**.
      In this case, 65% of the flow from ``media_filtration`` flows to ``cartridge_filtration``
      and 35% flows to ``anit_scalant_addition``.

    * Note that ``"split_fraction"`` must be provided in **Parameter** even if the split is 50/50.

* Row 4: Flow from ``cartridge_filtration`` flows to ``decarbonator``.

    * Note that this flow stream is bypassing the two-stage reverse osmosis process. You can
      arrange flows in any configuration desired provided the input sheet is correct.

* Row 5: The chemical addition unit ``anti_scalant_addition`` receives 35% of flow from
  ``media_filtration``

    * This unit requires a ``"dose"`` in the **Parameter** column to run correctly.

* Row 6: The permeate stream from ``ro_first_stage`` flows to ``decarbonator`` and the reject
  stream flows to ``ro_second_stage``

    * Note that the **ToUnitName** column does not match the **Unit** column. The user can
      provide any name they want for the unit in **ToUnitName**, but the **Unit** entry must match
      *exactly* the name of the Python file for that unit (without '.py' appended)

    * In this case, because there are two ``reverse_osmosis`` units, they must have different
      names for WaterTAP3 to correct the unit flows properly.

* Row 7: The permeate stream from ``ro_second_stage`` also flows to ``decarbonator`` and the reject
  ("waste") stream flows to ``landfill``

    * Both ``reverse_osmosis`` units require an ``"erd"`` parameter to indicate if the model
      should include an energy recovery device.

* Row 8: The ``decarbonator`` is receiving flows from ``cartridge_filtration``,
  ``ro_first_stage``, and ``ro_second_stage``.

    * The ``decarbonator`` is a basic unit so must have a **Parameter** ``"unit_process_name"``
      that matches the name of the desired unit in ``basic_unit.csv``

* Row 9-11: For each of these rows, 100% of the flow from the **UnitName** is flowing to
  **ToUnitName**.

    * Each have entries in **Parameters** as required.

* Row 12: For this treatment train ``municipal_drinking`` is the "use". Any water that flows
  through this unit is used to calculate LCOW.

    * The **ToUnitName** is empty for "use" units since flow does not go anywhere from here. It
      is a terminal unit. Similarly, it does not need an entry in **FromPort**


Water Recovery
--------------------

``data/water_revovery.csv``

Water recovery is represented as the fraction (between zero and one) of water recovered (treated)
after it passes through a unit process.  Case-study based water recovery is given for certain unit processes
if the case study has a unique recovery rate, otherwise default value are used. The total system water
recovery is calculated as:


The mass balance for water flow for each unit process is:

The columns are:

* **case_study**: The treatment facility name or default

* **scenario**: The name of the scenario that the values correspond with

* **unit_process**: The name of the unit process corresponding to the recovery value.

* **recovery**: How much water is recovered by each unit process (%)

* **reference**: The source of the recovery data


Constituent Removal
------------------------

``data/constituent_removal.csv``

Constituent removal is represented as the fraction (between zero and one) of the mass of the constituent
being removed after it is passes through a unit process. Case-study based constituent removal is given
for certain unit processes if the case study has a unique recovery rate, otherwise default value are used.

The total system constituent removal is calculated as:


The constituent removal data table states how much each unit process in each treatment facility removes
a given water constituent.  The model uses the information about the constituents in the source water
as well as the removal rates of each unit process given in this constituent removal table to calculate
constituent levels in the output water.

The constituent removal input dataset is arranged into the following columns:

* **units**: The units used for the constituent, such as kg/m3 (constituent concentration)

* **calculation_type**: How the model will handle the values when the unit process changes the
  constituent level, ultraviolet transmittance, or pH.

    * *fractional_constituent_removal*: fractional removal

    * *absolute_value*: percent removal for ultraviolet transmittance

    * *delta_constituent_or_property*: when the pH is changed

* **unit_process**: Which unit process is removing the constituent.

* **case_study**: The treatment facility name.

* **value**: The fraction or percent of the constituent in the source water that will be removed.

* **data_source**: The source of the data values and how values were calculated.

* **constituent**: The constituent being removed as named in the model

* **scenario**: The name of the scenario that the values correspond with

* **reference**: The name of the project that is using the mode

Financial Basis Inputs for TEA Calculations
-----------------------------------------------

The case study basis input data table contains the foundational technoeconomic assumptions for the entire treatment train.

The input dataset is arranged into the following columns:

* **case_study**:  The treatment facility name.

* **scenario**: The name of the scenario that the TEA values correspond with

* **value**:  The number or name of the variable of interest

* **reference**:  The name of the project that is using the model

* **variable**: The name of the variable of interest

    * *analysis_year*:  The first year of the plant is/was in operation

    * *location_basis*: The country or U.S. state where the plant is located. Used for assigning the
      electricity cost ($/kwh). Electricity costs are provided in the data folder.

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

    * *default_opex_scaling_exp*:  The typical value for economy-of-scale for fixed plant costs.
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