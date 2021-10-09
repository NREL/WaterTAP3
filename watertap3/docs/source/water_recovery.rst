.. _water_recovery:

Water Recovery
==========================

``data/water_revovery.csv``

Water recovery `x` is represented as the fraction (between zero and one) of water recovered
(treated) after it passes through a unit process.  Case-study based water recovery is given for
certain unit processes if the case study has a unique recovery rate, otherwise default values are
used.

The water balance for a single unit incorporates the water recovery:

    .. math::

        Q_{in} x = Q_{out}
|
And if the overall water balance for each unit is:

    .. math::

        Q_{in} = Q_{out} + Q_{waste}
|
Then the water flow for the waste stream is:

    .. math::

        Q_{waste} = Q_{in} (1 - x)
|
The total system water recovery along a single stream in the train for all `n` units is the
product of the water recovery for every unit in the stream:

    .. math::

        x_{stream} = \prod_{i}^{n} x_i
|
And therefore the outlet flow for the entire stream the system water recovery multiplied by the
sum of all `k` source flows to the system:

    .. math::

        Q_{out,stream} = x_{stream} \sum_{i}^{k} Q_{in,i}
|

The columns of ``data/water_recovery.csv`` are:

* **case_study**: The treatment facility name or default

* **scenario**: The name of the scenario that the values correspond with

* **unit_process**: The name of the unit process corresponding to the recovery value.

* **recovery**: How much water is recovered by each unit process (%)

* **reference**: The source of the recovery data

..  raw:: pdf

    PageBreak