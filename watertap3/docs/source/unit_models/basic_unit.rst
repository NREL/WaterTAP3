.. _basic_unit_unit:

Basic Unit
============================================================

Capital costs for the units defined as “basic” are based entirely on either the volumetric or mass flow
into the unit.

All of the data for each of the basic units is read in from the ``basic_unit.csv`` located in the
data folder.

Unit Parameters
--------------------

* ``"unit_process_name"`` - unit process name that is being represented as a basic unit.

    * Required parameter
    * Must be enclosed in double ``" "`` or single ``' '`` quotes
    * Must match *exactly* the entry in the ``unit_process`` column in ``basic_unit.csv``
|
basic_unit.csv
******************

This .csv file contains all of the data used to calculate fixed capital costs and electricity
intensity for all basic units. The columns are:

* ``unit_process`` - unit process name in WaterTAP3
* ``flow_basis`` - flow basis from costing source [m3/hr]
* ``cap_basis`` - `B` fixed capital investment from costing source [$MM]
* ``cap_exp`` - `x` fixed capital investment scaling exponent
* ``electricity_intensity`` - electricity intensity for unit [kWh/m3]
* ``year`` - costing basis year
* ``kind`` - determines if unit is based on water flow or mass flow
|
Capital Costs
---------------

Flow Based
**************

Capital costs for basic units based on water flow are calculated with the general form:

    .. math::

        C_{basic} = B f ^ {x}
|
The ratio of the unit water flow to the basis water flow is the scaling factor `f` used to scale
the unit costs to the basis costs:

    .. math::

        f = \frac{Q_{in}}{Q_{basis}}
|

Mass Based
*************

For those units based on mass flow, the mass flowing into the unit must be determined.
First we determine the concentration flowing into the unit [kg/m3], calculated as the
summation of the concentration of all constituents entering the unit:

    .. math::

       C_{in} = \sum_{i}^{n} c_i
|
Then, we estimate the density of the solution [kg/m3] from Bartholomew & Mauter (2019):

    .. math::

        \rho_{in} = 0.6312 ( C_{in} ) + 997.86
|
Mass flow [kg/hr] is determined with:

    .. math::

        M_{in} = \rho_{in} Q_{in}
|
Capital costs for basic units based on mass flow are calculated with the general form:

    .. math::

        C_{basic} = B f ^ {x}
|
The ratio of the unit mass flow to the basis mass flow is the scaling factor `f` used to scale
the unit costs to the basis costs:

    .. math::

        f = \frac{M_{in}}{M_{basis}}
|

Electricity Intensity
------------------------

Electricity intensity for basic units is read directly from the ``electricity_intensity`` column in
``basic_unit.csv`` (see above) and does not scale with flow (i.e. it is a fixed value).


..  raw:: pdf

    PageBreak


List of Basic Units
----------------------

* Treatment Technologies:

    * ABMET Intermediate Pumps
    * ABMET Interstage Pumps
    * Aeration Basins
    * Air Floation
    * Anaerobic Digestion Oxidation
    * Bio-Active Filtration
    * Bioreactor
    * Bioreactor BW Pump
    * Bioreactor Feed Pump
    * Bioreactor Effluent Pump
    * Blending Reservoir
    * Buffer Tank
    * Conventional Activated Sludge (CAS)
    * Clarifier
    * Decarbonators
    * Dissolved Air Flotation (DAF)
    * Drainage Sump Pumps
    * Filter Presses
    * Intrusion Mitigation
    * Membrane Bioreactors (MBR)
    * Microscreen Filtration
    * Nanofiltration (NF)
    * pH Adjustment
    * Raw Water Pumps
    * Screens
    * Separators
    * Settling Ponds
    * Settling Tanks
    * SMP
    * Transfer Pumps
    * Tramp Oil Tanks
    * Ultrafiltration (UF)
    * Ultratiltration Feed Pumps
    * WAIV
    * Walnut Shell Filter
|
* Uses/Waste Streams & Other:

    * Agriculture
    * Cooling Supply
    * Discharge
    * Industrial
    * Intrusion Mitigation
    * Injection Wells
    * Irrigation
    * Mining
    * Municipal WWTP
    * Passthrough

References
------------------

| Bartholomew, T. V. and M. S. Mauter (2019).
| "Computational framework for modeling membrane processes without process and solution property simplifications."
| *Journal of Membrane Science* 573: 682-693.


Basic Unit Module
----------------------------------------

.. autoclass:: watertap3.wt_units.basic_unit.UnitProcess
    :members: fixed_cap, elect
    :exclude-members: build


..  raw:: pdf

    PageBreak