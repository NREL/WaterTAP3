.. _fixed_bed_gravity_basin_unit:

Fixed Bed Gravity Basin
============================================================

The fixed bed gravity basin unit in WaterTAP3 is based off of a regression of several runs using
EPA's Work Breakdown Structure-Based (WBS EPA) model. These models each have some "standard
designs" that make default assumptions and span a range of flows 0.03 MGD to 75 MGD (USEPA (2019)).

The approach for the WT3 model is to regress the total capital cost output from the EPA model vs.
flow for each of the EPA model standard designs with the fixed bed gravity basin option. A
similar approach is taken to determine electricity intensity.

Both sets of data are fit to a power curve. Then `a` and `b` are used with the
flow for the model to determine capital and electricity intensity.

Unit Parameters
--------------------

None.

Capital Costs
---------------

The ``cap_total`` column is read in from the ``cost_curves.csv`` and is fit to a power curve.
Then `a` and `b` from that regression is used with the unit flow [m3/hr] to determine capital costs:

    .. math::

        C_{fbgb} = a Q_{in} ^ b
|
Electricity Intensity
------------------------

The ``electricity_flow`` column is read in from the ``cost_curves.csv`` and is fit to a power
curve. Then `a` and `b` from that regression is used with the unit flow [m3/hr] to determine
electricity intensity:

    .. math::

        E_{fbgb} = a Q_{in} ^ b
|
Chemical Use
--------------

The WBS EPA model includes costs for acetic acid, phosphoric acid, iron chloride, activated
carbon, sand, and anthracite. The average is taken for the range of flows and assumed to be the
"dose" for the particular chemical/material.

References
--------------

| US Environmental Protection Agency (2019)
| "Work Breakdown Structure-Based Cost Model for Biological Drinking Water Treatment"
| https://www.epa.gov/sites/production/files/2019-07/documents/wbs-biotreat-documentation-june-2019.pdf
| https://www.epa.gov/sdwa/drinking-water-treatment-technology-unit-cost-models

Fixed Bed Gravity Basin Module
----------------------------------------

.. autoclass:: watertap3.wt_units.fixed_bed_gravity_basin.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak