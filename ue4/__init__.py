from .types import FPackageReader, FName, FString, TArray, FGuid

debug = False

def debug_print(*args, **kwargs):
    if debug:
        print(*args, **kwargs)