#!/bin/bash
#
# download_databento_ndx.sh — Download NDX Options Data from Databento FTP
#
# Usage: bash download_databento_ndx.sh
#

set -e

# Load API key from environment
source /etc/gamma.env 2>/dev/null || true

DATABENTO_API_KEY="${DATABENTO_API_KEY:-}"

if [ -z "$DATABENTO_API_KEY" ]; then
    echo "ERROR: DATABENTO_API_KEY is not set."
    echo "Set it before running this script:"
    echo "  export DATABENTO_API_KEY=\"your_key_here\""
    exit 1
fi

# FTP details (configure before use)
FTP_HOST="ftp.databento.com"
FTP_PATH="${DATABENTO_FTP_PATH:-/YOUR_DATASET_ID/YOUR_BATCH_JOB_ID}"

# Download directory
DOWNLOAD_DIR="/root/gamma/databento_data"
mkdir -p "$DOWNLOAD_DIR"

echo "========================================="
echo "Databento NDX Options Data Download"
echo "========================================="
echo
echo "FTP Host: $FTP_HOST"
echo "FTP Path: $FTP_PATH"
echo "Download Dir: $DOWNLOAD_DIR"
echo

# Method 1: Using wget with FTP (if available)
if command -v wget &> /dev/null; then
    echo "Using wget to download..."

    # Databento FTP typically uses the API key as both username and password.

    cd "$DOWNLOAD_DIR"

    # Try with API key as username and password
    wget --ftp-user="$DATABENTO_API_KEY" \
         --ftp-password="$DATABENTO_API_KEY" \
         -r -np -nH --cut-dirs=1 \
         "ftp://$FTP_HOST$FTP_PATH/" \
         || echo "First method failed, trying alternative..."

# Method 2: Using curl with FTP
elif command -v curl &> /dev/null; then
    echo "Using curl to download..."

    cd "$DOWNLOAD_DIR"

    # Try with API key as credentials
    curl -u "$DATABENTO_API_KEY:$DATABENTO_API_KEY" \
         "ftp://$FTP_HOST$FTP_PATH/" \
         -o "databento_ndx_$(date +%Y%m%d).tar.gz"

# Method 3: Using lftp (most robust for FTP)
elif command -v lftp &> /dev/null; then
    echo "Using lftp to download..."

    lftp -c "
    set ftp:ssl-allow no;
    open -u $DATABENTO_API_KEY,$DATABENTO_API_KEY ftp://$FTP_HOST;
    cd $FTP_PATH;
    mirror --verbose --parallel=4 . $DOWNLOAD_DIR;
    bye
    "

else
    echo "❌ No FTP client found (wget, curl, or lftp required)"
    echo "   Install with: sudo apt-get install wget"
    exit 1
fi

echo
echo "========================================="
echo "Download complete!"
echo "========================================="
echo
echo "Files downloaded to: $DOWNLOAD_DIR"
ls -lh "$DOWNLOAD_DIR"
echo
