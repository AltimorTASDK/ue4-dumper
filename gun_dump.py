import sys
import os
import json
import re
import traceback
from enum import Enum
from numpy import float32
from ue4 import FPackageReader
from ue4.properties import UProperty, UArrayProperty, UObjectProperty
from ue4.properties import UStructProperty
from ue4.structs import STRUCT_TYPE_MAP
from ue4.structs import ERichCurveInterpMode as RCIM
from ue4.structs import ERichCurveTangentMode as RCTM
from ue4.structs import ERichCurveTangentWeightMode as RCTWM

GAME_PATH_RE     = re.compile(r"((?:.*[/\\]|^)(?:Game[/\\]|Content[/\\]))(.*)")
GUN_PATH_RE      = re.compile(r"((?:.*[/\\]|^)(?:Equippables[/\\]Guns[/\\]))(.*)")
ABILITY_PATH_RE  = re.compile(r"((?:.*[/\\]|^)(?:Characters[/\\]))(.*)")

def get_game_path(path):
    """Get the base game content path based on a uasset path."""
    return GAME_PATH_RE.match(os.path.abspath(path)).group(1)

def get_gun_path(path):
    """Get the path of a gun uasset relative to the Guns directory."""
    if match := ABILITY_PATH_RE.match(os.path.abspath(path)):
        return match.group(2)
    if match := GUN_PATH_RE.match(os.path.abspath(path)):
        return match.group(2)
    return os.path.basename(path)

