Costing Calculations
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

The four cost indicies are:

* Capital Cost Index Factor :math:`f_{cap}`

    * Analysis Year Index Value / Process Model Basis Year Index Value
* Chemical Cost Index Factor :math:`f_{chem}`

    * Analysis Year Index Value / Chemical Price Year Index Value
* Labor Cost Index Factor :math:`f_{labor}`

    * Analysis Year Index Value / Process Model Basis Year Index Value
* Other Cost Index Factor :math:`f_{other}`

    * Analysis Year Index Value / Process Model Basis Year Index Value


There are also various assumed costing factors for each case study read in from ``case_study_basis.csv``:

* Electricity price - :math:`P`

* Land cost as percent of FCI - :math:`f_{land}`

* Working capital as percent of FCI - :math:`f_{work}`

* Salaries as percent of FCI - :math:`f_{sal}`

* Maintenance costs as percent of FCI - :math:`f_{maint}`

* Laboratory costs as percent of FCI - :math:`f_{lab}`

* Insurance/taxes as percent of FCI - :math:`f_{ins}`

* Benefits as percent of salary - :math:`f_{ben}`

* Assumed plant lifetime - :math:`L`

* Weighted Average Cost of Capital (debt interest rate) - :math:`WACC`

* Plant capacity utilization - :math:`f_{util}`

System Capital Costs
-----------------------------------

The unadjusted Fixed Capital Investment :math:`FCI_{unadj}` are calculated on an individual unit process level
for each process represented in the treatment train. This represents the cost of capital
equipment plus the costs associated with installing the equipment in the plant. These include any
costs associated with foundations, piping, insulation, assembly, buildings, electrical systems,
and instrumentation. There are four approaches to calculating the unadjusted FCI in WaterTAP3,
depending on the process, that vary in their level of detail:

#. As a function of volumetric or mass flow only

    * e.g. Basic units

#. As function volumetric or mass flow and at least one other design criteria, such as chemical
   additions in which a dose is a required parameter

    * e.g. chemical additions

#. Based on physical performance/attributes of unit model, such as water recovery or constituent
   removal

    * e.g. UV/AOP

#. Multiple cost elements summed to calculate the TIC based on physical performance/attributes of unit model,
   such as pump and membrane costs for RO based on feed and osmotic pressures or evaporation pond
   costs that are based on evaporation rates, water recovery, and other design criteria.

    * e.g. Reverse osmosis

Depending on the costs assumed to be included in the unadjusted FCI calculation, some
units may require additional cost multipliers to adjust and fully represent the FCI. For these
units, the FCI (unadjusted – as calculated by one of the four methods above) is multiplied by the
Equipment Installation Factor :math:`f_{TPEC}` with a default value of 3.4 based on the published
values between 2.5 and 6.7 or the Indirect Cost Factor :math:`f_{TIC}` with a default value of
1.65 based on published values between 1.2 and 1.7 (Peters, Timmerhaus, & West, 1991). After
inclusion of either of these factors (if necessary), :math:`FCI_{unadj}` is assumed to include
indirect costs associated with constructing the process such as engineering costs,
construction expenses, legal expenses, contractor fees, and contingencies.

Units that use :math:`f_{TIC}` in unadjusted FCI calculation:

* Reverse osmosis

Units that use :math:`f_{TPEC}` in unadjusted FCI calculation:

* Coagulation/Flocculation
* Media Filtration
* Iron & Manganese Removal
* Sedimentation
* Chemical additions
* Static Mixer

If the unit is not included in either of the costs above, inclusion of either of these factors
was not necessary based on the reference used for costing.

Then :math:`FCI_{unadj}` is adjusted by the Capital Cost Index Factor (defined above) to get the
FCI:

    .. math::

        FCI = FCI_{unadj} f_{cap}

Finally, to arrive at the Total Capital Investment (TCI), land costs :math:`C_{land}` and the
working capital :math:`C_{work}` are added to the FCI:

    .. math::

        TCI = FCI + C_{land} + C_{work}

Where

    .. math::

        C_{land} = f_{land} FCI

        C_{work} = f_{work} FCI





System Operating Costs
-----------------------------------

WaterTAP3 considers both variable and fixed operating costs. Variable operating costs are dependent on the flow
rate of each treatment technology, while fixed costs are dependent on the capital costs of the treatment facility.

Variable Operating Costs
**********************************

Variable operating costs include any chemical additions, electricity costs, and other variable costs such as equipment
replacements (e.g., membrane replacement costs for a reverse osmosis unit).

