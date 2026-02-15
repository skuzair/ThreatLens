from sandbox_orchestrator import execute_sandbox

input_data = {
    "incident_id": "TEST-002",
    "file_hash": "sha256:test"
}

result = execute_sandbox(input_data)
print(result)
