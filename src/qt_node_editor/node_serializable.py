from collections.abc import Mapping
from typing import Any

type SerializableID = int
type SerializableMap = dict[SerializableID, Serializable]

class Serializable[T: Mapping[str, Any]]:
    def __init__(self) -> None:
        self.id: SerializableID = id(self)

    def serialize(self) -> T:
        raise NotImplementedError

    def deserialize(self, data: T, hashmap: SerializableMap,
                    ) -> bool:
        raise NotImplementedError