Chemical costs are based on the chemical dosage (kg/m3) as defined in the model or by the user
for a given chemical addition. The costs of the chemicals can be found in the data folder. The
annual chemical costs  :math:`C_{chem}` ($MM/yr) are calculated as:

    .. math::

        C_{chem} = \Big( \sum_{k}^{n} D_k C_k \Big) Q_{in} f_{util}

Where :math:`D_k` is the dose (kg/m3) of chemical :math:`k` and :math:`C_k` is the cost ($/kg) of
chemical :math:`k` as found in ``catalysts_chemicals.csv``.

Electricity costs are based on the electricity intensity (kWh/m3) of each unit process, which is
provided as a constant or calculated based on the configuration of the treatment process (see unit models for details).
The annual electricity costs :math:`C_{elec}` ($MM/yr) are calculated as:

    .. math::

        C_{elec} = \Big( \sum_{k}^{n} E_k \Big) Q_{in} f_{util} P

Where :math:`E_k` is the electricity intensity (kWh/m3) for unit :math:`k` and :math:`P` is the
price of electricity for the locale ($/kWh).

There is also possibility for the inclusion of other operating costs :math:`C_{other}` that are
unit specific. For most units, there are no costs included in this category.

Fixed Operating Costs
**********************************

Employee salaries :math:`C_{sal}` are calculated and scaled according to:

    .. math::

        C_{sal} = f_{labor} f_{sal} FCI_{unadj}

Employee benefits :math:`C_{ben}` are calculated according to:

    .. math::

        C_{ben} = C_{sal} f_{ben}

Plant maintenance costs :math:`C_{maint}` are calculated as:

    .. math::

        C_{maint} = f_{maint} FCI

Plant laboratory costs :math:`C_{lab}` are calculated as:

    .. math::

        C_{lab} = f_{lab} FCI

Plant insurance and taxes :math:`C_{ins}` are calculated according to:

    .. math::

        C_{ins} = f_{ins} FCI


Total & Annual Operating Costs
**********************************

The total fixed operating costs :math:`C_{op,tot}` are calculated as:

    .. math::

        C_{op,tot} = C_{sal} + C_{ben} + C_{maint} + C_{lab} + C_{ins}

And annual operating costs :math:`C_{op,an}` are:

    .. math::

        C_{op,an} = C_{chem} + C_{elec} + C_{other} + C_{op,tot}


Pipe Parity Metrics
---------------------------------------

Levelized Cost of Water (LCOW)
**************************************

The Levelized Cost Of Water (LCOW) ($/m3) is one of the primary pipe-parity metrics provided as an
output from WaterTAP3.

    .. math::

        LCOW = \frac{ f_{recov} TCI + C_{op,an} }{V_{treat} f_{util} }

Where :math:`f_{recov}` is the capital recovery factor calculated using the WACC and plant
lifetime :math:`L`:

    .. math::

        f_{recov} = \frac{ WACC (1 + WACC) ^ L}{ (1 + WACC) ^ L - 1}

And :math:`V_{treat}` is the total volume of treated water that goes toward a beneficial use. In
WaterTAP3, this is the volume of water that flows through any unit designated as a "use" in the
input sheet ``treatment_train_setup.xlsx``.

Other metrics can be calculated with a similar equation as LCOW for each cost category. The TCI
LCOW is calculated as:

    .. math::

        LCOW_{TCI} = \frac{ f_{recov} TCI }{ V_{treat} f_{util} }


The electricity LCOW is calculated as:

    .. math::

        LCOW_{elec} = \frac{ C_{elec} }{ V_{treat} f_{util} }

The fixed operating LCOW is calculated as:

    .. math::

        LCOW_{op} = \frac{ C_{op,an} }{ V_{treat} f_{util} }

The chemical and other operating cost LCOW is calculated as:

    .. math::

        LCOW_{other} = \frac{ C_{chem} + C_{other} }{ V_{treat} f_{util} }


You could also easily calculate each cost category as a fraction of LCOW. For example, the
electricity cost as a fraction of LCOW :math:`F_{elec}` is calculated according to:

    .. math::

        F_{elec} = \frac{ C_{elec} }{ f_{recov} TCI + C_{op,an} }

The electricity intensity for the system :math:`E_{sys}` is calculated as:

    .. math::

        E_{sys} = \frac{ C_{elec} }{ P V_{treat} }


Costing Module
----------------------------------------

.. autoclass:: watertap3.utils.financials
    :members: get_complete_costing, get_system_specs, get_system_costing, global_costing_parameters
    :exclude-members: SystemSpecs, get_ind_table
