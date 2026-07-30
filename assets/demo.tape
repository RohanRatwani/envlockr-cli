# EnvLockr demo — render a GIF with https://github.com/charmbracelet/vhs
#   vhs demo.tape   →   produces demo.gif
#
# Uses a throwaway vault dir so your real secrets are untouched.

Output demo.gif

Set FontSize 18
Set Width 1100
Set Height 600
Set Padding 20
Set Theme "Dracula"

Hide
Type "export ENVLOCKR_HOME=$(mktemp -d)" Enter
Type "clear" Enter
Show

Type "# 1. Store a secret — encrypted, local, no .env on disk" Sleep 800ms Enter
Type "envlockr add OPENAI_API_KEY --value sk-demo-not-a-real-key --force" Sleep 600ms Enter
Sleep 1s

Type "envlockr list" Sleep 500ms Enter
Sleep 1s

Type "# 2. Run your app with secrets injected — nothing written to disk" Sleep 800ms Enter
Type `envlockr run -- node -e "console.log('app sees:', process.env.OPENAI_API_KEY)"` Sleep 600ms Enter
Sleep 1500ms

Type "# 3. Check which stored keys are still live with their provider" Sleep 800ms Enter
Type "envlockr verify" Sleep 600ms Enter
Sleep 2s

Type "# No cloud. No subscription. Key lives in your OS keychain." Sleep 1s Enter
Sleep 1500ms
