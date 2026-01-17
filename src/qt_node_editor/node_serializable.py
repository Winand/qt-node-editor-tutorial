"A module containing Serializable interface."
from collections.abc import Mapping
from typing import Any

type SerializableID = int
type SerializableMap = dict[SerializableID, Serializable]

class Serializable[T: Mapping[str, Any]]:
    "Interface to use in implementation of serializable objects."

    def __init__(self) -> None:
        "Set up ``id`` field for any serializable class in default constructor."
        #: All the serializable objects in the project use ``id`` attribute for
        #: unique object identification
        self.id: SerializableID = id(self)


    def serialize(self) -> T:
        """
        Serialize data into a `dict` which can be stored in memory or file.

        :return: data serialized in a `dict`
        """
        raise NotImplementedError

    def deserialize(self, data: T, hashmap: SerializableMap, *,
                    restore_id: bool = True) -> bool:
        """
        Deserialize ``data`` from a Python `dict`.

        *hashmap* contains references to the existing entities.

        :param data: data serialized in a `dict`
        :param hashmap: helper dictionary containing references to existing objects
        :type hashmap: SerializableMap
        :param restore_id: ``True`` to keep ids from data, ``False`` to generate
            new ids when copying entities
        :type restore_id: bool
        :return: ``True`` on deserialization success
        :rtype: bool
        """
        raise NotImplementedError
