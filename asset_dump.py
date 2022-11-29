import sys
import os
import json
import re
import traceback
from enum import Enum
from numpy import float32
from ue4 import FPackageReader, FName, debug_print
from ue4.properties import UProperty, UArrayProperty, UObjectProperty
from ue4.properties import UStructProperty

GAME_PATH_RE = re.compile(r"((?:.*[/\\]|^)(?:[Gg]ame[/\\]|[Cc]ontent[/\\]))(.*)")

def get_asset_path(path):
    """Get the path of a uasset relative to the content directory."""
    match = GAME_PATH_RE.match(os.path.abspath(path))
    return match.group(2) if match else os.path.basename(path)

def get_output_path(path):
    """Generate an output path."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        "output",
                        f"{get_asset_path(path).replace('.uasset', '')}.json")

def read_package(reader):
    for i, name in enumerate(reader.NameTable):
        debug_print(f"Name {i}: {name}")

    for i in range(len(reader.ExportTable)):
        debug_print(f"Export {i}: {reader.GetObjectFullName(i + 1)}")

    for i in range(len(reader.ImportTable)):
        debug_print(f"Import {i}: {reader.GetObjectFullName(-i - 1)}")

    objects = {}
    for i, export in enumerate(reader.ExportTable):
        reader.seek(export.SerialOffset)
        name = reader.GetObjectFullName(i + 1)
        debug_print(f"Export {name} @ {reader.offset_string()}")
        obj = UStructProperty(reader)

        if reader.GetObjectName(export.ClassIndex) == "DataTable":
            reader.s32()
            NumRows = reader.s32()
            obj.RowMap = {FName(reader): UStructProperty(reader)
                          for _ in range(NumRows)}

        objects[name] = obj

    return objects

def dump_asset(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except (OSError, IOError):
        print(f"Unable to open \"{path}\"", file=sys.stderr)
        return

    uexp_offset = None

    if path.endswith(".uasset"):
        uexp = path.replace(".uasset", ".uexp")
        if os.path.exists(uexp):
            uexp_offset = len(data)
            try:
                with open(uexp, "rb") as f:
                    data += f.read()
            except (OSError, IOError):
                print(f"Unable to open \"{uexp}\"", file=sys.stderr)
                return

    out_path = get_output_path(path)
    reader = FPackageReader(data, uexp_offset)
    objects = read_package(reader)

    def json_default(obj):
        if isinstance(obj, Enum):
            return obj._name_
        elif isinstance(obj, UProperty):
            if obj.Type == "MapProperty" and obj.InnerType == "StructProperty":
                return [{"Key": json_default(k), "Value": json_default(v)}
                        for k, v in obj.Data.items()]
            return json_default(obj.Data)
        elif isinstance(obj, UArrayProperty):
            return json_default(obj.elems)
        elif isinstance(obj, UObjectProperty):
            return reader.GetObjectFullName(obj.Index)
        elif isinstance(obj, UStructProperty):
            return json_default(obj.fields)
        elif isinstance(obj, float):
            return round(obj, 7)
        elif isinstance(obj, dict):
            return {json_default(k): json_default(v) for k, v in obj.items()}
        elif hasattr(obj, "__dict__"):
            return json_default(obj.__dict__)
        else:
            return obj

    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(objects, f, default=json_default, indent=4)
        print(f"Wrote to \"{out_path}\"")
    except (OSError, IOError):
        print(f"Unable to open output file \"{out_path}\"", file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        print("Usage: asset_dump.py <uasset 1> <uasset 2> ...", file=sys.stderr)
        return

    for path in sys.argv[1:]:
        if path.endswith(".uexp"):
            continue

        try:
            dump_asset(path)
        except:
            print(f"Exception while processing {os.path.basename(path)}:")
            traceback.print_exc()

if __name__ == "__main__":
    main()
