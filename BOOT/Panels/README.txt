SCREEN (PANEL) FILES
====================

Each folder here holds the files for one screen:
  rk3326-r36s-android.dtb   the device tree Android boots with
  rg351mp-kernel.dtb        the panel setup U-Boot uses for the boot logo
  rg351v-kernel.dtb         and the charge screen, three copies of the same
  rg351p-kernel.dtb         file (U-Boot picks the name by board revision)
R36S-Plus also has logo.bmp and logo_kernel.bmp (the 720x720 boot logo)
and battery_*.bmp (the 720x720 charge screen).

The top of this partition holds a copy of Panel4. To switch, put the SD
card in a computer, back up rk3326-r36s-android.dtb and the three rg351*-kernel.dtb
files from the top of the partition, and copy all files from one folder
here over them (for R36S-Plus also copy logo.bmp, logo_kernel.bmp and the
battery_*.bmp files).

  Panel0     genuine R36S, Panel 0
  Panel1     genuine R36S, Panel 1
  Panel2     genuine R36S, Panel 2
  Panel3     genuine R36S, Panel 3
  Panel4     genuine R36S, Panel 4 (the default)
  Panel5     R36S board wiring with the "Panel 5" screen - see warning
  Panel6     R36S board wiring with the "Panel 6" screen - see warning
  R36S-Plus  R36S Plus (720x720 screen)

*** WARNING: SOY SAUCE BOARDS (board print Y3506_V03 / V04 / V05) ***
*** DO NOT USE Panel5 OR Panel6 ON A SOY SAUCE BOARD.              ***

Panel5 and Panel6 have the right screen for many Soy Sauce consoles, but
the rest of the files describe the genuine R36S board. On a Soy Sauce
board that puts 3.3 V (3.0 V while the logo shows) on a power rail that
should be 1.1 V, and the buttons, volume keys and charging detection are
on the wrong pins. Soy Sauce owners: use a Soy-* folder in ../Experimental
instead (see ../Experimental/README.txt), even though those are untested.

Not sure which board you have? Open the back and read the print on the
board, or ask where you bought it, before copying Panel5 or Panel6.

Other clones (G80, K36, HG36, R36 Ultra, R36 Max, XF35H and more) have
their own untested files in ../Experimental.
