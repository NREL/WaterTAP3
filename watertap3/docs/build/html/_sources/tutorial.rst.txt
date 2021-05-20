Tutorial
==========

Add note
-----------

.. note:: WaterTAP3 supports Python 3.6 and above.


Add code inline & block
--------------------------

The standard utility for installing Python packages is ``pip``. 

You can install WaterTAP3 in your system Python installation by executing::

   pip install watertap3


Add picture
--------------

.. image:: images/nrel-logo.png
   :scale: 50 %
   :align: center


Add math
--------------

For inline math, we use like this: :math:`a^2 + b^2 = c^2`.

For displayed math, the directive supports multiple equations, which should be separated by a blank line:

   .. math::

      (a + b)^2 = a^2 + 2ab + b^2

      (a - b)^2 = a^2 - 2ab + b^2


Add table
-------------

+------------+------------+-----------+
| Header 1   | Header 2   | Header 3  |
+============+============+===========+
| body row 1 | column 2   | column 3  |
+------------+------------+-----------+
| body row 2 | Cells may span columns.|
+------------+------------+-----------+
| body row 3 | Cells may  | - Cells   |
+------------+ span rows. | - contain |
| body row 4 |            | - blocks  |
+------------+------------+-----------+


Add internal link
-------------------

Here to introduce each component in WaterTAP3.

* :ref:`flowsheet`
* :ref:`prop_pkg`
* :ref:`unit_model`

.. _flowsheet:

Flowsheet
************
Flowsheet models are the top level of the modeling heirachy. 
Flowsheet models represent traditional process flowsheets, containing a number of unit models connected together into a flow network and the property packages.


.. _prop_pkg:

Property Package
********************
Property packages are a collection of related models that represent the physical, thermodynamic, and reactive properties of the process streams.


.. _unit_model:

Unit Model
**************
Unit models represent individual pieces of equipment and their processes.


Add external link
-------------------
Here is an introduction for `Water-TAP3 project <https://www.nawihub.org/watertap>`_.


Add docstring
---------------

This is WaterTAP3's full API documentation using Apidoc.

.. toctree::
   :maxdepth: 2
   
   watertap3
   watertap3.utils
   watertap3.wt_units