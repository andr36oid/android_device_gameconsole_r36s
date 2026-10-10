EXPERIMENTAL DEVICE TREES FOR R36S CLONES AND VARIANTS
======================================================

Nobody on the andr36oid side has tested these on real hardware. They are
ported from other projects and from the stock firmware of these consoles.
A wrong one can leave the screen black, the buttons dead, or put a wrong
voltage on a rail. Only try one if the normal files (the top of this
partition and ../Panels) do not work on your console, and only if you can
put the SD card in a computer to undo it.

Each folder holds one board:
  rk3326-r36s-android.dtb   the device tree Android boots with
  rg351mp-kernel.dtb        the panel setup U-Boot uses for the boot logo
  rg351v-kernel.dtb         and the charge screen, six copies of the same
  rg351p-kernel.dtb         file (U-Boot picks the name by board revision,
  rg351mp-uboot.dtb         older U-Boots read the -kernel names, the
  rg351v-uboot.dtb          andr36oid U-Boot the -uboot names)
  rg351p-uboot.dtb
  logo.bmp, logo_kernel.bmp, battery_*.bmp
                            only in the folders of 720x720 consoles

How to use one
--------------
1. Put the SD card in a computer and open the BOOT partition.
2. Back up rk3326-r36s-android.dtb, the six rg351*.dtb files,
   logo.bmp, logo_kernel.bmp and the battery_*.bmp files from the top of
   the partition (for example into a folder called Backup).
3. Copy all files from the folder that matches your console to the top
   of the partition, replacing the ones there.
4. Boot. If the logo stays black but Android comes up, the U-Boot file is
   wrong; if Android does not come up, try another folder or go back.

To go back, copy your backup (or the files from ../Panels/Panel4, or the
folder you used before) to the top of the partition again.

Which folder
------------
Genuine R36S wiring, only the screen differs:
  R36S-V22            R36S V22 board with its own panel
  R36S-V21            R36S V21 board
  R36S-V21-2551-2552  V21 batches 2551/2552 (USB host power on GPIO0_B7)
  R36S-Y02-Y07        R36S Y02..Y07 boards
  R36S-V30            R36S V30 board
  R36S-V30-2603       V30 batch 2603 (no second card slot, 3380 mAh)
  R36S-Panel3-Alt     Panel 3 with the init sequence ROCKNIX uses

"EE" clones (ship with EmuELEC, volume keys on one ADC pin), 640x480:
  EE-G80-Panel8       G80C / G80CA / G80D, panel 8
  EE-G80-Panel9       G80CA, panel 9
  EE-K36-Panel1       K36 / HG36 / L35 / R36 Pro / ANS11 / "R36S Panel 1"
  EE-K36-Panel4       K36 / RX6S / RX6H / "R36S Panel 4" clones
  EE-V12-Var2         R36S-V12 clone, variant 2
  EE-V12-Var3-Panel3  R36S-V12 clone, variant 3 with panel 3
  EE-V12-Var3-PanelA  R36S-V12 clone, variant 3 with the other panel
  K36S                K36S (RK915 Wi-Fi, see below)
  R36T                R36T (RK915 Wi-Fi)
  XF35H               XF35H (RK915 Wi-Fi, rumble)

"EE" clones with a 720x720 screen:
  R36-Ultra           R36 Ultra / GR36 (RK915 Wi-Fi, RGB LED, rumble)
  R36-Max             R36 Max
  S600                S600
  R39-Max             R39 Max, H50 Pro, T16 Max V2, ANS13
  T16-Max             T16 Max, first version
  XF40H               XF40H (RK915 Wi-Fi, rumble)
R36-Max and T16-Max drive the speaker through an extra amplifier; S600 and
R39-Max do not. If the speaker stays silent, try the other one of the
pair (R36-Max / S600, T16-Max / R39-Max): the panel is the same.

"Soy Sauce" clones (board print Y3506_V03 / V04 / V05):
  Soy-Panel5          Soy Sauce with panel 5
  Soy-Panel5-253x     same, batches 253x (Select and FN swapped)
  Soy-Panel6          Soy Sauce with panel 6
  Soy-Panel7          Soy Sauce with panel 7
  Soy-Panel7-253x     same, batches 253x (Select and FN swapped)
  Soy-V04-Panel2      Y3506_V04 with panel 2
  Soy-V05-2601        Y3506_V05, batch 2601

If you own a Soy Sauce board, do not use ../Panels/Panel5 or Panel6:
those have the right screen but the genuine R36S wiring, which puts 3.3 V
on a rail that is 1.1 V on the Soy Sauce board. Use a Soy-* folder.

RK915 Wi-Fi
-----------
R36-Ultra, XF40H, XF35H, K36S and R36T have an RK915 Wi-Fi chip on the
second card slot's bus. The device tree describes it, but Wi-Fi only
works on a build that has the RK915 driver. These consoles have no second
card slot.

eMMC consoles
-------------
The R36 Ultra, R36 Max, R39 Max, S600, T16 Max, ANS13, H50 Pro, XF35H,
XF40H and R36T keep their own system on built-in eMMC. The console starts
from the eMMC first and only looks at the SD card if the eMMC has no
working boot loader, so putting this SD card in may not do anything at all
on them.
