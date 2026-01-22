import hashlib
import json
import datetime
import os
import glob
import uuid

def generate_uuid():
    return str(uuid.uuid4())


REPORT_PATH = '../blackglass-variance-core/VARIANCE_REPORT.md'
CERTIFICATE_PATH = '../coherence-sre/compliance_certificate.json'

def main():
    print(">>")
    print(">> INITIATING COMPLIANCE CYCLE...")
    try:
        with open(REPORT_PATH, 'r') as f:
            report_content = f.read()
    except FileNotFoundError:
        print(f"ERROR: Report file not found at {REPORT_PATH}")
        return
    except Exception as e:
        print(f"ERROR: Could not read the report file: {e}")
        return

    sha256_hash = hashlib.sha256(report_content.encode('utf-8')).hexdigest()

    if "**Status:** HYPER-COHERENT" in report_content:
        compliance_status = "PASSED"
    else:
        compliance_status = "FAILED"

    certificate = {
        "id": generate_uuid(),
        "timestamp": datetime.datetime.utcnow().isoformat() + 'Z',
        "target_artifact": "VARIANCE_REPORT.md",
        "sha256_signature": sha256_hash,
        "compliance_status": compliance_status,
        "issuer": "COHERENCE-SRE | CAGE: 17TJ5"
    }

    try:
        with open(CERTIFICATE_PATH, 'w') as f:
            json.dump(certificate, f, indent=4)
    except Exception as e:
        print(f"ERROR: Could not write the certificate file: {e}")
        return

    hash_fragment = sha256_hash[:8]  # Display the first 8 characters of the hash
    print(f">> CERTIFICATE MINTED: {hash_fragment} >> STATUS: {compliance_status}")

if __name__ == "__main__":
    main()