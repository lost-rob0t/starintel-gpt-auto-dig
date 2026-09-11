import json
R="2026-09-11T16:10:00Z"
DS="danbury"
def src(url,pub,name,pub2,cred=0.9):
    return {"url":url,"accessed_at":R,"published_at":pub,"name":name,"publisher":pub2,"credibility":cred,"access_method":"web-search"}
SRC={
"city_pd":src("https://www.danbury-ct.gov/266/Police-Department","2026-09-11T00:00:00Z","Police Department | Danbury, CT","City of Danbury",0.97),
"city_dir":src("https://www.danbury-ct.gov/directory.aspx?did=35","2026-09-11T00:00:00Z","Police Department Staff Directory","City of Danbury",0.97),
"nt_ord":src("https://www.newstimes.com/news/article/danbury-police-hiring-daca-permanent-residents-22414279.php","2026-09-03T00:00:00Z","Danbury police hiring DACA, permanent residents (Brian Gioiele)","News-Times",0.9),
"cou":src("https://www.courant.com/2026/09/03/after-ice-raids-ct-city-votes-to-allow-immigrants-to-serve-as-police-officers/","2026-09-03T00:00:00Z","After ICE raids, CT city votes to allow immigrants to serve as police officers (Christopher Keating)","Hartford Courant",0.9),
"patch":src("https://patch.com/connecticut/danbury/danbury-opens-police-officer-applications-daca-recipients-green-card-holders","2026-09-02T00:00:00Z","Danbury opens police officer applications to DACA recipients, green card holders (Hayleigh Evans)","Patch Danbury",0.85),
"citizen":src("https://citizenportal.ai/articles/9769121/danbury-council-approves-ordinance-allowing-lawful-permanent-residents-and-daca-recipients-to-apply-for-police","2026-09-02T00:00:00Z","Danbury Council approves ordinance allowing lawful permanent residents and DACA recipients to apply for police (meeting video/transcript)","CitizenPortal.ai",0.75),
"alves_fb":src("https://www.facebook.com/DanburyJoe/posts/1650879020380884","2026-09-02T00:00:00Z","Mayor Roberto Alves public post on 18-2 ordinance vote","Facebook (Mayor Roberto Alves)",0.85),
"fox":src("https://www.foxnews.com/media/connecticut-council-member-sounds-alarm-after-city-opens-law-enforcement-jobs-noncitizens","2026-09-04T00:00:00Z","Connecticut council member sounds alarm after city opens law enforcement jobs to noncitizens (Peter Pinedo)","Fox News",0.75),
"nt_dc":src("https://www.newstimes.com/news/article/Danbury-s-new-deputy-chief-embraces-17160485.php","2022-05-13T00:00:00Z","Danbury's new deputy chief embraces new role","News-Times",0.9),
"nt_promo22":src("https://www.newstimes.com/news/article/Four-promoted-on-Danbury-police-force-17181665.php","2022-05-18T00:00:00Z","Four promoted on Danbury police force","News-Times",0.9),
"nt_promo21":src("https://www.newstimes.com/news/article/","2021-12-11T00:00:00Z","Danbury police promotions (December 2021)","News-Times",0.85),
"nt_lerose":src("https://www.newstimes.com/news/article/danbury-police-captain-joseph-lerose-highest-20213535.php","2025-03-13T00:00:00Z","Danbury police Captain Joseph LeRose highest-paid city employee 2024","News-Times",0.9),
"nt_chief":src("https://www.newstimes.com/local/article/Danbury-chief-named-first-Black-president-of-CT-16246770.php","2021-06-14T00:00:00Z","Danbury chief named first Black president of CT police chiefs association","News-Times",0.9),
"fb23":src("https://www.facebook.com/DanburyPolice/posts/693130592839679","2023-08-08T00:00:00Z","Danbury Police Department promotion ceremony post","Facebook (Danbury Police Dept)",0.8),
"fb_oy":src("https://www.facebook.com/DanburyPolice/posts/1411675060985225","2026-05-08T00:00:00Z","DPD recognizes Officer Christopher Rodriguez - Officer of the Year","Facebook (Danbury Police Dept)",0.8),
"fb_hires":src("https://www.facebook.com/cityofdanbury/","2025-01-09T00:00:00Z","City of Danbury welcomes new police officers (Ernst, Lopez-Castillo, Kops)","Facebook (City of Danbury)",0.8),
"fb_grad":src("https://www.facebook.com/DanburyPolice/","2026-03-19T00:00:00Z","Officer Recruit Sophia Cotroneo graduates Connecticut Police Academy","Facebook (Danbury Police Dept)",0.8),
"fb_grande":src("https://www.facebook.com/cityofdanbury/","2026-07-09T00:00:00Z","Detective Grande promoted to Sergeant","Facebook (City of Danbury)",0.8),
"fb_budget":src("https://www.facebook.com/cityofdanbury/","2026-04-14T00:00:00Z","City of Danbury FY2026 budget post - sworn officers to 175, West Side station","Facebook (City of Danbury)",0.75),
"policeapp":src("https://www.policeapp.com/Danbury-CT-Police-Department/242/","2026-09-11T00:00:00Z","Danbury CT Police Department recruitment listing","PoliceApp",0.7),
}
def base(id,dtype,title,data,keys,summary="",desc=""):
    if isinstance(keys,str): keys=[keys]
    return {"_id":id,"dataset":DS,"dtype":dtype,"schema_version":"0.9.0","version":1,
            "title":title,"summary":summary,"description":desc,"date_added":R,"date_updated":R,
            "sources":[SRC[k] for k in keys],"evidence":[],"data":data,"extensions":{}}
