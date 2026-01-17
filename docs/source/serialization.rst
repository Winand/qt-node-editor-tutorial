Serialization
=============
All of serializable classes derive from :class:`.Serializable` class.
`Serializable` sets common ``id`` attribute which is used to identify unique objects.

`Serializable` defines two methods which should be overriden in child classes:

- :meth:`~.Serializable.serialize`
- :meth:`~.Serializable.deserialize`

According to :ref:`coding-standards` we keep these two functions at the bottom
of a class source code.

Serialization structures are described with a `TypeDict`.

Classes which derive from :class:`.Serializable`:

- :class:`.Scene`
- :class:`.Node`
- :class:`.QDMContentWidget`
- :class:`.Edge`
- :class:`.Socket`
