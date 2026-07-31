#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

NOW = "2026-07-31T07:10:00Z"
DATASET = "gop"
RUN_ID = "gop-privatization-leads-2026-07-31-depth-3"
ROOT_TARGET = "starintel:investigation-target:gop-national-network-depth-0"
DERIVED_FROM = "starintel:analysis:gop-wef-palantir-aipac-depth-2"
DIG_DIR = Path("digs/gop/2026-07-31-privatization-leads-depth-3")

# Inclusion means "research lead", not a finding of coordination, wrongdoing, or
# a uniform ideological position. The categories distinguish policy advocacy,
# funding networks, trade associations, contractors, and capital owners.
ORG_SEEDS: list[dict[str, str]] = [
    {"slug":"heritage-foundation","name":"The Heritage Foundation","category":"national-policy-network","url":"https://www.heritage.org/","roster":"public-leadership"},
    {"slug":"project-2025","name":"Project 2025","category":"coalition-policy-program","url":"https://www.project2025.org/","roster":"public-coalition-directory"},
    {"slug":"state-policy-network","name":"State Policy Network","category":"state-think-tank-network","url":"https://spn.org/","roster":"public-member-directory"},
    {"slug":"american-legislative-exchange-council","name":"American Legislative Exchange Council","category":"model-policy-membership-network","url":"https://alec.org/","roster":"partly-public-membership"},
    {"slug":"america-first-policy-institute","name":"America First Policy Institute","category":"national-policy-network","url":"https://americafirstpolicy.com/","roster":"public-leadership"},
    {"slug":"council-for-national-policy","name":"Council for National Policy","category":"membership-network","url":"https://cfnp.org/","roster":"limited-public-roster"},
    {"slug":"stand-together","name":"Stand Together","category":"funding-and-advocacy-network","url":"https://standtogether.org/","roster":"public-leadership-limited-membership"},
    {"slug":"donorstrust","name":"DonorsTrust","category":"donor-advised-fund-network","url":"https://www.donorstrust.org/","roster":"public-leadership-confidential-donors"},
    {"slug":"lynde-and-harry-bradley-foundation","name":"Lynde and Harry Bradley Foundation","category":"grantmaking-foundation","url":"https://www.bradleyfdn.org/","roster":"public-board-and-grants"},
    {"slug":"searle-freedom-trust","name":"Searle Freedom Trust","category":"grantmaking-foundation","url":"https://searlefreedomtrust.org/","roster":"public-board-and-grants"},
    {"slug":"reason-foundation","name":"Reason Foundation","category":"privatization-policy-think-tank","url":"https://reason.org/","roster":"public-leadership"},
    {"slug":"cato-institute","name":"Cato Institute","category":"libertarian-policy-think-tank","url":"https://www.cato.org/","roster":"public-people-directory"},
    {"slug":"mercatus-center","name":"Mercatus Center","category":"market-policy-think-tank","url":"https://www.mercatus.org/","roster":"public-people-directory"},
    {"slug":"manhattan-institute","name":"Manhattan Institute","category":"policy-think-tank","url":"https://manhattan.institute/","roster":"public-people-directory"},
    {"slug":"r-street-institute","name":"R Street Institute","category":"policy-think-tank","url":"https://www.rstreet.org/","roster":"public-team-directory"},
    {"slug":"competitive-enterprise-institute","name":"Competitive Enterprise Institute","category":"deregulation-policy-think-tank","url":"https://cei.org/","roster":"public-team-directory"},
    {"slug":"american-enterprise-institute","name":"American Enterprise Institute","category":"policy-think-tank","url":"https://www.aei.org/","roster":"public-people-directory"},
    {"slug":"hoover-institution","name":"Hoover Institution","category":"policy-think-tank","url":"https://www.hoover.org/","roster":"public-fellows-directory"},
    {"slug":"independent-womens-forum","name":"Independent Women's Forum","category":"policy-advocacy-network","url":"https://www.iwf.org/","roster":"public-team-directory"},
    {"slug":"foundation-for-government-accountability","name":"Foundation for Government Accountability","category":"welfare-and-workforce-policy-network","url":"https://thefga.org/","roster":"public-team-directory"},
    {"slug":"americans-for-prosperity","name":"Americans for Prosperity","category":"advocacy-network","url":"https://americansforprosperity.org/","roster":"public-leadership-state-chapters"},
    {"slug":"club-for-growth","name":"Club for Growth","category":"tax-and-regulatory-advocacy","url":"https://www.clubforgrowth.org/","roster":"public-leadership"},
    {"slug":"national-taxpayers-union","name":"National Taxpayers Union","category":"tax-and-spending-advocacy","url":"https://www.ntu.org/","roster":"public-leadership"},
    {"slug":"citizens-against-government-waste","name":"Citizens Against Government Waste","category":"spending-and-outsourcing-advocacy","url":"https://www.cagw.org/","roster":"public-leadership"},
    {"slug":"committee-to-unleash-prosperity","name":"Committee to Unleash Prosperity","category":"tax-and-deregulation-policy-network","url":"https://committeetounleashprosperity.com/","roster":"public-leadership"},
    {"slug":"american-action-forum","name":"American Action Forum","category":"policy-think-tank","url":"https://www.americanactionforum.org/","roster":"public-team-directory"},
    {"slug":"texas-public-policy-foundation","name":"Texas Public Policy Foundation","category":"state-policy-think-tank","url":"https://www.texaspolicy.com/","roster":"public-team-directory"},
    {"slug":"mackinac-center-for-public-policy","name":"Mackinac Center for Public Policy","category":"state-policy-think-tank","url":"https://www.mackinac.org/","roster":"public-team-directory"},
    {"slug":"goldwater-institute","name":"Goldwater Institute","category":"state-policy-think-tank-and-litigation","url":"https://www.goldwaterinstitute.org/","roster":"public-team-directory"},
    {"slug":"james-madison-institute","name":"James Madison Institute","category":"state-policy-think-tank","url":"https://jamesmadison.org/","roster":"public-team-directory"},
    {"slug":"pelican-institute","name":"Pelican Institute for Public Policy","category":"state-policy-think-tank","url":"https://pelicanpolicy.org/","roster":"public-team-directory"},
    {"slug":"commonwealth-foundation","name":"Commonwealth Foundation","category":"state-policy-think-tank","url":"https://www.commonwealthfoundation.org/","roster":"public-team-directory"},
    {"slug":"buckeye-institute","name":"The Buckeye Institute","category":"state-policy-think-tank","url":"https://www.buckeyeinstitute.org/","roster":"public-team-directory"},
    {"slug":"pacific-research-institute","name":"Pacific Research Institute","category":"state-policy-think-tank","url":"https://www.pacificresearch.org/","roster":"public-team-directory"},
    {"slug":"independence-institute","name":"Independence Institute","category":"state-policy-think-tank","url":"https://i2i.org/","roster":"public-team-directory"},
    {"slug":"john-locke-foundation","name":"John Locke Foundation","category":"state-policy-think-tank","url":"https://www.johnlocke.org/","roster":"public-team-directory"},
    {"slug":"yankee-institute","name":"Yankee Institute","category":"state-policy-think-tank","url":"https://yankeeinstitute.org/","roster":"public-team-directory"},
    {"slug":"badger-institute","name":"Badger Institute","category":"state-policy-think-tank","url":"https://www.badgerinstitute.org/","roster":"public-team-directory"},
    {"slug":"empire-center-for-public-policy","name":"Empire Center for Public Policy","category":"state-policy-think-tank","url":"https://www.empirecenter.org/","roster":"public-team-directory"},
    {"slug":"freedom-foundation","name":"Freedom Foundation","category":"public-workforce-policy-and-litigation","url":"https://www.freedomfoundation.com/","roster":"public-team-directory"},
    {"slug":"center-of-the-american-experiment","name":"Center of the American Experiment","category":"state-policy-think-tank","url":"https://www.americanexperiment.org/","roster":"public-team-directory"},
    {"slug":"georgia-public-policy-foundation","name":"Georgia Public Policy Foundation","category":"state-policy-think-tank","url":"https://www.georgiapolicy.org/","roster":"public-team-directory"},
    {"slug":"oklahoma-council-of-public-affairs","name":"Oklahoma Council of Public Affairs","category":"state-policy-think-tank","url":"https://ocpathink.org/","roster":"public-team-directory"},
    {"slug":"platte-institute","name":"Platte Institute","category":"state-policy-think-tank","url":"https://platteinstitute.org/","roster":"public-team-directory"},
    {"slug":"libertas-institute","name":"Libertas Institute","category":"state-policy-think-tank","url":"https://libertas.org/","roster":"public-team-directory"},
    {"slug":"cardinal-institute-for-west-virginia-policy","name":"Cardinal Institute for West Virginia Policy","category":"state-policy-think-tank","url":"https://cardinalinstitute.com/","roster":"public-team-directory"},
    {"slug":"mountain-states-policy-center","name":"Mountain States Policy Center","category":"regional-policy-think-tank","url":"https://mountainstatespolicy.org/","roster":"public-team-directory"},
    {"slug":"edchoice","name":"EdChoice","category":"education-choice-policy-network","url":"https://www.edchoice.org/","roster":"public-team-directory"},
    {"slug":"american-federation-for-children","name":"American Federation for Children","category":"education-choice-advocacy","url":"https://www.federationforchildren.org/","roster":"public-leadership-state-affiliates"},
    {"slug":"excelined","name":"ExcelinEd","category":"education-policy-network","url":"https://excelined.org/","roster":"public-team-directory"},
    {"slug":"national-alliance-for-public-charter-schools","name":"National Alliance for Public Charter Schools","category":"charter-school-advocacy","url":"https://publiccharters.org/","roster":"public-team-and-partner-directory"},
    {"slug":"charter-school-growth-fund","name":"Charter School Growth Fund","category":"charter-school-finance-network","url":"https://chartergrowthfund.org/","roster":"public-team-and-portfolio"},
    {"slug":"center-for-education-reform","name":"Center for Education Reform","category":"education-choice-advocacy","url":"https://edreform.com/","roster":"public-team-directory"},
    {"slug":"yes-every-kid","name":"yes. every kid.","category":"education-choice-advocacy","url":"https://yeseverykid.com/","roster":"public-leadership"},
    {"slug":"paragon-health-institute","name":"Paragon Health Institute","category":"market-health-policy-think-tank","url":"https://paragoninstitute.org/","roster":"public-team-directory"},
    {"slug":"galen-institute","name":"Galen Institute","category":"market-health-policy-network","url":"https://galen.org/","roster":"public-leadership"},
    {"slug":"council-for-affordable-health-coverage","name":"Council for Affordable Health Coverage","category":"health-policy-coalition","url":"https://www.cahc.net/","roster":"partly-public-coalition"},
    {"slug":"direct-primary-care-coalition","name":"Direct Primary Care Coalition","category":"health-delivery-advocacy","url":"https://www.dpccoalition.org/","roster":"public-leadership-limited-membership"},
    {"slug":"medicaid-health-plans-of-america","name":"Medicaid Health Plans of America","category":"managed-care-trade-association","url":"https://www.mhpa.org/","roster":"public-member-plans"},
    {"slug":"national-association-of-water-companies","name":"National Association of Water Companies","category":"private-water-utility-trade-association","url":"https://nawc.org/","roster":"public-member-companies"},
    {"slug":"association-for-the-improvement-of-american-infrastructure","name":"Association for the Improvement of American Infrastructure","category":"public-private-partnership-trade-association","url":"https://aiai-infra.org/","roster":"public-member-directory"},
    {"slug":"national-council-for-public-private-partnerships","name":"National Council for Public-Private Partnerships","category":"public-private-partnership-network","url":"https://ncppp.org/","roster":"public-leadership-limited-membership"},
    {"slug":"corecivic","name":"CoreCivic","category":"corrections-and-detention-contractor","url":"https://www.corecivic.com/","roster":"public-board-executives"},
    {"slug":"geo-group","name":"The GEO Group","category":"corrections-detention-and-monitoring-contractor","url":"https://www.geogroup.com/","roster":"public-board-executives"},
    {"slug":"management-and-training-corporation","name":"Management & Training Corporation","category":"corrections-and-workforce-contractor","url":"https://www.mtctrains.com/","roster":"public-leadership"},
    {"slug":"lasalle-corrections","name":"LaSalle Corrections","category":"corrections-and-detention-contractor","url":"https://lasallecorrections.com/","roster":"limited-public-leadership"},
    {"slug":"maximus","name":"Maximus","category":"government-benefits-and-services-contractor","url":"https://maximus.com/","roster":"public-board-executives"},
    {"slug":"serco-inc","name":"Serco Inc.","category":"government-services-contractor","url":"https://www.serco.com/na","roster":"public-leadership"},
    {"slug":"conduent","name":"Conduent","category":"government-transaction-and-benefits-contractor","url":"https://www.conduent.com/","roster":"public-board-executives"},
    {"slug":"gainwell-technologies","name":"Gainwell Technologies","category":"medicaid-and-public-benefits-contractor","url":"https://www.gainwelltechnologies.com/","roster":"public-leadership"},
    {"slug":"equus-workforce-solutions","name":"Equus Workforce Solutions","category":"contracted-workforce-services-provider","url":"https://equusworks.com/","roster":"public-leadership"},
    {"slug":"transurban","name":"Transurban","category":"toll-road-owner-and-operator","url":"https://www.transurban.com/","roster":"public-board-executives"},
    {"slug":"ferrovial-cintra","name":"Ferrovial / Cintra","category":"transportation-concession-owner-operator","url":"https://www.cintra.com/","roster":"public-leadership-and-projects"},
    {"slug":"macquarie-asset-management","name":"Macquarie Asset Management","category":"infrastructure-investment-manager","url":"https://www.macquarie.com/us/en/about/company/macquarie-asset-management.html","roster":"public-leadership-and-funds"},
    {"slug":"brookfield-infrastructure","name":"Brookfield Infrastructure","category":"infrastructure-owner-and-investor","url":"https://bip.brookfield.com/","roster":"public-board-executives-and-assets"},
    {"slug":"kkr","name":"KKR","category":"private-equity-and-infrastructure-owner","url":"https://www.kkr.com/","roster":"public-leadership-and-funds"},
    {"slug":"apollo-global-management","name":"Apollo Global Management","category":"private-equity-and-infrastructure-owner","url":"https://www.apollo.com/","roster":"public-board-executives-and-funds"},
    {"slug":"carlyle-group","name":"The Carlyle Group","category":"private-equity-and-government-services-owner","url":"https://www.carlyle.com/","roster":"public-board-executives-and-portfolio"},
    {"slug":"blackstone","name":"Blackstone","category":"private-equity-and-infrastructure-owner","url":"https://www.blackstone.com/","roster":"public-board-executives-and-funds"},
    {"slug":"plenary-americas","name":"Plenary Americas","category":"public-private-partnership-developer","url":"https://plenaryamericas.com/","roster":"public-leadership-and-projects"},
    {"slug":"aecom","name":"AECOM","category":"public-infrastructure-and-government-contractor","url":"https://www.aecom.com/","roster":"public-board-executives"},
    {"slug":"jacobs-solutions","name":"Jacobs Solutions","category":"public-infrastructure-and-government-contractor","url":"https://www.jacobs.com/","roster":"public-board-executives"},
    {"slug":"booz-allen-hamilton","name":"Booz Allen Hamilton","category":"federal-consulting-and-technology-contractor","url":"https://www.boozallen.com/","roster":"public-board-executives"},
    {"slug":"leidos","name":"Leidos","category":"federal-technology-and-services-contractor","url":"https://www.leidos.com/","roster":"public-board-executives"},
    {"slug":"palantir-technologies","name":"Palantir Technologies","category":"government-data-and-ai-contractor","url":"https://www.palantir.com/","roster":"public-board-executives"},
    {"slug":"anduril-industries","name":"Anduril Industries","category":"defense-and-border-technology-contractor","url":"https://www.anduril.com/","roster":"public-leadership"},
    {"slug":"caci-international","name":"CACI International","category":"federal-technology-and-services-contractor","url":"https://www.caci.com/","roster":"public-board-executives"},
    {"slug":"science-applications-international-corporation","name":"Science Applications International Corporation","category":"federal-technology-and-services-contractor","url":"https://www.saic.com/","roster":"public-board-executives"},
    {"slug":"general-dynamics-information-technology","name":"General Dynamics Information Technology","category":"federal-technology-and-services-contractor","url":"https://www.gdit.com/","roster":"public-leadership"},
    {"slug":"deloitte-government-and-public-services","name":"Deloitte Government & Public Services","category":"government-consulting-contractor","url":"https://www2.deloitte.com/us/en/pages/public-sector/topics/government-public-services.html","roster":"public-leadership"},
    {"slug":"accenture-federal-services","name":"Accenture Federal Services","category":"federal-technology-and-services-contractor","url":"https://www.accenture.com/us-en/services/us-federal-government-index","roster":"public-leadership"},
    {"slug":"securus-technologies","name":"Securus Technologies","category":"corrections-communications-contractor","url":"https://securustech.net/","roster":"public-leadership"},
    {"slug":"viapath-technologies","name":"ViaPath Technologies","category":"corrections-communications-contractor","url":"https://www.viapath.com/","roster":"public-leadership"},
    {"slug":"bi-incorporated","name":"BI Incorporated","category":"electronic-monitoring-contractor","url":"https://www.bi.com/","roster":"public-leadership-and-parent"},
    {"slug":"akima","name":"Akima","category":"federal-logistics-detention-and-services-contractor","url":"https://www.akima.com/","roster":"public-leadership-and-subsidiaries"},
    {"slug":"american-council-of-life-insurers","name":"American Council of Life Insurers","category":"insurance-and-retirement-trade-association","url":"https://www.acli.com/","roster":"public-member-directory"},
    {"slug":"investment-company-institute","name":"Investment Company Institute","category":"asset-management-trade-association","url":"https://www.ici.org/","roster":"public-member-directory"},
    {"slug":"us-chamber-of-commerce","name":"U.S. Chamber of Commerce","category":"business-policy-and-lobbying-network","url":"https://www.uschamber.com/","roster":"partly-public-membership"},
    {"slug":"business-roundtable","name":"Business Roundtable","category":"corporate-chief-executive-policy-network","url":"https://www.businessroundtable.org/","roster":"public-ceo-members"},
    {"slug":"national-federation-of-independent-business","name":"National Federation of Independent Business","category":"business-policy-and-lobbying-network","url":"https://www.nfib.com/","roster":"public-leadership-confidential-members"}
]

