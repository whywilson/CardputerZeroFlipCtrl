# Public screenshots

These four PNGs were captured from CardputerZero's 320×170 RGB565 framebuffer. They show the current client's Auto connection page, WiFi connection page, H key guide, and invalid-IP message. Interface text was not retouched. The PNGs contain no device, location, or capture-software metadata.

Capture used a temporary `XDG_CONFIG_HOME` and FIFO keyboard with Ethernet probing disabled. No real target was contacted, and the user's saved WiFi address was neither read nor modified. The WiFi page displays the RFC 5737 documentation address `192.0.2.10`. The validation page displays the intentionally invalid address `999.1.2.3`.

On the device, stop FlipCTL and APPLaunch before running:

```sh
python3 tools/capture_public_screenshots.py --output /tmp/flipctl-public-screenshots
```

The current client must already be installed, and the caller needs framebuffer access. The script does not manage system services. Restore the app afterwards, or run `systemctl --user start APPLaunch.service`. Do not capture while another app owns the display.

Historical files in `dist/` may contain real device names or network addresses and are excluded from public source packaging. Public documentation uses only the four reviewed images in this directory. Real remote screens are not included as promotional screenshots.
