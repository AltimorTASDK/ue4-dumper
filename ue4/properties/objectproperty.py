from .property import PROPERTY_TYPE_MAP

class UObjectProperty:
    def __init__(self, reader):
        self.Index = reader.s32()

PROPERTY_TYPE_MAP["ObjectProperty"] = UObjectProperty
