# 🔐 Security Guidelines

## API Key Management

### ⚠️ CRITICAL: Never commit API keys to Git

This project uses environment variables for sensitive configuration.

### Setup Instructions

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Add your API key:**
   Edit `.env` and replace `your_api_key_here` with your actual Gemini API key.

3. **Verify .gitignore:**
   Ensure `.env` is listed in `.gitignore` (already configured).

### What's Protected

The following files contain sensitive data and are **never** committed:
- `.env` - API keys and configuration
- `audit_ledger.jsonl` - Audit logs
- `echo_memory.json` - Runtime memory
- `echo_status.json` - System status
- `*.key`, `*.pem` - Cryptographic keys

### If You Accidentally Commit Secrets

1. **Immediately revoke the exposed key** (Google Cloud Console)
2. **Generate a new key**
3. **Remove from Git history:**
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```
4. **Force push:**
   ```bash
   git push origin --force --all
   ```

### Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] No API keys in code files
- [ ] `.env.example` has placeholder values only
- [ ] Sensitive data files are excluded from Git
- [ ] API keys are rotated regularly

### Reporting Security Issues

If you discover a security vulnerability, please email: cleanbell2222@gmail.com

**Do not** create public GitHub issues for security vulnerabilities.

---

## Data Privacy

### Audit Logs

The `audit_ledger.jsonl` file may contain sensitive runtime data.
- This file is excluded from Git
- Rotate logs periodically
- Sanitize before sharing

### Echo Memory

Memory files (`echo_memory.json`, `echo_memory_graph.json`) may contain:
- System state information
- Internal decision logs
- Potentially sensitive metadata

These are excluded from version control by default.

---

## Best Practices

1. **Environment Separation**
   - Use different API keys for development/production
   - Never use production keys in testing

2. **Key Rotation**
   - Rotate API keys every 90 days
   - Revoke unused keys immediately

3. **Access Control**
   - Limit API key permissions to minimum required
   - Use separate keys per environment

4. **Monitoring**
   - Monitor API key usage
   - Set up alerts for unusual activity

---

**Last Updated:** 2026-01-29
**Version:** 1.0
