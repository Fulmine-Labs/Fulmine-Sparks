# Security Policy for Fulmine-Sparks

## Reporting Security Issues

If you discover a security vulnerability in Fulmine-Sparks, please **do not** open a public GitHub issue. Instead:

1. **Email:** security@fulmine-labs.com
2. **Include:**
   - Description of the vulnerability
   - Steps to reproduce (if applicable)
   - Potential impact
   - Suggested fix (if you have one)

3. **Response time:** We aim to acknowledge reports within 48 hours and provide a fix within 7 days

4. **Credit:** We will credit you for responsible disclosure unless you prefer anonymity

## Security Best Practices

### For Deployment

#### 1. Environment Variables
- **Never commit `.env` files** - use `.env.example` instead
- Store sensitive values in AWS Secrets Manager or Parameter Store
- Rotate keys regularly (recommended: every 90 days)
- Use separate credentials for dev/staging/production

#### 2. API Keys & Tokens
- `ALBY_NWC_URL`: Your Alby wallet connection string
  - Keep this secret - never share or commit to version control
  - Rotate immediately if exposed

- `ALBY_API_TOKEN`: API authentication token
  - Restrict to test/prod environments only
  - Regenerate if compromised

- `REPLICATE_API_TOKEN`: Image generation API key
  - Use API key with minimal required permissions
  - Enable rate limiting on Replicate

#### 3. Lambda Configuration
- Enable VPC endpoint for DynamoDB to avoid internet exposure
- Use IAM roles with least-privilege permissions
- Enable CloudTrail for audit logging
- Encrypt DynamoDB tables at rest

#### 4. DynamoDB Security
- Enable point-in-time recovery
- Enable encryption (both at-rest and in-transit)
- Restrict IAM permissions to specific tables
- Use TTL for automatic data cleanup

### For Users

#### 1. Lightning Wallet Safety
- Use a dedicated wallet for payments (not your primary wallet)
- Verify invoice amounts before paying
- Be cautious of phishing links - always use the official client

#### 2. API Usage
- Never share your API credentials
- Use rate limiting to prevent abuse (documented in llms.txt)
- Monitor your spending in the Alby dashboard
- Report suspicious activity immediately

#### 3. Prompt Security
- Avoid including personal information in prompts
- Understand that prompts are not permanently stored
- Generated images are cached for only 1 minute

## Known Security Considerations

### Current Implementation
- **Rate limiting:** IP-based (not user-based) - suitable for public APIs
- **No authentication:** Payment via Lightning is the only "auth" - no API keys required
- **Prompts not stored:** Generated on-demand, cached briefly for payment confirmation
- **Payment finality:** Lightning payments are irreversible - no refund capability

### Limitations
- Rate limiting can be bypassed by changing IP address (this is acceptable for a public API)
- No permanent user tracking (intentional privacy feature)
- Payment reversals not possible (Lightning limitation)

## Dependency Security

### Critical Dependencies
- **boto3:** AWS SDK - kept up-to-date
- **requests:** HTTP library - monitor security advisories
- **replicate:** API client - verify official package only

### How to Report Dependency Issues
1. Run: `pip check` or `safety check`
2. If vulnerability found, report via security contact above
3. We will update and re-deploy patches within 24 hours

## Compliance & Standards

- **GDPR:** Compliant - no personal data stored long-term
- **CCPA:** Compliant - user data deletion supported
- **PCI DSS:** Not directly applicable (payments via Lightning/Alby)
- **Rate Limiting:** Fair-use policy described in llms.txt

## Security Checklist Before Deployment

- [ ] All `.env` files added to .gitignore
- [ ] `ALBY_NWC_URL` and `REPLICATE_API_TOKEN` stored securely (not in code)
- [ ] Lambda IAM role has minimal necessary permissions
- [ ] DynamoDB tables have encryption enabled
- [ ] CloudTrail logging configured
- [ ] Alby wallet configured with spending limits
- [ ] API Gateway has WAF rules enabled (optional but recommended)
- [ ] Rate limiting thresholds reviewed and appropriate
- [ ] CloudWatch alerts configured for suspicious activity

## Incident Response

If a security incident occurs:

1. **Immediate (0-1 hour):**
   - Assess scope and impact
   - Notify via `security@fulmine-labs.com` if user data affected
   - Disable compromised credentials

2. **Short-term (1-24 hours):**
   - Identify root cause
   - Deploy fix in hotfix branch
   - Release patched version

3. **Follow-up (1-7 days):**
   - Post-incident review
   - Audit logs for unauthorized access
   - Update documentation

## Version History

- **1.0.0** (Feb 28, 2026): Initial security policy
  - Rate limiting implemented
  - DynamoDB-backed tracking
  - Lightning payment integration
  - TTL-based automatic cleanup
