class FQuat():
    def __init__(self, reader):
        self.X = reader.f32()
        self.Y = reader.f32()
        self.Z = reader.f32()
        self.W = reader.f32()