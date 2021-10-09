.. _well_field_unit:

Well Field
============================================================

Unit Parameters
--------------------

There are two unit parameters:

* ``"pipe_distance"`` - pipe distance to be included in costing model [miles]

    * Optional parameter
    * If not provided, piping cost is not included in cost model
    * Cost is $280,000 per mile assuming an 8 in pipe
|
* ``"pump"`` - to include pumping costs

    * Optional parameter
    * Options are "yes" or "no"
    * Default value is "yes"
|

Capital Costs
---------------

The capital costs are a function of flow [m3/hr] from Voutchkov (2018). If a pipe distance is not
provided, the capital costs are:

    .. math::

        C_{wf} = 4731.6 Q_{in} ^ {0.9196}
|
If pipe distance `d` is provided, the piping cost is:

    .. math::

        C_{pipe} = 280000 d
|
And the total cost then would be:

    .. math::

        C_{tot} = C_{wf} + C_{pipe}
|
Electricity Intensity
------------------------

There are no electricity costs associated with well field in WaterTAP3.

References
______________

| Voutchkov, N. (2018).
| Desalination Project Cost Estimating and Management.
| https://doi.org/10.1201/9781351242738

Well Field Module
----------------------------------------

.. autoclass:: watertap3.wt_units.well_field.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak