# AgriLoop: Operational Workflow & Logistics Overview

## 1. Introduction
AgriLoop is a digital agricultural residue platform designed to bridge the gap between individual farmers (sellers) and corporate hubs/biomass operators (buyers). The platform ensures traceability, quality assessment, and fair, direct payouts. 

This document outlines the end-to-end operational flow and clarifies the role of logistics within the AgriLoop ecosystem.

---

## 2. The Operational Workflow: How Things Work

The AgriLoop system is heavily specialized into role-locked applications to ensure data integrity and ease of use. The flow is as follows:

### Step 1: Secure Onboarding
* **Identity Lock**: Both farmers and company operators securely log in via an Email/OTP authentication system. The app uses a local database (`IndexedDB`) to persist sessions and lock users into their respective views—preventing operators from accessing farmer dashboards and vice versa.

### Step 2: Harvesting & Baling (Operator Side)
* **Telemetry Sync**: Contracted baler operators (acting on behalf of the company/hub) arrive at the registered farmer's field. The operator uses the **Baler Operator Hub**.
* **Data Capture**: The operator's machine captures real-time RTK GPS coordinates. The operator manually validates the core moisture percentage and bale density via the mobile interface.
* **Certificate Issuance**: Once the load is verified, the operator triggers the API pipeline. This generates a secure Digital Certificate (QR Code) linking the crop residue directly to the farmer.

### Step 3: Virtual Pooling & E-Way Bill (Logistics Side)
* **Risk Scoring**: The backend AI evaluates the bale data (moisture, density, location) and assigns it to a "Virtual Risk Pool".
* **Transit Compliance**: For transportation to the processing facility, an automated E-Way Bill is generated to ensure legal compliance during transit.

### Step 4: Traceability & Payouts (Farmer Side)
* **Real-time Ledger**: The farmer logs into the **Farmer Dashboard**. They do not see machine telemetry; instead, they see the exact verified net weight of their crop.
* **Chain-of-Custody**: A 4-step timeline shows exactly where their crop is in the process (Certificate Created → Risk Pool Assigned → Quality Verified → Payment Settled).
* **Direct Payout**: Once the quality is verified and the pool is confirmed, a direct payment (via DBT) is triggered to the farmer. The banner highlights their accrued payout.

---

## 3. Logistics Clarification: Contract vs. Quick Commerce

**AgriLoop's logistics model is strictly Contract-Based and deeply integrated with industrial transport networks.** 

It does **not** act like a "Quick Commerce" delivery partner (e.g., Swiggy, Zepto, or Uber Connect).

### Why a Contract-Based Model is Required:

1. **Volume & Equipment**: Agricultural residue (like paddy straw) is transported in massive, high-density industrial bales. This requires heavy-duty flatbed trucks and specialized loaders, not independent gig-economy riders.
2. **Predictable Supply Chains**: Biomass plants and biofuel refineries rely on a steady, forecasted supply of raw materials. Logistics must be scheduled and contracted in advance to match the processing capacity of the hubs.
3. **Legal Compliance (E-Way Bills)**: The movement of large commercial quantities across state or district lines requires strict adherence to E-Way bill regulations, which necessitates registered, contracted transport vendors rather than ad-hoc deliveries.
4. **Quality Degradation**: Unlike delivering hot food in 10 minutes, biomass logistics is about minimizing moisture exposure and fire risks over multi-day transit periods. Contracted logistics companies provide the necessary industrial tarping and secure transport environments.

In short, the operators in the field (balers) and the logistics teams (transporters) operate under dedicated B2B contracts with the central AgriLoop Hub to ensure compliance, scale, and safety.
