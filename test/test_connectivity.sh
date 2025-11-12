#!/bin/bash
# Test script for fake internet connectivity feature
# This script tests all connectivity check endpoints

echo "========================================"
echo "Comitup Fake Internet Connectivity Test"
echo "========================================"
echo ""

# Configuration
AP_IP="${1:-10.41.0.1}"
echo "Testing against AP IP: $AP_IP"
echo ""

# Test counter
TOTAL=0
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local url="$1"
    local expected_code="$2"
    local description="$3"
    local expected_content="$4"
    
    TOTAL=$((TOTAL + 1))
    echo -n "[$TOTAL] Testing $description... "
    
    response=$(curl -s -o /tmp/curl_body.txt -w "%{http_code}" "http://${AP_IP}${url}" 2>/dev/null)
    
    if [ "$response" == "$expected_code" ]; then
        if [ -n "$expected_content" ]; then
            if grep -q "$expected_content" /tmp/curl_body.txt 2>/dev/null; then
                echo "✓ PASSED (HTTP $response with content)"
                PASSED=$((PASSED + 1))
            else
                echo "✗ FAILED (HTTP $response but wrong content)"
                FAILED=$((FAILED + 1))
            fi
        else
            echo "✓ PASSED (HTTP $response)"
            PASSED=$((PASSED + 1))
        fi
    else
        echo "✗ FAILED (Expected HTTP $expected_code, got $response)"
        FAILED=$((FAILED + 1))
    fi
}

echo "Testing Android connectivity checks:"
echo "------------------------------------"
test_endpoint "/generate_204" "204" "Android /generate_204"
test_endpoint "/gen_204" "204" "Android /gen_204"
test_endpoint "/generate204" "204" "Samsung /generate204"

echo ""
echo "Testing iOS connectivity checks:"
echo "--------------------------------"
test_endpoint "/library/test/success.html" "200" "iOS success.html" "Success"
test_endpoint "/hotspot-detect.html" "200" "iOS hotspot-detect.html" "Success"
test_endpoint "/success.txt" "200" "Apple success.txt" "Success"

echo ""
echo "Testing Windows connectivity checks:"
echo "-------------------------------------"
test_endpoint "/ncsi.txt" "200" "Windows NCSI" "Microsoft NCSI"
test_endpoint "/connecttest.txt" "200" "Windows Connect Test" "Microsoft Connect Test"

echo ""
echo "Testing other connectivity checks:"
echo "-----------------------------------"
test_endpoint "/canonical.html" "200" "Firefox canonical.html" "success.txt"
test_endpoint "/check_network_status.txt" "200" "Generic network status" "OK"

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo "Total tests: $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed. Check comitup-web service status."
    exit 1
fi

# Cleanup
rm -f /tmp/curl_body.txt
