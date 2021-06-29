Coagulation and Flocculation
============================================================

Unit Parameters
--------------------

The coagulation/flocculation has two parameters:

* ``"alum_dose"`` - alum dose for the unit [mg/L]

    * Required parameter
|
* ``"polymer_dose"`` - polymer dose for the unit [mg/L]

    * Required parameter
|
Capital Costs
---------------

The coagulation/flocculation unit in WaterTAP3 includes costing for rapid mix, flocculation,
coagulant injection, and flocculant injection:

    .. math::

        C_{c/f} = C_{rm} + C_{floc} + C_{floc,inj} + C_{coag,inj}

|
Rapid mix capital is calculated as:

    .. math::

        C_{rm} = (7.0814 V_{rm} + 33269) n_{rm}
|
Where the rapid mix basin volume is calculated with [gal]:

    .. math::

        V_{rm} = Q_in} t_{rm}
|
Flocculation capital is calculated as:

    .. math::

        C_{floc} = (952902 V_{floc} + 177335) n_{floc,proc}
|
Where the flocculation basin volume is calculated with [gal]:

    .. math::

        V_{floc} = Q_{in} t_{floc}
|
Flocculation injection capital is calculated as:

    .. math::

        C_{floc,inj} = (13662 Q_{poly} + 20861) n_{floc,inj}
|
Where the flow of polymer is calculated with [lb/hr]:

    .. math::

        Q_{poly} = D_{poly} Q_{in}
|
Coagulant injection capital is calculated as:

    .. math::

        C_{coag,inj} = (212.32 Q_{alum} + 73225) n_{coag}
|
Where the flow of alum is calculated with [lb/hr]:

    .. math::

        Q_{alum} = D_{alum} Q_{in}
|
Assumptions
--------------

Several aspects of the unit are assumed:

There is one rapid mixers per process and one rapid mix process:

    .. math::

        n_{rm} = n_{rm,proc} = 1
|
The rapid mix retention time is 5.5 sec:

    .. math::

        t_{rm} = 5.5
|
There are three flocculation mixers, two floc processes, and one floc injection process:

    .. math::

        n_{floc} = 3, n_{floc,proc} = 2, n_{floc,inj} = 1
|
The flocculation retention time is 12 minutes:

    .. math::

        t_{floc} = 12
|
There is one coagulant process:

    .. math::

        n_{coag} = 1
|
The cationic polymer dose and the anionic polymer dose are each equal to half the user provided
``"polymer_dose"`` [mg/L]:

    .. math::

        D_{cat} = D_{an} = 0.5 D_{poly}
|
Electricity Intensity
------------------------

The total electricity intensity for coagulation/flocculation includes rapid mix power and
flocculation power [kWh/m3]:

    .. math::

        E_{c/f} = \frac{p_{rm} + p_{floc}}{Q_{in}}
|
With rapid mix power calculated with the rapid mix basin volume in m3 [W]:

    .. math::

        p_{rm} = (0.001 V_{rm} 900 ^ 2) n_{rm}
|
And flocculation power calculated with the flocculation basin volume in m3 [W]:

    .. math::

        p_{floc} = (0.001 V_{floc} 80 ^ 2) n_{floc}
|
References
-------------

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036


Coagulation and Flocculation Module
----------------------------------------

.. autoclass:: watertap3.wt_units.coag_and_floc.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build
