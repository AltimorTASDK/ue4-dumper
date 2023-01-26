class FFrameNumber():
    def __init__(self, reader):
        self.Value = reader.s32()