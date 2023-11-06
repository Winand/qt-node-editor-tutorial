class Serializable:
    def __init__(self) -> None:
        self.id = id(self)
    
    def serialize(self):
        raise NotImplementedError()
    
    def deserialize(self, data, hashmap: dict={}):
        raise NotImplementedError()
