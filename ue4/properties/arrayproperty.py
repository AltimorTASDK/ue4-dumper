from .property import FPropertyTag, UProperty, PROPERTY_TYPE_MAP

def UArrayProperty(reader):
    Length = reader.s32()
    InnerTag = FPropertyTag(reader)
    return [UProperty(reader, InnerTag) for _ in range(Length)]

PROPERTY_TYPE_MAP["ArrayProperty"] = UArrayProperty
