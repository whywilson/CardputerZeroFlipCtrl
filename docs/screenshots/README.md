# Public screenshots

The current store listing and README use these four 320×170 screenshots captured from CardputerZero's framebuffer:

1. `connection-auto.png`: the local Auto connection page.
2. `connection-active.png`: a connected remote view.
3. `key-guide.png`: the H-key pixel-art guide.
4. `remote-system-info.png`: remote system information, captured while connected.

The connected views were captured at the developer's request without injecting keys or adding a help overlay during capture. Their interface pixels are unretouched. The Auto page and key guide were originally captured with an isolated configuration and FIFO keyboard. The old invalid-IP example is not part of the current screenshot set.

`tools/capture_public_screenshots.py` reproduces the original isolated test screens, rather than the current connected views. It uses a temporary `XDG_CONFIG_HOME`, disables Ethernet probing, and does not modify the user's saved WiFi address. Run that test capture only after stopping other framebuffer apps, then restore APPLaunch afterwards.

Connected remote screens may display device identifiers or network settings. Review any new capture before publishing it. Historical raw captures and logs under `dist/` are excluded from the source repository.

The developer-provided real-hardware demonstration for store review is available at https://x.com/mtoolstec/status/2120067252976586806.
