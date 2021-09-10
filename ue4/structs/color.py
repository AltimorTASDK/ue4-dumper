class FColor():
    def __init__(self, reader):
        self.R = reader.u8()
        self.G = reader.u8()
        self.B = reader.u8()
        self.A = reader.u8()

class FLinearColor():
    def __init__(self, reader):
        self.R = reader.f32()
        self.G = reader.f32()
        self.B = reader.f32()
        self.A = reader.f32()