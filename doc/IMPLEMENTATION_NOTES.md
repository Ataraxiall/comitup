# Implementation Notes: Fake Internet Connectivity Feature

## Summary

This implementation adds support for preventing mobile devices from automatically disconnecting when connecting to a Comitup hotspot without internet access.

## Files Modified

### 1. `comitup/config.py`
- Added `enable_fake_internet` configuration option with default value `false`
- This allows future conditional behavior if needed

### 2. `conf/comitup.conf`
- Added documentation for the `enable_fake_internet` configuration option
- Explains when and why to use this feature

### 3. `conf/dns-hotspot.conf`
- Added DNS address redirections for connectivity check domains
- Covers Android, iOS, Windows, and manufacturer-specific domains (Samsung, Xiaomi, Huawei, OnePlus, Oppo, Vivo)
- All connectivity check domains resolve to 10.41.0.1 (the AP IP)

### 4. `web/comitupweb.py`
- Added multiple HTTP endpoint routes to respond to connectivity checks:
  - `/generate_204` and `/gen_204` - Android checks (HTTP 204)
  - `/generate204` - Samsung variant (HTTP 204)
  - `/library/test/success.html` - iOS success page (HTTP 200 with HTML)
  - `/hotspot-detect.html` - iOS hotspot detection (HTTP 200 with HTML)
  - `/success.txt` - Apple text check (HTTP 200 with "Success")
  - `/ncsi.txt` - Windows Network Connectivity Status Indicator (HTTP 200)
  - `/connecttest.txt` - Windows connectivity test (HTTP 200)
  - `/canonical.html` - Firefox connectivity check (HTTP 200)
  - `/check_network_status.txt` - Generic check (HTTP 200)

### 5. `test/test_web.py`
- Added 10 new test cases covering all connectivity check endpoints
- All tests verify correct HTTP status codes and response content
- Tests pass independently and as part of the full test suite

### 6. `README.md`
- Added "Fake Internet Mode" section
- Links to detailed documentation

### 7. `doc/FAKE_INTERNET.md` (new file)
- Comprehensive documentation explaining:
  - The problem and solution
  - Configuration steps
  - Testing procedures
  - Compatibility information
  - Troubleshooting guide
  - Advanced customization options

## Design Decisions

### 1. Always-On DNS Redirection
The DNS redirections are always active in hotspot mode, regardless of the `enable_fake_internet` config option. This was chosen because:
- DNS redirects are harmless even if not needed
- Simplifies the implementation
- The config option is available for future use if conditional behavior is desired

### 2. Comprehensive Domain Coverage
We included a wide range of connectivity check domains because:
- Different OS versions use different domains
- Manufacturers customize Android with their own checks
- Better to over-cover than under-cover

### 3. Appropriate HTTP Responses
Each endpoint returns the specific response expected by the checking system:
- Android expects HTTP 204 (No Content) with no body
- iOS expects HTTP 200 with "Success" in the HTML
- Windows expects HTTP 200 with specific text content
- This ensures compatibility across all major platforms

### 4. Logging
All connectivity check endpoints log their access, which helps:
- Debugging connection issues
- Understanding which devices are checking
- Discovering new check URLs not yet covered

## Security Considerations

### 1. No New Attack Surface
The new endpoints only return static content and don't accept user input or perform any actions.

### 2. DNS Security
The DNS redirects only affect specific domains and don't interfere with normal DNS resolution.

### 3. No Credential Exposure
No authentication or sensitive data is involved in these endpoints.

### 4. CodeQL Analysis
Passed CodeQL security scanning with 0 alerts.

## Testing

### Unit Tests
- 28 total tests for web module (10 new, 18 existing)
- All tests pass
- Code coverage for new endpoints is 100%

### Linting
- Passes flake8 with no warnings
- Follows existing code style conventions

### Manual Testing Recommendations
See `doc/FAKE_INTERNET.md` for detailed manual testing procedures.

## Performance Impact

### Minimal Impact
- DNS redirects are handled by dnsmasq (same as existing portal behavior)
- HTTP endpoints are simple string returns (no database or complex logic)
- No impact on existing functionality when devices aren't checking connectivity

### Scalability
- Can handle multiple concurrent devices checking connectivity
- Flask's threaded mode already enabled in comitup-web

## Backward Compatibility

### Fully Compatible
- No breaking changes to existing functionality
- New endpoints don't interfere with existing routes
- DNS redirects only apply to specific connectivity check domains
- Works with existing Comitup installations without changes

### Migration
- No migration steps required
- Feature is automatically available after update
- Optional configuration to document usage

## Future Enhancements

Potential improvements that could be added:

1. **Conditional Activation**: Make DNS redirects conditional on `enable_fake_internet` setting
2. **Dynamic Domain Learning**: Automatically detect and cache new connectivity check domains
3. **Statistics Dashboard**: Track which devices/manufacturers make which checks
4. **Custom Responses**: Allow configuring HTTP responses per endpoint
5. **State-Based Behavior**: Only enable in HOTSPOT mode, disable when connected to upstream WiFi

## Known Limitations

1. **Not Foolproof**: Some devices may have additional checks not covered
2. **OS Updates**: Vendors may change connectivity check mechanisms
3. **App-Specific**: Individual apps may perform their own checks
4. **User Confusion**: Users might not understand why device shows "internet" when there isn't any

## Maintenance

### Adding New Domains
1. Monitor `/var/log/comitup-web.log` for unknown connectivity check requests
2. Add domain to `conf/dns-hotspot.conf` with format: `address=/domain.com/10.41.0.1`
3. Restart comitup service
4. Update documentation

### Adding New Endpoints
1. Add route to `web/comitupweb.py` following existing pattern
2. Add test to `test/test_web.py`
3. Run tests to verify
4. Update documentation

## References

- [Android Connectivity Checks](https://android.googlesource.com/platform/frameworks/base/+/master/services/core/java/com/android/server/connectivity/NetworkMonitor.java)
- [iOS Captive Portal](https://support.apple.com/en-us/HT210239)
- [Windows NCSI](https://docs.microsoft.com/en-us/windows-server/networking/ncsi/ncsi-overview)
- [Comitup Documentation](https://davesteele.github.io/comitup/)
