EXPERIMENTAL DEVICE TREES FOR R36S CLONES AND VARIANTS
======================================================

Nobody on the andr36oid side has tested these on real hardware. They are
ported from other projects and from the stock firmware of these consoles.
A wrong one can leave the screen black, the buttons dead, or put a wrong
voltage on a rail. Only try one if the normal files (the BOOT root and
Panels/PanelN) do not work on your console, and only if you can put the SD
card in a computer to undo it.

Each folder holds one board:
  rk3326-r36s-android.dtb   the device tree Android boots with
  rg351mp-kernel.dtb        the panel setup U-Boot uses for the boot logo
                            and the charge screen

How to use one
--------------
1. Put the SD card in a computer and open the BOOT partition.
2. Back up rk3326-r36s-android.dtb and rg351mp-kernel.dtb from the top
   of the partition (for example into a folder called Backup).
3. Copy both files from the folder that matches your console to the top
   of the partition, replacing the ones there.
4. For R36-Ultra also copy logo.bmp and logo_kernel.bmp from that folder.
5. Boot. If the logo stays black but Android comes up, the U-Boot file is
   wrong; if Android does not come up, try another folder or go back.

To go back, copy your backup (or the two files from Panels/Panel4, or the
PanelN you used before) to the top of the partition again.

If the logo never shows, your console may ask U-Boot for rg351p-kernel.dtb
or rg351v-kernel.dtb instead. Copy rg351mp-kernel.dtb under those names too.

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

"EE" clones (ship with EmuELEC 4.7, volume keys on one ADC pin):
  EE-G80-Panel8       G80C / G80CA / G80D, panel 8
  EE-G80-Panel9       G80CA, panel 9
  EE-K36-Panel1       K36 / HG36 / "R36S Panel 1" clones
  EE-K36-Panel4       K36 / HG36 / "R36S Panel 4" clones
  EE-V12-Var2         R36S-V12 clone, variant 2
  EE-V12-Var3-Panel3  R36S-V12 clone, variant 3 with panel 3
  EE-V12-Var3-PanelA  R36S-V12 clone, variant 3 with the other panel
  R36-Ultra           R36 Ultra / GR36, 720x720 screen, see below

"Soy Sauce" clones (board print Y3506_V03 / V04 / V05):
  Soy-Panel5          Soy Sauce with panel 5
  Soy-Panel5-253x     same, batches 253x (Select and FN swapped)
  Soy-Panel6          Soy Sauce with panel 6
  Soy-Panel7          Soy Sauce with panel 7
  Soy-Panel7-253x     same, batches 253x (Select and FN swapped)
  Soy-V04-Panel2      Y3506_V04 with panel 2
  Soy-V05-2601        Y3506_V05, batch 2601

If you own a Soy Sauce board, do not use Panels/Panel5 or Panels/Panel6:
those have the right screen but the genuine R36S wiring, which puts 3.3 V
on a rail that is 1.1 V on the Soy Sauce board. Use a Soy-* folder.

R36 Ultra
---------
The screen is 720x720. This build is set up for 640x480, so Android may
draw everything at the wrong size.
Its Wi-Fi chip is an RK915; the device tree describes it, but Wi-Fi only
works on a build with the RK915 driver.
The Ultra boots from its built-in eMMC. The SD card is only used if the
eMMC has no working boot loader, so putting this SD card in may not do
anything at all on an Ultra.