def get_output_path(path):
    """Generate an output path."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        "guns",
                        f"{os.path.split(get_gun_path(path))[0]}.json")

class AssetManager:
    def __init__(self, game_path):
        self.game_path = game_path
        self.package_cache = {}
        self.object_cache = {}

    def open_package(self, path):
        if path in self.package_cache:
            return self.package_cache[path]

        with open(path, "rb") as f:
            data = f.read()

        uexp_offset = None
        root, ext = os.path.splitext(path)

        if ext == ".uasset":
            uexp = f"{root}.uexp"
            if os.path.exists(uexp):
                uexp_offset = len(data)
                with open(uexp, "rb") as f:
                    data += f.read()

        reader = FPackageReader(data, uexp_offset)
        self.package_cache[path] = reader
        self.object_cache[reader] = {}
        self.visited = []
        return reader

    def read_export(self, reader, name):
        if name in self.object_cache[reader]:
            return self.object_cache[reader][name]

        for export in reader.ExportTable:
            if export.ObjectName == name:
                reader.seek(export.SerialOffset)
                obj = UStructProperty(reader)
                self.object_cache[reader][name] = obj
                self.resolve_references(reader, obj)

                obj.default = self.read_export(reader, f"Default__{name}")
                outer       = self.read_object(reader, export.SuperIndex)
                obj.outer_package, obj.outer = outer
                return obj

    def read_object(self, reader, index, *, default=False):
        if index > 0:
            name = reader.ExportTable[index - 1].ObjectName
            if default:
                name = f"Default__{name}"
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

            name = imp.ObjectName
            if default:
                name = f"Default__{name}"
            return (package, self.read_export(package, name))
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
            reader, obj = self.read_object(reader, obj.Index)
        elif isinstance(obj, UProperty):
            obj.Data = self.resolve_references(reader, obj.Data)

        self.visited.append(obj)
        return obj

def inherit_properties(sub, base):
    if isinstance(sub, dict):
        new = {**base, **{k: inherit_properties(sub[k], base[k])
                             if k in base else sub[k] for k in sub}}
        sub.clear()
        sub.update(new)
    elif isinstance(sub, UStructProperty):
        sub.fields = inherit_properties(sub.fields, base.fields)
    elif isinstance(sub, UProperty):
        if sub.Type == "StructProperty" and sub.StructName in STRUCT_TYPE_MAP:
            return sub
        if sub.Type == "ObjectProperty":
            return sub
        sub.Data = inherit_properties(sub.Data, base.Data)
    return sub

def only_fields(obj, *whitelist):
    if obj is None:
        return None
    for field in set(obj.fields).difference(set(whitelist)):
        del obj.fields[field]
    return obj

def skip_fields(obj, *blacklist):
    if obj is None:
        return None
    for field in set(obj.fields).intersection(set(blacklist)):
        del obj.fields[field]
    return obj

def get_component(blueprint, name):
    try:
        for node in blueprint.SimpleConstructionScript.AllNodes:
            if node.InternalVariableName == name:
                if node.ComponentClass is not None:
                    base = node.ComponentClass.default
                    if base is not None:
                        return inherit_properties(node.ComponentTemplate, base)
                return node.ComponentTemplate
    except AttributeError:
        pass
    try:
        for node in blueprint.InheritableComponentHandler.Records:
            if node.ComponentKey.SCSVariableName == name:
                if blueprint.outer is not None:
                    base = get_component(blueprint.outer, name)
                return inherit_properties(node.ComponentTemplate, base)
    except AttributeError:
        pass
    if blueprint.outer is not None:
        return get_component(blueprint.outer, name)

def read_gun(manager, path):
    reader = manager.open_package(path)

    for export in reader.ExportTable:
        if reader.GetObjectName(export.ClassIndex) == "BlueprintGeneratedClass":
            blueprint = manager.read_export(reader, export.ObjectName)
            break

    magazine    = get_component(blueprint, "MagazineAmmo")
    reserve     = get_component(blueprint, "ReserveAmmo")
    firing      = get_component(blueprint, "FiringState")
    zoom_rof    = get_component(blueprint, "Comp_Gun_ZoomFiringRateModifier")
    stability   = get_component(blueprint, "Stability")
    stab_zoom   = get_component(blueprint, "ZoomedStability")
    stab_burst1 = get_component(blueprint, "SecondaryModeStability")
    stab_burst2 = get_component(blueprint, "BurstStability")
    stab_burst3 = get_component(blueprint, "BurstModeStability")
    readying    = get_component(blueprint, "ReadyingState")

    projectile  = firing.ProjectileTuning.ProjectileFired
    damage_comp = get_component(projectile, "DamageProjectileEffectComponent")
    wall_pen    = get_component(projectile, "WallPenetrationComponent")
    damage      = damage_comp.DamageTuning

    wall_pen.fields.setdefault("StoppingDistanceMultiplier", 1.0)
    wall_pen.fields.setdefault("PenetrationPowerMultiplier", 1.0)

    gun = {
        'DamageTuning':    skip_fields(damage,      "DamageType"),
        'MagazineAmmo':    magazine,
        'ReserveAmmo':     reserve,
        'FiringState':     only_fields(firing,      "FiringRate",
                                                    "ErrorPower",
                                                    "ErrorRetries"),
        'ZoomFiringRate':  only_fields(zoom_rof,    "ZoomFiringRateMultiplier"),
        'Penetration':     only_fields(wall_pen,    "StoppingDistanceMultiplier",
                                                    "PenetrationPowerMultiplier"),
        'Stability':       skip_fields(stability,   "ComponentTags"),
        'ZoomedStability': skip_fields(stab_zoom,   "ComponentTags"),
        'BurstStability1': skip_fields(stab_burst1, "ComponentTags"),
        'BurstStability2': skip_fields(stab_burst2, "ComponentTags"),
        'BurstStability3': skip_fields(stab_burst3, "ComponentTags"),
        'ReadyingState':   only_fields(readying,    "ReadyingTimes[0]",
                                                    "ReadyingTimes[1]",
                                                    "ReadyingTimes[2]")
    }

    return {k: v for k, v in gun.items() if v is not None}

def process_curve(keys):
    for i, (prev, key) in enumerate(zip([None, *keys], keys)):
        if key.TangentWeightMode != RCTWM.RCTWM_WeightedNone:
            raise NotImplementedError

        out = {}

        if i != len(keys) - 1:
            out['InterpMode'] = json_default(key.InterpMode)
        if len(keys) != 1:
            out['Time'] = json_default(key.Time)
        out['Value'] = json_default(key.Value)
        if i != 0 and prev.InterpMode == RCIM.RCIM_Cubic:
            out['ArriveTangent'] = json_default(key.ArriveTangent)
        if i != len(keys) - 1 and key.InterpMode == RCIM.RCIM_Cubic:
            out['LeaveTangent'] = json_default(key.LeaveTangent)

        yield out

def json_default(obj):
    if isinstance(obj, Enum):
        return obj._name_
    elif isinstance(obj, UProperty):
        if obj.StructName == "RuntimeFloatCurve":
            external = obj.Data.get("ExternalCurve", None)
            editor = obj.Data.get("EditorCurveData", None)
            if external is not None:
                return json_default(external.FloatCurve.get("Keys", []))
            elif editor is not None:
                return json_default(editor.get("Keys", []))

        return json_default(obj.Data)
    elif isinstance(obj, UArrayProperty):
        if obj.elems and obj.elems[0].StructName == "RichCurveKey":
            return [*process_curve(obj)]
        return json_default(obj.elems)
    elif isinstance(obj, UStructProperty):
        return json_default(obj.fields)
    elif isinstance(obj, float):
        return next((r for r in (round(obj, n) for n in range(10))
                             if float32(obj) == float32(r)), obj)
    elif isinstance(obj, dict):
        return {k: json_default(v) for k, v in obj.items()}
    elif hasattr(obj, "__dict__"):
        return json_default(obj.__dict__)
    else:
        return obj

def dump_gun(path):
    game_path = get_game_path(path)
    out_path = get_output_path(path)
    gun = read_gun(AssetManager(game_path), path)

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
