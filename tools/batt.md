# batt - MacBook Battery protection

> https://github.com/charlie0129/batt

Control and limit battery charging on Apple Silicon MacBooks.

Quick setup guide for installing and using batt via Homebrew on macOS. First, confirm your device is Apple Silicon (M1/M2, etc.).

## Installation

```bash
brew install batt
```

After installation, start the daemon service with administrator privileges.

```bash
sudo brew services start batt
```

## Common Commands

| Operation | Command | Description |
| --- | --- | --- |
| View current status | `batt status` | Display battery and charge limit information. |
| Set maximum charge percentage (e.g., 80%) | `sudo batt limit 80` | Set the maximum charging threshold to 80%. |
| Restore system default (allow charging to 100%) | `sudo batt disable` | Remove the limit setting and restore normal charging behavior. |
| Stop service and uninstall (if installed via Homebrew) | `sudo brew services stop batt` && `brew uninstall batt` | Completely remove the tool. |

## Important Notes

- Only supports Apple Silicon Mac.
- Service startup and configuration must be executed with sudo/administrator privileges. Without proper permissions, you may not be able to access the battery interface.
- macOS's built-in "Optimized Battery Charging" feature is not the same as strictly "limiting charging to 80%".
- If the tool stops working after a macOS update, check the GitHub Issues to see if the compatibility problem has been reported.
