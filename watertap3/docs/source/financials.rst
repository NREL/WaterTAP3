Financials
============================================================

This page describes the different costing and pipe partiy metrics calculated in WaterTAP3 and how
they are calculated in the model.

Costing Indices and Factors
-----------------------------------

Costing indicies are available in ``plant_cost_indices.csv`` located in the data folder.

There are four types of cost indices applied in WaterTAP3 – Capital, Catalysts and Chemicals, Labor and Consumer Price Index.
These factors are used to help account for the time-value of investments and are used in the capital
and operating cost calculations. The following index factors are calculated for each process model in the treatment train based on:

* The user input for Analysis Year (for Cost Indices). This value is consistent across the entire treatment train.
* The Basis Year for the specific Process Model, Catalyst, Chemical, Replacement Part or other purchased item.
  This value is process-model-dependent with potentially different values across unit models
  within a treatment train.

The four cost indicies are (where `Y` is the year):

* Capital Cost Index Factor:

    .. math::

        f_{cap} = \frac{Y_{analysis}}{Y_{model}}
|
* Chemical Cost Index Factor:

    .. math::

        f_{chem} = = \frac{Y_{analysis}}{Y_{chem}}
|
* Labor Cost Index Factor:

    .. math::

        f_{labor} = \frac{Y_{analysis}}{Y_{model}}
|
* Other Cost Index Factor:

    .. math::

        f_{other} = \frac{Y_{analysis}}{Y_{model}}
|
There are also various assumed costing factors for each case study read in from ``case_study_basis.csv``:

* Electricity price:

    .. math::

        P
|
* Plant capacity utilization:

    .. math::

        f_{util}
|
* Land cost as percent of FCI:

    .. math::

        f_{land}
|
* Working capital as percent of FCI:

    .. math::

        f_{work}
|
* Salaries as percent of FCI:

    .. math::

        f_{sal}
|
* Maintenance costs as percent of FCI:

    .. math::

        f_{maint}
|
* Laboratory costs as percent of FCI:

    .. math::

        f_{lab}
|
* Insurance/taxes as percent of FCI:

    .. math::

        f_{ins}
|
* Benefits as percent of salary:

    .. math::

        f_{ben}
|
* Assumed plant lifetime:

    .. math::

        L
|
* Weighted Average Cost of Capital (debt interest rate):

    .. math::

        WACC
|
Financial Basis Inputs
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

|
System Capital Costs
-----------------------------------

The **Total Installed Costs (TIC)** are calculated for each individual unit process within the
treatment train.  This represents the cost of capital equipment plus the costs associated with
installing the equipment in the plant. These include any costs associated with foundations,
piping, insulation, assembly, buildings, electrical systems, and instrumentation. There are four
approaches to calculating TIC in WaterTAP3, depending on the process, that vary in their level of
detail:

* As a function of volumetric or mass flow only:

    * e.g. Basic units

|
* As function volumetric or mass flow and at least one other design criteria, such as chemical
  additions in which a dose is a required parameter:

    * e.g. chemical additions

|
* Based on physical performance/attributes of unit model, such as water recovery or constituent
  removal:

    * e.g. UV/AOP

|
* Multiple cost elements summed to calculate the TIC based on physical performance/attributes of
  unit model, such as pump and membrane costs for RO based on feed and osmotic pressures or
  evaporation pond costs that are based on evaporation rates, water recovery, and other design
  criteria:

    * e.g. Reverse osmosis

|
Depending on the costs assumed to be included in the unit’s capital cost calculation (one of the four
methods described above), some units may require additional cost multipliers to fully represent the TIC.
For these units, the calculated capital cost is multiplied by either the **Equipment Installation
Factor (EIF)** or the **Indirect Cost Factor (ICF)**. The EIF and ICF have default values of 3.4
(typical value range: 2.5-6.7) and 1.65 (typical value range: 1.2-1.7), respectively. After inclusion
of either of these factors (if necessary), TIC is assumed to include indirect costs associated with
constructing the process such as engineering costs, construction expenses, legal expenses, contractor fees, and contingencies.
This is the **unadjusted Fixed Capital Investment**:

    .. math::

        FCI_{unadj} = (EIF) TIC
|

Or:
    .. math::

        FCI_{unadj} = (ICF) TIC
|
Then TIC is adjusted by the Capital Cost Index Factor (defined above) to get the
FCI:

    .. math::

        FCI = f_{cap} FCI_{unadj}