docs=[]
docs.append(base("starintel:org:danbury-police-department","org","Danbury Police Department (Danbury, Connecticut)",{
 "etype":"police-department","name":"Danbury Police Department","display_name":"Danbury Police Department",
 "jurisdiction":"Danbury, Connecticut, United States","country":"US","status":"active",
 "org_type":"municipal-law-enforcement","government_levels":["municipal"],
 "description":"Municipal police department for the City of Danbury, Connecticut. Official page lists an authorized strength of 160 sworn officers plus civilian personnel (accessed 2026-09-11); FY2026 city budget messaging described increasing sworn officers to 175. Divisions: Patrol, Investigations (Detective Bureau), Professional Standards (each captain-led), and Administrative Services (headed by a civilian administrative manager). Command: Chief Patrick Ridenhour, Deputy Chief Michael Sturdevant.",
 "employee_count":160},["city_pd","policeapp","fb_budget"]))
docs[-1]["assessment"]={"confidence":0.95,"gaps":["Authorized strength varies by source: 160 (official page, accessed 2026-09-11), 175 (FY2026 budget messaging), 156 'up to' (recruitment copy). Issue baseline of ~175 authorized / 159 sworn (March 2026 report) / 158 sworn (Aug 2026) was not independently confirmed against a primary document in this pass."]}
docs.append(base("starintel:org:danbury-city-council","org","Danbury City Council",{
 "etype":"city-council","name":"Danbury City Council","display_name":"Danbury City Council",
 "jurisdiction":"Danbury, Connecticut, United States","country":"US","status":"active",
 "org_type":"municipal-legislature","government_levels":["municipal"],
 "description":"Legislative body of the City of Danbury, Connecticut. On 2026-09-02 it adopted by an 18-2 vote an ordinance allowing lawful permanent residents and DACA recipients to apply to become Danbury police officers."},["alves_fb","citizen"]))
