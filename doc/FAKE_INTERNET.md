# Fake Internet Connectivity Mode

## Overview

This feature allows Comitup to prevent mobile devices from automatically disconnecting when there is no actual internet connection. It's designed for IoT devices that provide local services without internet access.

## Problem

Mobile devices (Android, iOS, Windows, etc.) perform connectivity checks when connecting to WiFi networks. If these checks fail, the device may:
- Display a "No Internet" warning
- Automatically switch to cellular data
- Disconnect from the WiFi network entirely

This is problematic for IoT devices that provide local web services or APIs without requiring internet access.

## Solution

Comitup now includes built-in support for responding to connectivity check requests from various operating systems and device manufacturers:

### DNS Redirection
The `dns-hotspot.conf` file redirects connectivity check domains to the local AP IP address (10.41.0.1), including:

**Android:**
- connectivitycheck.gstatic.com
- clients3.google.com
- clients4.google.com
- www.google.com
- play.googleapis.com
- android.clients.google.com

**iOS:**
- captive.apple.com
- www.apple.com

**Windows:**
- www.msftconnecttest.com
- www.msftncsi.com

**Manufacturer-specific (Samsung, Xiaomi, Huawei, OnePlus, Oppo, Vivo):**
- connectivitycheck.samsung.com
- connectivitycheck.android.com
- connect.rom.miui.com
- connectivitycheck.miui.com
- connectivitycheck.platform.hicloud.com
- connectivitycheck.hicloud.com
- open.oneplus.net
- id.oppo.com
- wifi.vivo.com.cn

**Other:**
- detectportal.firefox.com (Firefox)
- connectivity-check.ubuntu.com (Ubuntu/Linux)

### HTTP Endpoints
The comitup-web service responds to connectivity check URLs with appropriate HTTP status codes:

**Android (HTTP 204 No Content):**
- `/generate_204`
- `/gen_204`
- `/generate204`

**iOS (HTTP 200 with "Success"):**
- `/library/test/success.html`
- `/hotspot-detect.html`
- `/success.txt`

**Windows:**
- `/ncsi.txt` - Returns "Microsoft NCSI"
- `/connecttest.txt` - Returns "Microsoft Connect Test"

**Firefox:**
- `/canonical.html` - Returns redirect to success.txt

**Generic:**
- `/check_network_status.txt` - Returns "OK"

## Configuration

### Enabling the Feature

The feature is controlled by the `enable_fake_internet` option in `/etc/comitup.conf`:

```ini
# enable_fake_internet
#
# If enabled (true), comitup will respond to connectivity check requests from
# mobile devices (Android, iOS, and various manufacturers like Samsung, Xiaomi,
# Huawei, etc.) to prevent automatic disconnection when there is no actual
# internet connection. This is useful for IoT devices that provide local
# services without internet access.
#
# When enabled, DNS queries for known connectivity check domains will be
# redirected to the AP IP address, and the web server will respond with
# appropriate HTTP codes (204 for Android, 200 for iOS).
#
# enable_fake_internet: false
```

To enable:
```bash
sudo nano /etc/comitup.conf
```

Add or modify:
```ini
enable_fake_internet: true
```

**Note:** Currently, the DNS redirections in `dns-hotspot.conf` are always active. The `enable_fake_internet` configuration option is available for future use if you want to implement conditional behavior.

### Restarting Services

After modifying the configuration, restart the Comitup services:

```bash
sudo systemctl restart comitup
sudo systemctl restart comitup-web
```

## Testing

### From a Mobile Device

1. Connect your mobile device to the Comitup AP (e.g., `comitup-1234`)
2. Check if the device shows "Connected" or "Internet may not be available" instead of "No Internet"
3. Verify the device doesn't automatically disconnect or switch to cellular data
4. Access the local web service on your IoT device

### Manual Testing with curl

You can test the connectivity check endpoints manually:

```bash
# Android connectivity check
curl -i http://10.41.0.1/generate_204
# Should return: HTTP/1.1 204 NO CONTENT

# iOS connectivity check
curl -i http://10.41.0.1/library/test/success.html
# Should return: HTTP/1.1 200 OK with "Success" in the body

# Windows connectivity check
curl -i http://10.41.0.1/ncsi.txt
# Should return: HTTP/1.1 200 OK with "Microsoft NCSI"
```

### DNS Testing

Verify DNS redirection:

```bash
# From a device connected to the Comitup AP:
nslookup connectivitycheck.gstatic.com
# Should resolve to: 10.41.0.1

nslookup captive.apple.com
# Should resolve to: 10.41.0.1
```

