from ue4 import TArray, FName

class FGameplayTagContainer():
    def __init__(self, reader):
        self.GameplayTags = TArray(reader, FName)