P=[
 ("ridenhour","Patrick","Ridenhour","Chief of Police","chief","active","Head of agency. Longtime Danbury chief; named first Black president of the Connecticut Police Chiefs Association (News-Times, June 2021). Publicly advocated the 2026 hiring-eligibility ordinance, stating it aligned DPD eligibility with POSTC standards without lowering hiring standards. Email p.ridenhour@danbury-ct.gov per CPCANet listing.",["city_pd","city_dir","nt_chief","nt_ord"]),
 ("sturdevant","Michael","Sturdevant","Deputy Chief of Police","deputy-chief","active","Second in command. Joined DPD 1994; promoted Sergeant, Lieutenant, Captain, then Deputy Chief; Council confirmation May 3, 2022, succeeding retiring Deputy Chief Shaun McColgan.",["city_pd","city_dir","nt_dc"]),
 ("lerose","Joseph","LeRose","Captain, Professional Standards Division","captain","active","With DPD since 1985; promoted Lieutenant to Captain with Council approval May 3, 2022. Named highest-earning City of Danbury employee for 2024 (~$259,853; News-Times, March 2025).",["city_dir","nt_promo22","nt_lerose"]),
 ("carroccio","Christian","Carroccio","Detective Captain","captain","active","Promoted to Captain at the August 8, 2023 promotion ceremony; directory title Detective Captain, associated with Investigations/Detective Bureau.",["city_dir","fb23"]),
 ("williams","Mark","Williams","Detective Captain","captain","active","Listed in the official staff directory with the title Detective Captain under the Patrol Division listing; title/assignment ambiguity flagged (captain commanding Patrol vs detective title).",["city_dir"]),
 ("antonelli","James","Antonelli","Lieutenant","lieutenant","active","Listed as Lieutenant in the official staff directory (accessed 2026-09-11).",["city_dir"]),
 ("malone","Matthew","Malone","Detective Lieutenant","lieutenant","active","Listed as Detective Lieutenant in the official staff directory (accessed 2026-09-11).",["city_dir"]),
 ("mable","Ethan","Mable","Detective Lieutenant","lieutenant","active","Listed as Detective Lieutenant in the official staff directory (accessed 2026-09-11).",["city_dir"]),
 ("relyea","Alexander","Relyea","Sergeant","sergeant","active","Listed as Sergeant in the official staff directory (accessed 2026-09-11).",["city_dir"]),
 ("wakeman","Brian","Wakeman","Sergeant","sergeant","active","Listed as Sergeant in the official staff directory (accessed 2026-09-11).",["city_dir"]),
 ("lafantano","Amity","LaFantano","Sergeant","sergeant","active","Sergeant; reported as the first female sergeant in DPD history (WLAD); recognized in 2025 Exchange Club award context.",["city_dir"]),
 ("davis","Robert","Davis","Deputy Chief","deputy-chief","historical","Promoted Lieutenant to Deputy Chief at the August 8, 2023 ceremony. NOT on the current staff directory; current status (departed/retired) unconfirmed - retained as historical.",["fb23"]),
 ("phelan","Dennis","Phelan","Captain","captain","historical","Promoted Lieutenant to Captain August 8, 2023. Not on current directory; current status unconfirmed - retained as historical.",["fb23"]),
 ("krchnavy","Jon","Krchnavy","Lieutenant","lieutenant","historical","Promoted Sergeant to Lieutenant August 8, 2023. Not on current directory; current status unconfirmed.",["fb23"]),
 ("wochek","Mark","Wochek","Lieutenant","lieutenant","historical","Promoted Sergeant to Lieutenant with Council approval May 3, 2022. Not on current directory; current status unconfirmed.",["nt_promo22"]),
 ("guertin","Gary","Guertin","Lieutenant","lieutenant","historical","With DPD since April 2001, detective August 2005; promoted to Lieutenant December 2021. Not on current directory; current status unconfirmed.",["nt_promo21"]),
 ("pardovich","David","Pardovich","Lieutenant","lieutenant","historical","Promoted to Lieutenant December 2021. Not on current directory; current status unconfirmed.",["nt_promo21"]),
 ("grande","Grande","Grande","Sergeant (promoted July 2026, previously Detective)","sergeant","active","City of Danbury social post (July 9, 2026) celebrating Detective Grande's promotion to Sergeant; first name not captured in indexed snippets.",["fb_grande"]),
 ("cotroneo","Sophia","Cotroneo","Police Officer (recruit graduate March 2026)","officer","active","Officer Recruit Sophia Cotroneo graduated the Connecticut Police Academy (Meriden) March 19, 2026 and entered field training (DPD social post).",["fb_grad"]),
 ("rodriguez","Christopher","Rodriguez","Police Officer","officer","active","Named DPD/Exchange Club 2026 Officer of the Year (DPD social post, May 8, 2026).",["fb_oy"]),
 ("ernst","Brandon","Ernst","Police Officer","officer","active","New officer welcomed by the City of Danbury January 9, 2025.",["fb_hires"]),
 ("lopez-castillo","Jaime","Lopez-Castillo","Police Officer","officer","active","New officer welcomed by the City of Danbury January 9, 2025.",["fb_hires"]),
 ("kops","Kristen","Kops","Police Officer","officer","active","New officer welcomed by the City of Danbury January 9, 2025.",["fb_hires"]),
]
for slug,f,l,rank,rtier,status,desc,keys in P:
    docs.append(base("starintel:person:danbury-pd-"+slug,"person",f"{f} {l} - Danbury PD {rank.split(' (')[0]}",{
      "etype":"person","name":f"{f} {l}","full_name":f"{f} {l}","fname":f,"lname":l,
      "jurisdiction":"Danbury, Connecticut, United States","country":"US",
      "positions":[rank],"occupations":["police officer"],
      "status":status,"description":desc,
      "employers":["starintel:org:danbury-police-department"],
      "misc":[f"rank_at_observation: {rank}",f"status: {status}"]},keys))
