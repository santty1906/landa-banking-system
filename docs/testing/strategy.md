# Testing Strategy (ISTQB-Oriented)

## Quality objectives

- Validate reliability and regression protection for backend foundations.
- Prioritize authentication/security and standardized error contracts as critical risk areas.
- Keep tests deterministic, modular, and maintainable for beginner/intermediate contributors.

## Test levels and scope

- **Unit tests**: isolated validation of configuration, JWT logic, exception envelopes, and auth dependencies.
- **Integration tests**: real PostgreSQL connectivity, readiness behavior, and startup/runtime DB interaction.
- **API tests**: HTTP contract validation for status codes and response structures.
- **Security/Auth tests**: unauthorized-access scenarios at backend trust boundary.
- **Face recognition tests**:
  - Contract/provider-independent tests in default CI.
  - Provider-heavy tests only in nightly/manual workflows.

## Entry and exit criteria

### Entry

- Lint and compile checks pass.
- Test environment variables and fixtures are available.
- PostgreSQL service is reachable for integration stage.

### Exit

- Required suites pass for the target pipeline.
- Coverage gates pass:
  - Global backend coverage >= 80%
  - Critical modules (auth/security/exceptions) >= 90%
- No unresolved critical defects in auth/security/error-contract paths.

## Regression policy

- Every bug fix adds or updates at least one deterministic regression test.
- Security/auth regressions are treated as high priority and validated before merge.

## Traceability map (quality-focused scaffold)

- Authentication token validation -> `tests/unit/test_auth_dependency.py`, `tests/security/test_unauthorized_access.py`
- Standardized error envelopes -> `tests/unit/test_exceptions.py`, security tests
- Database readiness and connectivity -> `tests/integration/test_database_readiness.py`, `tests/api/test_system_endpoints.py`
- Facial recognition contract boundary -> `tests/face/test_face_contract.py`
