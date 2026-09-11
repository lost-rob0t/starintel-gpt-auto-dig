# Election communications ecosystem pass 42 — The Movement Cooperative

## Scope

Bounded public-web enumeration pass for the `anarchist-violence` corpus focused on previously uncovered 2026 shared progressive data, organizing, voter-contact, identity-resolution and communications infrastructure around The Movement Cooperative (TMC). This pass favors current first-party technical and governance material and preserves reported versus directly stated edges.

## Materialized graph

The packet contains 26 canonical StarIntel v0.9 records: 9 sources, 3 organizations, 4 products, 4 public professional people, 5 explicit professional/governance/partnership relations, 1 explicit infrastructure relation, and 1 recursive investigation target.

## Shared infrastructure

Current TMC material describes a member-led cooperative providing shared data infrastructure, engineering, analytics, research, trainings, tool strategy and access to voter-contact technologies for almost 90 national/state members and more than 1,400 affiliates. A March 2026 first-party article describes the connective layer as linking tools used for email, text, volunteers and other organizing workflows.

TMC's June 2026 engineering material identifies Haven as its proprietary member data warehouse, built on Google BigQuery, and describes members syncing data from more than 70 tools. It documents modular transformation and connector infrastructure, with common destination examples including EveryAction and Action Network. The August 2026 election-readiness article separately describes 175+ ingestion/reverse-ETL pipelines and 6,600+ dbt models.

## Identity resolution

The March 2026 TMC engineering article describes Compass as a member-exclusive transformation layer and IDR as a statistical identity-resolution system used to reconcile profiles from multiple vendor datasets. The packet represents both as TMC products and does not materialize individual supporter/voter records.

## 2026 election products

A public Action Network event page for TMC's June 24, 2026 Election Products Release describes targeting data, polling-place and campus-precinct assets, scores, historical election results and a GOTV-focused Voter Status List. The Voter Status List is materialized as a product because the public event directly identifies it as a discrete election-season list-pulling tool.

## Action Network partnership

Campaigns & Elections reported on February 11, 2026 that TMC and Action Network partnered to provide organizing and fundraising tools to TMC members. Because this edge is reported by reputable industry press rather than a first-party TMC announcement retrieved in this run, the relation retains a slightly lower confidence than direct first-party relations.

## Governance and fiscal structure

TMC's current privacy notice states that TMC executes the strategy, planning and mission of The Movement Institute Fund (TMIF), and that TMIF is a fund of Tides Foundation. Tides' July 22, 2026 profile describes TMC as operating through Model C / single-entity-fund fiscal sponsorship and identifies Julia Barnes as CEO.

## Public people

The pass materializes current public professional records for Julia Barnes (CEO), Bella Wang (CTO), Reta Gasser (Senior Manager, Solutions and Analytics Engineering) and Cody Braun (Staff Data Engineer). Each role is tied to current 2026 first-party or fiscal-sponsor material.

## Recursive frontier

The queued target expands into publicly disclosed TMC members and affiliates, governance boards/delegates, current vendor integrations and Marketplace offerings, next-generation voter-contact pilots, public trainings/events and observable data → email/text/phone/field/relational-organizing pathways. It explicitly excludes private supporter/voter records, CRM contents, credentials, nonpublic member data and private delivery logs.

## Dedupe

Repository search on current `main` returned no exact indexed record for `The Movement Cooperative` before this pass. Existing canonical `starintel:org:action-network` is reused for the 2026 partnership edge rather than duplicated.
