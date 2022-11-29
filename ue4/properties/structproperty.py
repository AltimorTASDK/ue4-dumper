from .property import UProperty, PROPERTY_TYPE_MAP
from ue4.structs import STRUCT_TYPE_MAP

class UStructProperty:
    def __init__(self, reader):
        self.fields = {}
        while True:
            field = UProperty(reader)
            name = field.Name

            if name == "None":
                break

            if field.ArrayIndex != 0:
                if name in self.fields:
                    if f"{name}[0]" in self.fields:
                        raise RuntimeError(f"Duplicate field {name}[0]")
                    self.fields[f"{name}[0]"] = self.fields.pop(name)
                name += f"[{field.ArrayIndex}]"

            if name in self.fields:
                raise RuntimeError(f"Duplicate field {name}")
            self.fields[name] = field

    def get(self, name, default):
        if name in self.fields:
            return self[name]
        else:
            return default

    def __getitem__(self, name):
        if name not in self.fields:
            raise AttributeError(name)
        return self.fields[name].Data

    def __getattr__(self, name):
        return self[name]

PROPERTY_TYPE_MAP["StructProperty"] = UStructProperty

STRUCT_TYPE_MAP["RuntimeFloatCurve"] = UStructProperty