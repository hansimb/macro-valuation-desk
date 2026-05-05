# MVD Future Scaling Considerations

## Purpose

Capture the most likely scaling and product-architecture changes if Macro Valuation Desk later evolves from a public analytics site into a more application-heavy or enterprise-style product.

This note is intentionally forward-looking. It does not change the current deployment plan.

## Current Assumption

The current hosted model is optimized for:

- public read-heavy traffic
- no user accounts
- no tenant isolation
- scheduled pipelines running `1-2` times per day
- API reads against prepared warehouse and marts data

That model remains the right starting point.

## Likely Future Change

If MVD later adds:

- user accounts
- organizations or teams
- saved views or dashboards
- notes, watchlists, and preferences
- entitlements or paid plans
- audit trails
- internal or enterprise workflows

then the biggest architectural change will likely happen in the `API` and application-data layer, not in the pipelines layer.

## Expected Application Architecture Shift

### Web

The web layer would still remain a consumer of the product API.

Its responsibilities would grow in user experience, account flows, and application behavior, but the biggest structural change would still happen behind it.

### API

The API would likely become a much richer application boundary responsible for:

- authentication
- authorization
- account lifecycle logic
- organization or tenant-level isolation
- feature access and entitlements
- audit logging
- application settings and saved user objects

This means the API would evolve from a mostly analytics-serving layer into a more complete application service.

### Pipelines

Pipelines would likely remain conceptually similar:

- ingest data
- normalize and validate it
- transform and model it
- write prepared data for analytics use

They may grow in scope, but they would not need to change nearly as much as the API if accounts and enterprise features are added.

## Database Split Path

One of the most natural later scaling steps would be to separate:

- analytics and pipeline data storage
- application and user data storage

## Why This Split Can Make Sense

The two data domains behave differently.

### Analytics / pipeline database

Typical characteristics:

- larger historical datasets
- heavy ingest jobs
- batch transforms
- warehouse and marts patterns
- more read-heavy analytics behavior

### Application / API database

Typical characteristics:

- users
- organizations
- roles and permissions
- saved objects
- watchlists
- notes
- app settings
- audit logs
- billing or subscription data later

This side is usually more transactional and user-state oriented.

## Benefits Of Separating Them Later

- user-facing application traffic is less likely to contend with pipeline-heavy warehouse workloads
- backup and restore strategies can differ by data domain
- security boundaries can become cleaner
- scaling decisions can be made independently
- operational ownership becomes clearer

## Important Guardrail

This split should not be done too early.

The better near-term approach is:

1. keep one PostgreSQL instance initially
2. separate data domains clearly in schema design and ownership
3. keep public analytics data and future app data logically distinct
4. split physically only when scale, security, or operational complexity justifies it

## Recommended Near-Term Design Habit

Even before accounts exist, MVD should avoid mixing domains carelessly.

Good direction:

- keep market and macro data in warehouse-oriented schemas such as `raw`, `staging`, `warehouse`, and `marts`
- if application data is added later, place it in clearly separate app-oriented schemas or ownership boundaries

This makes a future physical split easier without forcing it prematurely.

## Scaling Interpretation

If MVD grows into a more serious product, scaling will likely happen on multiple tracks:

- `web` scales as the public or product-facing interface
- `api` scales as the application-serving layer
- analytics data scales through better warehouse design, marts, and storage strategy
- user/application data scales through more transactional patterns and stricter app-domain controls

In other words, future scale is unlikely to be solved by only adding more API pods.

## Summary

The current architecture is a good public-analytics-first foundation.

If the product later becomes more account-heavy or enterprise-like:

- the biggest changes will be in the API layer
- the web layer will mostly consume those new capabilities
- the pipelines layer will remain broadly similar
- a later split between analytics data and application data will likely become a strong option

That future path is compatible with the current design and does not require immediate architectural changes now.