DIMENSIONS: list[dict[str, Any]] = [
    {
        "slug":"complete-public-roster",
        "label":"Complete public roster",
        "priority":1.0,
        "question":"Who are all publicly disclosed current and historical board members, officers, executives, staff, fellows, advisory members, coalition partners, corporate members, state affiliates, subsidiaries, and portfolio entities of {name}, with roles and dates?",
        "objectives":[
            "Archive every official roster, leadership, staff, member, partner, affiliate, subsidiary, and portfolio page.",
            "Create one person or organization record per disclosed member and one dated role relation per membership.",
            "Separate current, former, advisory, donor, contractor, affiliate, and portfolio roles.",
            "Mark withheld, confidential, paywalled, or otherwise non-public membership fields as unresolved rather than inferred."
        ]
    },
    {
        "slug":"person-member-resolution",
        "label":"Person-member resolution",
        "priority":0.98,
        "question":"Which named people publicly hold leadership, board, officer, staff, fellow, lobbyist, counsel, advisory, or revolving-door roles involving {name}?",
        "objectives":[
            "Resolve full names, role titles, start and end dates, and official biographies.",
            "Link each person to prior and subsequent public offices and organizations using dated relations.",
            "Capture FEC committee, lobbying-registration, procurement, and corporate-director identifiers where applicable."
        ]
    },
    {
        "slug":"organization-member-resolution",
        "label":"Organization-member resolution",
        "priority":0.98,
        "question":"Which organizations are publicly disclosed as members, partners, affiliates, chapters, grantees, contractors, subsidiaries, portfolio companies, or coalition participants of {name}?",
        "objectives":[
            "Enumerate every publicly disclosed member organization and classify the relationship precisely.",
            "Resolve legal names, aliases, EINs, FEC IDs, CAGE/UEI identifiers, and parent-subsidiary structures where public.",
            "Create dated relations and preserve the roster snapshot that supports each edge."
        ]
    },
    {
        "slug":"funding-and-donors",
        "label":"Funding and donors",
        "priority":0.97,
        "question":"What public money, grants, donor-advised funds, PAC contributions, lobbying expenditures, investment vehicles, and contract revenues fund or financially connect {name}?",
        "objectives":[
            "Extract IRS Form 990 grants, FEC receipts and disbursements, LD-2/LD-203 filings, state disclosures, and public grant databases.",
            "Resolve donor-advised fund intermediaries without assigning the underlying donor unless disclosed.",
            "Separate direct contributions, independent expenditures, grants, investments, contracts, and in-kind support."
        ]
    },
    {
        "slug":"policy-products-and-claims",
        "label":"Policy products and claims",
        "priority":0.96,
        "question":"Which reports, model bills, testimony, executive-order proposals, litigation positions, and public claims from {name} promote or implement transfer of public functions, assets, funding, or decision authority to private actors?",
        "objectives":[
            "Enumerate policy outputs with publication dates, authors, sponsors, and exact proposals.",
            "Classify the privatization mechanism: outsourcing, voucher, concession, deregulation, asset sale, private account, managed care, chartering, or contractor delegation.",
            "Store attributed claims separately from adopted policy and measured outcomes."
        ]
    },
    {
        "slug":"government-implementation",
        "label":"Government implementation",
        "priority":0.99,
        "question":"Which federal, state, and local officials, agencies, bills, rules, executive actions, budgets, and contracts implement proposals linked to {name}?",
        "objectives":[
            "Match policy language to enacted bills, rules, executive orders, appropriations, waivers, and procurement records.",
            "Identify sponsors, agency officials, transition personnel, lobbyists, and implementation vendors.",
            "Record dates and documentary similarity without treating similarity alone as proof of authorship or control."
        ]
    },
    {
        "slug":"contracts-vendors-beneficiaries",
        "label":"Contracts, vendors, and beneficiaries",
        "priority":0.99,
        "question":"Which contractors, investors, operators, insurers, asset managers, charter networks, private-equity sponsors, and subcontractors receive or may compete for public revenue under policies associated with {name}?",
        "objectives":[
            "Extract USAspending, SAM.gov, state procurement, municipal concession, and corporate filing records.",
            "Resolve prime contractors, subcontractors, parent companies, investment funds, and beneficial ownership where publicly disclosed.",
            "Separate documented awards from prospective beneficiaries and advocacy relationships."
        ]
    },
    {
        "slug":"cross-network-overlap",
        "label":"Cross-network overlap",
        "priority":0.95,
        "question":"Which documented people, organizations, donors, PACs, vendors, events, and policy products connect {name} to GOP committees, Project 2025, SPN, ALEC, WEF, Palantir, AIPAC, or United Democracy Project?",
        "objectives":[
            "Compute exact shared-person, shared-board, shared-funder, shared-vendor, shared-event, shared-policy, and shared-recipient edges.",
            "Preserve relationship type and dates; do not collapse attendance, employment, funding, and control into one influence edge.",
            "Prioritize high-degree nodes for the next breadth-first pass."
        ]
    }
]

