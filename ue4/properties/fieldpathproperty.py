from ue4 import TArray, FName
from .objectproperty import UObjectProperty
from .property import PROPERTY_TYPE_MAP

class FFieldPathProperty:
    def __init__(self, reader):
        self.Path = TArray(reader, FName)
        self.Owner = UObjectProperty(reader)

PROPERTY_TYPE_MAP["FieldPathProperty"] = FFieldPathProperty
