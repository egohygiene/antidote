# Security Policy

Antidote is an experimental research and publication repository. The runtime
prototype is not a medical device and is not ready for private participant data
or unsupervised clinical use.

## Supported scope

Security reports should focus on the current default branch and public
automation surfaces, including:

- publication, CI, Pages, dependency, and generated-artifact behavior;
- contract validation and path or archive handling;
- future Tauri command and sidecar permissions;
- model loading, remote code, weight integrity, and subprocess isolation;
- consent bypass, private-context exposure, logging, retention, or export;
- audio playback, cancellation, partial artifacts, and unsafe recovery behavior.

Target scaffold directories are not executable supported software. Reports that
identify a design-level risk in those contracts are still welcome.

## Sensitive-data boundary

Do not submit real journal entries, therapy content, health records, credentials,
model tokens, participant data, or private audio when demonstrating a problem.
Use synthetic minimal examples. If a vulnerability already exposed sensitive
information, do not place that information in a public issue.

## Reporting a vulnerability

1. Use GitHub private vulnerability reporting when available.
2. If private reporting is unavailable, contact the maintainer through GitHub
   before opening a public issue.
3. Include affected revision, reproduction steps with synthetic data, impact,
   relevant trust boundary, and suggested remediation when known.

## Model and dependency policy

- Pin model, code, workflow, and cross-repository revisions.
- Prefer non-executable weight formats, but do not assume a safe weight container
  makes repository code safe.
- Audit any required `trust_remote_code` before enabling it.
- Never commit credentials, proprietary weights, private datasets, or signing
  material.
- Treat localhost and sidecar messages as untrusted, size-bounded input.

## Clinical and emotional safety

A bug that enables hidden context use, removes stop controls, suppresses an
adverse response, or presents unsupported clinical guidance is in security and
safety scope even when it does not resemble a traditional exploit.
