# 🎮 Bazzite Home Assistant Integration

**Integrate your Bazzite gaming PC to Home Assistant!**

Monitor and control your Bazzite PC directly from Home Assistant.

---

## ⭐ Features

✅ Detects if a game or app is currently running on Bazzite  
✅ Reports which game or app is active (Activity sensor)  
✅ Monitors CPU temperature  
✅ Online and In Game sensors  
✅ Shows Unavailable when the PC is asleep or powered off  
✅ WebSocket-based for instant state updates  
✅ Supports Home Assistant commands to:

- Shutdown
- Suspend

---

## 🚀 How It Works

This custom integration communicates with a **companion server** running on your Bazzite PC (built with FastAPI).

It connects via WebSocket to get **real-time updates** and can send **commands** for power management.

✅ *Low overhead, instant updates.*

---

## 📦 Requirements

- Home Assistant (2023.5 or newer recommended)
- [HACS](https://hacs.xyz/)
- Bazzite PC running the [Bazzite Integration Server](https://github.com/ddilapojr/bazzite-server)

---

## 🛠️ Installation

### ✅ Option 1: HACS (recommended)

1. In Home Assistant, open **HACS**.
2. Click the ⋮ menu (top right) → **Custom repositories** (or **Add from a GitHub link**).
3. Paste `https://github.com/ddilapojr/bazzite-ha-integration`, set the type to **Integration**, and click **Add**.
4. Find **Bazzite Integration** in HACS and click **Download**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration**, search for **Bazzite**, and enter your PC's IP address, port (`5000`) and a device name.

---

### ✅ Option 2: Manual Install

1. Copy the `custom_components/bazzite` folder from this repository into your Home Assistant `config/custom_components/` folder (the folder name must be lowercase).
2. Restart Home Assistant.
3. Add the **Bazzite** integration as in step 6 above.

---

## 🙏 Credits

- [Tijgerd](https://github.com/Tijgerd) created the original [Bazzite Home Assistant Integration](https://github.com/Tijgerd/BazziteHaIntegration) and server.
- [bendamschke](https://github.com/bendamschke) contributed the added sensors.