for slug,f,l,title,desc in [
 ("primus","Liliana","Primus","Administrative Manager (Administrative Services)","Civilian administrative manager heading the Administrative Services division per official department description; directory listing accessed 2026-09-11."),
 ("henry","Erin","Henry","Public Relations Specialist","Civilian public relations specialist for the Danbury Police Department per official staff directory."),
 ("leonard","Misti","Leonard","Executive Secretary to the Chief of Police","Civilian executive secretary to the Chief per official staff directory.")]:
    docs.append(base("starintel:person:danbury-pd-civilian-"+slug,"person",f"{f} {l} - Danbury PD civilian staff ({title})",{
      "etype":"person","name":f"{f} {l}","full_name":f"{f} {l}","fname":f,"lname":l,
      "jurisdiction":"Danbury, Connecticut, United States","country":"US","positions":[title],
      "occupations":["civilian municipal staff"],"status":"active","description":desc,
      "employers":["starintel:org:danbury-police-department"]},["city_dir","city_pd"]))
for slug,f,l,rank,*rest in P:
    keys=P[[p[0] for p in P].index(slug)][7]
    docs.append(base("starintel:relation:danbury-pd-employment-"+slug,"relation",
       f"{f} {l} employed by Danbury Police Department",
       {"subject":{"id":"starintel:person:danbury-pd-"+slug,"dtype":"person","role":"sworn officer"},
        "predicate":"employed_by",
        "object":{"id":"starintel:org:danbury-police-department","dtype":"org","role":"municipal police department"}},keys))
for slug in ["primus","henry","leonard"]:
    docs.append(base("starintel:relation:danbury-pd-employment-civilian-"+slug,"relation",
       f"Civilian staff {slug} employed by Danbury Police Department",
       {"subject":{"id":"starintel:person:danbury-pd-civilian-"+slug,"dtype":"person","role":"civilian staff"},
        "predicate":"employed_by",
        "object":{"id":"starintel:org:danbury-police-department","dtype":"org","role":"municipal police department"}},["city_dir"]))
def rel(id,subj,obj,pred,role_s,role_o,title,keys):
    otype="person" if obj.startswith("starintel:person") else "org"
    return base(id,"relation",title,{"subject":{"id":subj,"dtype":"person","role":role_s},
        "predicate":pred,"object":{"id":obj,"dtype":otype,"role":role_o}},keys)
docs.append(rel("starintel:relation:danbury-pd-command-sturdevant-reports-ridenhour",
  "starintel:person:danbury-pd-sturdevant","starintel:person:danbury-pd-ridenhour","reports_to","deputy chief","chief of police","Deputy Chief Sturdevant reports to Chief Ridenhour",["city_pd","nt_dc"]))
for slug,name in [("lerose","Capt. LeRose (Professional Standards)"),("carroccio","Capt. Carroccio (Investigations)"),("williams","Capt. Williams (Patrol)")]:
    docs.append(rel("starintel:relation:danbury-pd-command-"+slug+"-reports-ridenhour",
      "starintel:person:danbury-pd-"+slug,"starintel:person:danbury-pd-ridenhour","reports_to","division captain","chief of police",name+" reports to Chief Ridenhour",["city_pd","city_dir"]))
docs.append(rel("starintel:relation:danbury-pd-admin-services-headed-by-primus",
  "starintel:person:danbury-pd-civilian-primus","starintel:org:danbury-police-department","manages","civilian administrative manager","Administrative Services division","Liliana Primus manages Administrative Services",["city_pd","city_dir"]))
