## 1. Create new capability specs

- [x] 1.1 Write `openspec/specs/organization-model/spec.md` from delta spec (requirements + implementation decisions for org model, membership, invitation, ownership transfer, per-org billing, has_org_feature())
- [x] 1.2 Write `openspec/specs/outbound-webhooks/spec.md` from delta spec (requirements + decisions for endpoint registry, HMAC delivery, circuit breaker, event catalog)
- [x] 1.3 Write `openspec/specs/api-key-authentication/spec.md` from delta spec (requirements + decisions for key creation, Bearer auth, RequireScope, rate limiting, usage tracking)
- [x] 1.4 Write `openspec/specs/audit-logging/spec.md` from delta spec (requirements + decisions for pghistory triggers, AuditContextMiddleware, org-scoped read API)
- [x] 1.5 Write `openspec/specs/admin-backoffice/spec.md` from delta spec (requirements + decisions for django-unfold theme, django-hijack impersonation, audit integration)

## 2. Update modified capability spec

- [x] 2.1 Append ADDED requirement to `openspec/specs/cli-scaffolder/spec.md` for SCAFF-01 (`--with b2b` opt-in flag, removeB2BModule(), B2B_START/B2B_END markers, CI validation)

## 3. Archive change

- [ ] 3.1 Run `/opsx:archive gsd-milestone-1-4` to close this change
