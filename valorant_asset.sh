#!/bin/bash
dir="$1/Equippables/Guns"
dump="python asset_dump.py"

$dump "$dir/_Core/Gun.uasset" \
      "$dir/_Core/Gun_Sniper.uasset" \
      "$dir/_Core/Gun_Zoomable.uasset" \
      "$dir/_Core/Projectile_Gun.uasset"

find "$dir/_Core" -type f -name 'Curve_*.uasset' -exec $dump {} +
find "$dir/_Core" -type f -name 'Comp_Gun_*.uasset' -exec $dump {} +
find "$dir/_Core/Curves" -type f -exec $dump {} +
find "$dir/_Core/WallPenetration" -type f -name 'WallPen_*.uasset' -exec $dump {} +

$dump "$dir/HvyMachineGuns/HMG/HeavyMachineGun.uasset" \
      "$dir/HvyMachineGuns/LMG/LightMachineGun.uasset" \
      "$dir/Rifles/AK/AssaultRifle_AK.uasset" \
      "$dir/Rifles/Burst/AssaultRifle_Burst.uasset" \
      "$dir/Rifles/Carbine/AssaultRifle_ACR.uasset" \
      "$dir/Shotguns/AutoShotgun/AutomaticShotgun.uasset" \
      "$dir/Shotguns/PumpShotgun/PumpShotgun.uasset" \
      "$dir/Sidearms/AutoPistol/AutomaticPistol.uasset" \
      "$dir/Sidearms/BasePistol/BasePistol.uasset" \
      "$dir/Sidearms/Luger/LugerPistol.uasset" \
      "$dir/Sidearms/Revolver/RevolverPistol.uasset" \
      "$dir/Sidearms/Slim/SawedOffShotgun.uasset" \
      "$dir/SniperRifles/Boltsniper/BoltSniper.uasset" \
      "$dir/SniperRifles/DMR/DMR.uasset" \
      "$dir/SniperRifles/Leversniper/LeverSniperRifle.uasset" \
      "$dir/SubMachineGuns/MP5/SubMachineGun_MP5.uasset" \
      "$dir/SubMachineGuns/Vector/Vector.uasset"

find "$dir" -type f -name 'Projectile_*.uasset' -exec $dump {} +