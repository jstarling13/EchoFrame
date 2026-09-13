# DNS Safety Checklist

Before:
- [ ] exact domain confirmed
- [ ] registrar confirmed
- [ ] DNS provider confirmed
- [ ] existing records exported/screenshot
- [ ] email records identified
- [ ] old site dependencies identified
- [ ] TTL considered
- [ ] MFA enabled

During:
- [ ] only records required by Vercel changed
- [ ] MX untouched unless intentionally changing email
- [ ] SPF preserved/updated correctly
- [ ] DKIM preserved
- [ ] DMARC preserved
- [ ] no duplicate/conflicting apex records
- [ ] canonical host chosen

After:
- [ ] apex works
- [ ] www works
- [ ] intended redirect works
- [ ] HTTPS valid
- [ ] email send test
- [ ] email receive test
- [ ] contact form test
- [ ] production deploy uses main branch
- [ ] Search Console updated
- [ ] sitemap host correct

Rollback:
- [ ] old DNS values retained
- [ ] known prior working state documented