docs.append(base("starintel:event:danbury-council-vote-2026-09-02-police-eligibility-ordinance","event",
 "Danbury City Council 18-2 vote adopting police-hiring eligibility ordinance (2026-09-02)",{
 "event_kind":"legislative-vote","name":"Danbury City Council vote on police applicant eligibility ordinance",
 "description":"On Tuesday, September 2, 2026, the Danbury City Council adopted by an 18-2 roll-call vote an ordinance allowing lawful permanent residents and DACA recipients to apply to become Danbury police officers. Reported as agenda item number 10. Transcript records the no votes as Councilmember Michelle Coelho and Councilwoman Candace Fay (Fay had moved, unsuccessfully, to split LPR and DACA eligibility into separate votes); news coverage described both no votes as the council's Republicans. No effective date was stated in public discussion. Trigger context: large ICE enforcement operations in Danbury, Stamford, and Bridgeport in late August 2026 (~65-100 arrests, locally estimated 6-7 with criminal records); Mayor Alves joined Gov. Lamont, Sen. Murphy, and Rep. Hayes at Kennedy Park on Aug 26 condemning the operations.",
 "organizer_ids":["starintel:org:danbury-city-council"],
 "participants":["Mayor Roberto Alves","Chief Patrick Ridenhour","Councilman Joe Britton","Councilmember Michelle Coelho (no vote)","Councilwoman Candace Fay (no vote)","State Rep. Farley Santos"],
 "start_at":"2026-09-02T00:00:00Z","end_at":"2026-09-02T00:00:00Z",
 "jurisdiction":"Danbury, Connecticut, United States",
 "decisions":["Adopted ordinance allowing lawful permanent residents and DACA recipients to apply to become Danbury police officers, 18-2."],
 "outcome":"Adopted 18-2; effective date not publicly stated; ordinance text and resolution number not located on danbury-ct.gov in this pass."},["alves_fb","citizen","nt_ord","cou","patch","fox"]))
docs.append(base("starintel:policy:danbury-police-applicant-eligibility-ordinance-2026","policy",
 "Danbury ordinance allowing LPR and DACA applicants to the police department (adopted 2026-09-02)",{
 "policy_id":"danbury-police-applicant-eligibility-ordinance-2026",
 "name":"Danbury ordinance allowing lawful permanent residents and DACA recipients to apply to become police officers",
 "issuer_id":"starintel:org:danbury-city-council","jurisdiction":"Danbury, Connecticut, United States",
 "policy_type":"municipal-ordinance","status":"adopted",
 "text":"Full ordinance text NOT retrieved in this pass. CitizenPortal transcript fragment: the ordinance amends sections cited in meeting materials as '20 through 2230 of the Danbury Police Department ordinances' (likely transcription of section numbering). Reported as agenda item number 10. Mechanics: removes the local bar preventing LPRs and DACA recipients from APPLYING to DPD (application/eligibility stage only); all downstream hiring standards unchanged (written testing, polygraph, psychological exam, medical/drug screening, background investigation, civil-service testing) per Chief Ridenhour and Mayor's chief of staff Taylor O'Brien. Ridenhour: 'This is not asking you to lower our hiring standards... simply asking you to align our hiring eligibility with the eligibility requirements set forth by our governing body' (POSTC). O'Brien: amendment follows the POSTC standard 'followed by over 30 municipalities in Connecticut and several states'. Context: POSTC reportedly removed its US-citizenship requirement extending certification eligibility to lawful permanent residents (reported 2020) and expanded to DACA recipients (reported 2025); underlying POSTC policy documents and CGS citations not retrieved in this pass.",
 "effective_at":None,
 "affected_ids":["starintel:org:danbury-police-department"]},["nt_ord","cou","patch","citizen","fox"]))
