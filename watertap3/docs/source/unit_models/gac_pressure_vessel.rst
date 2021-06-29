GAC - Pressure Vessel
============================================================

Unit Basics
--------------

The GAC pressure vessel model in WaterTAP3 is based off of a regression of several runs using EPA's
Work Breakdown Structure-Based (WBS EPA) model (see reference). These models incorporate
several aspects of cost of the treatment process, including treatment, monitoring, and
administrative costs. Both capital cost and electricity intensity are based entirely on
volumetric flow, but are assumed to incorporate these costing aspects of the EPA model.

The WBS EPA models each have some "standard designs" that make default assumptions (see EPA
documentation) and span a range of flows 7.4 MGD to 75 MGD. Empty bed contact time (EBCT) also
affects cost. The EPA model outputs several costing parameters, including total
capital cost.

The approach for the WT3 model is to regress the total capital cost output from the EPA model vs.
flow for each ofthe EPA model standard designs using influent sulfate of 30 and 60 minutes.
The different capital costs for each of these model runs is determined from the user input
``"ebct"``. i.e. the cost curve is different if the EBCT is 10 min vs. 90 min. A
similar approach is taken to determine electricity intensity.

Both sets of data are fit to a power curve:

    .. math::

        Y = a Q ^ b

Where `Q` is the flows for the standard design EPA models. Then `a` and `b` are used with the
flow in for the particular case study.

Unit Parameters
--------------------

Anion exchange has one parameter:

* ``"ebct"`` - empty bed contact time for the unit [min]:

    * Required parameter

    * There are different costing data for 0-60 min and >60 min

Capital Costs
---------------

The ``cap_total`` column is read in from the ``cost_curves.csv`` based on influent TDS and is
fit to the power curve described above. Then `a` and `b` from that regression is used with the
unit flow [m3/hr] to determine capital costs:

    .. math::

        C_{gac} = a Q_{in} ^ b


Electricity Intensity
------------------------

The ``electricity_flow`` column is read in from the ``cost_curves.csv`` based on influent TDS
and is fit to the power curve described above. Then `a` and `b` from that regression is used with
the unit flow [m3/hr] to determine capital costs:

    .. math::

        E_{gac} = a Q_{in} ^ b


Chemical Use
--------------

The WBS EPA model includes costs for activated carbon. The average is taken for the range of flows
and assumed to be the "dose" for the particular chemical/material.


References
--------------

| US Environmental Protection Agency (2017)
| "Work Breakdown Structure-Based Cost Model for Granular Activated Carbon Drinking Water Treatment"
| https://www.epa.gov/sites/production/files/2019-03/documents/wbs-gac-documentation-dec-2017_v2.pdf

Unit Template
----------------------------------------

.. autoclass:: watertap3.wt_units.gac_pressure_vessel.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build
