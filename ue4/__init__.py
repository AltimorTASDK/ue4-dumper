from .types import FPackageReader, FName, FString, TArray, FGuid

debug = True

def debug_print(*args, **kwargs):
    if debug:
        print(*args, **kwargs)