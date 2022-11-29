from .richcurvekey import FRichCurveKey
from .rotator import FRotator
from .vector import FVector, FVector2D, FVector4, FIntPoint
from .quat import FQuat
from .color import FColor, FLinearColor
from .gameplaytagcontainer import FGameplayTagContainer
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
    "KeyHandleMap": lambda r: None
}