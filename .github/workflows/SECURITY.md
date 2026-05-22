# Security Considerations

## Disclaimer

**This repository contains no sensitive information.**

The following configurations are provided as documentation only:

- `dependabot.yml` - Uses standard GitHub Actions, no secrets required
- `release.yml` - Uses `secrets.GITHUB_TOKEN` which is automatically provided by GitHub
- `publish.yml` - Uses OIDC for PyPI authentication (no long-lived secrets stored)

## Required Secrets

Before the `publish.yml` workflow can publish to PyPI, repository administrators must:

1. **Configure PyPI OIDC**
   - Go to https://pypi.org/manage/account/publishing/
   - Add a new pending publisher with:
     - **PyPI Project Name**: `amazon-connect-mcp`
     - **Owner**: `nousresearch`
     - **Repository Name**: `amazon-connect-mcp`
     - **Workflow Name**: `publish.yml`
     - **Environment Name**: `pypi`

2. **Configure Test PyPI OIDC (optional)**
   - Go to https://test.pypi.org/manage/account/publishing/
   - Add a new pending publisher with:
     - **PyPI Project Name**: `amazon-connect-mcp`
     - **Owner**: `nousresearch`
     - **Repository Name**: `amazon-connect-mcp`
     - **Workflow Name**: `publish.yml`
     - **Environment Name**: `testpypi`

## No Secrets Stored in Repository

We do NOT store:
- PyPI tokens
- AWS credentials
- API keys
- Personal access tokens

All authentication uses:
- GitHub's built-in `GITHUB_TOKEN`
- OIDC for PyPI (trust-based authentication)

## Security Best Practices

1. **No secrets committed to code** - All sensitive data is passed via GitHub Secrets
2. **Minimal permissions** - Workflows use least-privilege permissions
3. **OIDC authentication** - PyPI uses short-lived tokens via OIDC
4. **Environment protection** - Publishing requires repository admin approval
