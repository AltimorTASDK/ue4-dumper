from ue4 import FName, FString

class FSoftObjectPath():
    def __init__(self, reader):
        self.AssetPathName = FName(reader)
        self.SubPathString = FString(reader)