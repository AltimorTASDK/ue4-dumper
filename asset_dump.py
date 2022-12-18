import json
import logging
import os
import re
import sys
import traceback
from collections import UserString
from enum import Enum
from numpy import float32
from ue4 import FPackageReader, FName
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
                        f"{os.path.splitext(get_asset_path(path))[0]}.json")

def read_package(reader):
    for i, name in enumerate(reader.NameTable):
        logging.debug(f"Name {i}: {name}")

    for i in range(len(reader.ExportTable)):
        logging.debug(f"Export {i}: {reader.GetObjectDeclName(i + 1)}")

    for i in range(len(reader.ImportTable)):
        logging.debug(f"Import {i}: {reader.GetObjectDeclName(-i - 1)}")

    objects = {}
    for i, export in enumerate(reader.ExportTable):
        logging.debug(f"Export {reader.GetObjectFullName(i + 1)} @ "
                      f"{reader.offset_string()} size {export.SerialSize:08X}")

        reader.seek(export.SerialOffset)
        obj = UStructProperty(reader)

        if reader.GetObjectName(export.ClassIndex) == "DataTable":
            reader.s32()
            NumRows = reader.s32()
            obj.RowMap = {FName(reader): UStructProperty(reader)
                          for _ in range(NumRows)}

        objects[reader.GetObjectDeclName(i + 1)] = obj

    return objects

def dump_asset(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except (OSError, IOError):
        print(f"Unable to open \"{path}\"", file=sys.stderr)
        return

    uexp_offset = None
    root, ext = os.path.splitext(path)

    if ext == ".uasset":
        uexp = f"{root}.uexp"
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
        elif isinstance(obj, UserString):
            return str(obj)
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
            return next((r for r in (round(obj, n) for n in range(10))
                                if float32(obj) == float32(r)), obj)
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
    logging.basicConfig(format="%(levelname)s: %(message)s",
                        level=logging.DEBUG)

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
