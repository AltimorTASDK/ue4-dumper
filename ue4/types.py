import struct

PACKAGE_FILE_TAG = 0x9E2A83C1

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
        self.VersionUE3 = reader.s32()
        self.FileVersion = reader.s32()
        self.LicenseeVersion = reader.s32()
        self.CustomVersionContainer = FCustomVersionContainer(reader)
        self.HeadersSize = reader.u32()
        self.PackageGroup = FString(reader)
        self.PackageFlags = reader.u32()
        self.NameCount = reader.u32()
        self.NameOffset = reader.u32()
        self.GatherableTextDataCount = reader.u32()
        self.GatherableTextDataOffset = reader.u32()
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

class ExImTable():
    """Read only export/import table with more detailed IndexError"""
    def __init__(self, table):
        self.table = table

    def __getitem__(self, index):
        try:
            return self.table[index]
        except IndexError as exception:
            exception.args = (*exception.args,
                              f"index {index}/{len(self) - 1}")
            raise exception

    def __len__(self):
        return len(self.table)

class FPackageReader(BinaryReader):
    def __init__(self, buffer, uexp_offset=None):
        super().__init__(buffer)

        self.uexp_offset = uexp_offset

        self.Summary = FPackageFileSummary(self)

        self.seek(self.Summary.NameOffset)
        self.NameTable = read_array(
            self, FNameEntry, self.Summary.NameCount)

        self.seek(self.Summary.ExportOffset)
        self.ExportTable = ExImTable(read_array(
            self, FObjectExport, self.Summary.ExportCount))

        self.seek(self.Summary.ImportOffset)
        self.ImportTable = ExImTable(read_array(
            self, FObjectImport, self.Summary.ImportCount))

    def offset_string(self):
        if self.uexp_offset is not None and self.offset >= self.uexp_offset:
            return f"uexp:{self.offset - self.uexp_offset:08X}"
        else:
            return f"uasset:{self.offset:08X}"

    def GetObjectName(self, index):
        if index < 0:
            return self.ImportTable[-index - 1].ObjectName
        elif index > 0:
            return self.ExportTable[index - 1].ObjectName
        else:
            return "None"

    def GetObjectQualifiedName(self, index):
        if index < 0:
            outer = self.ImportTable[-index - 1].PackageIndex
        elif index > 0:
            outer = self.ExportTable[index - 1].SuperIndex
        else:
            return "None"

        name = self.GetObjectName(index)
        if outer == 0:
            return name
        else:
            return f"{self.GetObjectQualifiedName(outer)}.{name}"

    def GetObjectClassName(self, index):
        if index < 0:
            return self.ImportTable[-index - 1].ClassName
        elif index > 0:
            return self.GetObjectName(self.ExportTable[index - 1].ClassIndex)
        else:
            return "None"

    def GetObjectFullName(self, index):
        if index == 0:
            return "None"
        return (f"{self.GetObjectClassName(index)} "
                f"{self.GetObjectQualifiedName(index)}")

def FName(reader):
    Index = reader.u32()
    ExtraIndex = reader.u32()

    if Index > len(reader.NameTable):
        print(f"Invalid name index 0x{Index:08X} @ {reader.offset_string()}")

    name = reader.NameTable[Index]
    if ExtraIndex == 0:
        return name

    return f"{name}_{ExtraIndex - 1}"

def FNameEntry(reader):
    name = FString(reader)
    reader.u16() # NonCasePreservingHash
    reader.u16() # CasePreservingHash
    return name

def FString(reader):
    return reader.string(reader.u32())[:-1].decode()

def TArray(reader, type):
    return read_array(reader, type, reader.u32())

def read_array(reader, type, count):
    return [type(reader) for _ in range(count)]