# Data Processing Agreement

> DRAFT — prepared with AI assistance, not reviewed by an attorney, not effective until counsel approval and placeholder facts are finalized.

Effective date: [DPA_EFFECTIVE_DATE]. Related MSA/SOW: [AGREEMENT_REFERENCES].

## 1. Parties, roles and scope

Client: [CLIENT_LEGAL_NAME], address [CLIENT_ADDRESS], privacy contact [CLIENT_PRIVACY_CONTACT]. Consultant: [LEGAL_ENTITY_NAME], [ENTITY_TYPE] formed in [FORMATION_STATE], principal address 17 Ridgeway Drive, Cataula, GA 31804, privacy contact jacobstarling4313@gmail.com, incident contact jacobstarling4313@gmail.com. White Oak Operations is the selected working company name, pending trademark, entity-name, domain, and common-law clearance. Consultant operates from Georgia and initially serves New York clients.

For covered personal data processed only on Client's documented instructions, Client acts as controller/business and Consultant as processor/service provider to the extent those roles apply under the governing law. Client's upstream processor role, if any, and required authorizations must be recorded in Annex A. Consultant's independent administration of its own invoices, contacts, and legally required records is outside this processor scope and must be addressed in its privacy notice and applicable law. This DPA controls data-processing conflicts with the MSA. It does not determine that GDPR, a particular state statute, or HIPAA applies.

## 2. Instructions and authorized use

Consultant processes covered data only for the signed SOW and Annex A purposes, or binding legal requirements. It promptly informs Client if an instruction appears unlawful and pauses the affected processing pending resolution. Client is responsible for lawful collection, notices, permissions and instructions; Consultant remains responsible for its own obligations. Consultant may not sell covered data, use it for targeted advertising, combine it for unrelated purposes, or train shared/general-purpose AI models on it. Any proposed new use requires a separate lawful agreement; a general website consent is insufficient.

The parties will minimize inputs, prefer synthetic or de-identified test data, and restrict production data to approved accounts and locations. Re-identification of de-identified data is prohibited except an expressly authorized, lawful security/quality test. PHI, payment-card data, sensitive financial identifiers, biometric data and special-category data are excluded unless specifically approved with necessary additional agreements and controls. This document is not a business associate agreement or an international-transfer instrument.

## 3. Confidentiality and security

Authorized personnel must have confidentiality obligations, role-based access and training appropriate to their duties. Consultant must implement Annex B before receiving covered data, review access periodically, and remove access promptly on role changes or offboarding. No claim of certification is made. Consultant will not materially weaken agreed safeguards without prior written agreement and a documented risk assessment.

## 4. Subprocessors and AI providers

Only the named, approved subprocessors in Annex C may process covered data. Consultant remains responsible for their contracted performance and must impose materially equivalent data-protection obligations. Proposed additions or replacements require written notice at least [SUBPROCESSOR_NOTICE_DAYS] days in advance, identifying data, purpose, locations, retention and transfer safeguards. Client may reasonably object on data-protection grounds; the parties seek an alternative and, if none is available, terminate the affected scope with the MSA settlement procedure. No new subprocessor receives data before required authorization.

OpenAI, Anthropic, automation vendors and document tools are not approved merely because services involve AI. Vercel, Stripe, Resend and Upstash are planned website/administration providers; whether any acts as a subprocessor for Client data depends on the actual data flow and must be documented, not assumed.

## 5. Incidents

A personal-data incident means a confirmed or reasonably suspected unauthorized disclosure, access, loss, alteration or destruction affecting covered data, not every unsuccessful attack. Consultant notifies [CLIENT_INCIDENT_CONTACT] without undue delay after awareness and within [CONTRACTUAL_INCIDENT_NOTICE_HOURS] hours at the latest, subject to any shorter mandatory deadline. Initial notice need not await a complete investigation. It includes known facts, affected categories, likely consequences, containment actions, contact person and next-update timing; supplementary information follows as available.

Consultant will contain, investigate, preserve relevant evidence, mitigate and cooperate. Client coordinates notices to affected individuals and regulators for its controller role unless law requires otherwise. Neither party may prevent the other from satisfying independent legal duties. Notification is not itself an admission of liability. Allocation of incident costs follows the counsel-approved MSA, not an unstated unlimited reimbursement promise.

## 6. Assistance and oversight

