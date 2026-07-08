# Security Policy

## Supported Versions

canvodpy-extensions packages are currently in **beta** (pre-1.0 release). Security
updates are provided for:

| Version | Supported          |
| ------- | ------------------ |
| 0.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of canvodpy-extensions seriously. If you discover a security
vulnerability, please follow these steps:

### 1. **Do Not** Open a Public Issue

Please **do not** report security vulnerabilities through public GitHub issues,
discussions, or pull requests.

### 2. Report Privately

Report security vulnerabilities via one of these methods:

**Preferred:** Use GitHub's private vulnerability reporting:
- Go to https://github.com/nfb2021/canvodpy-extensions/security/advisories
- Click "Report a vulnerability"
- Fill in the details

**Alternative:** Email the maintainer directly:
- Email: nicolas.bader@tuwien.ac.at
- Include "SECURITY" in the subject line
- Provide a detailed description of the vulnerability

### 3. What to Include

Please include as much of the following information as possible:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Impact of the issue, including how an attacker might exploit it

### 4. Response Timeline

- **Initial Response:** Within 48 hours of report
- **Confirmation:** Within 7 days (whether we accept or decline the report)
- **Fix Timeline:** Depends on severity
  - Critical: 7 days
  - High: 30 days
  - Medium: 60 days
  - Low: 90 days

## Security Best Practices for Users

- Keep canvodpy-extensions packages and their dependencies up to date
- Monitor GitHub Dependabot alerts and PyPI security notifications
- **Never commit credentials** to version control
- Validate configuration and data files loaded from untrusted sources

## Dependency Chain

canvodpy-extensions packages are built against [canvodpy](https://github.com/nfb2021/canvodpy)
and its dependency chain (NumPy, Pydantic, xarray, Zarr, etc.). Vulnerabilities in
that chain may affect these packages; we monitor and update dependencies regularly.

## Contact

For security-related questions or concerns:
- **Maintainer:** Nicolas François Bader
- **Email:** nicolas.bader@tuwien.ac.at
- **Affiliation:** Climate and Environmental Remote Sensing (CLIMERS), TU Wien

For general (non-security) questions, use GitHub Issues:
https://github.com/nfb2021/canvodpy-extensions/issues
