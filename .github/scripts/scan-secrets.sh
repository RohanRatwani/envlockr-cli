#!/bin/bash

# EnvLockr Secret Scanner
# Scans code for exposed secrets and API keys
# https://github.com/RohanRatwani/envlockr-cli

set -e

echo "🔐 EnvLockr Secret Scanner v1.0"
echo "================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Secret patterns to detect
declare -a PATTERNS=(
  "AKIA[0-9A-Z]{16}"                          # AWS Access Key
  "sk_live_[0-9a-zA-Z]{24,}"                  # Stripe Live Key
  "sk_test_[0-9a-zA-Z]{24,}"                  # Stripe Test Key
  "rk_live_[0-9a-zA-Z]{24,}"                  # Stripe Restricted Key
  "sq0csp-[0-9A-Za-z\\-_]{43}"                # Square Access Token
  "sq0atp-[0-9A-Za-z\\-_]{22}"                # Square OAuth Secret
  "ghp_[0-9a-zA-Z]{36}"                       # GitHub Personal Access Token
  "gho_[0-9a-zA-Z]{36}"                       # GitHub OAuth Token
  "ghs_[0-9a-zA-Z]{36}"                       # GitHub Server Token
  "ghr_[0-9a-zA-Z]{36}"                       # GitHub Refresh Token
  "github_pat_[0-9a-zA-Z_]{82}"               # GitHub Fine-grained PAT
  "AIza[0-9A-Za-z\\-_]{35}"                   # Google API Key
  "ya29\\.[0-9A-Za-z\\-_]+"                   # Google OAuth Token
  "[0-9]+-[0-9A-Za-z_]{32}\\.apps\\.googleusercontent\\.com" # Google OAuth Client
  "sk-[a-zA-Z0-9]{48}"                        # OpenAI API Key
  "sk-proj-[a-zA-Z0-9]{48,}"                  # OpenAI Project API Key
  "xoxb-[0-9]{11,13}-[0-9]{11,13}-[0-9a-zA-Z]{24}" # Slack Bot Token
  "xoxp-[0-9]{11,13}-[0-9]{11,13}-[0-9a-zA-Z]{24}" # Slack User Token
  "xapp-[0-9]{1}-[A-Z0-9]+-[0-9]{10,13}-[a-z0-9]{64}" # Slack App Token
  "xoxe\\.xoxp-[0-9]{1}-[A-Za-z0-9-]+"        # Slack XOXE Token
  "dop_v1_[a-f0-9]{64}"                       # DigitalOcean Token
  "mongodb\\+srv://[^:]+:[^@]+@"              # MongoDB Connection String
  "postgres://[^:]+:[^@]+@"                   # PostgreSQL Connection String
  "mysql://[^:]+:[^@]+@"                      # MySQL Connection String
  "redis://[^:]+:[^@]+@"                      # Redis Connection String
  "amqp://[^:]+:[^@]+@"                       # RabbitMQ Connection String
  "Bearer [a-zA-Z0-9\\-._~+/]{20,}"           # Bearer Token
  "-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----" # Private Keys
  "token[\"']?\\s*[:=]\\s*[\"'][a-zA-Z0-9\\-._~+/]{20,}" # Generic token
  "api[_-]?key[\"']?\\s*[:=]\\s*[\"'][a-zA-Z0-9\\-._~+/]{20,}" # Generic API key
  "password[\"']?\\s*[:=]\\s*[\"'][^\"']{8,}" # Password assignment
  "secret[\"']?\\s*[:=]\\s*[\"'][a-zA-Z0-9\\-._~+/]{20,}" # Secret assignment
  "access[_-]?token[\"']?\\s*[:=]\\s*[\"'][a-zA-Z0-9\\-._~+/]{20,}" # Access token
  "client[_-]?secret[\"']?\\s*[\"'][a-zA-Z0-9\\-._~+/]{20,}" # Client secret
)

