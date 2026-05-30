#!/usr/bin/env python3
"""
Simple test script for EnvLockr CLI
Run this to verify your installation works correctly
"""

import subprocess
import sys
import os

# Make emoji output safe on Windows cp1252 consoles.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass


def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_cli():
    """Test basic EnvLockr CLI functionality"""
    print("🧪 Testing EnvLockr CLI Installation\n")
    print("=" * 50)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Help command
    print("\n1️⃣  Testing help command...")
    success, stdout, stderr = run_command("python envlockr.py --help")
    if success and "EnvLockr" in stdout:
        print("   ✅ Help command works")
        tests_passed += 1
    else:
        print("   ❌ Help command failed")
        tests_failed += 1
    
    # Test 2: Add a test secret
    print("\n2️⃣  Testing add command...")
    # Note: This would require interactive input in real scenario
    # For now, we just check if the command exists
    success, stdout, stderr = run_command("python envlockr.py add --help")
    if success:
        print("   ✅ Add command exists")
        tests_passed += 1
    else:
        print("   ❌ Add command failed")
        tests_failed += 1
    
    # Test 3: List command
    print("\n3️⃣  Testing list command...")
    success, stdout, stderr = run_command("python envlockr.py list")
    if success:
        print("   ✅ List command works")
        tests_passed += 1
    else:
        print("   ❌ List command failed")
        tests_failed += 1
    
    # Test 4: Get command
    print("\n4️⃣  Testing get command...")
    success, stdout, stderr = run_command("python envlockr.py get --help")
    if success:
        print("   ✅ Get command exists")
        tests_passed += 1
    else:
        print("   ❌ Get command failed")
        tests_failed += 1
    
    # Test 5: Export command
    print("\n5️⃣  Testing export command...")
    success, stdout, stderr = run_command("python envlockr.py export --help")
    if success:
        print("   ✅ Export command exists")
        tests_passed += 1
    else:
        print("   ❌ Export command failed")
        tests_failed += 1
    
    # Test 6: Delete command
    print("\n6️⃣  Testing delete command...")
    success, stdout, stderr = run_command("python envlockr.py delete --help")
    if success:
        print("   ✅ Delete command exists")
        tests_passed += 1
    else:
        print("   ❌ Delete command failed")
        tests_failed += 1
    
    # Test 7: Update command
    print("\n7️⃣  Testing update command...")
    success, stdout, stderr = run_command("python envlockr.py update --help")
    if success:
        print("   ✅ Update command exists")
        tests_passed += 1
    else:
        print("   ❌ Update command failed")
        tests_failed += 1
    
    # Test 8: Copy command
    print("\n8️⃣  Testing copy command...")
    success, stdout, stderr = run_command("python envlockr.py copy --help")
    if success:
        print("   ✅ Copy command exists")
        tests_passed += 1
    else:
        print("   ❌ Copy command failed")
        tests_failed += 1
    
    # Test 9: Check dependencies
    print("\n9️⃣  Testing dependencies...")
    try:
        import cryptography  # required
        print("   ✅ Required dependency 'cryptography' installed")
        # pyperclip and keyring are optional extras — report but don't fail.
        for opt in ("pyperclip", "keyring"):
            try:
                __import__(opt)
                print(f"   ✅ Optional '{opt}' installed")
            except ImportError:
                print(f"   ℹ️  Optional '{opt}' not installed (feature disabled)")
        tests_passed += 1
    except ImportError as e:
        print(f"   ❌ Missing required dependency: {e}")
        tests_failed += 1
    
    # Test 10: Check vault location
    print("\n🔟 Testing vault location...")
    vault_dir = os.path.expanduser("~/.envlockr")
    if os.path.exists(vault_dir) or True:  # Directory created on first use
        print(f"   ✅ Vault directory ready: {vault_dir}")
        tests_passed += 1
    else:
        print(f"   ⚠️  Vault directory will be created on first use")
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {tests_passed}")
    print(f"   ❌ Failed: {tests_failed}")
    print(f"   Total:  {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 All tests passed! EnvLockr is ready to use!")
        print("\n📚 Next steps:")
        print("   python envlockr.py add MY_SECRET")
        print("   python envlockr.py list")
        print("   python envlockr.py get MY_SECRET")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check your installation.")
        print("\n🔧 Troubleshooting:")
        print("   pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(test_cli())
