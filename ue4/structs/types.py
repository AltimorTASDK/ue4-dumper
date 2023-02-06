from .richcurvekey import FRichCurveKey
from .rotator import FRotator
from .vector import FVector, FVector2D, FVector4, FIntPoint
from .quat import FQuat
from .color import FColor, FLinearColor
from .gameplaytagcontainer import FGameplayTagContainer
from .moviesceneframerange import FMovieSceneFrameRange
from .framenumber import FFrameNumber
from .softobjectpath import FSoftObjectPath
from ue4 import FGuid

STRUCT_TYPE_MAP = {
    "RichCurveKey": FRichCurveKey,
    "Rotator": FRotator,
    "Vector": FVector,
    "Vector2D": FVector2D,
    "Vector4": FVector4,
    "IntPoint": FIntPoint,
    "Quat": FQuat,
    "Color": FColor,
    "LinearColor": FLinearColor,
    "Guid": FGuid,
    "GameplayTagContainer": FGameplayTagContainer,
    "MovieSceneFrameRange": FMovieSceneFrameRange,
    "MovieSceneFloatChannel": None,
    "MovieSceneEvaluationKey": None,
    "MovieSceneEvaluationTemplate": None,
    "MovieSceneSequenceID": None,
    "MovieSceneTrackIdentifier": None,
    "MovieSceneEvaluationFieldEntityTree": None,
    "ColorMaterialInput": None,
    "DateTime": None,
    "Timespan": None,
    "Box2D": None,
    "FrameNumber": FFrameNumber,
    "SoftObjectPath": FSoftObjectPath,
    "KeyHandleMap": lambda r: None
}