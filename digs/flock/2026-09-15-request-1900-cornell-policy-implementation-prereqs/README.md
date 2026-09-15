# Request #1900 — Cornell Flock policy-implementation prerequisites

Worker 4/8 bounded continuation pass.

## Added in this slice

Cornell's current University Policy 8.1 requires cameras to be integrated into the university's centralized security-video system unless an exemption is granted and makes that centralized surface viewable by the Division of Public Safety Communications Center, Cornell University Police Department, and the Access Control Program.

An official Cornell Design and Construction Standard, `281316 — Electronic Safety and Security Systems` (June 23, 2023), supplies a more concrete implementation/control trail for university security-camera work: Access Control Program setup includes camera configuration/labeling, device hardening, user/password configuration, and creation of a device instance in the video-management software; the building/unit Network Video Surveillance System Operator (NVSSO) approves camera views after commissioning; and local-management access is not granted until training plus authorization/activation forms are completed.

Primary sources:

- https://policy.cornell.edu/policy-library/physical-security-systems
- https://fcs.cornell.edu/sites/default/files/2023-08/281316_Electronic%20Safety%20and%20Security_2023.06.23.pdf

## Evidence boundary

This pass **does not** assert that Cornell's seven reported Flock readers are actually integrated into the centralized video-management system, that the 2023 construction standard governed their October 2024 deployment, that a specific NVSSO held Flock credentials, or that any named person had platform access. Those remain implementation questions.

Instead, the sources narrow the evidence request for #1900. If the Flock readers were integrated under the university security-video regime, the relevant native records should include the integration/exemption decision, authorization and activation forms, NVSSO designation/training records, camera/device commissioning records, video-management-system instances, and Access Control Program configuration records. If the readers were exempted or otherwise outside that implementation path, the exemption or alternate control record is the evidence needed.

## Remaining issue #1900 gaps

- executed Flock contract/order form, invoices, renewal/support terms;
- complete seven-reader serial/location/model/activation inventory;
- evidence that the readers are integrated into the centralized security-video system or the applicable exemption/alternate implementation record;
- NVSSO / authorized-user / administrator records actually tied to the Flock deployment;
- native Flock configured-retention history and deletion execution;
- Organization Audit, Network Audit, SharedNetworks and event/configuration exports;
- proof or disproof of any directed CUPD ↔ Ithaca Police access edge.

Canonical machine-readable records are in `starintel-documents.jsonl`. This packet reuses the existing Cornell organization and investigation-target identities and creates no new camera, user, administrator, or sharing-edge identity.