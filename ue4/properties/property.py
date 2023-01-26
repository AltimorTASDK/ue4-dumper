import logging
from ue4 import FName, FGuid, FString, FPackageReader
from ue4.structs import STRUCT_TYPE_MAP

PROPERTY_TYPE_MAP = {
    "BoolProperty": FPackageReader.bool,
    "Int16Property": FPackageReader.s16,
    "UInt16Property": FPackageReader.u16,
    "IntProperty": FPackageReader.s32,
    "UInt32Property": FPackageReader.u32,
    "Int64Property": FPackageReader.s64,
    "UInt64Property": FPackageReader.u64,
    "FloatProperty": FPackageReader.f32,
    "ByteProperty": FName,
    "EnumProperty": FName,
    "NameProperty": FName,
    "StrProperty": FString,
    "SoftObjectProperty": lambda r: f"{FName(r)}-{r.s32()}"
}

class FPropertyTag():
    def __init__(self, reader):
        self.Name = FName(reader)
        if self.Name == "None":
            return

        self.Type = FName(reader)
        self.Size = reader.u32()
        self.ArrayIndex = reader.u32()

        if self.Type == "StructProperty":
            self.StructName = FName(reader)
            self.StructGuid = FGuid(reader)
        elif self.Type == "BoolProperty":
            self.BoolVal = reader.bool()
        elif self.Type in ["ByteProperty", "EnumProperty"]:
            self.EnumName = FName(reader)
        elif self.Type in ["ArrayProperty", "SetProperty"]:
            self.InnerType = FName(reader)
        elif self.Type == "MapProperty":
            self.InnerType = FName(reader)
            self.ValueType = FName(reader)

        self.HasPropertyGuid = reader.bool()
        if self.HasPropertyGuid:
            self.PropertyGuid = FGuid(reader)

class FDummyTag():
    def __init__(self, type):
        self.Name = None
        self.Type = type
        self.Size = 0
        self.ArrayIndex = 0
        if type == "StructProperty":
            self.StructName = ""

class UProperty():
    IndentLevel = 0

    @staticmethod
    def debug(msg, *args, **kwargs):
        logging.debug(f"{'    ' * UProperty.IndentLevel}{msg}", *args, **kwargs)

    def __init__(self, reader, tag=None):
        offset = reader.offset_string()
        tag_size = 0

        if tag is None:
            tag_start = reader.tell()
            tag = FPropertyTag(reader)
            tag_size = reader.tell() - tag_start
            if tag.Name == "None":
                self.Name = "None"
                self.Type = "None"
                self.ArrayIndex = 0
                self.Data = None
                return
        elif tag.Type == "BoolProperty":
            # Tagless bools in MapProperty
            tag.BoolVal = reader.bool()

        if tag.Type == "StructProperty":
            display_type = f"struct {tag.StructName}"
        else:
            display_type = tag.Type

        UProperty.debug(f"Property @ {offset} "
                        f"tag size {tag_size:04X} size {tag.Size:04X}: "
                        f"{display_type} {tag.Name}")

        self.Name = tag.Name
        self.Type = tag.Type
        self.ArrayIndex = tag.ArrayIndex

        UProperty.IndentLevel += 1

        if tag.Type == "StructProperty":
            self.StructName = tag.StructName
            if tag.StructName in STRUCT_TYPE_MAP:
                if STRUCT_TYPE_MAP[tag.StructName] is None:
                    # Explicitly skipped
                    self.Data = f"*Skipped struct {tag.StructName}*"
                    reader.skip(tag.Size)
                    UProperty.IndentLevel -= 1
                    return
                self.Data = STRUCT_TYPE_MAP[tag.StructName](reader)
                UProperty.IndentLevel -= 1
                return
        else:
            self.StructName = None

        if tag.Type == "BoolProperty":
            self.Data = tag.BoolVal
            UProperty.IndentLevel -= 1
            return

        if tag.Type == "MapProperty":
            self.InnerType = tag.InnerType
            self.ValueType = tag.ValueType
            key_tag = FDummyTag(tag.InnerType)
            value_tag = FDummyTag(tag.ValueType)

            NumKeysToRemove = reader.s32()

            [UProperty(reader, key_tag) for _ in range(NumKeysToRemove)]

            NumEntries = reader.s32()

            UProperty.debug(f"InnerType {tag.InnerType} "
                            f"ValueType {tag.ValueType} "
                            f"NumEntries {NumEntries} "
                            f"NumKeysToRemove {NumKeysToRemove}")

            self.Data = {
                UProperty(reader, key_tag).Data: UProperty(reader, value_tag)
                for _ in range(NumEntries)}

            UProperty.IndentLevel -= 1
            return

        if tag.Type not in PROPERTY_TYPE_MAP:
            # No handler
            self.Data = f"*Unhandled type {tag.Type}*"
            reader.skip(tag.Size)
            UProperty.IndentLevel -= 1
            return

        if tag.Type == "ArrayProperty" and tag.InnerType != "StructProperty":
            # Primitive array
            Length = reader.s32()
            if tag.InnerType == "ByteProperty":
                handler = FPackageReader.u8
            else:
                handler = PROPERTY_TYPE_MAP[tag.InnerType]
            self.Data = [handler(reader) for _ in range(Length)]
            UProperty.IndentLevel -= 1
            return

        self.Data = PROPERTY_TYPE_MAP[tag.Type](reader)
        UProperty.IndentLevel -= 1