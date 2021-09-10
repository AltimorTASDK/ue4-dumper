from ue4 import FString, FName
from .property import UProperty, PROPERTY_TYPE_MAP
from enum import Enum

class ETextHistoryType(Enum):
    _None = 0xFF
    Base = 0
    StringTableEntry = 11

class UTextProperty():
    def __init__(self, reader):
        Flags = reader.s32()
        HistoryType = ETextHistoryType(reader.u8())

        if HistoryType == ETextHistoryType._None:
            bHasCultureInvariantString = reader.u32()
            if bHasCultureInvariantString:
                self.CultureInvariantString = FString(reader)
        elif HistoryType == ETextHistoryType.StringTableEntry:
            self.TableId = FName(reader)
            self.Key = FString(reader)
        else:
            self.Namespace = FString(reader)
            self.Key = FString(reader)
            self.SourceString = FString(reader)

PROPERTY_TYPE_MAP["TextProperty"] = UTextProperty
