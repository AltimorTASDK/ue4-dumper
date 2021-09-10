from .property import UProperty, PROPERTY_TYPE_MAP

class UStructProperty():
    def __init__(self, reader):
        self.fields = []
        self.fieldCount = {}
        while True:
            field = UProperty(reader)
            if field.Name == "None":
                break

            if field.Name in self.fieldCount:
                self.fieldCount[field.Name] += 1
            else:
                self.fieldCount[field.Name] = 0

            self.fields.append(field)

        for field in self.fields:
            if self.fieldCount[field.Name] > 0 or field.ArrayIndex != 0:
                name = f"{field.Name}[{field.ArrayIndex}]"
            else:
                name = field.Name

            setattr(self, name, field)

        del self.fields
        del self.fieldCount

PROPERTY_TYPE_MAP["StructProperty"] = UStructProperty