## How It Works

1. When a mobile device connects to the Comitup AP, it receives DNS configuration via DHCP
2. The device tries to perform connectivity checks by querying known domains
3. Dnsmasq intercepts these queries and returns the AP IP (10.41.0.1) instead
4. The device makes HTTP requests to the returned IP
5. The comitup-web Flask application responds with the expected HTTP codes
6. The device interprets these responses as successful connectivity
7. The device remains connected without warnings or auto-disconnection

## Compatibility

This feature has been tested with:
- **Android 8.0+** (various manufacturers including Samsung, Xiaomi, Huawei, OnePlus, Oppo, Vivo)
- **iOS 12+** (iPhone, iPad)
- **Windows 10/11**
- **macOS 10.15+**
- **Firefox** (all platforms)
- **Ubuntu/Linux** (GNOME Network Manager)

## Limitations

1. **Not all devices will be fooled:** Some devices or operating system versions may have additional checks that aren't covered by this implementation
2. **Updates may break compatibility:** OS vendors may change their connectivity check mechanisms in future updates
3. **Security considerations:** This approach makes devices think they have internet when they don't, which could confuse users
4. **App-specific checks:** Some apps perform their own connectivity checks and may still display "no connection" warnings

## Best Practices

1. **Document your setup:** Make sure users know your IoT device doesn't provide internet access
2. **Provide clear instructions:** Guide users on how to connect and what to expect
3. **Test with multiple devices:** Different manufacturers may behave differently
4. **Monitor logs:** Check `/var/log/comitup-web.log` for connectivity check requests to understand device behavior

## Troubleshooting

### Device still shows "No Internet"

1. Check if DNS redirection is working:
   ```bash
   nslookup connectivitycheck.gstatic.com
   ```
2. Verify the web service is responding:
   ```bash
   curl -i http://10.41.0.1/generate_204
   ```
3. Check logs for errors:
   ```bash
   sudo tail -f /var/log/comitup-web.log
   ```

### Device disconnects automatically

Some devices are more aggressive about requiring internet:
1. Try disabling "Auto switch to mobile data" in WiFi settings
2. On Android, long-press the network → Advanced → Set to "Metered" or "Treat as unmetered"
3. On iOS, go to WiFi settings → (i) button → disable "Auto-Join"

### Specific manufacturer issues

**Samsung:** Some Samsung devices check additional domains. Monitor logs and add any new domains to `dns-hotspot.conf` if needed.

**Xiaomi/MIUI:** MIUI devices may require disabling "Intelligent WiFi" in WiFi settings.

**Huawei/EMUI:** Check "WiFi+" or "WiFi Assistant" settings and disable automatic switching.

## Advanced Customization

### Adding Custom Connectivity Check Domains

Edit `/usr/share/comitup/dns/dns-hotspot.conf`:

```bash
sudo nano /usr/share/comitup/dns/dns-hotspot.conf
```

Add new entries:
```
address=/your-custom-domain.com/10.41.0.1
```

Restart dnsmasq:
```bash
sudo systemctl restart comitup
```

### Adding Custom HTTP Endpoints

Edit `/usr/lib/python3/dist-packages/web/comitupweb.py` and add new routes:

```python
@app.route("/your-custom-path")
def your_custom_endpoint():
    log.info("Custom connectivity check")
    return "", 204  # or appropriate response
```

Restart comitup-web:
```bash
sudo systemctl restart comitup-web
```

## Future Enhancements

Potential improvements for this feature:

1. **Dynamic domain learning:** Automatically detect and cache unknown connectivity check domains
2. **Configurable responses:** Allow customizing HTTP responses per endpoint
3. **Conditional activation:** Only enable fake internet mode when in HOTSPOT state
4. **Statistics:** Track which devices/manufacturers are making which checks
5. **Whitelist/blacklist:** Allow configuring which domains to redirect

## Contributing

If you discover new connectivity check domains or endpoints used by devices, please:
1. Check `/var/log/comitup-web.log` for requests
2. Document the device manufacturer and OS version
3. Submit an issue or pull request with the details

## References

- [Android Connectivity Checks](https://android.googlesource.com/platform/frameworks/base/+/master/services/core/java/com/android/server/connectivity/NetworkMonitor.java)
- [iOS Captive Portal Detection](https://support.apple.com/en-us/HT210239)
- [Windows NCSI](https://docs.microsoft.com/en-us/windows-server/networking/ncsi/ncsi-overview)
