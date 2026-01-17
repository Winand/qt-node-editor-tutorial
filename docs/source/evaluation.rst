.. _evaluation:

Evaluation
==========

TL;DR: The evaluation system uses :meth:`~.Node.eval` and :meth:`~.Node.eval_children`.
``eval`` is supposed to be overriden by your own implementation.
The evaluation logic uses flags for marking the `Nodes` to be `Dirty` and/or `Invalid`.

Evaluation Functions
--------------------

There are 2 main methods used for evaluation:

- :meth:`~.Node.eval`
- :meth:`~.Node.eval_children`

These functions are mutually exclusive. That means that ``eval_children`` does
**not** eval current `Node`, but only children of the current `Node`.

By default the implementation of :meth:`~.Node.eval` is "empty" and return ``0``. However
it seems logical, that eval (if successfull) resets the `Node` not to be `Dirty` nor `Invalid`.
This method is supposed to be overriden by your own implementation. As an example, you can check out
the repository's ``examples/example_calculator`` to get inspiration on how to set up the
`Node` evaluation on your own.

The evaluation takes advantage of `Node` flags described below.

:class:`.Node` Flags
-----------------------------------------

Each :class:`.Node` has 2 flags:

- ``Dirty``
- ``Invalid``

The `Invalid` flag has always higher priority. That means when the `Node` is `Invalid` it
doesn't matter if it is `Dirty` or not.

To mark a node `Dirty` or `Invalid` there are respective methods :meth:`~.Node.mark_dirty`
and :meth:`~.Node.mark_invalid`. Both methods take `bool` parameter for the new state.
You can mark `Node` dirty by setting the parameter to ``True``. Also you can un-mark the
state by passing ``False`` value.

For both flags there are 3 methods available:

- :meth:`~.Node.mark_invalid` - to mark only the `Node`
- :meth:`~.Node.mark_children_invalid` - to mark only the direct (first level) children of the `Node`
- :meth:`~.Node.mark_descendants_invalid` - to mark it self and all descendant children of the `Node`

The same goes for the `Dirty` flag of course:

- :meth:`~.Node.mark_dirty` - to mark only the `Node`
- :meth:`~.Node.mark_children_dirty` - to mark only the direct (first level) children of the `Node`
- :meth:`~.Node.mark_descendants_dirty` - to mark it self and all descendant children of the `Node`

Descendants or Children are always connected to Output(s) of current `Node`.

When a node is marked `Dirty` or `Invalid` event methods :meth:`~.Node.onMarkedInvalid` and
:meth:`~.Node.on_marked_invalid` are being called. By default, these methods do nothing.
But still they are implemented in case you would like to override them and use in you own evaluation system.
