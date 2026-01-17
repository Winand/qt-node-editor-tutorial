Event system
============

Nodeeditor uses its own events (and tries to avoid using ``Signal``) to handle logic
happening inside the Scene. If a class does handle some events, they are usually described
in its docstring.

Any of the events is subscribable to and the methods for registering callback are called:

.. code-block:: python

    add_{event_name}_listener(callback)

You can register to any of these events any time.
