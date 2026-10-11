"""Build a bounded, non-executing public-announcement packet through canonical CLI."""
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'digs/columbus/2026-10-11-public-event-announcements'
DATASET = 'columbus-public-event-announcements'
OBSERVED = '2026-10-11T07:35:10Z'
CALENDAR = 'https://indivisiblecentralohio.org/events'
PRIMARY = CALENDAR + '/no-kings-vote-early-rally'
SECONDARY = 'https://columbusunderground.com/events/no-kings-vote-early-rally/'
ISSUE = 'https://github.com/lost-rob0t/starintel-gpt-auto-dig/issues/2745'
EVENTS = [
    ('stop-the-cruelty-columbus-2026-10-12', 'Stop the Cruelty, Columbus', '2026-10-12T16:15:00-04:00', '2026-10-12T17:15:00-04:00', '1 E Nationwide Blvd, Columbus; High Street side', 'Calendar explicitly reports relocation to this address.'),
    ('veterans-columbus-2026-10-13', 'Support Veterans Rush Hour Rally', '2026-10-13T16:00:00-04:00', '2026-10-13T17:00:00-04:00', 'Public sidewalks on both sides of James Road at 420 N James Rd, Columbus', 'Announcement specifies public sidewalks; not clinic grounds.'),
    ('worthington-2026-10-13', 'Worthington Rush Hour Rally', '2026-10-13T16:30:00-04:00', '2026-10-13T17:30:00-04:00', 'High Street / Route 161, Worthington, Ohio', 'Worthington is a separate municipality in the Columbus area.'),
    ('husted-moreno-columbus-2026-10-14', 'Wednesday Husted and Moreno Protest', '2026-10-14T12:00:00-04:00', '2026-10-14T13:00:00-04:00', '200 N High St, Columbus', 'Only this dated calendar instance is in scope.'),
    ('clintonville-2026-10-17', 'Weekly Clintonville pop-up protest', '2026-10-17T12:00:00-04:00', '2026-10-17T13:00:00-04:00', 'N High St / E North Broadway, Columbus', 'Only this dated calendar instance is in scope.'),
    ('no-kings-vote-early-columbus-2026-10-17', 'No Kings Vote Early Rally', '2026-10-17T16:30:00-04:00', '2026-10-17T18:00:00-04:00', 'Ohio Statehouse, 1 Capitol Square, Columbus', 'Secondary listing says Atrium; organizer does not specify assembly point. Announced downtown march has no verified precise route.'),
]
EXCLUSIONS = ['attendee identities or RSVPs', 'personal political profiling', 'devices or location traces', 'private WiGLE data', 'registration, forms, contact or group joining', 'live collection, deployment or automatic scheduling']


def identifier(dtype, slug):
    return f'starintel:{dtype}:columbus-public-announcements:{slug}'


def ref(dtype, slug):
    return {'schema': dtype, 'id': identifier(dtype, slug)}


