# Geopixi | Three-Zone Architecture & Identity Plan

> **Document Version:** 1.0
> **Date:** 2026-08-19
> **Author:** Rodney
> **Scope:** Three-zone hardware segmentation, dual-tenant Azure identity design, and zone setup procedures.
> **Note:** No migration plan. This is a greenfield decoupled architecture. Existing OHGIS identity is stable and untouched.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Identity Strategy](#2-identity-strategy)
3. [Zone 1 — Legacy IoT Zone](#3-zone-1--legacy-iot-zone)
4. [Zone 2 — Modern Identity Boundary Zone](#4-zone-2--modern-identity-boundary-zone)
5. [Zone 3 — High-End Workstation Zone](#5-zone-3--high-end-workstation-zone)
6. [Zone Interaction & Topology](#6-zone-interaction--topology)
7. [Azure Identity Setup Plan — Geopixi Tenant](#7-azure-identity-setup-plan--geopixi-tenant)
8. [DNS Coexistence with Google Workspace](#8-dns-coexistence-with-google-workspace)
9. [Setup Checklist](#9-setup-checklist)
10. [Appendix A — DNS TXT Record Setup for Azure Entra ID Verification](#appendix-a--dns-txt-record-setup-for-azure-entra-id-verification)

---

## 1. Architecture Overview

This document defines the three-zone architecture segmenting hardware, workloads, and identity
boundaries across the environment. Each zone is isolated by function, hardware capability, and
identity trust level.

The architecture is built around two governing principles:

- **Identity isolation first.** The OHGIS Azure tenant (Legacy IoT) and the Geopixi Azure tenant
  (Modern + Workstation) are hard-separated. No shared directory objects, no shared Conditional
  Access policies, no shared admin roles.
- **No cross-zone lateral movement.** Zones communicate only through defined, controlled pathways
  — VLAN segmentation enforces this at the network layer.

---

## 2. Identity Strategy

### The Two-Tenant Split

A single-tenant design was evaluated and rejected. Adding `geopixi.com` to the OHGIS tenant would
place Legacy IoT nodes and modern managed workstations in the same identity plane — shared Intune
scope, shared admin roles, shared Conditional Access. That is the collision this architecture is
designed to prevent.

**Two separate Entra ID tenants are used:**

| Tenant | Domain | Zones Served | Status |
|---|---|---|---|
| OHGIS | `ohgis.onmicrosoft.com` | Zone 1 only | Existing — untouched |
| Geopixi | `geopixi.com` | Zone 2 and Zone 3 | New — to be created |

### Identity Boundary Summary

```
Geopixi Entra ID Tenant (geopixi.com)
├── Zone 2 — EE-1130 (enrolled, Conditional Access enforced)
└── Zone 3 — High-End Workstations (enrolled, RBAC scoped)

OHGIS Entra ID Tenant (ohgis.onmicrosoft.com)
└── Zone 1 — i3 10th Gen, NUC units (NOT enrolled in Entra — local/legacy accounts only)
```

No cross-tenant trust or B2B federation is required or configured at this time.

---

## 3. Zone 1 — Legacy IoT Zone

### Purpose

The Legacy IoT Zone houses older-generation Intel hardware supporting constrained, specialized
workloads — primarily IoT data collection, edge telemetry, and lightweight automation. These
machines operate at the perimeter of the identity boundary and are treated as lower-trust,
unmanaged endpoints.

### Identity Boundary

- **Tenant:** OHGIS (`ohgis.onmicrosoft.com`) — existing, stable, no changes
- **Trust Level:** Low / Untrusted perimeter
- Devices are **not enrolled** in Entra ID or Intune — local accounts or legacy domain credentials only
- Network access is restricted at the VLAN/firewall layer; no lateral movement to Zones 2 or 3 permitted
- No Azure AD join, no MDM enrollment, no Conditional Access scope

### Workloads

| Workload | Description |
|---|---|
| IoT data ingestion | Sensor and edge telemetry collection from connected field devices |
| Edge automation | Lightweight scheduled tasks, scripts, and local processing loops |
| Protocol bridging | MQTT, Modbus, or other IoT protocol translation to upstream consumers |
| Local logging | On-device or LAN-scoped log aggregation |

### Hardware Roles

| Device | Role |
|---|---|
| Intel i3 (10th Gen) | Primary IoT host; runs constrained workloads and edge agents |
| Intel NUC units | Secondary IoT nodes; protocol bridging and local automation tasks |

### Constraints & Notes

- Hardware in this zone is **not eligible** for AI or ESRI workloads due to resource limitations
- Do not store sensitive credentials or licensed software keys on Zone 1 devices
- Firmware and BIOS should be locked where possible to reduce attack surface
- All data leaving Zone 1 must be sanitized and transformed before entering Zone 3

---

## 4. Zone 2 — Modern Identity Boundary Zone

### Purpose

Zone 2 is the secure identity hub and control plane for the environment. The Intel Evo EE-1130
anchors this zone as a cloud-connected, fully managed endpoint — the administrative gateway and
identity trust boundary between the untrusted IoT perimeter (Zone 1) and the high-trust
workstation tier (Zone 3).

### Identity Boundary

- **Tenant:** Geopixi (`geopixi.com`) — new tenant, created per Section 7
- **Trust Level:** High / Trusted modern boundary
- Device is **enrolled in Entra ID and Intune** under the Geopixi tenant
- Conditional Access enforced: MFA required, compliant device status verified before access is granted
- Zero Trust posture: never-trust-always-verify for all cross-zone communications
- Certificates and device compliance policies are issued from this zone

### Workloads

| Workload | Description |
|---|---|
| Identity & access management | Entra ID, MFA, Conditional Access policy enforcement for Zones 2 and 3 |
| Device management | Intune enrollment, compliance monitoring, and policy push |
| Administrative operations | Remote management coordination across all zones |
| Certificate services | Cloud-integrated cert issuance for cross-zone device trust |
| Secure remote access | Zero Trust Network Access (ZTNA) endpoint |

### Hardware Roles

| Device | Role |
|---|---|
| Intel Evo EE-1130 | Primary identity boundary node; Entra ID and Intune enrolled, cloud-connected control plane |

### Constraints & Notes

- This device must maintain **continuous cloud connectivity** for identity services to function
- Do **not** install resource-intensive workloads (AI inference, GIS rendering) on this device — its role is control-plane only
- Admin credentials and secrets are scoped to the Geopixi tenant; they must not persist on Zone 1 devices
- Assigned Entra role: **Cloud Device Administrator** or **Intune Administrator** — not Global Admin unless explicitly required

---

## 5. Zone 3 — High-End Workstation Zone

### Purpose

Zone 3 provides the compute-intensive environment for professional GIS/ESRI workflows and AI model
workloads. Hardware here is selected for raw processing power, GPU capability, and memory headroom.
This zone consumes identity services from Zone 2 but has no administrative responsibility for them.

### Identity Boundary

- **Tenant:** Geopixi (`geopixi.com`) — same tenant as Zone 2
- **Trust Level:** High / Trusted workstation tier
- Devices are **Entra ID-joined**, with identity services consumed from the Geopixi tenant
- Access to AI models, GIS datasets, and ESRI licenses is gated by role-based access control (RBAC)
- GPU and high-memory resources are physically and logically isolated from Zone 1 devices
- Audit logging enabled for all privileged workload access

### Workloads

| Workload | Description |
|---|---|
| ESRI / ArcGIS | Full GIS desktop and server workloads; spatial analysis, map rendering, geodatabase management |
| AI model training | Local LLM fine-tuning, inference, and batch processing |
| AI inference serving | On-premise model serving endpoints for internal consumers |
| Data pipeline processing | Large dataset ingestion, transformation, and analysis |
| Visualization & rendering | High-fidelity map and data visualization requiring GPU acceleration |

### Hardware Roles

| Device | Role |
|---|---|
| High-End Workstation (GIS) | ESRI production node; ArcGIS Pro, ArcGIS Server, spatial analysis |
| High-End Workstation (AI) | AI training and inference; GPU-accelerated model workloads |

### Constraints & Notes

- ESRI licensing is node-locked or network-licensed — license server must be reachable within Zone 3 only
- AI workloads should use isolated Python/conda environments to prevent dependency conflicts with GIS tooling
- Raw IoT data from Zone 1 must **not** enter Zone 3 directly — all ingestion must be sanitized through Zone 2
- GPU driver, CUDA, and ROCm versions must be pinned and tested before any workload promotion

---

## 6. Zone Interaction & Topology

```
┌──────────────────────────────────────────────────────────────┐
│              Zone 3 — High-End Workstation Zone              │
│         ESRI / ArcGIS  |  AI Training  |  AI Inference       │
│         Intel High-End Workstations (GIS + AI nodes)         │
│         Identity: geopixi.com  [Geopixi Entra Tenant]        │
└──────────────────────────────┬───────────────────────────────┘
                               |  Identity consumed from Zone 2
                               |  Sanitized data only
┌──────────────────────────────▼───────────────────────────────┐
│            Zone 2 — Modern Identity Boundary Zone            │
│     Entra ID  |  Intune  |  Conditional Access  |  ZTNA      │
│                     Intel Evo EE-1130                        │
│         Identity: geopixi.com  [Geopixi Entra Tenant]        │
└──────────────────────────────┬───────────────────────────────┘
                               |  VLAN-segmented
                               |  No lateral movement permitted
┌──────────────────────────────▼───────────────────────────────┐
│               Zone 1 — Legacy IoT Zone                       │
│      IoT Ingestion  |  Edge Automation  |  Protocol Bridge   │
│          Intel i3 10th Gen  |  Intel NUC units               │
│         Identity: ohgis.onmicrosoft.com  [OHGIS Tenant]      │
│                        UNTOUCHED                             │
└──────────────────────────────────────────────────────────────┘
```

| Zone | Tenant | Trust Level | Key Hardware | Primary Function |
|---|---|---|---|---|
| Zone 1 — Legacy IoT | OHGIS | Low / Perimeter | i3 10th Gen, NUCs | IoT ingestion, edge automation |
| Zone 2 — Identity Boundary | Geopixi | High / Control plane | Intel Evo EE-1130 | Identity, MDM, policy, ZTNA |
| Zone 3 — Workstations | Geopixi | High / Data plane | High-End Workstations | ESRI GIS, AI training and inference |

---

## 7. Azure Identity Setup Plan — Geopixi Tenant

### Step 1 — Create the New Geopixi Tenant

From within the OHGIS Entra Admin Center (`entra.microsoft.com`):

> **Identity → Overview → Manage tenants → Create**

| Field | Value |
|---|---|
| Tenant type | Microsoft Entra ID (Workforce) |
| Organization name | Geopixi |
| Initial domain | `geopixi.onmicrosoft.com` (temporary placeholder) |
| Country / Region | United States |

Click **Review + Create → Create**. Provisioning typically completes in under 2 minutes.

---

### Step 2 — Switch into the Geopixi Tenant

> **Account icon (top-right) → Switch directory → Geopixi**

All subsequent steps are performed inside the Geopixi tenant.

---

### Step 3 — Add geopixi.com as a Custom Domain

> **Identity → Settings → Domain names → Add custom domain**

- Enter `geopixi.com` → click **Add domain**
- Azure displays a **TXT verification record** — copy the full value before proceeding

---

### Step 4 — Add the TXT Record at DNS (See Appendix A)

Follow Appendix A in full to add the Azure TXT record via Google Workspace Admin Console
and the Squarespace DNS editor. Use **Firefox** for this step.

---

### Step 5 — Verify the Domain and Set as Primary

> **Identity → Settings → Domain names → geopixi.com → Verify**

Once verified, click **Make primary** so all new user UPNs default to `@geopixi.com`.

---

### Step 6 — Create the Admin Identity

> **Identity → Users → New user → Create new user**

| Field | Value |
|---|---|
| User principal name | `admin@geopixi.com` |
| Display name | Rodney (Geopixi Admin) |
| Role | Global Administrator (Geopixi tenant only) |
| Password | Set strong initial password; require change on first sign-in |

This account is scoped entirely to the Geopixi tenant — zero visibility into or
authority over the OHGIS tenant.

---

### Step 7 — Enroll the EE-1130 (Zone 2 Device)

On the EE-1130:

> **Settings → Accounts → Access work or school → Connect → Join this device to Azure Active Directory**

Enter `admin@geopixi.com` credentials. The device enrolls into the Geopixi tenant and
falls under Intune policy scope immediately.

Verify enrollment:

> **Entra Admin Center (Geopixi) → Devices → All devices**

---

### Step 8 — Configure Conditional Access for Zone 2

> **Protection → Conditional Access → New policy**

| Setting | Value |
|---|---|
| Name | `Zone2-EE1130-Baseline` |
| Users | All users in Geopixi tenant |
| Cloud apps | All cloud apps |
| Conditions — Device platforms | Windows |
| Conditions — Device state | Compliant devices only |
| Grant | Require MFA + Require compliant device |
| Session | Sign-in frequency: 8 hours |

---

### Step 9 — Enroll Zone 3 Workstations

Repeat Step 7 for each Zone 3 workstation (GIS node and AI node) using `admin@geopixi.com`.
Assign distinct Intune device compliance profiles per workload role as needed.

---

## 8. DNS Coexistence with Google Workspace

`geopixi.com` is currently used with Google Workspace. The Azure TXT verification record is
**fully additive** and does not interfere with any Google services.

| DNS Record | Owned By | Action |
|---|---|---|
| MX records (`ASPMX.L.GOOGLE.COM` etc.) | Google Workspace | ✅ Leave as-is |
| TXT — SPF (`v=spf1 include:_spf.google.com ~all`) | Google Workspace | ✅ Leave as-is |
| TXT — DKIM (`google._domainkey...`) | Google Workspace | ✅ Leave as-is |
| TXT — `google-site-verification=...` | Google Workspace | ✅ Leave as-is |
| TXT — `MS=msXXXXXXXX` | Azure (new) | ✅ Add as new record only |
| CNAME — Autodiscover | Google Workspace | ✅ Leave as-is |

Azure reads the TXT record only to confirm domain ownership. It does not modify routing,
email delivery, or any other DNS behavior. A domain can hold multiple TXT records
simultaneously with no conflict.

---

## 9. Setup Checklist

### OHGIS Tenant (Zone 1)
- [ ] Confirm OHGIS tenant remains untouched
- [ ] Verify Zone 1 devices have no Entra ID join or Intune enrollment
- [ ] Confirm VLAN segmentation blocks Zone 1 → Zone 2/3 lateral movement
- [ ] Lock BIOS/firmware on i3 and NUC units

### Geopixi Tenant — Identity (Zones 2 & 3)
- [ ] Create new Entra ID tenant — Organization: Geopixi
- [ ] Switch directory into Geopixi tenant
- [ ] Add `geopixi.com` as custom domain — copy the Azure TXT value
- [ ] Add Azure TXT verification record via Google Admin Console → Squarespace DNS (see Appendix A, Firefox)
- [ ] Confirm TXT record live on dnschecker.org
- [ ] Verify `geopixi.com` in Entra Admin Center
- [ ] Set `geopixi.com` as primary domain
- [ ] Create `admin@geopixi.com` Global Administrator account

### Zone 2 — EE-1130
- [ ] Entra ID join the EE-1130 under Geopixi tenant
- [ ] Confirm device appears in Entra → Devices → All devices
- [ ] Apply Intune compliance policy
- [ ] Configure Conditional Access baseline policy (`Zone2-EE1130-Baseline`)
- [ ] Verify MFA enforcement on `admin@geopixi.com`

### Zone 3 — High-End Workstations
- [ ] Entra ID join GIS workstation under Geopixi tenant
- [ ] Entra ID join AI workstation under Geopixi tenant
- [ ] Apply workload-specific Intune device compliance profiles
- [ ] Confirm ESRI license server is accessible within Zone 3 only
- [ ] Pin GPU driver, CUDA, and ROCm versions before workload deployment
- [ ] Enable audit logging for all privileged workload access

---

## Appendix A — DNS TXT Record Setup for Azure Entra ID Verification

> **Browser note:** Use **Firefox for all steps in this appendix.**
> The handoff from Google Admin Console to the Squarespace DNS editor
> is unstable in Edge — Firefox handles the redirect cleanly.

### Before You Start — Get the Azure TXT Value First

Complete Steps 1–3 of Section 7 (create Geopixi tenant, initiate `geopixi.com` custom domain
addition) in Entra Admin Center before touching DNS. Azure will display a verification record
in this format:

| Field | Value |
|---|---|
| Record type | TXT |
| Name / Host | `@` |
| Value | `MS=msXXXXXXXX` (unique — copy exactly as shown) |

Copy that value, then switch to Firefox.

---

### Step A1 — You Are Already Here

You are on the **Domains Overview** screen in Google Workspace Admin Console (`admin.google.com`),
showing:

```
Primary domain
geopixi.com

Manage domains  |  Add a domain  |  Change your primary domain
```

This is the correct starting point.

---

### Step A2 — Click "Manage Domains"

Click the **Manage domains** link. This opens the full domain list view with per-domain
options for `geopixi.com`.

---

### Step A3 — Find the DNS Link for geopixi.com

In the Manage Domains list, locate the `geopixi.com` row. Look for one of these links:

- **View DNS records**
- **Manage DNS**
- **Go to registrar**

Click whichever appears. Because Google Domains migrated to Squarespace in 2024, this link
opens `domains.squarespace.com` in Firefox and authenticates you automatically via your
Google account — no separate Squarespace login required.

> ⚠️ If this step crashes in Edge, switch to Firefox — this is the known redirect that
> causes Edge instability at this exact step.

---

### Step A4 — Add the TXT Record in the Squarespace DNS Editor

Once inside the Squarespace DNS editor for `geopixi.com`:

1. Scroll to **Custom Records**
2. Click **Add record**
   *(You may be prompted to re-enter your password or a 2FA code — expected for DNS changes)*
3. Fill in the fields:

| Field | What to Enter |
|---|---|
| Type | Select **TXT** from the dropdown |
| Name / Host | `@` |
| Value | Paste the `MS=msXXXXXXXX` value copied from Azure |

4. Click **Save**

---

### Step A5 — Confirm Propagation Before Returning to Azure

Open a new tab in Firefox and go to `https://dnschecker.org`:

1. Select record type **TXT**
2. Enter `geopixi.com` and search
3. Look for your `MS=ms...` value appearing across global nodes

Propagation via Squarespace is typically **minutes to 1 hour**. Once the record shows
live on dnschecker.org, Azure will verify immediately.

---

### Step A6 — Return to Entra Admin Center and Verify

Back in the Geopixi Entra tenant (Edge is fine from here):

> **Identity → Settings → Domain names → geopixi.com → Verify**

Once verified, click **Make primary**.

---

### Existing Google Workspace DNS Records — Leave Untouched

| Record | Type | Action |
|---|---|---|
| `ASPMX.L.GOOGLE.COM` and alternates | MX | ✅ Do not touch |
| `v=spf1 include:_spf.google.com ~all` | TXT | ✅ Do not touch |
| `google-site-verification=...` | TXT | ✅ Do not touch |
| `google._domainkey...` (DKIM) | TXT | ✅ Do not touch |
| `MS=msXXXXXXXX` | TXT | ✅ Add this as a new record only |

---

### Troubleshooting

| Issue | Fix |
|---|---|
| No DNS / registrar link next to geopixi.com in Manage Domains | Scroll right — it may be hidden; or click the domain name itself for expanded options |
| Edge crashes on the Squarespace redirect | Switch to Firefox — confirmed behavior at this specific step |
| Squarespace asks for password again on Save | Expected — re-auth required for all DNS changes |
| Azure Verify fails after 1+ hour | Check dnschecker.org for the TXT record; if missing, confirm the value was saved without extra spaces |
| geopixi.com not visible in Squarespace dashboard | Confirm you are signed in with the Google account that originally owned the Google Domains registration |

---

### Weekend Browser Reference

| Step | Location | Browser |
|---|---|---|
| Create Geopixi tenant, get `MS=ms...` TXT value | Entra Admin Center (`entra.microsoft.com`) | Edge |
| Manage domains → geopixi.com → View DNS records | Google Admin Console (`admin.google.com`) | Firefox |
| Add TXT record in Squarespace DNS editor | `domains.squarespace.com` (auto-redirect) | Firefox |
| Confirm propagation | `dnschecker.org` | Firefox |
| Verify domain, set as primary, create admin account | Entra Admin Center (`entra.microsoft.com`) | Edge |

---

*End of document. No cross-zone migration plan is included. OHGIS tenant is stable and out of scope.*
