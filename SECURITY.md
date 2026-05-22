# Security Policy

## Supported Versions

The following versions of Amazon Connect MCP Server are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

We take the security of the Amazon Connect MCP Server seriously. If you believe you've found a security vulnerability, please follow these steps:

### Please Do NOT:

- **Do not** open a public issue on GitHub
- **Do not** disclose the vulnerability publicly until it has been addressed
- **Do not** test the vulnerability on production systems without permission

### Please DO:

1. **Report privately** by emailing security@nousresearch.com
2. **Include details** about the vulnerability:
   - Type of vulnerability (e.g., XSS, injection, privilege escalation)
   - Affected versions
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Assessment**: We will assess the vulnerability and determine its impact
- **Updates**: We will keep you informed about our progress
- **Resolution**: Once fixed, we will release a security update and credit you (if desired)

## Security Measures

This project implements several security measures:

### AWS Credential Handling

- No AWS credentials are stored within the MCP server
- Credentials are obtained from standard AWS credential providers
- Environment variables or IAM roles are used for authentication

### Data Handling

- Sensitive data (API keys, tokens) is not logged
- AWS API responses are processed but not stored persistently
- No customer data is cached or retained

### API Bridge Security

- Lambda API Gateway uses HTTPS/TLS 1.2+
- API keys can be configured for additional authentication
- CORS settings should be configured appropriately

## Best Practices

When using this MCP server, we recommend:

1. **Principle of Least Privilege**: Grant only necessary AWS permissions
2. **Credential Rotation**: Regularly rotate AWS credentials
3. **Audit Logging**: Enable CloudTrail for AWS API calls
4. **VPC Endpoints**: Use VPC endpoints where possible for AWS service access
5. **API Gateway Security**: Configure proper authorization and throttling

## Security Updates

Security updates will be released as patch versions (e.g., 0.1.1) and announced via:

- GitHub releases
- Security advisories on the repository

## Credits

We acknowledge and thank security researchers who responsibly disclose vulnerabilities.
