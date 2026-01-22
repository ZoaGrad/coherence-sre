import hashlib
import json
import datetime
import os
import uuid

# --- CONFIGURATION ---
TARGET_ARTIFACT = "../blackglass-variance-core/VARIANCE_REPORT.md"
CERTIFICATE_FILE = "compliance_certificate.json"
REQUIRED_STRING = "**Status:** HYPER-COHERENT"

def generate_certificate():
    print(f">> AUDITING ARTIFACT: {TARGET_ARTIFACT}")
    
    if not os.path.exists(TARGET_ARTIFACT):
        print("!! ARTIFACT NOT FOUND.")
        return

    # 1. READ ARTIFACT
    with open(TARGET_ARTIFACT, "r", encoding="utf-8") as f:
        content = f.read()

    # 2. CALCULATE SHA-256
    sha_signature = hashlib.sha256(content.encode()).hexdigest()

    # 3. VERIFY CONTENT (THE TRUTH)
    if REQUIRED_STRING in content:
        status = "PASSED"
        print(f">> VERIFIED: {REQUIRED_STRING} FOUND.")
    else:
        status = "FAILED"
        print(f"!! FAILED: {REQUIRED_STRING} NOT FOUND.")

    # 4. MINT CERTIFICATE (STANDARD 1.1)
    certificate = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "target_artifact": "VARIANCE_REPORT.md",
        "sha256_signature": sha_signature,
        "compliance_status": status,  # AMENDED KEY
        "issuer": "COHERENCE-SRE | CAGE: 17TJ5",
        "standard": "1.1"
    }

    with open(CERTIFICATE_FILE, "w", encoding="utf-8") as f:
        json.dump(certificate, f, indent=2)

    print(f">> CERTIFICATE MINTED: {CERTIFICATE_FILE} [{status}]")

if __name__ == "__main__":
    generate_certificate()