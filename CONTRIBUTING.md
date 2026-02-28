# Contributing to Fulmine-Sparks

Thank you for your interest in contributing! This guide explains how to get started.

## Getting Started

### Prerequisites
- Python 3.8+
- Git
- An Alby account (for testing payments)
- AWS account (for Lambda deployment)

### Development Setup
```bash
git clone https://github.com/Fulmine-Labs/Fulmine-Sparks.git
cd Fulmine-Sparks
pip install -r requirements.txt
export ALBY_API_TOKEN=your_token_here
python client.py
```

## How to Contribute

### Reporting Issues
1. **Bug report?** Include:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment (Python version, OS, etc.)

2. **Feature request?** Describe:
   - The problem you're trying to solve
   - Your proposed solution
   - Expected use case

3. **Security issue?** See [SECURITY.md](SECURITY.md) for responsible disclosure

### Making Changes

1. **Fork and branch:** Create a feature branch from `master`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make focused changes:** One feature per PR
   - Don't mix refactoring with features
   - Keep commits atomic and descriptive

3. **Test thoroughly:** Run the test suite before submitting
   ```bash
   python client.py test-rate-manual        # Full rate limit test
   python client.py health                  # Health check
   python client.py bot-sim                 # Bot compliance test
   ```

4. **Document your changes:**
   - Update README if adding functionality
   - Add docstrings to new functions
   - Update FINAL_WORKING_VERSION.md if behavior changes

5. **Commit with clear messages:**
   ```
   Fix: [Description of what was fixed]
   Feature: [Description of new feature]
   Docs: [Documentation updates]
   ```

### Submitting a Pull Request

1. Push your branch to your fork
2. Open a PR against the `master` branch
3. Fill out the PR template with:
   - Summary of changes
   - Why this change is needed
   - How to test it
   - Any breaking changes

4. Respond to review feedback
5. Once approved, we'll merge!

## Code Standards

### Style
- Follow PEP 8 conventions
- Use type hints where practical
- Keep functions focused and under 50 lines when possible

### Error Handling
- Use try/except for external API calls
- Provide clear error messages to users
- Log errors for debugging in CloudWatch

### Security
- Never commit secrets or API keys (.env files)
- Validate user input before using it
- Use IAM roles instead of hardcoded credentials
- Review SECURITY.md before deployment

### Testing
- Test rate limiting scenarios (0, 1, 2, 3, 4+ invoices)
- Test payment flow with real Alby API
- Test error cases (network failures, timeouts, etc.)
- Include test results in PR description

## Development Workflow

### Before You Start
```bash
# Create a feature branch
git checkout -b feature/my-feature

# Install dependencies
pip install -r requirements.txt

# Set up environment
export ALBY_API_TOKEN=your_test_token
```

### During Development
```bash
# Run the interactive client
python client.py

# Run specific tests
python client.py test-rate-manual  # Rate limit test
python client.py bot-sim           # Bot compliance test
```

### Before Submitting PR
```bash
# Check your changes
git status
git diff

# Make sure all tests pass
python client.py test-rate-manual

# Review commit messages
git log -3 --oneline
```

## Architecture & Key Files

- **client.py** - CLI client for testing and integration
- **lambda_handler_simple.py** - AWS Lambda function (main API)
- **billing.py** - Alby payment integration
- **FINAL_WORKING_VERSION.md** - Complete feature documentation

For architectural questions, see FULMINE_SPARKS_ANALYSIS.md.

## Testing on AWS

### Deploy to staging
```bash
# Build deployment package
python3 -c "
import zipfile
with zipfile.ZipFile('fulmine-sparks.zip', 'w') as z:
    z.write('lambda_handler_simple.py')
    z.write('billing.py')
"

# Upload to Lambda
aws lambda update-function-code \
  --function-name fulmine-sparks-staging \
  --zip-file fileb://fulmine-sparks.zip
```

### Verify deployment
```bash
python client.py health
python client.py test-rate-manual
```

## Questions?

- Check existing GitHub issues
- Review FINAL_WORKING_VERSION.md for common scenarios
- Ask in your PR - we're here to help!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make Fulmine-Sparks better!** ⚡