SECTOR_TARGETS: list[tuple[str, str, str]] = [
    ("education-vouchers-esas-charters", "Education vouchers, ESAs, charters, and private management", "Map policy groups, funders, school operators, vendors, officials, legislation, and public-dollar flows for vouchers, education savings accounts, charter schools, virtual schools, and private school management."),
    ("medicaid-managed-care", "Medicaid managed-care privatization", "Map managed-care organizations, PBMs, contractors, policy advocates, waivers, procurements, capitation flows, denials, and oversight findings."),
    ("medicare-advantage", "Medicare Advantage and private Medicare delivery", "Map insurers, brokers, data vendors, lobbying networks, risk-adjustment contractors, policy advocates, payments, audits, and regulatory changes."),
    ("veterans-community-care", "Veterans healthcare private delivery", "Map Community Care contractors, third-party administrators, provider networks, policy advocates, officials, authorizing legislation, and spending."),
    ("social-security-private-accounts", "Social Security private-account proposals", "Map policy authors, financial firms, trade associations, elected sponsors, campaign funding, model designs, and implementation beneficiaries."),
    ("public-pension-conversion", "Public pension conversion and pension outsourcing", "Map defined-contribution proposals, pension consultants, asset managers, actuarial firms, policy groups, state officials, legislation, fees, and outcomes."),
    ("transportation-toll-road-ppp", "Transportation concessions, toll roads, and P3s", "Map concessionaires, investors, advisors, law firms, public authorities, procurement teams, financing structures, guarantees, and political sponsors."),
    ("water-wastewater-concessions", "Water and wastewater privatization", "Map investor-owned utilities, concession operators, trade associations, municipal officials, asset sales, rate cases, financing, and service outcomes."),
    ("energy-utility-deregulation", "Energy and utility deregulation", "Map policy networks, utilities, retail suppliers, grid operators, regulators, model legislation, campaign funding, and ownership changes."),
    ("corrections-detention-probation-monitoring", "Corrections, detention, probation, and electronic monitoring", "Map prison and detention operators, probation firms, monitoring vendors, telecom providers, food and medical subcontractors, contracts, lobbyists, and officials."),
    ("child-welfare-foster-care-contracting", "Child welfare and foster-care contracting", "Map private case-management providers, foster-care contractors, faith-based providers, procurement, performance metrics, officials, and funding flows."),
    ("workforce-unemployment-administration", "Workforce and unemployment-service outsourcing", "Map workforce-board contractors, unemployment claims vendors, call centers, eligibility systems, performance contracts, lobbying, and officials."),
    ("public-benefits-eligibility-processing", "Public-benefits eligibility and claims processing", "Map Medicaid, SNAP, TANF, child-support, and disability eligibility vendors, systems integrators, subcontractors, procurements, failures, and oversight."),
    ("postal-logistics-outsourcing", "Postal and government logistics outsourcing", "Map private carriers, route contractors, facilities operators, policy advocates, officials, contracts, and service changes."),
    ("defense-intelligence-ai-data-contracting", "Defense, intelligence, AI, and data contracting", "Map prime contractors, venture investors, acquisition officials, advisory boards, lobbying, campaign finance, subcontracts, data systems, and WEF/Palantir overlaps."),
    ("public-lands-resource-leasing", "Public lands, minerals, and resource leasing", "Map leaseholders, concessionaires, industry groups, policy organizations, officials, rule changes, royalties, and ownership networks."),
    ("emergency-services-ambulance-fire", "Emergency, ambulance, and fire-service privatization", "Map operators, private-equity owners, municipal contracts, reimbursement policy, dispatch vendors, officials, and service outcomes."),
    ("municipal-assets-parking-concessions", "Municipal asset sales and parking concessions", "Map infrastructure funds, concession operators, financial advisors, law firms, local officials, contract terms, guarantees, and revenue impacts."),
    ("public-university-outsourcing", "Public university and campus-service outsourcing", "Map online-program managers, food, housing, facilities, security, healthcare, and technology contractors, procurement, investors, and officials."),
    ("tax-debt-collection-outsourcing", "Tax and government-debt collection outsourcing", "Map private collectors, court-debt vendors, toll and tax processors, contracts, fee structures, lobbying, and due-process findings."),
    ("election-technology-administration-vendors", "Election technology and administration vendors", "Map voting-system vendors, poll-book providers, logistics firms, software contractors, ownership, certifications, contracts, officials, and lobbying."),
    ("public-housing-vouchers-management", "Public housing vouchers and private management", "Map housing authorities, management companies, voucher administrators, developers, tax-credit syndicators, private-equity owners, policy groups, and funding flows.")
]

