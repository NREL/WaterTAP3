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

The generic chemical addition module is based off costing parameters for sulfuric acid.

The chemical solution flow `S` is used in a cost curve of the general form:

    .. math::

        C = S a ^ b

For a single unit, `a` = 900.97 and `b` = 0.6179. The full cost equation in WaterTAP3 is:

    .. math::

        C_{chem} = N_{units} ( 900.97 S ) ^ {0.6179}

These parameters were determined by fitting data from FIGURE 5.5.11 - SULFURIC ACID FEED in the
below reference to the general form.

Assumptions:
****************

* Number of units = 2
* Chemical solution density [kg/m3] = 1000

Reference:
*************

| Cost Estimating Manual for Water Treatment Facilities (2008)
| William McGivney & Susumu Kawamura
| DOI:10.1002/9780470260036

Electricity Intensity
------------------------

Electricity intensity for chemical additions in WaterTAP3 is based off the pump used to inject
the chemical solution, the chemical solution flow rate, and the influent flow rate. The model
assumes:

* Lift height = 100 ft
* Pump efficiency = 90%
* Motor efficiency = 90%

Reference
------------------------

| Cost Estimating Manual for Water Treatment Facilities (2008)
| William McGivney & Susumu Kawamura
| DOI:10.1002/9780470260036


Chemical Addition Module
----------------------------------------

.. autoclass:: watertap3.wt_units.chemical_addition.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak