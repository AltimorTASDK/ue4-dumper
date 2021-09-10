class FRotator():
    def __init__(self, reader):
        self.Pitch = reader.f32()
        self.Yaw = reader.f32()
        self.Roll = reader.f32()