import sys
import os
import json
import re
import traceback
from enum import Enum
from ue4 import FPackageReader, debug_print
from ue4.properties import UProperty

# GAME_PATH_RE = re.compile(r"[/\\][Gg]ame[/\\]")
GAME_PATH_RE = re.compile(r"[/\\][Cc]ontent[/\\]")

class UObject():
    pass

def json_default(obj):
    if isinstance(obj, Enum):
        return obj._name_
    elif isinstance(obj, UProperty):
        return json_default(obj.Data)
    elif isinstance(obj, float):
        return round(obj, 5)
    elif isinstance(obj, dict):
        return {k: json_default(v) for k, v in obj.items()}
    elif hasattr(obj, "__dict__"):
        return json_default(obj.__dict__)
    else:
        return obj

def default_output_path(path):
    """Generate an output path if none is specified."""
    abs_path = os.path.abspath(path)
    match = GAME_PATH_RE.search(abs_path)
    if match:
        relative_path = abs_path[match.end():]
    else:
        relative_path = os.path.basename(path)

    result = os.path.dirname(os.path.realpath(__file__)) + "/output/"
    result += f"{relative_path.replace('.uasset', '')}.json"
    return result

def read_package(data, uexp_offset):
    reader = FPackageReader(data, uexp_offset)
    for i, name in enumerate(reader.NameTable):
        debug_print(f"Name {i}: {name}")

    for i, export in enumerate(reader.ExportTable):
        debug_print(
            f"Export {i}: {reader.GetObjectName(export.ClassIndex)} "
            f"{export.ObjectName}")

    for i, imp in enumerate(reader.ImportTable):
        debug_print(
            f"Import {i}: {imp.ClassName} "
            f"{reader.GetObjectName(imp.PackageIndex)}.{imp.ObjectName}")

    objects = {}
    for i, export in enumerate(reader.ExportTable):
        obj = {}
        reader.seek(export.SerialOffset)
        end = export.SerialOffset + export.SerialSize
        while reader.tell() < end:
            try:
                prop = UProperty(reader)
            except Exception as exception:
                exception.args = (*exception.args, reader.offset_string())
                raise exception

            if prop.Name == "None":
                break

            obj[prop.Name] = prop

        objects[reader.GetObjectFullName(i + 1)] = obj

    return objects

def dump_asset(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except (OSError, IOError):
        print("Unable to open uasset", file=sys.stderr)
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
                print("Unable to open uexp", file=sys.stderr)
                return

    out_path = default_output_path(path)

    objects = read_package(data, uexp_offset)

    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(objects, f, default=json_default, indent=4)
    except (OSError, IOError):
        print(f"Unable to open output file \"{out_path}\"", file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        print("Usage: ue4_dumper.py <uasset 1> <uasset 2> ...", file=sys.stderr)
        return

    for path in sys.argv[1:]:
        if path.endswith(".uexp"):
            continue

        try:
            dump_asset(path)
        except:
            name = os.path.basename(path)
            print(f"Exception while processing {name}:")
            traceback.print_exc()

if __name__ == "__main__":
    main()
