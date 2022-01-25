.. _backwash_solids_handling_unit:

Backwash Solids Handling
============================================================

The backwash solids handling unit model represents the handling of the waste/backwash streams
from  filtration processes (e.g. tri-media filtration). It is typically recycled back into the
treatment train or sent to a final waste unit.

Unit Parameters
--------------------

There is one parameter for backwash solids handling:

* ``"recovery"`` - proportion of flow recycled back to treatment technology

    * Required parameter
    * Value between 0 and 1
|
Capital Costs
---------------

The costing for backwash solids handling is derived from combining costs for the following processes typically used to handle solids:

* Filter backwash pumping system
* Surface wash system
* Air scour system
* Wash water surge basins
* Wash water storage tank
* Gravity sludge thickener
* Sludge dewatering lagoons
* Sand drying beds


The assumed, cost per unit, number of units, and scaling factor for each of these processes was taken from Table 5.7.1 in McGivney & Kawamura (2008):

+--------------------------------+-------------------+-----------+--------------------+----------------+
| Process                        | Cost per unit     | # Units   | Total process cost | Scaling factor |
+================================+===================+===========+====================+================+
| Filter backwash pumping system | $186,458          | 2         | $372,916           | 1.0            |
+--------------------------------+-------------------+-----------+--------------------+----------------+
| Surface wash system            | $99,941           | 2         | $199,882           | 1.0            |               
+--------------------------------+-------------------+-----------+--------------------+----------------+
| Air scour system               | $463,853          | 2         | $927,706           | 1.0            |
+--------------------------------+-------------------+-----------+--------------------+----------------+
| Wash water surge basins        | $770,643          | 1         | $770,643           | 0.751          |
+--------------------------------+-------------------+-----------+--------------------+----------------+
| Wash water storage tank        | $216,770          | 1         | $216,770           | 0.847          |
+--------------------------------+-------------------+-----------+--------------------+----------------+
| Gravity sludge thickener       | $94,864           | 1         | $94,864            | 1.305          |
+--------------------------------+-------------------+-----------+--------------------+----------------+
| Sludge dewatering lagoons      | $4,173            | 3         | $12,519            | 0.714          |
+--------------------------------+-------------------+-----------+--------------------+----------------+
| Sand drying beds               | $45,801           | 6         | $274,806           | 0.875          |
+--------------------------------+-------------------+-----------+--------------------+----------------+

| 




Summation of the total cost column gives the cost basis of 9.76 and the scaling exponent is calculated as the summation of each entry for total process cost multiplied by the scaling factor divided by
the summation of the scaling factors:

    .. math::

        b_{bw} = \frac{\sum{C_i * b_i}}{\sum{b_i}} = 0.918
     
|
The capital costs are a function of mass flow [kg/hr]. The costing basis is for 100 MGD (15772.55 m3/hr) and assumes a density of 1000 kg/m3. Thus, the basis is 1577255 kg/hr:

    .. math::

        C_{bw} = 9.76 \frac{M_{in}}{1577255} ^ {0.918}
|
The mass flow in is the sum of all the constituents flowing into the unit:

    .. math::

       C_{in} = \sum_{i}^{n} c_i
|
Then, the density of the solution is [kg/m3]:

    .. math::

        \rho_{in} = 0.6312 ( C_{in} ) + 997.86
|
And mass flow is determined with [kg/hr]:

    .. math::

        M_{in} = \rho_{in} Q_{in}
|

Electricity Intensity
------------------------

Electricity intensity for backwash solids handling is based off the pump used. The
calculation includes:

* Lift height [ft]:

    .. math::

        h
|
* The pump and motor efficiencies:

    .. math::

        \eta_{pump}, \eta_{motor}
|
* And the influent flow in [gal/min] and [m3/hr]:

    .. math::

        Q_{gpm}, Q_{m3hr}
|
Then the electricity intensity is calculated as:

    .. math::

        E_{bw} = \frac{0.746 Q_{gpm} h}{3960 \eta_{pump} \eta_{motor} Q_{m3hr}}
|

Assumptions
------------------------

* Lift height [ft] = 100
* Pump efficiency = 0.9
* Motor efficiency = 0.9

References
-------------

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

Backwash Solids Handling Module
----------------------------------------

.. autoclass:: watertap3.wt_units.backwash_solids_handling.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak