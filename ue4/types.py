from collections import UserString
from .version import *
import struct

PACKAGE_FILE_TAG = 0x9E2A83C1

PKG_FilterEditorOnly = 0x80000000

class InvalidPackageMagic(Exception):
    pass

class BinaryReader():
    def __init__(self, buffer, offset=0):
        self.buffer = buffer
        self.offset = offset

    def seek(self, offset):
        self.offset = offset

    def skip(self, count):
        self.offset += count

    def tell(self):
        return self.offset

    def bool(self):
        (result,) = struct.unpack_from("?", self.buffer, self.offset)
        self.offset += 1
        return result

    def s8(self):
        (result,) = struct.unpack_from("b", self.buffer, self.offset)
        self.offset += 1
        return result

    def u8(self):
        (result,) = struct.unpack_from("B", self.buffer, self.offset)
        self.offset += 1
        return result

    def s16(self):
        (result,) = struct.unpack_from("<h", self.buffer, self.offset)
        self.offset += 2
        return result

    def u16(self):
        (result,) = struct.unpack_from("<H", self.buffer, self.offset)
        self.offset += 2
        return result

    def s32(self):
        (result,) = struct.unpack_from("<i", self.buffer, self.offset)
        self.offset += 4
        return result

    def u32(self):
        (result,) = struct.unpack_from("<I", self.buffer, self.offset)
        self.offset += 4
        return result

    def s64(self):
        (result,) = struct.unpack_from("<q", self.buffer, self.offset)
        self.offset += 8
        return result

    def u64(self):
        (result,) = struct.unpack_from("<Q", self.buffer, self.offset)
        self.offset += 8
        return result

    def f32(self):
        (result,) = struct.unpack_from("<f", self.buffer, self.offset)
        self.offset += 4
        return result

    def f64(self):
        (result,) = struct.unpack_from("<d", self.buffer, self.offset)
        self.offset += 8
        return result

    def string(self, size):
        (result,) = struct.unpack_from(f"{size}s", self.buffer, self.offset)
        self.offset += size
        return result

class FGuid():
    def __init__(self, reader):
        self.A = reader.u32()
        self.B = reader.u32()
        self.C = reader.u32()
        self.D = reader.u32()

    def __str__(self):
        return f"{self.A:08X}-{self.B:08X}-{self.C:08X}-{self.D:08X}"

class FCustomVersion():
    def __init__(self, reader):
        self.Key = FGuid(reader)
        self.Version = reader.s32()

class FCustomVersionContainer():
    def __init__(self, reader):
        self.Versions = TArray(reader, FCustomVersion)

class FPackageFileSummary():
    def __init__(self, reader):
        self.Tag = reader.u32()

        if self.Tag != PACKAGE_FILE_TAG:
            raise InvalidPackageMagic()

        self.Version = reader.s32()

        if self.Version != -4:
            self.VersionUE3 = reader.s32()
        else:
            self.VersionUE3 = -1

        self.FileVersion = reader.s32()

        if self.Version <= -8:
            self.VersionUE5 = reader.s32()
        else:
            self.VersionUE5 = -1

        self.LicenseeVersion = reader.s32()

        if self.Version <= -2:
            self.CustomVersionContainer = FCustomVersionContainer(reader)
        else:
            self.CustomVersionContainer = None

        self.HeadersSize = reader.u32()
        self.PackageGroup = FString(reader)
        self.PackageFlags = reader.u32()
        self.NameCount = reader.u32()
        self.NameOffset = reader.u32()

        if (self.FileVersion >= VER_UE4_ADDED_PACKAGE_SUMMARY_LOCALIZATION_ID
                and not (self.PackageFlags & PKG_FilterEditorOnly)):
            self.LocalizationId = FString(reader)
        else:
            self.LocalizationId = None

        if self.FileVersion >= VER_UE4_SERIALIZE_TEXT_IN_PACKAGES:
            self.GatherableTextDataCount = reader.u32()
            self.GatherableTextDataOffset = reader.u32()
        else:
            self.GatherableTextDataCount = 0
            self.GatherableTextDataOffset = 0

        self.ExportCount = reader.u32()
        self.ExportOffset = reader.u32()
        self.ImportCount = reader.u32()
        self.ImportOffset = reader.u32()
        self.DependsOffset = reader.u32()

class FObjectExport():
    def __init__(self, reader):
        self.ClassIndex = reader.s32()
        self.SuperIndex = reader.s32()
        self.TemplateIndex = reader.s32()
        self.PackageIndex = reader.s32()
        self.ObjectName = FName(reader)
        self.ObjectFlags = reader.u32()
        self.SerialSize = reader.u64()
        self.SerialOffset = reader.u64()
        self.bForcedExport = reader.u32()
        self.bNotForClient = reader.u32()
        self.bNotForServer = reader.u32()
        self.Guid = FGuid(reader)
        self.PackageFlags = reader.u32()
        self.bNotForEditorGame = reader.u32()
        self.bIsAsset = reader.u32()

        if reader.Summary.VersionUE5 >= VER_UE5_OPTIONAL_RESOURCES:
            self.bGeneratePublicHash = reader.u32()
        else:
            self.bGeneratePublicHash = False

        self.FirstExportDependency = reader.s32()
        self.SerializationBeforeSerializationDependencies = reader.s32()
        self.CreateBeforeSerializationDependencies = reader.s32()
        self.SerializationBeforeCreateDependencies = reader.s32()
        self.CreateBeforeCreateDependencies = reader.s32()

