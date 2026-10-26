# CampusHub Mobile Network Connectivity & Troubleshooting Guide

## 1. Overview & Context
This guide explains how the Flutter mobile application locates and connects to the Django backend server running on your computer (`0.0.0.0:8000`), why network disconnections occur when testing on a physical phone, and how the automatic fallback mechanism and ADB reverse tethering resolve connection failures.

---

## 2. Root Cause Analysis: Why the Mobile Phone Could Not Reach Django
When you run `python manage.py runserver 0.0.0.0:8000` on your PC, Django binds to all network interfaces on the computer. However, the mobile phone was failing to load data due to three specific issues:

1. **Dynamic IP Assignment (DHCP)**:
   - Your PC previously had IPv4 address `192.168.0.159`, which was hardcoded as the default in [api_config.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/config/api_config.dart#L11-L15).
   - Upon reconnecting to the Wi-Fi network, your Wi-Fi router assigned your computer a new IP: **`192.168.0.122`**.
   - Because `192.168.0.122` was not in the configuration, the mobile app was still sending requests to the dead IP address `192.168.0.159`, resulting in connection timeouts (`nc: Timeout`).
2. **Missing Localhost Loopback Fallback (`127.0.0.1`)**:
   - When a phone is connected via USB or wireless ADB, running `adb reverse tcp:8000 tcp:8000` routes `http://127.0.0.1:8000` on the phone directly into the PC's Django server, bypassing Wi-Fi routers entirely.
   - [api_config.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/config/api_config.dart#L18-L28) was missing `127.0.0.1` in its fallback candidate list.
3. **Public Network Category & Campus Wi-Fi AP Isolation**:
   - The current Wi-Fi connection (`USTP Library_5G 2`) is categorized as **Public** in Windows, and university Wi-Fi routers frequently enforce **AP Client Isolation** (blocking communication between two connected devices).

---

## 3. Data Flow & Network Architecture

### How the Flutter App Discovers the Working Server
```
[Flutter Mobile App]
        │
        ▼
[ApiConfig.serverBaseUrls]
  ├── 1. Try hostIp (http://192.168.0.122:8000)
  ├── 2. Try fallback 1 (http://127.0.0.1:8000 via ADB reverse)
  ├── 3. Try fallback 2 (http://192.168.137.1:8000 via Mobile Hotspot)
  └── 4. Try other historical fallback IPs
        │
  (First server responding with HTTP 200)
        │
        ▼
[ApiConfig.recordWorkingBaseUrl(workingUrl)]
        │
        ▼
[Subsequent API calls, Facility images & Chat WebSockets use effectiveBaseUrl]
```

### Relevant Classes and Functions

#### 1. `ApiConfig` ([api_config.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/config/api_config.dart#L6-L85))
- **`hostIp`**: Primary IPv4 address used to construct the default `baseUrl`. Updated to default to `'192.168.0.122'`.
- **`fallbackHostIps`**: Ordered list of backup addresses tried sequentially or concurrently when the primary host is unreachable. Now includes `'127.0.0.1'` at index 0.
- **`serverBaseUrls`**: Computed getter that returns an ordered set of base URLs: `_activeBaseUrl` (if known), followed by `http://$hostIp:8000`, followed by all fallbacks.
- **`recordWorkingBaseUrl(String url)`**: Caches the confirmed live backend URL into `_activeBaseUrl` so subsequent requests do not have to rediscover the server.

#### 2. `FacilityService` ([facility_service.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/services/facility_service.dart#L19-L54))
- **`fetchFacilities()`**: Queries `_baseUrls` in order. Upon receiving a 200 response, it now invokes `ApiConfig.recordWorkingBaseUrl(baseUrl)` to ensure facility photos and subsequent interactions immediately know the working server.

---

## 4. Connection Options for Physical Phones

### Option 1: Direct Wi-Fi Connection (Recommended when on same home or personal router)
1. Verify PC IPv4:
   ```powershell
   ipconfig
   ```
   Look for the `Wireless LAN adapter Wi-Fi` -> `IPv4 Address` (e.g. `192.168.0.122`).
2. Verify Django is running with `0.0.0.0`:
   ```powershell
   python manage.py runserver 0.0.0.0:8000
   ```

### Option 2: ADB Reverse Tethering (Most Reliable — Bypasses Wi-Fi & Firewalls)
If your phone is plugged in via USB (or paired over wireless debugging):
1. Run in your PC terminal:
   ```powershell
   adb reverse tcp:8000 tcp:8000
   adb reverse tcp:8001 tcp:8001
   ```
2. The phone can now reach Django at `http://127.0.0.1:8000` directly through the ADB cable/link, completely unaffected by router isolation or firewall restrictions.

### Option 3: Windows Mobile Hotspot (Best on University/Public Wi-Fi)
If university Wi-Fi has AP client isolation enabled:
1. Turn on **Mobile Hotspot** in Windows Settings.
2. Connect your phone to your PC's hotspot Wi-Fi.
3. The PC hotspot gateway is always `192.168.137.1`, which is already built into `ApiConfig.fallbackHostIps`.

---

## 5. Verification Steps & Hands-on Practice

### Quick Test from PC:
Check if phone's port forward is responding:
```powershell
adb shell "nc -z -w 2 127.0.0.1 8000; echo EXIT_CODE=$?"
```
Expected output: `EXIT_CODE=True`.

### Hands-on Learning Exercise:
1. Open [api_config.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/config/api_config.dart#L11-L15).
2. Notice `defaultValue: '192.168.0.122'`.
3. Try launching the Flutter app with a specific IP override from the command line without editing files:
   ```powershell
   flutter run -d <device_id> --dart-define=CAMPUSHUB_HOST_IP=192.168.0.122
   ```
4. Confirm in the phone's login and dashboard screens that products and facilities load instantly.