def build():
    timestamp = int(datetime.fromisoformat(OBSERVED.replace('Z', '+00:00')).timestamp())
    source_refs = [ref('url', s) for s in ('calendar-2026-10-11', 'no-kings-primary-2026-10-11', 'no-kings-secondary-2026-10-11')]
    common = dict(createdAt=timestamp, observedAt=timestamp, sourceRetrievedAt=timestamp,
                  visibility='public', sensitivity='public', timezone='America/New_York',
                  sources=source_refs, sourceUrls=[CALENDAR, PRIMARY, SECONDARY],
                  provenance={'method': 'Manual review of web tool rendered pages; no origin response bytes archived.',
                              'retrievalTimePrecision': 'Session receipt timestamp; individual requests completed before this time.',
                              'publishedAt': None, 'publicationTimeStatus': 'Not established from reviewed event text',
                              'issue': ISSUE, 'agent': 'Codex', 'iteration': 1},
                  notes='Announced plans only; no occurrence or attendance established. No automated execution configured.')
    records = []

    def add(dtype, slug, **fields):
        # The repository create command validates each flat document before any packet write.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fields.json'
            path.write_text(json.dumps({**common, **fields}))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/starintel.py'), 'create', dtype,
                                     '--dataset', DATASET, '--id', identifier(dtype, slug), '--fields', '@' + str(path)],
                                    check=True, capture_output=True, text=True, cwd=ROOT)
            records.append(json.loads(result.stdout))

    for slug, url, title, content in [
        ('calendar-2026-10-11', CALENDAR, 'Organizer calendar, October 12–17 instances', 'Calendar announces five scoped protests: Oct 12, 16:15–17:15, Nationwide/High; Oct 13, 16:00–17:00, James Road sidewalks; Oct 13, 16:30–17:30, Worthington High/161; Oct 14, 12:00–13:00, 200 N High; Oct 17, 12:00–13:00, Clintonville High/North Broadway. Times interpreted in America/New_York. The first is explicitly relocated.'),
        ('no-kings-primary-2026-10-11', PRIMARY, 'Organizer No Kings announcement', 'Organizer announces October 17, 2026, 16:30–18:00 at Ohio Statehouse, 1 Capitol Square. A downtown march is planned afterward; no precise route or assembly point is established.'),
        ('no-kings-secondary-2026-10-11', SECONDARY, 'Columbus Underground event listing', 'Secondary listing agrees on October 17, 2026, 16:30–18:00 and Ohio Statehouse, but labels the venue Atrium. This detail remains unconfirmed by the organizer announcement.'),
    ]:
        add('url', slug, url=url, contentTitle=title, content=content, sources=[ref('url', slug)], sourceUrls=[url],
            collectionMethod='web tool rendered-page review', fetchedAt=timestamp)
    add('scope', 'october-12-17-2026', name='Public announcement verification only',
        inScope=['Six dated public event announcements', 'Official public changes to date, location or status', 'Dated evidence preservation'],
        outOfScope=EXCLUSIONS, prohibitedActions=EXCLUSIONS,
        rules='Stop at event-level public announcements. Preserve contradictions and distinguish event time from retrieval and publication time.')
    for slug, title, start, end, location, caveat in EVENTS:
        nokings = slug.startswith('no-kings')
        refs = source_refs[1:] if nokings else source_refs[:1]
        urls = [PRIMARY, SECONDARY] if nokings else [CALENDAR]
        event = {'name': title, 'start': start, 'end': end, 'timezone': 'America/New_York',
                 'announcedLocation': location, 'status': 'announced', 'uncertainty': caveat}
        add('mission', slug, name='Verify public announcement: ' + title, state='draft',
            objective=f'Review public date, location and status updates for {title} ({start}); preserve dated evidence.',
            scope=ref('scope', 'october-12-17-2026'), targets=[ref('mission-target', slug)],
            constraints={'excluded': EXCLUSIONS, 'executionEnabled': False}, sources=refs, sourceUrls=urls,
            statusReason='Reviewable planning object only; no collector dispatched or schedule activated.')
        add('finding', slug, title=title + ': announced schedule', findingType='public-event-announcement',
            status='announced', description=f'{start} to {end}; {location}. {caveat}',
            evidence=refs, sources=refs, sourceUrls=urls,
            extensions={'org.starintel.columbus.publicEvent': event})
        add('target', slug, actor='manual-public-source-review', target=urls[0], targetType='public-event-announcement',
            state='paused', recurring=False, scope=ref('scope', 'october-12-17-2026'), sources=refs, sourceUrls=urls,
            options={'eventKey': slug, 'executionEnabled': False, 'question': 'Has the official announcement changed its date, place or status?'},
            notes=f'{title}: {caveat} Paused planning target; no actor dispatch.')
        add('mission-target', slug, mission=ref('mission', slug), subject=ref('target', slug),
            state='pending', objective=f'Check official public updates for {title}; preserve changes and unresolved location details.',
            resultRefs=[ref('finding', slug)], sources=refs, sourceUrls=urls,
            options={'executionEnabled': False, 'stopAfter': end, 'excluded': EXCLUSIONS})
    return records


if __name__ == '__main__':
    documents = build()
    PACKET.mkdir(parents=True, exist_ok=True)
    (PACKET / 'starintel-documents.jsonl').write_text(''.join(json.dumps(d, ensure_ascii=False, separators=(',', ':')) + '\n' for d in documents))
    print(f'Wrote {len(documents)} canonical records to {PACKET}')
