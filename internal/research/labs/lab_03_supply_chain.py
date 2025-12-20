"""
Lab 3: Supply Chain Security & Dependency Auditing (SY0-701: 3.2)
Scenario: A dependency introduces a known vulnerability.
Objective: Simulate a CI/CD check that scans `requirements.txt` for prohibited packages.
"""

BANNED_PACKAGES = {
    "telnetlib": "Unencrypted communication (MITM Risk)",
    "pickle-mixin": "Insecure deserialization risk",
    "old-crypto": "Deprecated algorithms"
}

def audit_dependencies(requirements: str):
    findings = []
    for line in requirements.splitlines():
        pkg = line.split("==")[0].strip()
        if pkg in BANNED_PACKAGES:
            findings.append(f"VULN: {pkg} -> {BANNED_PACKAGES[pkg]}")
    return findings

def test_supply_chain_audit():
    # Simulated Requirements File
    unsafe_reqs = """
    requests==2.28.0
    telnetlib==0.1
    flask==2.0.1
    """
    
    print("Auditing dependencies...")
    report = audit_dependencies(unsafe_reqs)
    
    if report:
        print("Audit Findings:")
        for r in report: print(f" - {r}")
        
    assert len(report) > 0, "Audit failed to detect banned dependency"
    assert "telnetlib" in report[0], "Correct dependency not identified"

if __name__ == "__main__":
    print("Running Security+ Lab 3: Supply Chain Audit...")
    try:
        test_supply_chain_audit()
        print("[PASS] Supply chain audit verified.")
    except AssertionError as e:
        print(f"[FAIL] {e}")
