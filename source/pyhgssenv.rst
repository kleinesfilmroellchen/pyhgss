.. py:module:: pyhgss.environment

.. contents::

.. note:: This page serves as an in-depth documentation for the Environment object that the PyHG scripts access through their ``globals()``. It is **not** intended to be a reference for PyHG scripting.

.. autoclass:: ScriptExited

.. autofunction:: make_environment


The PyHGSs Environment object
=============================

:PRIVATE_METHODS: A list of inaccessible methods. This is used to protect special methods from access from the PyHGSs script.

.. autoclass:: HypertextGenerationEnvironment

	.. automethod:: __getitem__

	.. automethod:: __setitem__

	.. automethod:: __getattribute__

	.. automethod:: __setattr__

Integrated Enumerations
=======================

These enumerations are integrated into the global script namespace, i.e. their members are available without the type specification.

.. autoclass:: Type