class FObjectImport():
    def __init__(self, reader):
        self.ClassPackage = FName(reader)
        self.ClassName = FName(reader)
        self.PackageIndex = reader.s32()
        self.ObjectName = FName(reader)

        if (not reader.IsFilterEditorOnly() and
                reader.Summary.FileVersion >= VER_UE4_NON_OUTER_PACKAGE_IMPORT):
            self.PackageName = FName(reader)
        else:
            self.PackageName = None

        if reader.Summary.VersionUE5 >= VER_UE5_OPTIONAL_RESOURCES:
            self.bImportOptional = reader.u32()
        else:
            self.bImportOptional = False

class PackageTable():
    """Read only table with more detailed IndexError"""
    def __init__(self, table):
        self.table = table

    def __getitem__(self, index):
        try:
            return self.table[index]
        except IndexError as exception:
            exception.args = (*exception.args, f"index {index}/{len(self) - 1}")
            raise exception

    def __len__(self):
        return len(self.table)

class FPackageReader(BinaryReader):
    def __init__(self, buffer, uexp_offset=None):
        super().__init__(buffer)

        self.uexp_offset = uexp_offset

        self.Summary = FPackageFileSummary(self)

        self.seek(self.Summary.NameOffset)
        self.NameTable = PackageTable(self.array(FNameEntry,
                                                 self.Summary.NameCount))

        self.seek(self.Summary.ExportOffset)
        self.ExportTable = PackageTable(self.array(FObjectExport,
                                                   self.Summary.ExportCount))

        self.seek(self.Summary.ImportOffset)
        self.ImportTable = PackageTable(self.array(FObjectImport,
                                                   self.Summary.ImportCount))

    def array(self, type, count):
        return [type(self) for _ in range(count)]

    def offset_string(self):
        if self.uexp_offset is not None and self.offset >= self.uexp_offset:
            return f"uexp:{self.offset - self.uexp_offset:08X}"
        else:
            return f"uasset:{self.offset:08X}"

    def ExIm(self, index):
        if index < 0:
            return self.ImportTable[-index - 1]
        if index > 0:
            return self.ExportTable[index - 1]
        return None

    def IsFilterEditorOnly(self):
        return (self.Summary.PackageFlags & PKG_FilterEditorOnly) != 0

    def GetObjectPackage(self, index):
        while index != 0 and (package := self.ExIm(index).PackageIndex) != 0:
            index = package
        return self.GetObjectName(index)

    def GetObjectName(self, index):
        return str(self.ExIm(index).ObjectName) if index != 0 else "None"

    def GetObjectPath(self, index):
        if index == 0:
            return "None"
        if (outer := self.ExIm(index).PackageIndex) != 0:
            return f"{self.GetObjectPath(outer)}.{self.GetObjectName(index)}"
        return self.GetObjectName(index)

    def GetObjectClassName(self, index):
        if index < 0:
            return self.ImportTable[-index - 1].ClassName
        if index > 0:
            return self.GetObjectName(self.ExIm(index).ClassIndex)
        return "None"

    def GetObjectFullName(self, index):
        if index == 0:
            return "None"
        return f"{self.GetObjectClassName(index)} {self.GetObjectPath(index)}"

    def GetObjectDeclName(self, index):
        name = self.GetObjectFullName(index)
        if index > 0:
            export = self.ExIm(index)
            if export.SuperIndex != 0:
                name += f" : {self.GetObjectPath(export.SuperIndex)}"
            elif export.TemplateIndex != index:
                name += f" : {self.GetObjectPath(export.TemplateIndex)}"
        return name

class FName(UserString):
    def __init__(self, reader):
        match reader:
            case FPackageReader():
                self.Index = reader.u32()
                self.ExtraIndex = reader.u32()
                self.data = reader.NameTable[self.Index]
                if self.ExtraIndex != 0:
                    self.data += f"_{self.ExtraIndex - 1}"
            case _:
                self.Index = None
                self.ExtraIndex = None
                super().__init__(reader)

    def __hash__(self):
        return hash(self.data)

class FNameEntry(UserString):
    def __init__(self, reader):
        match reader:
            case FPackageReader():
                self.data = FString(reader)
                self.NonCasePreservingHash = reader.u16()
                self.CasePreservingHash = reader.u16()
            case _:
                self.NonCasePreservingHash = None
                self.CasePreservingHash = None
                super().__init__(reader)

def FString(reader):
    length = reader.s32()
    if length >= 0:
        return reader.string(length)[:-1].decode()
    else:
        return reader.string(length * -2)[:-1].decode("utf-16", "ignore")

def TArray(reader, type):
    return reader.array(type, reader.u32())