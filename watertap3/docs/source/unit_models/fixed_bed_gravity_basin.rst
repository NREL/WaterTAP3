Fixed Bed Gravity Basin
============================================================


Unit Basics
--------------

The fixed bed gravity basin unit in WaterTAP3 is based off of a regression of several runs using
EPA's Work Breakdown Structure-Based (WBS EPA) model (see reference). These models incorporate
several aspects of cost of the treatment process, including treatment, monitoring, and
administrative costs. Both capital cost and electricity intensity are based entirely on
volumetric flow, but are assumed to incorporate these costing aspects of the EPA model.

The WBS EPA models each have some "standard designs" that make default assumptions (see EPA
documentation) and span a range of flows 0.03 MGD to 75 MGD.

The approach for the WT3 model is to regress the total capital cost output from the EPA model vs.
flow for each of the EPA model standard designs with the fixed bed gravity basin option. A
similar approach is taken to determine electricity intensity.

Both sets of data are fit to a power curve:

    .. math::

        Y = a Q ^ b

Where `Q` is the flows for the standard design EPA models. Then `a` and `b` are used with the
flow in for the particular case study.

Unit Parameters
--------------------

None

Capital Costs
---------------

The ``cap_total`` column is read in from the ``cost_curves.csv`` based on influent TDS and is
fit to the power curve described above. Then `a` and `b` from that regression is used with the
unit flow [m3/hr] to determine capital costs:

    .. math::

        C_{fbgb} = a Q_{in} ^ b

Electricity Intensity
------------------------

The ``electricity_flow`` column is read in from the ``cost_curves.csv`` based on influent TDS
and is fit to the power curve described above. Then `a` and `b` from that regression is used with
the unit flow [m3/hr] to determine capital costs:

    .. math::

        E_{fbgb} = a Q_{in} ^ b


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

Unit Template
----------------------------------------

.. autoclass:: watertap3.wt_units.fixed_bed_gravity_basin.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build
