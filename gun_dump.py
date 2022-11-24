import sys
import os
import json
import re
import traceback
from enum import Enum
from ue4 import FPackageReader
from ue4.properties import UProperty, UArrayProperty, UObjectProperty
from ue4.properties import UStructProperty

GAME_PATH_RE = re.compile(r"((?:.*[/\\]|^)(?:[Gg]ame[/\\]|[Cc]ontent[/\\]))(.*)")

def get_game_path(path):
    """Get the base game content path based on a uasset path."""
    return GAME_PATH_RE.match(os.path.abspath(path)).group(1)

def get_asset_path(path):
    """Get the path of a uasset relative to the content directory."""
    return GAME_PATH_RE.match(os.path.abspath(path)).group(2)

def get_output_path(path):
    """Generate an output path."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        "guns",
                        f"{get_asset_path(path).replace('.uasset', '')}.json")

class AssetManager:
    def __init__(self, game_path):
        self.game_path = game_path
        self.package_cache = {}
        self.object_cache = {}
        self.visited = []

    def open_package(self, path):
        if path in self.package_cache:
            return self.package_cache[path]

        with open(path, "rb") as f:
            data = f.read()

        uexp_offset = None

        if path.endswith(".uasset"):
            uexp = path.replace(".uasset", ".uexp")
            if os.path.exists(uexp):
                uexp_offset = len(data)
                with open(uexp, "rb") as f:
                    data += f.read()

        reader = FPackageReader(data, uexp_offset)
        self.package_cache[path] = reader
        self.object_cache[reader] = {}
        return reader

    def read_export(self, reader, name):
        if name in self.object_cache[reader]:
            return self.object_cache[reader][name]

        for export in reader.ExportTable:
            if export.ObjectName == name:
                reader.seek(export.SerialOffset)
                obj = UStructProperty(reader)
                self.object_cache[reader][name] = obj
                return obj

    def read_object(self, reader, index):
        if index > 0:
            name = reader.ExportTable[index - 1].ObjectName
            return (reader, self.read_export(reader, name))
        elif index < 0:
            imp = reader.ImportTable[-index - 1]
            path = reader.GetObjectName(imp.PackageIndex)

            if not path.startswith("/Game/"):
                return (None, None)

            try:
                path = os.path.join(self.game_path, path[6:]) + ".uasset"
                package = self.open_package(os.path.join(self.game_path, path))
            except IOError:
                return (None, None)

            return (package, self.read_export(package, imp.ObjectName))
        else:
            return (None, None)

    def resolve_references(self, reader, obj):
        if obj in self.visited:
            return obj

        if isinstance(obj, dict):
            for key in obj:
                obj[key] = self.resolve_references(reader, obj[key])
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                obj[i] = self.resolve_references(reader, value)
        elif isinstance(obj, UArrayProperty):
            obj.elems = self.resolve_references(reader, obj.elems)
        elif isinstance(obj, UStructProperty):
            obj.fields = self.resolve_references(reader, obj.fields)
        elif isinstance(obj, UObjectProperty):
            new_reader, resolved = self.read_object(reader, obj.Index)
            #if resolved is not None and resolved in self.visited:
                #return reader.GetObjectFullName(obj.Index)
            obj = self.resolve_references(new_reader, resolved)
        elif isinstance(obj, UProperty):
            obj.Data = self.resolve_references(reader, obj.Data)

        self.visited.append(obj)
        return obj

def inherit_properties(sub, base):
    if isinstance(sub, dict):
        for key in set(base.keys()).difference(set(sub.keys())):
            sub[key] = base[key]
        for key in set(base.keys()).intersection(set(sub.keys())):
            sub[key] = inherit_properties(sub[key], base[key])
    elif isinstance(sub, UStructProperty):
        sub.fields = inherit_properties(sub.fields, base.fields)
    elif isinstance(sub, UProperty):
        sub.Data = inherit_properties(sub.Data, base.Data)
    return sub

def only_fields(obj, *whitelist):
    for field in set(obj.fields).difference(set(whitelist)):
        del obj.fields[field]
    return obj

def skip_fields(obj, *blacklist):
    for field in set(obj.fields).intersection(set(blacklist)):
        del obj.fields[field]
    return obj

def get_component(blueprint, name):
    try:
        for node in blueprint.SimpleConstructionScript.AllNodes:
            if node.InternalVariableName == name:
                return node.ComponentTemplate
    except KeyError:
        pass
    try:
        for node in blueprint.InheritableComponentHandler.Records:
            if node.ComponentKey.SCSVariableName == name:
                return node.ComponentTemplate
    except KeyError:
        pass

def read_gun(manager, path):
    reader = manager.open_package(path)

    for export in reader.ExportTable:
        if reader.GetObjectName(export.ClassIndex) == "BlueprintGeneratedClass":
            blueprint = manager.read_export(reader, export.ObjectName)
            break

    blueprint = manager.resolve_references(reader, blueprint)
    firing_state = get_component(blueprint, "FiringState")
    stability = get_component(blueprint, "Stability")

    projectile = firing_state.ProjectileTuning.ProjectileFired
    proj_damage = get_component(projectile, "DamageProjectileEffectComponent")

    return {
        'DamageTuning': skip_fields(proj_damage.DamageTuning, "DamageType"),
        'FiringState': only_fields(firing_state, "FiringRate", "ErrorPower"),
        'Stability': skip_fields(stability, "ComponentTags")
    }

def dump_gun(path):
    game_path = get_game_path(path)
    out_path = get_output_path(path)

    manager = AssetManager(game_path)

    gun = read_gun(manager, path)

    base_path = os.path.join(game_path, "Equippables/Guns/_Core/Gun.uasset")
    base_gun = read_gun(manager, base_path)

    gun = inherit_properties(gun, base_gun)

    def json_default(obj):
        if isinstance(obj, Enum):
            return obj._name_
        elif isinstance(obj, UProperty):
            if obj.StructName == "RuntimeFloatCurve":
                external = obj.Data.get("ExternalCurve", None)
                if external is not None:
                    curve = external.FloatCurve
                else:
                    curve = obj.Data.EditorCurveData
                return json_default(curve.get("Keys", {}))
            return json_default(obj.Data)
        elif isinstance(obj, UArrayProperty):
            return json_default(obj.elems)
        elif isinstance(obj, UStructProperty):
            return json_default(obj.fields)
        elif isinstance(obj, float):
            return round(obj, 5)
        elif isinstance(obj, dict):
            return {k: json_default(v) for k, v in obj.items()}
        elif hasattr(obj, "__dict__"):
            return json_default(obj.__dict__)
        else:
            return obj

    output = json.dumps(gun, default=json_default, indent=4)

    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as file:
            file.write(output)
        print(f"Wrote to \"{out_path}\"")
    except (OSError, IOError):
        print(f"Unable to open output file \"{out_path}\"", file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        print("Usage: gun_dump.py <uasset 1> <uasset 2> ...", file=sys.stderr)
        return

    for path in sys.argv[1:]:
        if path.endswith(".uexp"):
            continue

        try:
            dump_gun(path)
        except:
            print(f"Exception while processing {os.path.basename(path)}:")
            traceback.print_exc()

if __name__ == "__main__":
    main()
