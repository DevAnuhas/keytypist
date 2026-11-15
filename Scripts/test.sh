#!/bin/bash
# Native tests in a freshly owned synthetic home. No model/network/capture opt-ins.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# SwiftPM names the artifact folder after the checkout directory, so match any.
if ! compgen -G "$ROOT/.build/artifacts/*/llama/llama.xcframework/Info.plist" >/dev/null; then
    echo "The pinned llama XCFramework is not cached. Approve dependency resolution before running native tests." >&2
    exit 1
fi
exec python3 - "$@" <<'PY'
from pathlib import Path
import hashlib
import os
import subprocess
import sys
import tempfile
import uuid

with tempfile.TemporaryDirectory(prefix="keytypist-gate0-tests-") as test_directory:
    test_home = Path(test_directory)
    test_home.chmod(0o700)
    token = str(uuid.uuid4())
    (test_home / ".keytypist-test-home").write_text(token)
    environment = os.environ.copy()
    for key in list(environment):
        if key.startswith("TABTYPE_"):
            del environment[key]
    environment["KEYTYPIST_TEST_HOME"] = str(test_home)
    environment["KEYTYPIST_TEST_TOKEN"] = token
    try:
        result = subprocess.run(["swift", "test", "--disable-automatic-resolution", *sys.argv[1:]], env=environment)
    finally:
        domain = "dev.anuhas.keytypist.test." + hashlib.sha256(str(test_home).encode()).hexdigest()
        subprocess.run(["/usr/bin/defaults", "delete", domain], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    raise SystemExit(result.returncode)
PY
