#!/bin/bash
dir="$1/Equippables/Guns"
dump="python gun_dump.py"

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