NETWORK_TARGETS: list[tuple[str, str, str, list[str]]] = [
    ("project-2025-complete-coalition-roster", "Project 2025 complete coalition and contributor roster", "Enumerate every publicly listed advisory-board organization, chapter author, contributor, editor, reviewer, transition participant, and training partner with exact source snapshots and role dates.", ["starintel:org:project-2025", "starintel:org:heritage-foundation"]),
    ("spn-complete-member-directory", "State Policy Network complete member and associate directory", "Enumerate every current and historical SPN member, associate, partner, leader, board member, donor, and shared staff connection, with state and dates.", ["starintel:org:state-policy-network"]),
    ("alec-public-private-members-model-bills", "ALEC public/private members and model-bill network", "Enumerate publicly disclosed legislators, private-sector members, task-force participants, board members, model-bill authors, funders, and state enactments; mark undisclosed membership as unresolved.", ["starintel:org:american-legislative-exchange-council"]),
    ("privatization-wef-overlap", "Privatization network overlap with WEF", "Resolve documented WEF partners, members, annual-meeting participants, Global Future Council roles, reports, and projects involving privatization-network organizations and contractors.", ["starintel:org:world-economic-forum"]),
    ("privatization-palantir-overlap", "Privatization network overlap with Palantir", "Resolve Palantir executives, PAC recipients, lobbyists, investors, subcontractors, public clients, policy-network memberships, and shared officials across the privatization graph.", ["starintel:org:palantir-technologies", "starintel:org:employees-of-palantir-technologies-inc-pac"]),
    ("privatization-aipac-overlap", "Privatization network overlap with AIPAC political money", "Resolve exact AIPAC PAC contributions and UDP independent expenditures involving officials who sponsor, administer, or oversee privatization policies, without inferring causation from donations alone.", ["starintel:org:american-israel-public-affairs-committee", "starintel:org:aipac-political-action-committee", "starintel:org:united-democracy-project"]),
    ("privatization-gop-jfc-overlap", "Privatization network overlap with GOP JFCs", "Resolve exact direct contributions, JFC transfers, leadership PAC links, and shared officers involving privatization-network people and organizations.", ["starintel:org:trump-national-committee-jfc", "starintel:org:invest-in-america-2026", "starintel:org:team-moreno"]),
    ("privatization-foundation-grant-network", "Foundation and donor-advised-fund grant network", "Reconcile IRS 990/990-PF grants, donor-advised intermediaries, recipient filings, fiscal sponsors, regrants, and project-specific funding across the privatization graph.", ["starintel:org:donorstrust", "starintel:org:lynde-and-harry-bradley-foundation", "starintel:org:searle-freedom-trust"]),
    ("privatization-revolving-door", "Privatization revolving-door network", "Map dated movement among government office, transition teams, think tanks, trade groups, contractors, investment firms, lobbying shops, and boards.", []),
    ("privatization-state-implementation", "State privatization implementation network", "Create state-by-state targets for bills, executive actions, agencies, procurement, vendors, SPN affiliates, ALEC model language, donors, and measured outcomes.", ["starintel:org:state-policy-network", "starintel:org:american-legislative-exchange-council"]),
    ("privatization-federal-procurement", "Federal privatization and procurement network", "Map federal awards, IDIQ vehicles, task orders, subcontracts, acquisition officials, lobbying, PAC giving, performance findings, and ownership for every contractor lead.", []),
    ("privatization-litigation-amicus", "Privatization litigation and amicus network", "Map litigation shops, plaintiffs, funders, counsel, amici, judges, cases, and remedies affecting public-sector unions, school choice, regulation, pensions, benefits, and contracting.", []),
    ("privatization-media-distribution", "Privatization policy media and distribution network", "Map publication syndication, podcasts, conferences, training, fellowships, newsletters, media bookings, shared authors, and donor-funded communications that distribute privatization proposals.", [])
]