docs[-1]["assessment"]={"confidence":0.85,"gaps":["Ordinance text, resolution/agenda item number, and codified section text not located on danbury-ct.gov (agenda center JS-rendered).","Effective date not stated in public discussion or any indexed coverage.","POSTC 2020 citizenship-waiver and 2025 DACA-expansion primary documents and CGS citations not retrieved; whether a CT statute vs POSTC standard imposed the citizenship bar is unresolved.","Police union position: no statement found.","Litigation: none found as of 2026-09-11 (absence of evidence).","Attribution of the two no votes: transcript names Coelho and Fay; news coverage describes them as Republicans; Coelho party affiliation unconfirmed."]}
docs.append(base("starintel:analysis:danbury-pd-enum-2026-09-11","analysis",
 "Danbury PD sworn-force enumeration and non-citizen eligibility - analysis (2026-09-11)",{
 "conclusions":[
  "Command structure confirmed from official sources: Chief Patrick Ridenhour and Deputy Chief Michael Sturdevant lead DPD; Patrol, Investigations, and Professional Standards are captain-led; Administrative Services is headed by a civilian administrative manager.",
  "Approximately 23 named sworn personnel and 3 named civilian staff are captured from attributable public sources; the full ~149-158-officer effective roster is NOT publicly enumerated and remains a gap.",
  "The 2026-09-02 ordinance (18-2) changes application-stage eligibility only, aligning Danbury with POSTC standards; effective date, ordinance text, and codification remain unresolved.",
  "Several 2021-2023-promoted officers (Davis, Phelan, Krchnavy, Wochek, Guertin, Pardovich) are absent from the current directory and are retained as historical status pending confirmation."],
 "confidence":0.85,
 "counterarguments":[
  "Staff-directory titles may lag actual assignments (e.g., 'Detective Captain' Williams listed under Patrol Division).",
  "Social-platform promotion records (DPD/City Facebook) are attributable but not archival; absence from the current directory does not prove retirement or departure.",
  "Authorized-strength figures conflict across sources (160 vs 175 vs 156); the issue baseline (175/159/149, March 2026; 158 sworn Aug 2026) was not independently confirmed against a primary document."],
 "findings":[
  "Official directory enumerates 11 sworn personnel by name plus 3 civilians; press and social sources add 12 more named sworn personnel (2021-2026 promotions, hires, graduates, awards).",
  "CT POSTC certification status could not be verified for any individual; POSTC lists are not publicly searchable in this pass.",
  "The ordinance mechanics are application-stage only; Chief Ridenhour stated vetting standards are unchanged; POSTC alignment framing (30+ CT municipalities) is consistent across sources."],
 "unresolved":[
  "Full sworn roster (~149-158 officers) unenumerated; CT POSTC certification records; FOIA-able monthly reports and budgets.",
  "Ordinance primary text, resolution number, effective date; POSTC policy documents and CGS citations.",
  "School resource officer and named sworn public-information-officer assignments not identified.",
  "Police union position and litigation status unknown."]},["city_pd","city_dir","nt_ord","cou"]))
docs.append(base("starintel:research-pass:danbury-pd-enum-2026-09-11","research-pass",
 "Research pass: Danbury PD sworn-force enumeration + non-citizen eligibility (2026-09-11)",{
 "research_question":"What can be established from attributable public sources about the Danbury Police Department sworn force (command, divisions, named personnel, staffing levels) and the 2026-09-02 ordinance allowing LPR/DACA applicants?",
 "method":"Live web search and direct fetch of official City of Danbury pages; local and national news; official agency social posts; meeting transcript. Enumerated named personnel from official directory first, then cross-enumerated from dated promotion/hiring/award records; conflict resolution by date; stale entries retained as historical. Policy reconstructed from five independent news sources plus meeting transcript and mayor's post; primary ordinance text not retrievable.",
 "classification_rules":[
  "Only persons named in attributable public sources are recorded; no name fabrication.",
  "Directory absence is treated as status uncertainty, not retirement.",
  "Agency social posts are attributable but medium-credibility; confidence reflects this.",
  "Unverified issue-baseline staffing figures are preserved as claims, not facts.",
  "Statements in coverage remain attributed claims until independently corroborated."],
 "findings":[{"finding":"23 named sworn + 3 named civilian personnel captured; command and division structure confirmed from official sources."},
             {"finding":"Ordinance adopted 2026-09-02, 18-2 (no: Coelho, Fay per transcript); application-stage eligibility change aligned to POSTC; text/effective date unresolved."},
             {"finding":"Staffing figures conflict across sources (160 official page vs 175 budget messaging vs issue baseline 175/159/149 and 158 sworn)."}],
 "finding_ids":["starintel:analysis:danbury-pd-enum-2026-09-11"],
 "source_ids":[],"started_at":"2026-09-11T15:40:00Z","completed_at":"2026-09-11T16:10:00Z","iteration":1,
 "agent_identity":"StarIntel Auto-Dig OSINT worker (issue #2514)"},["city_pd","city_dir","nt_ord","cou","alves_fb"]))
with open("tmp/pack/pack.jsonl","w") as f:
    for d in docs: f.write(json.dumps(d,separators=(",",":"))+"\n")
print(len(docs),"docs")
