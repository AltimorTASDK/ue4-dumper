from ue4 import VER_UE5_LARGE_WORLD_COORDINATES

class FVector():
    def __init__(self, reader):
        if reader.Summary.VersionUE5 >= VER_UE5_LARGE_WORLD_COORDINATES:
            self.X = reader.f64()
            self.Y = reader.f64()
            self.Z = reader.f64()
        else:
            self.X = reader.f32()
            self.Y = reader.f32()
            self.Z = reader.f32()

class FVector2D():
    def __init__(self, reader):
        if reader.Summary.VersionUE5 >= VER_UE5_LARGE_WORLD_COORDINATES:
            self.X = reader.f64()
            self.Y = reader.f64()
        else:
            self.X = reader.f32()
            self.Y = reader.f32()

class FVector4():
    def __init__(self, reader):
        if reader.Summary.VersionUE5 >= VER_UE5_LARGE_WORLD_COORDINATES:
            self.X = reader.f64()
            self.Y = reader.f64()
            self.Z = reader.f64()
            self.W = reader.f64()
        else:
            self.X = reader.f32()
            self.Y = reader.f32()
            self.Z = reader.f32()
            self.W = reader.f32()

class FIntPoint():
    def __init__(self, reader):
        self.X = reader.s32()
        self.Y = reader.s32()