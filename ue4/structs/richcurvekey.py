from enum import Enum

class ERichCurveInterpMode(Enum):
    RCIM_Linear = 0
    RCIM_Constant = 1
    RCIM_Cubic = 2
    RCIM_None = 3

class ERichCurveTangentMode(Enum):
    RCTM_Auto = 0
    RCTM_User = 1
    RCTM_Break = 2
    RCTM_None = 3

class ERichCurveTangentWeightMode(Enum):
    RCTWM_WeightedNone = 0
    RCTWM_WeightedArrive = 1
    RCTWM_WeightedLeave = 2
    RCTWM_WeightedBoth = 3

class FRichCurveKey():
    def __init__(self, reader):
        self.InterpMode = ERichCurveInterpMode(reader.u8())
        self.TangentMode = ERichCurveTangentMode(reader.u8())
        self.TangentWeightMode = ERichCurveTangentWeightMode(reader.u8())
        self.Time = reader.f32()
        self.Value = reader.f32()
        self.ArriveTangent = reader.f32()
        self.ArriveTangentWeight = reader.f32()
        self.LeaveTangent = reader.f32()
        self.LeaveTangentWeight = reader.f32()