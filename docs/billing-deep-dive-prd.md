# Billing Deep Dive — Product Boundary

Status: adopted from `Contract Billing & Drone Asset Tracking Portal`, v1.1, supplied 2026-09-06.

This document governs **only the Billing Deep Dive**. It does not replace the SkyStation Operations Intelligence PRD for Activity Tracking, Inventory, Crew Management, Analytics, MIS, or Central Dashboard.

## Scope boundary

The wider portal answers operational questions across planned work, execution, assets, people, delivery, reporting, and management attention. Billing Deep Dive owns the commercial lifecycle for autonomous drone service contracts:

```text
Customer → Contract / PO → Site → Autonomous Drone Asset → Billing Period
→ Billability → Service Sheet → Invoice → Payment
```

Central Dashboard may show summarized billing readiness, confirmation progress, or exception state. Detailed rates, billable amounts, invoice values, payment data, and commercial records belong only in protected Billing Deep Dive views.

## Primary billing view

The primary screen is a **Month × Drone Asset Matrix**. Rows represent a specific asset in its valid site/deployment context; columns represent billing periods. Asset movement is modeled through deployment history, so the same asset must not be permanently tied to one site.

Each cell is a commercial state with text and icon, never color alone:

- Future
- In Progress
- Confirmation Due
- Billability Confirmation Pending
- Billable
- Partially Billable
- Not Billable
- Not Applicable
- Service Sheet Pending
- Ready to Invoice
- Invoiced
- Payment Pending
- Paid
- Disputed

A billable tick means the service obligation is accepted as eligible for billing. It does not mean an invoice exists.

## Required workflows

1. During the configured closing window, create a confirmation action for each active asset-period.
2. Authorized users confirm Billable, Not Billable, Partially Billable, or Not Applicable.
3. Not Billable requires a reason and remarks.
4. Partial billing requires billable days, contractual days, percentage, approved value, and reason.
5. Confirmed billable periods move to the billing queue for service-sheet and invoice processing.
6. Service sheet, invoice, and payment states advance independently and retain their evidence.
7. Changes after invoicing require an authorized override, reason, warning, and audit trail.

The cut-off date and optional two-step approval flow are configurable per contract. The default date is only a configuration default, never a hard-coded business rule.

## Cell drill-down

Selecting a matrix cell opens the complete commercial record:

- customer, contract/PO, site, asset ID, and billing period;
- deployment and service-completion evidence;
- billability state, confirmation user/date, remarks, and support document;
- effective rate, quantity, percentage, and amount;
- service-sheet number/status/document;
- invoice number/date, allocation, tax, gross value, submission and due dates;
- payment records, deductions, received amount, outstanding amount, UTR/reference, and remarks.

Invoices must allocate to **Asset + Month**, including quarterly or multi-period invoices. A link only from Invoice → Asset is insufficient.

## Billing Queue

The queue is the action-oriented view for Accounts, Finance, Operations, and contract owners:

- Billability Confirmation Pending
- Billable — Service Sheet Pending
- Service Sheet Ready — Invoice Pending
- Invoice Raised — Submission Pending
- Payment Pending
- Payment Overdue

The monthly closing view summarizes active assets, confirmation progress, billability states, value ready for billing, service-sheet pending value, and invoice-pending value. Financial amounts remain protected and must carry source/evidence state.

## Domain entities

The billing data model must support multiple customers, contracts, POs, sites, assets, deployment periods, rates, service sheets, invoices, invoice allocations, payments, amendments, extensions, and configurable billing periods.

Minimum stable-key entities:

- Customer
- Contract / PO
- Site
- Autonomous Drone Asset
- Deployment / Assignment History
- Effective-Dated Rate
- Billing Period
- Billability Confirmation
- Service Sheet
- Invoice
- Invoice Allocation (asset + billing period)
- Payment
- Audit Event

Use source IDs and explicit relations for joins. Never infer contract, customer, site, asset, or period relationships from display text alone.

## Roles and audit

Support configurable authorization for Super Admin, Contract/Account Owner, Operations, Finance, and Management. Customer access is future scope. Mandatory audit events cover billability confirmations and overrides, rate changes, invoice/payment changes, asset reassignment, and contract-value changes, retaining user, time, previous value, new value, and reason.

## Reports

Mandatory Excel exports:

- Month × Drone Billing Matrix
- Monthly Billability Report
- Invoice Register
- Service Sheet Register
- Outstanding Report
- Billable but Uninvoiced Report
- Contract Utilization Report
- Customer Billing Statement
- Asset-wise Billing History

Customer-facing exports must exclude internal-only fields and include only approved customer, contract/PO, asset, site, period, billability, service-sheet, invoice, and basic-value fields.

## Open configuration

Production sign-off requires customer/contract billing rules, approval configuration, asset and rate mappings, document sources, and role permissions. Until those are configured, the UI must use explicit `Needs review` / `Not configured` states rather than invented thresholds or values.
