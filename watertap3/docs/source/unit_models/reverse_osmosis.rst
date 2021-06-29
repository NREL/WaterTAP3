Reverse Osmosis
============================================================

Unit Basics
--------------

The capital cost, O&M costs, electricity consumption, TDS removal, and water recovery of the
reverse osmosis unit model are based on a basic representation of the physical performance of the
process. This includes calculations of osmostic pressure and mass balance across the membrane.
The feed pressure (i.e. pump power required) and membrane area are estimated based on optimizing
for  LCOW, unless specified otherwise. All other variables in the reverse osmosis model have
default assumptions, provided below, that factor into calculating the water recovery, TDS
removal, pure water flux, and osmotic pressure.

Unit Parameters
--------------------

The user only has to specify whether or not to include an energy recovery device (ERD).

* ``"erd"`` - whether or not to include an ERD

    * Required parameter

    * Options are ``"yes"`` or ``"no"``

Unit Constraints
------------------

The reverse osmosis unit in WaterTAP3 is broken up into a feed, permeate, and retentate IDAES
``Block()`` to track the different mass, flow, and pressure changes for each stream.

Mass and Pressure Constraints
*******************************

The unit only uses the TDS concentration into the unit to estimate the total concentration of
mass going into each reverse osmosis unit.

Thus, for each block (feed, permeate, retentate), some or all of the following mass and/or
energy balance equations apply.

The total concentration of TDS flowing into the unit is [kg/m3]:

    .. math::

         c_{tot} = 0.6312 c_{tds} + 997.86

The mass concentration of water into the block is [kg/m3]:

    .. math::

        c_{w} = c_{tot} - c_{tds}

The mass flow of water into the block is [kg/s]:

    .. math::

        M_{w} = c_{w} Q_{in}

The mass flow of TDS into the block is [kg/s]:

    .. math::

        M_{TDS} = c_{TDS} Q_{in}

The mass fraction of TDS into the block is:

    .. math::

        x_{TDS} = \frac{ M_{TDS}}{M_{w} + M_{TDS}}

The mass fraction of water into the block is:

    .. math::

        x_{w} = \frac{ M_{w}}{M_{w} + M_{TDS}}

The overall mass balance around water flow is:

    .. math::

        M_{w,f} = M_{w,p} + M_{w,r}

And the overall mass balance around TDS is:

    .. math::

        M_{tds,f} = M_{tds,p} + M_{tds,r}

Feed Block
++++++++++++

The osmotic coefficient is calculated according to the reference below:

    .. math::

        \sigma = 4.92 x_{TDS} ^ 2 + 0.0889 x_{TDS} + 0.918

Then the osmotic pressure [bar] is calculated as:

    .. math::

        P_{osm} = \frac{ 8.45 \times 10 ^ 7 \sigma x_{TDS}}{1 - x_{TDS}}

The flux is calculated from the feed stream as:

    .. math::

        J_w = \rho_w K_w (P_{feed} - P_{atm} - 0.5 P_d) - (0.5 ( P_{osm,f} + P_{osm,r} ))

The pressure drop is assumed to be 3 bar.


Permeate Stream
+++++++++++++++++++

The equation for mass into permeate is slightly different than for feed or retentate streams:

    .. math::

         c_{tot,p} = 756 c_{tds} \times 10 ^ {-6} + 995

The concentration coming out of the unit is:

    .. math::

        c_{tds,out} = c_{tot,p} x_{tds,p}

The mass flow of water is determined from the membrane area and pure water flux:

    .. math::

        M_{w,p} = J_w A

The mass flow of TDS is determined from the membrane area and the salt permeability coefficient:

    .. math::

        M_{TDS,p} = 0.5 A K_s ( c_{tds,f} + c_{tds,r} )

The pressure on the permeate side is assumed to be atmospheric:

    .. math::

        P_p = P_{atm}


Capital Costs
---------------

The capital costs for reverse osmosis has several components:

#. Pump capital cost
#. Membrane capital cost
#. Pressure vessel and & rack capital cost
#. Energy recovery device (optional)

The total capital costs for RO are calculated as follows, which each component described below:

    .. math::

        C_{RO} = C_{pump} + C_{mem} + C_{erd} + 3.3 C_{pv,r}

Pump Capital Costs
+++++++++++++++++++++++

The pump power is calculated as:

    .. math::

        p_{pump} = \frac{Q_{in} P_f}{\eta_p}

The pump cost is then:

    .. math::

        C_{pump} = p_{pump} \frac{53}{10^5 \times 3600} ^ {0.97}

Membrane Capital Costs
++++++++++++++++++++++++++++

The cost per meter squared of membrane area is $30 assumed from EPA documentation below. The
membrane costs are calculated as:

    .. math::

        C_{mem} = A \times 30


Pressure Vessel & Rack Capital Costs
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The pressure vessel cost is a function of area and the number of vessels per membrane area
(assumed to be 0.025 vessels/m2) and the vessel cost (assumed to be $1000) based on the default
EPA assumptions:

    .. math::

        C_{pv} = A * 0.025

The rack capital costs assumes 2 trains, 150 ft start, and 5 ft per additional vessel:

    .. math::

        C_{rack} = (150 + (x_{add} A 0.025)) 33 n_{trains}

And the total for this component is:

    .. math::

        C_{pv,r} = C_{pv} + C_{rack}

Energy Recovery Device
+++++++++++++++++++++++++++

The capital costs for the ERD option is taken from __________ and is based on the volumetric mass
flow into the ERD device [kg/hr]:

    .. math::

        M_{tot,r} = M_{H20,r} + M_{tds,r}

And the capital costs are calculated:

    .. math::

        C_{erd} = 3134.8 M_{tot,r} ^ {0.58}


Electricity Intensity
------------------------

The electricity intensity is a function of the pump power, ERD power, and the flow into the unit:

The pump power is calculated as [kW]:

    .. math::

        p_{pump} = \frac{Q_{in} P_f}{\eta_p}

The ERD power is function of the retentate flow (flow out of the unit), retentate pressure, and
the ERD efficiency [kW]:

    .. math::

        p_{erd} = \frac{Q_{out} (P_r - 1)}{ \eta_{erd}}


And the electricity intensity for the unit is calculated as [kWh/m3]:

    .. math::

        E_{RO} = \frac{p_{pump} - p_{erd} }{ Q_{in} }


Membrane Replacement Rate & Chemical Cost
-----------------------------------------------

The membrane replacement rate is included in the other variable operating costs for reverse
osmosis.

Membrane replacement costs (assumed to be 25% of area per year):

    .. math::

        C_{replace} = 0.25 C_{mem}


Chemical costs are assumed to equal 1% of the capital cost.

References
-------------------

| Bartholomew, T. V. and M. S. Mauter (2019).
| "Computational framework for modeling membrane processes without process and solution property simplifications."
| *Journal of Membrane Science* 573: 682-693.

| Lu, Y.-Y., et al. (2007).
| "Optimum design of reverse osmosis system under different feed concentration and product specification."
| *Journal of Membrane Science* 287(2): 219-229.

| US Environmental Protection Agency (2019)
| "Work Breakdown Structure-Based Cost Model for Reverse Osmosis/Nanofiltration Drinking Water Treatment"
| https://www.epa.gov/sites/production/files/2019-07/documents/wbs-ronf-documentation-june-2019.pdf

Reverse Osmosis Module
----------------------------------------

.. autoclass:: watertap3.wt_units.reverse_osmosis.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build
