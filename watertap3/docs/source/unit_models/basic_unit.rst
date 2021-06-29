Basic Unit
============================================================

Unit Basics
--------------

The basic unit in WaterTAP3 is used to create cost curves for units that do not yet have a more
developed WaterTAP3 model. Capital costs for these units are based entirely on either the
flow into the unit or the mass flow into the unit. They typically incorporate a single data
point for costing the given unit.

All of the data for each of the basic units is read in from the ``basic_unit.csv`` located in the
data folder.


Unit Parameters
--------------------

* ``"unit_process_name"`` - unit process name that is being represented as a basic unit.

    * Required parameter
    * Must be enclosed in double ``" "`` or single ``' '`` quotes
    * Must match *exactly* the entry in the ``unit_process`` column in ``basic_unit.csv``


basic_unit.csv
******************

This .csv file contains all of the data used to calculate fixed capital costs and electricity
intensity for all basic units. The columns are:

* ``unit_process`` - unit process name in WaterTAP3

* ``flow_basis`` - `Q_{basis}` flow from costing source [m3/hr]

* ``cap_basis`` - `B` fixed capital investment from costing source [$MM]

* ``cap_exp`` - `x` fixed capital investment scaling exponent

* ``elect`` - electricity intensity for unit [kWh/m3]

* ``year`` - costing basis year

* ``kind`` - determines if unit is based on water flow or mass flow


Capital Costs
---------------

Flow Based
**************

Capital costs for basic units based on water flow are calculated with the general form:

    .. math::

        C_{basic} = B * \frac{Q_{in}}{Q_{basis}} ^ {x}

Where `B` is the capital costing basis, `Q_{in}` is flow into the unit,
`Q_{basis}` is the flow from the source for the costing basis, and `x` is the
scaling exponent from the source (read in from csv).

Mass Based
*************

For those units based on mass flow, the mass flowing into the unit must be determined.
First we determine the concentration flowing into the unit [kg/m3], calculated as the
summation of the concentration of all constituents entering the unit:

    .. math::

       C_{in} = \sum_{i}^{n} c_i

Then, we estimate the density of the solution [kg/m3]:

    .. math::

        \rho_{in} = 0.6312 ( C_{in} ) + 997.86

Mass flow [kg/hr] is determined with:

    .. math::

        M_{in} = \rho_{in} Q_{in}

Capital costs for basic units based on mass flow are calculated with the general form:

    .. math::

        C_{basic} = B \frac{M_{in}}{M_{basis}} ^ {x}

Where `M_{in}` is the mass flow into the unit and `M_{basis}` is the mass flow from
the source for the costing basis.


Electricity Intensity
------------------------

Electricity intensity for basic units is read directly from the ``elect`` column in
``basic_unit.csv`` (see above) and does not scale with flow (i.e. it is a fixed value).

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

        * Note: some basic units, like passthroughs, have no cost associated with them and
        instead can serve as a blank unit through which to direct tricky process flows.


Basic Unit Module
----------------------------------------

.. autoclass:: watertap3.wt_units.basic_unit.UnitProcess
    :members: fixed_cap, elect
    :exclude-members: build


..  raw:: pdf

    PageBreak