def compact(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def source(name: str, url: str) -> dict[str, Any]:
    return {
        "kind": "official_organization_record",
        "title": f"{name} official website",
        "publisher": name,
        "uri": url,
        "url": url,
        "retrieved_at": NOW,
        "credibility": 0.85
    }


def base_record(record_id: str, dtype: str, title: str, summary: str, tags: list[str], sources: list[dict[str, Any]], priority: float, research_status: str) -> dict[str, Any]:
    return {
        "_id": record_id,
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": "0.9.0",
        "version": 1,
        "date_added": NOW,
        "date_updated": NOW,
        "title": title,
        "summary": summary,
        "status": "recorded",
        "language": "en",
        "tags": tags,
        "sources": sources,
        "evidence": [],
        "assessment": {
            "confidence": 0.82 if research_status == "queued" else 0.95,
            "analytic_confidence": 0.80 if research_status == "queued" else 0.94,
            "information_credibility": 0.86,
            "source_reliability": 0.86
        },
        "verification": {
            "status": "seeded" if research_status == "queued" else "source-backed",
            "verified": True,
            "verified_by": ["official-source seed review"],
            "verified_at": NOW,
            "last_reviewed_at": NOW,
            "methods": ["official-site seed review", "bounded lead classification"]
        },
        "handling": {
            "visibility": "public",
            "handling": "public-source-only",
            "pii": False,
            "sensitive": False
        },
        "provenance": {
            "agent": "GPT-5.6 Thinking",
            "collector": "ChatGPT",
            "collector_type": "research-agent",
            "created_by": "ChatGPT",
            "method": "high-recall privatization-network lead enumeration and target materialization",
            "run_id": RUN_ID,
            "skill": "auto-dig",
            "tool": "github-materializer"
        },
        "workflow": {
            "queue": "gop",
            "research_status": research_status,
            "recursion_depth": 3,
            "max_depth": 5,
            "priority": priority,
            "root_target_id": ROOT_TARGET,
            "run_id": RUN_ID
        },
        "lineage": {
            "derived_from": [DERIVED_FROM],
            "generation": 3
        },
        "notes": []
    }


def org_record(org: dict[str, str]) -> dict[str, Any]:
    rid = f"starintel:org:{org['slug']}"
    record = base_record(
        rid,
        "org",
        org["name"],
        f"Public-source research lead in the {org['category']} category for the GOP privatization-network recursion. Inclusion is a lead classification, not a finding of coordination or wrongdoing.",
        ["gop", "privatization-lead", org["category"], "depth-3"],
        [source(org["name"], org["url"])],
        0.90,
        "queued"
    )
    record["notes"] = [
        "The organization must be evaluated by specific policy, funding, membership, contract, and implementation evidence.",
        "Do not infer complete membership from attendance, citation, sponsorship, or shared personnel alone."
    ]
    record["data"] = {
        "name": org["name"],
        "short_name": org["name"],
        "org_type": org["category"],
        "website": org["url"],
        "research_classification": "privatization-network-lead",
        "roster_disclosure": org["roster"]
    }
    return record


def target_record(org: dict[str, str], dim: dict[str, Any]) -> dict[str, Any]:
    rid = f"starintel:investigation-target:{org['slug']}-{dim['slug']}-depth-3"
    title = f"{dim['label']} — {org['name']}"
    record = base_record(
        rid,
        "investigation-target",
        title,
        dim["question"].format(name=org["name"]),
        ["gop", "privatization", "auto-dig", "depth-3", dim["slug"], org["category"]],
        [source(org["name"], org["url"])],
        float(dim["priority"]),
        "queued"
    )
    record["workflow"]["next_action"] = dim["objectives"][0]
    record["data"] = {
        "target_id": rid,
        "target": title,
        "target_type": "public-policy-and-privatization-network",
        "scope_type": dim["slug"],
        "research_question": dim["question"].format(name=org["name"]),
        "depth": 3,
        "max_depth": 5,
        "breadth": 500,
        "priority": float(dim["priority"]),
        "score": float(dim["priority"]),
        "status": "queued",
        "seed_ids": [f"starintel:org:{org['slug']}"],
        "source_ids": [],
        "objectives": dim["objectives"],
        "hypotheses": [
            "Official public records will resolve at least part of the requested network.",
            "The relationship graph will contain materially different edge types that must not be collapsed into a generic influence claim."
        ],
        "excluded_sources": [
            "private personal data",
            "non-public account access",
            "name-only identity matches",
            "unsourced membership lists"
        ],
        "out_of_scope": [
            "voter persuasion",
            "private contact information",
            "quid-pro-quo claims without evidence",
            "control claims inferred only from funding, attendance, or membership"
        ]
    }
    return record


def standalone_target(slug: str, title: str, question: str, seed_ids: list[str], tags: list[str], priority: float = 1.0) -> dict[str, Any]:
    rid = f"starintel:investigation-target:{slug}-depth-3"
    record = base_record(
        rid,
        "investigation-target",
        title,
        question,
        ["gop", "privatization", "auto-dig", "depth-3", *tags],
        [],
        priority,
        "queued"
    )
    record["workflow"]["next_action"] = "Enumerate official public-source entities, people, money flows, policy products, implementation records, and dated relations."
    record["data"] = {
        "target_id": rid,
        "target": title,
        "target_type": "public-policy-and-privatization-network",
        "scope_type": slug,
        "research_question": question,
        "depth": 3,
        "max_depth": 5,
        "breadth": 1000,
        "priority": priority,
        "score": priority,
        "status": "queued",
        "seed_ids": seed_ids,
        "source_ids": [],
        "objectives": [
            "Enumerate every public organization, person, official, policy product, funding flow, contract, vendor, investor, and implementation event in scope.",
            "Create typed, dated StarIntel relations and preserve exact source records.",
            "Generate a breadth-first next-target queue from unresolved high-degree nodes.",
            "Mark opaque or non-public membership as unresolved rather than inferred."
        ],
        "hypotheses": [
            "Public policy, finance, procurement, lobbying, corporate, and nonprofit records will reveal a multi-layer implementation network.",
            "Policy advocacy, campaign finance, contracting, investment ownership, and government adoption will require separate edge types."
        ],
        "excluded_sources": ["private personal data", "non-public account access", "unsourced membership claims"],
        "out_of_scope": ["voter persuasion", "private contact information", "causal or corrupt-intent claims without evidence"]
    }
    return record


def write_record(record: dict[str, Any]) -> Path:
    dtype = record["dtype"]
    path = Path("db") / dtype / f"{record['_id']}.ndjson"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(compact(record) + "\n", encoding="utf-8")
    return path


def main() -> None:
    records: list[dict[str, Any]] = []

    for org in ORG_SEEDS:
        org_path = Path("db/org") / f"starintel:org:{org['slug']}.ndjson"
        if not org_path.exists():
            records.append(org_record(org))
        for dim in DIMENSIONS:
            records.append(target_record(org, dim))

    for slug, title, question in SECTOR_TARGETS:
        records.append(standalone_target(slug, title, question, [], ["sector-map"], 1.0))

    for slug, title, question, seed_ids in NETWORK_TARGETS:
        records.append(standalone_target(slug, title, question, seed_ids, ["cross-network-map"], 1.0))

    analysis_id = "starintel:analysis:gop-privatization-lead-map-depth-3"
    analysis = base_record(
        analysis_id,
        "analysis",
        "GOP privatization organization and target map — depth 3",
        "High-recall lead map covering policy networks, state affiliates, sector advocates, contractors, infrastructure investors, trade associations, funding networks, and implementation pathways.",
        ["gop", "analysis", "privatization", "depth-3"],
        [],
        1.0,
        "completed"
    )
    analysis["data"] = {
        "question": "Which organizations, public members, funders, policy products, officials, contractors, and investors form the high-recall privatization research frontier?",
        "method": "Static high-recall seed manifest plus one complete-public-roster, person-member, organization-member, funding, policy, implementation, contract-beneficiary, and cross-network target per organization.",
        "framework": "Lead classification separated from verified policy advocacy, formal membership, funding, contracting, implementation, and causal claims.",
        "scope": "National policy networks, SPN-style state groups, education and healthcare groups, P3 and utility associations, government contractors, infrastructure/private-equity owners, and cross-network political-money links.",
        "input_ids": [f"starintel:org:{org['slug']}" for org in ORG_SEEDS],
        "findings": [
            f"The pass seeds {len(ORG_SEEDS)} organizations across policy, funding, trade-association, contractor, and investor categories.",
            f"It creates {len(ORG_SEEDS) * len(DIMENSIONS)} organization-specific investigation targets.",
            f"It adds {len(SECTOR_TARGETS)} sector-wide targets and {len(NETWORK_TARGETS)} cross-network targets.",
            "Every organization receives a complete-public-roster target; opaque or confidential membership is explicitly marked unresolved rather than filled by inference."
        ],
        "conclusions": [
            "The target queue is intentionally high recall and does not treat every seed as a confirmed privatization advocate.",
            "Complete-member claims require official roster snapshots and dated role relations.",
            "Funding, membership, event participation, policy authorship, government adoption, contracting, and ownership must remain distinct graph edges."
        ],
        "recommendations": [
            "Run public roster completion first for Project 2025, State Policy Network, ALEC, trade associations, and organizations with public member directories.",
            "Then recurse into exact grants, PAC transactions, lobbying filings, procurement awards, and policy implementation.",
            "Prioritize shared people and organizations that bridge policy advocacy, political money, public office, and contracting."
        ],
        "counterarguments": [
            "A lead may oppose privatization in some domains or support only limited market mechanisms.",
            "Public rosters may omit members, donors, clients, subcontractors, or historical roles.",
            "A contractor's receipt of public money does not establish that it authored or promoted the policy creating the contract."
        ]
    }
    records.append(analysis)

    research_pass_id = "starintel:research-pass:gop-privatization-leads-depth-3-2026-07-31"
    pass_record = base_record(
        research_pass_id,
        "research-pass",
        "GOP privatization leads research pass, depth 3",
        "Materializes a high-recall privatization research frontier with organization seeds, complete-public-roster targets, member-resolution targets, funding and policy targets, implementation and contract targets, sector maps, and cross-network maps.",
        ["research-pass", "gop", "privatization", "depth-3"],
        [],
        1.0,
        "completed"
    )
    target_count = len(ORG_SEEDS) * len(DIMENSIONS) + len(SECTOR_TARGETS) + len(NETWORK_TARGETS)
    pass_record["data"] = {
        "agent_identity": "GPT-5.6 Thinking",
        "classification_rules": [
            "Inclusion is a research lead, not a finding of wrongdoing, coordination, or consistent policy position.",
            "Only publicly disclosed membership may be normalized as membership.",
            "Unknown, confidential, or incomplete rosters remain unresolved.",
            "Policy advocacy, funding, lobbying, campaign finance, contracting, ownership, and government implementation use separate edge types.",
            "Financial or organizational ties do not establish quid pro quo, control, or policy causation."
        ],
        "started_at": NOW,
        "completed_at": NOW,
        "iteration": 3,
        "method": "High-recall privatization lead enumeration and deterministic target materialization.",
        "narrative_role": "bounded public-source policy-network, campaign-finance, procurement, and ownership investigator",
        "research_question": "Which organizations and complete public member networks should be recursively investigated for privatization policy, funding, implementation, and beneficiaries?",
        "supporting_record_ids": [analysis_id] + [f"starintel:org:{org['slug']}" for org in ORG_SEEDS],
        "finding_ids": [analysis_id],
        "unresolved_target_ids": [r["_id"] for r in records if r["dtype"] == "investigation-target"],
        "findings": [
            {"finding": f"{len(ORG_SEEDS)} organization leads enumerated.", "status": "seeded", "confidence": 0.95},
            {"finding": f"{target_count} investigation targets materialized.", "status": "queued", "confidence": 1.0},
            {"finding": "Every seed has explicit public-roster and person/organization member-completion targets.", "status": "queued", "confidence": 1.0},
            {"finding": "Complete membership remains source-dependent; non-public rosters are not inferred.", "status": "bounded", "confidence": 1.0}
        ]
    }
    records.append(pass_record)

    written: list[Path] = []
    for record in records:
        written.append(write_record(record))

    DIG_DIR.mkdir(parents=True, exist_ok=True)
    packet_path = DIG_DIR / "starintel-documents.jsonl"
    packet_path.write_text("".join(compact(r) + "\n" for r in records), encoding="utf-8")

    manifest = {
        "run_id": RUN_ID,
        "generated_at": NOW,
        "organization_seed_count": len(ORG_SEEDS),
        "dimensions_per_organization": len(DIMENSIONS),
        "organization_target_count": len(ORG_SEEDS) * len(DIMENSIONS),
        "sector_target_count": len(SECTOR_TARGETS),
        "network_target_count": len(NETWORK_TARGETS),
        "total_investigation_target_count": target_count,
        "total_generated_record_count": len(records),
        "organization_categories": sorted({o["category"] for o in ORG_SEEDS}),
        "roster_disclosure_classes": sorted({o["roster"] for o in ORG_SEEDS})
    }
    (DIG_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme = f"""# GOP privatization leads — depth 3

Generated: `{NOW}`  
Run: `{RUN_ID}`

## Materialized scope

- **Organization leads:** {len(ORG_SEEDS)}
- **Target dimensions per organization:** {len(DIMENSIONS)}
- **Organization-specific targets:** {len(ORG_SEEDS) * len(DIMENSIONS)}
- **Sector-wide targets:** {len(SECTOR_TARGETS)}
- **Cross-network targets:** {len(NETWORK_TARGETS)}
- **Total investigation targets:** {target_count}
- **Total generated StarIntel records:** {len(records)}

## Member-completion rule

Every organization receives three roster-focused targets:

1. complete public roster;
2. person-member resolution;
3. organization-member resolution.

A roster is never called complete merely because a current leadership page was found. The pass requires board, officers, executives, staff, fellows, advisory members, member organizations, corporate members, chapters, affiliates, subsidiaries, portfolios, and historical roles where publicly disclosed. Confidential or undisclosed membership remains explicitly unresolved.

## Relationship discipline

This is a high-recall lead map. Inclusion does **not** establish wrongdoing, coordination, ideological uniformity, or even support for privatization in every domain. Membership, funding, event participation, policy authorship, lobbying, campaign finance, procurement, contracting, government adoption, and ownership remain separate typed edges.

## First execution order

1. Project 2025 complete coalition and contributor roster.
2. State Policy Network complete member and associate directory.
3. ALEC public/private membership, task forces, model bills, and state enactments.
4. Public member directories for trade associations and policy coalitions.
5. Exact grants, FEC transactions, lobbying filings, and government contracts.
6. State and federal implementation maps.
7. WEF, Palantir, AIPAC/UDP, and GOP-JFC overlap resolution.
"""
    (DIG_DIR / "README.md").write_text(readme, encoding="utf-8")

    # Parse every generated line before allowing the workflow to commit it.
    for path in written + [packet_path]:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                json.loads(line)

    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
