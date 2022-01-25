.. _packed_tower_aeration_unit:

Packed Tower Aeration
============================================================

The packed tower aeration model in WaterTAP3 is based off of a regression of several runs using
EPA's Work Breakdown Structure-Based (WBS EPA) model (see reference). These models incorporate
several aspects of cost of the treatment process, including treatment, monitoring, and
administrative costs. Both capital cost and electricity intensity are based entirely on
volumetric flow, but are assumed to incorporate these costing aspects of the EPA model.

The WBS EPA models each have some "standard designs" that make default assumptions (see EPA
documentation) and span a range of flows 0.03 MGD to 75 MGD. Radon removal (called ``radon_rem``
in WaterTAP3) also affects cost. The EPA model outputs several costing parameters, including total
capital cost.

The approach for the WT3 model is to regress the total capital cost output from the EPA model vs.
flow for each of the EPA model standard designs using radon removal of 90% and 99%.
The different capital costs for each of these model runs is determined from the radon removal
percentage user input. A similar approach is taken to determine electricity intensity.

Both sets of data are fit to a power curve:

    .. math::

        Y = a Q ^ b

Where `Q` is the flows for the standard design EPA models. Then `a` and `b` are used with the
flow in for the particular case study.

Unit Parameters
--------------------

There is one unit parameter:

* ``"radon_rem"`` - Radon removal for unit [%]

    * Required parameter
|

Capital Costs
---------------

The ``cap_total`` column is read in from the ``epa_cost_curves.csv`` based on radon removal and is
fit to the power curve described above. Then `a` and `b` from that regression is used with the
unit flow [m3/hr] to determine capital costs:

    .. math::

        C_{ax} = a Q_{in} ^ b


Electricity Intensity
------------------------

The ``electricity_intensity`` column is read in from the ``epa_cost_curves.csv`` based on radon
removal and is fit to the power curve described above. Then `a` and `b` from that regression is
used with the unit flow [m3/hr] to determine capital costs:

    .. math::

        E_{ax} = a Q_{in} ^ b



Chemical Use
--------------

There is no chemical use for the packed tower aeration model in WaterTAP3.


References
--------------

| US Environmental Protection Agency (2017)
| "Work Breakdown Structure-Based Cost Model for Packed Tower Aeration Drinking Water Treatment"
| https://www.epa.gov/sites/default/files/2019-03/documents/wbs-pta-documentation-dec-2017_v2.pdf

Packed Tower Aeration Module
----------------------------------------

.. autoclass:: watertap3.wt_units.packed_tower_aeration.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak