class FMovieSceneFrameRange():
    def __init__(self, reader):
        reader.bool()
        self.LowerBound = reader.s32()
        reader.bool()
        self.UpperBound = reader.s32()