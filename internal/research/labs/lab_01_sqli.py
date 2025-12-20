"""
Lab 1: Input Validation & SQL Injection Simulation (SY0-701: 2.3)
Scenario: A dashboard endpoint is vulnerable to SQL injection via un-sanitized input.
Objective: Demonstrate how strict typing and ORM usage (or parameterized queries) prevents this.
"""
import sqlite3
import pytest

# Vulnerable Function (Simulation)
def get_user_vulnerable(username: str):
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INT, name TEXT, role TEXT)")
    cursor.execute("INSERT INTO users VALUES (1, 'admin', 'superuser')")
    
    # BAD PRACTICE: String concatenation
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return cursor.execute(query).fetchall()

# Secure Function
def get_user_secure(username: str):
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INT, name TEXT, role TEXT)")
    cursor.execute("INSERT INTO users VALUES (1, 'admin', 'superuser')")
    
    # GOOD PRACTICE: Parameterized Query
    query = "SELECT * FROM users WHERE name = ?"
    return cursor.execute(query, (username,)).fetchall()

def test_sql_injection_simulation():
    # Attack String: Bypass authentication or dump data
    attack_payload = "admin' OR '1'='1"
    
    # Vulnerable Check
    result_vuln = get_user_vulnerable(attack_payload)
    # Expectation: Returns users because '1'='1' is true
    assert len(result_vuln) > 0, "Vulnerable function failed to demonstrate injection"
    
    # Secure Check
    result_secure = get_user_secure(attack_payload)
    # Expectation: Returns nothing because no user is named "admin' OR '1'='1"
    assert len(result_secure) == 0, "Secure function failed to block prohibition"

if __name__ == "__main__":
    print("Running Security+ Lab 1: SQL Injection...")
    try:
        test_sql_injection_simulation()
        print("[PASS] SQL Injection vulnerabilities demonstrated and mitigated.")
    except AssertionError as e:
        print(f"[FAIL] {e}")
