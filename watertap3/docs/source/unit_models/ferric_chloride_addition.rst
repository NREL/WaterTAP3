Ferric Chloride Addition
=====================================

In general, costs for chemical additions in WaterTAP3 are a function of the chemical dose and the
flow in. The chemical solution flow is calculated from these two values and assumed solution
densities to use in a cost curve. All chemical additions assume 2 chemical addition units.

Unit Parameters
--------------------

* ``"dose"`` - dose of chemical [mg/L]

    * Required parameter

Capital Costs
---------------

The ferric chloride solution flow `S` is used in a cost curve of the general form:

    .. math::

        C = S a ^ b

For a single ferric chloride addition unit, `a` = 34153 and `b` = 0.319. The full cost equation in
WaterTAP3 is:

    .. math::

        C_{ferric} = N_{units} ( 34153 S ) ^ {0.319}

These parameters were determined by fitting data from FIGURE 5.5.13 - FERRIC CHLORIDE FEED 42% SOLUTION
in the below reference to the general form.

Assumptions:
****************

* Number of units = 2
* Alum solution density [kg/m3] = 1460
* Ratio in solution = 42%


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

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

Ferric Chloride Addition Module
----------------------------------------

.. autoclass:: watertap3.wt_units.ferric_chloride_addition.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak