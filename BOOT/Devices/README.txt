OTHER CONSOLES
==============

The same andr36oid image runs on these consoles too. Each folder holds the
files for one of them:
  rk3326-r36s-android.dtb   the device tree Android boots with
  rg351*-uboot.dtb, rg351*-kernel.dtb
                            the screen setup U-Boot uses for the boot logo,
                            the same file under the six names U-Boot looks for
  logo.bmp, logo_kernel.bmp the boot logo
  boot.ini-android          the Android boot script with this console's screen
                            settings (orientation, density)

The andr36oid SD card flasher copies them for you when you pick the console.
By hand: copy all files of the folder to the top of the BOOT partition,
replacing the ones there.
Keep a copy of the files you replace so you can go back.

R46H  1024x768 screen
R50S  480x854 screen, mounted sideways