# Files and patterns to ignore
IGNORE_PATTERNS=(
  ".git/"
  "node_modules/"
  "vendor/"
  "dist/"
  "build/"
  ".lock"
  "package-lock.json"
  "yarn.lock"
  "pnpm-lock.yaml"
  ".min.js"
  ".min.css"
  ".jpg"
  ".png"
  ".gif"
  ".svg"
  ".ico"
  ".woff"
  ".ttf"
)

FOUND_SECRETS=false
FINDINGS_FILE="secret_scan_results.txt"
> "$FINDINGS_FILE"

# Function to check if file should be ignored
should_ignore() {
  local file=$1
  for pattern in "${IGNORE_PATTERNS[@]}"; do
    if [[ "$file" == *"$pattern"* ]]; then
      return 0
    fi
  done
  return 1
}

# Get list of files to scan
if [ -d ".git" ]; then
  # In a git repo, scan changed files
  if [ -n "$GITHUB_BASE_REF" ]; then
    # Pull request
    FILES=$(git diff --name-only "origin/$GITHUB_BASE_REF"...HEAD 2>/dev/null || git diff --name-only HEAD~1 HEAD)
  else
    # Push to branch
    FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || git ls-files)
  fi
else
  # Not a git repo, scan all files
  FILES=$(find . -type f 2>/dev/null)
fi

echo "🔍 Scanning files for exposed secrets..."
echo ""

FILE_COUNT=0
SCANNED_COUNT=0

# Scan each file
for FILE in $FILES; do
  if [ -f "$FILE" ]; then
    FILE_COUNT=$((FILE_COUNT + 1))
    
    # Skip ignored files
    if should_ignore "$FILE"; then
      continue
    fi
    
    SCANNED_COUNT=$((SCANNED_COUNT + 1))
    
    for PATTERN in "${PATTERNS[@]}"; do
      MATCHES=$(grep -inE "$PATTERN" "$FILE" 2>/dev/null || true)
      if [ -n "$MATCHES" ]; then
        FOUND_SECRETS=true
        echo -e "${RED}❌ Potential secret found in: $FILE${NC}" | tee -a "$FINDINGS_FILE"
        echo "$MATCHES" | while IFS= read -r line; do
          # Redact the actual secret value
          REDACTED=$(echo "$line" | sed 's/\([:=]\s*["\x27]\)[^"\x27]*\(["\x27]\)/\1***REDACTED***\2/g')
          echo -e "   ${YELLOW}$REDACTED${NC}" | tee -a "$FINDINGS_FILE"
        done
        echo "" | tee -a "$FINDINGS_FILE"
      fi
    done
  fi
done

echo ""
echo "📊 Scan Summary:"
echo "   Files checked: $FILE_COUNT"
echo "   Files scanned: $SCANNED_COUNT"
echo ""

if [ "$FOUND_SECRETS" = true ]; then
  echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${RED}🚨 SECRETS DETECTED IN YOUR CODE!${NC}"
  echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo "📚 How to fix this:"
  echo ""
  echo "1️⃣  Remove the secrets from your code"
  echo "2️⃣  Store them securely with EnvLockr:"
  echo "    ${GREEN}python envlockr.py add SECRET_NAME${NC}"
  echo ""
  echo "3️⃣  Use environment variables in your code:"
  echo "    ${GREEN}const apiKey = process.env.API_KEY;${NC}"
  echo ""
  echo "4️⃣  Add sensitive files to .gitignore:"
  echo "    ${GREEN}echo '.env' >> .gitignore${NC}"
  echo ""
  echo "🔗 Get EnvLockr: https://github.com/RohanRatwani/envlockr-cli"
  echo ""
  cat "$FINDINGS_FILE"
  exit 1
else
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${GREEN}✅ No secrets detected! Good job! 🎉${NC}"
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo "Keep your secrets safe with EnvLockr:"
  echo "🔗 https://github.com/RohanRatwani/envlockr-cli"
  exit 0
fi
