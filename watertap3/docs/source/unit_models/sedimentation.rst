Sedimentation
============================================================

Unit Basics
--------------

This is a template file for all unit models in WaterTAP3.

Unit Parameters
--------------------

There is one parameter:

* ``"settling_velocity"`` - `v` the assumed settling velocity for the unit [m/s]:

    * Required parameter

Capital Costs
---------------

The capital costs are a function of basin surface area:

    .. math::

        C_{sed} = 13572 A_{basin} ^ {0.3182}

Basin surface area is calculated as [ft3]:

    .. math::

        A_{basin} = \frac{ Q_{in} }{ v }

Electricity Intensity
------------------------

There are no electricity costs associated with sedimentation in WaterTAP3.

References
--------------

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

Unit Template
----------------------------------------

.. autoclass:: watertap3.wt_units.unit_template.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build


..  raw:: pdf

    PageBreak