Consultant promptly forwards requests from individuals concerning covered data and assists Client with access, correction, deletion, portability and other applicable rights, verification, risk assessments and regulator inquiries. It will not independently deny a request on Client's behalf unless instructed and lawful. Assistance already included in the SOW carries no additional fee; extraordinary work requires an agreed change order except urgent mandatory action cannot be delayed solely over a fee dispute.

Consultant provides reasonably necessary compliance information and permits proportionate audits on [AUDIT_NOTICE_PERIOD], ordinarily no more than [ROUTINE_AUDIT_FREQUENCY], with exceptions for material incidents, credible noncompliance or regulator requirements. Audits protect other clients, secrets and system availability. Cost allocation: [AUDIT_COST_ALLOCATION]. Findings require a documented remediation plan; certification or self-attestation alone is not conclusive.

## 7. Return, deletion and transfers

On completion or termination, at Client's choice Consultant returns or securely deletes covered data within [RETURN_DELETION_PERIOD], including subprocessor copies where required, and provides written confirmation. Client-controlled production accounts are transferred, not destroyed. Legally required retention is identified, isolated and purpose-limited. Backups expire within [BACKUP_EXPIRY_PERIOD] and are not restored for ordinary use; if restored for recovery, deletion instructions are reapplied.

Processing countries, remote-access countries, hosting regions and approved transfer mechanisms are recorded in Annex C. No restricted international transfer is authorized until counsel determines the applicable mechanism, executes required instruments and completes required assessments. These clauses do not substitute for standard contractual clauses or another mandated instrument.

## Annex A — Processing particulars (complete before data access)

| Item | Required entry |
| --- | --- |
| Subject matter and signed workflow scope | [PROCESSING_SUBJECT_AND_SCOPE] |
| Duration and deletion trigger | [PROCESSING_DURATION] |
| Client role and upstream authorization | [CLIENT_ROLE_AND_AUTHORITY] |
| Data subjects | [DATA_SUBJECT_CATEGORIES] |
| Personal-data fields and sensitivity | [PERSONAL_DATA_CATEGORIES] |
| Purpose and operations | [PROCESSING_PURPOSE_AND_OPERATIONS] |
| Frequency and scale | [PROCESSING_FREQUENCY_AND_VOLUME] |
| Permitted sources and destinations | [APPROVED_DATA_FLOWS] |
| Applicable laws and required supplements | [APPLICABLE_DATA_PROTECTION_LAWS] |

## Annex B — Minimum controls and evidence

The following are proposed contractual requirements, not assertions of completed implementation. Before access, record the control owner, evidence and exceptions in [SECURITY_CONTROL_VERIFICATION_RECORD].

- MFA for administrative access; individual accounts; least privilege; periodic access review.
- Encryption in transit and at rest where supported; secrets stored server-side in approved secret management; no secrets in prompts, repositories or logs.
- Approved-tool register documenting retention/training settings, accounts, locations and data restrictions.
- Separate test/production environments; synthetic test data; human approval for external actions and high-impact output.
- Security logging that minimizes personal data; monitored failures; documented incident response and escalation.
- Patch/change management, tested backups where needed, recovery/rollback ownership and secure offboarding.
- Secure deletion, limited export permissions, and documented subprocessor due diligence.

Unmet required controls block affected processing unless a lawful written alternative is agreed; they are not silently waived by payment.

## Annex C — Approved subprocessors and locations

| Legal provider name | Function/data | Processing and access countries | Account/settings/retention | Authorization and transfer basis |
| --- | --- | --- | --- | --- |
| [SUBPROCESSOR_LEGAL_NAME_OR_NONE] | [FUNCTION_AND_DATA] | [COUNTRIES_AND_REGIONS] | [ACCOUNT_CONTROLS_AND_RETENTION] | [APPROVAL_AND_TRANSFER_MECHANISM] |

Add one row per actual authorized provider. An uncompleted row authorizes none.

## Signatures and counsel decisions

Consultant signer/title/signature/date: [CONSULTANT_SIGNATURE_BLOCK]. Client signer/title/signature/date: [CLIENT_SIGNATURE_BLOCK]. Governing law: [GOVERNING_LAW]. Venue: [DISPUTE_VENUE]. Counsel approval: [COUNSEL_APPROVAL_RECORD].

Counsel must review every clause and annex, legal roles, applicability, restricted-data exclusions, state contract requirements, breach deadlines, audit rights, liability, retention and cross-border instruments. New York client geography alone does not settle the analysis. Reference: [New York Attorney General data-breach resources](https://ag.ny.gov/resources/organizations/data-breach-reporting).