|
Finally, to arrive at the **Total Capital Investment (TCI)**, land costs and the working capital are
added to the FCI:

    .. math::

        TCI = FCI + C_{land} + C_{work}
|
Where:

    .. math::

        C_{land} = f_{land} FCI
|
And:

    .. math::

        C_{work} = f_{work} FCI
|
System Operating Costs
-----------------------------------

WaterTAP3 considers both variable and fixed operating costs. Variable operating costs are dependent on the flow
rate and capacity utilization of each treatment technology, while fixed costs are dependent on
the capital costs of the treatment facility.

Variable Operating Costs
**********************************

Variable operating costs include any chemical additions, electricity costs, and other variable costs such as equipment
replacements (e.g., membrane replacement costs for a reverse osmosis unit).

Chemical costs are based on the chemical dosage [kg/m3] as defined in the model or by the user
for a given chemical addition. The costs of the chemicals can be found in the data folder. The
annual chemical costs [$MM/yr] are calculated as:

    .. math::

        C_{chem} = \sum_{k}^{n} D_k C_k Q_{in} f_{util}
|
Where `D` is the dose [kg/m3] of chemical `k` and `C` is the unit cost [$/kg] of chemical `k` as
found in ``catalysts_chemicals.csv``.

Electricity costs are based on the electricity intensity [kWh/m3] of each unit process, which is
provided as a constant or calculated based on the configuration of the treatment process (see unit models for details).
The annual electricity costs [$MM/yr] are calculated as:

    .. math::

        C_{elec} = \sum_{k}^{n} E_k Q_{in} f_{util} P
|
Where `E` is the electricity intensity [kWh/m3] for unit `k` and `P` is the price of electricity
for the locale [$/kWh].

There is also possibility for the inclusion of other operating costs that are unit specific. For
most units, there are no costs included in this category.

Fixed Operating Costs
**********************************

Employee salaries are calculated and scaled according to:

    .. math::

        C_{sal} = f_{labor} f_{sal} FCI_{unadj}
|
Employee benefits are calculated according to:

    .. math::

        C_{ben} = C_{sal} f_{ben}
|
Plant maintenance costs are calculated as:

    .. math::

        C_{maint} = f_{maint} FCI
|
Plant laboratory costs are calculated as:

    .. math::

        C_{lab} = f_{lab} FCI
|
Plant insurance and taxes are calculated according to:

    .. math::

        C_{ins} = f_{ins} FCI
|
Total & Annual Operating Costs
**********************************

The total fixed operating costs are calculated as:

    .. math::

        C_{op,tot} = C_{sal} + C_{ben} + C_{maint} + C_{lab} + C_{ins}
|
And annual operating costs are:

    .. math::

        C_{op,an} = C_{chem} + C_{elec} + C_{other} + C_{op,tot}
|
Pipe Parity Metrics
---------------------------------------

Levelized Cost of Water (LCOW)
**************************************

The Levelized Cost Of Water (LCOW) [$/m3] is one of the primary pipe-parity metrics provided as an
output from WaterTAP3.

    .. math::

        LCOW = \frac{ f_{recov} TCI + C_{op,an} }{V f_{util} }
|
With the capital recovery factor:

    .. math::

        f_{recov} = \frac{ WACC (1 + WACC) ^ L}{ (1 + WACC) ^ L - 1}
|
And `V` is the total volume of treated water that goes toward a beneficial use. In
WaterTAP3, this is the volume of water that flows through any unit designated as a "use" in the
input sheet ``treatment_train_setup.xlsx``.

The individual components that sum to the total LCOW are calculated as:

    .. math::

        LCOW_{TCI} = \frac{ f_{recov} TCI }{ V_{treat} f_{util} }
|
The electricity LCOW is calculated as:

    .. math::

        LCOW_{elec} = \frac{ C_{elec} }{ V_{treat} f_{util} }
|
The fixed operating LCOW is calculated as:

    .. math::

        LCOW_{op} = \frac{ C_{op,an} }{ V_{treat} f_{util} }
|
The chemical cost LCOW is calculated as:

    .. math::

        LCOW_{other} = \frac{ C_{chem}}{ V_{treat} f_{util} }
|
The other cost LCOW is calculated as:

    .. math::

        LCOW_{other} = \frac{ C_{other}}{ V_{treat} f_{util} }
|
The electricity intensity for the system is calculated as:

    .. math::

        E_{sys} = \frac{ C_{elec} }{ P V_{treat} }


..  raw:: pdf

    PageBreak
