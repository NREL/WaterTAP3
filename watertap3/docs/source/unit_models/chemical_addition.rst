Generic Chemical Addition
=====================================

This unit is for a generic chemical addition that does not have a specific unit model in WaterTAP3.

In general, costs for chemical additions in WaterTAP3 are a function of the chemical dose and the
flow in. The chemical solution flow is calculated from these two values and assumed solution
densities to use in a cost curve. All chemical additions assume 2 chemical addition units.

.. tip:: You can add any chemical you want to the ``catalyst_chemicals.csv`` located in the data
        folder. The entry must include a price per kg and a year for the unit price.

Capital Costs
---------------
.. important:: Because this is a generic chemical addition unit model, the costs are based off of the
          sulfuric acid addition costing parameters. The model assumes a solution density of 1000
          kg/m3.

The chemical solution flow :math:`\big( S \big)` is used in a cost curve of the general form:

:math:`\text{Cost} = \big( S a \big) ^ b`

For a single sulfuric acid addition unit, `a` = 900.97 and `b` = 0.6179. The full cost equation in
WaterTAP3 is:

:math:`\text{Cost } ($MM) = N_{units}\big( 900.97 S \big) ^{0.6179}\times 10^{-6}`

These parameters were determined by fitting data from FIGURE 5.5.11 - SULFURIC ACID FEED to the
general form.

.. image:: images/sulfuric_acid.png
   :scale: 100 %
   :align: center

Assumptions:
****************

* Number of units = 2
* Chemical solution density [kg/m3] = 1000

Reference:
*************

| Cost Estimating Manual for Water Treatment Facilities (2008)
| William McGivney & Susumu Kawamura
| DOI:10.1002/9780470260036

Electricity Cost
------------------

Electricity intensity for chemical additions in WaterTAP3 is based off the pump used to inject
the chemical solution, the chemical solution flow rate, and the influent flow rate. The model
assumes:

* Lift height = 100 ft
* Pump efficiency = 90%
* Motor efficiency = 90%

Chemical Addition Module
----------------------------------------

.. autoclass:: watertap3.wt_units.chemical_addition.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build
