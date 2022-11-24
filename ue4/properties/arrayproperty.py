from .property import FPropertyTag, UProperty, PROPERTY_TYPE_MAP

class UArrayProperty:
    def __init__(self, reader):
        Length = reader.s32()
        InnerTag = FPropertyTag(reader)
        self.elems = [UProperty(reader, InnerTag) for _ in range(Length)]

    def __getitem__(self, index):
        return self.elems[index].Data

    def __len__(self):
        return len(self.elems)

PROPERTY_TYPE_MAP["ArrayProperty"] = UArrayProperty
