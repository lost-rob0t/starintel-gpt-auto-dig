from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from .auditor import AuditorCollector
from .github import GitHubCollector
from .legistar import LegistarCollector
from .site import SiteCollector
from .wayback import WaybackCollector
from .model import COLLECTORS, CollectJob, Collector, Observation, Stop, TargetPlan
from .network import HttpClient

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "scrapers" / "wef-depth-7.json"
DEFAULT_OUTPUT = Path("imports/wef-depth-7/raw-observations.jsonl")


class WriterActor:
    def __init__(self, output: Path) -> None:
        self.output = output
        self.queue: asyncio.Queue[Observation | Stop] = asyncio.Queue()
        self.count = 0
        self.seen: set[str] = set()

    async def send(self, message: Observation | Stop) -> None:
        await self.queue.put(message)

    async def run(self) -> None:
        self.output.parent.mkdir(parents=True, exist_ok=True)
        with self.output.open("w", encoding="utf-8") as handle:
            while True:
                message = await self.queue.get()
                try:
                    if isinstance(message, Stop):
                        return
                    record = message.as_dict()
                    observation_id = record["observation_id"]
                    if observation_id in self.seen:
                        continue
                    self.seen.add(observation_id)
                    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                    handle.flush()
                    self.count += 1
                finally:
                    self.queue.task_done()


class CollectorActor:
    def __init__(self, collectors: Mapping[str, Collector], writer: WriterActor) -> None:
        self.collectors = collectors
        self.writer = writer
        self.queue: asyncio.Queue[CollectJob | Stop] = asyncio.Queue()
        self.errors: list[str] = []

    async def send(self, message: CollectJob | Stop) -> None:
        await self.queue.put(message)

    async def run(self) -> None:
        while True:
            message = await self.queue.get()
            try:
                if isinstance(message, Stop):
                    return
                collector = self.collectors[message.collector]
                try:
                    observations = await asyncio.to_thread(lambda: list(collector.collect(message.target)))
                except Exception as error:
                    self.errors.append(f"{message.collector}:{message.target.target_id}:{error}")
                    continue
                for observation in observations:
                    await self.writer.send(observation)
            finally:
                self.queue.task_done()


def load_config(path: Path) -> tuple[dict[str, Any], list[TargetPlan]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("config root must be an object")
    targets = [TargetPlan.from_dict(item) for item in value.get("targets", ())]
    ids = [target.target_id for target in targets]
    if len(targets) != 8 or len(ids) != len(set(ids)):
        raise ValueError("WEF depth 7 config must contain eight unique targets")
    return dict(value), targets


def select_targets(targets: Sequence[TargetPlan], selected: Sequence[str]) -> list[TargetPlan]:
    if not selected:
        return list(targets)
    wanted = set(selected)
    result = [target for target in targets if target.target_id in wanted or target.title in wanted]
    missing = wanted - {target.target_id for target in result} - {target.title for target in result}
    if missing:
        raise SystemExit(f"unknown targets: {', '.join(sorted(missing))}")
    return result


def enumerate_jobs(targets: Sequence[TargetPlan], collectors: Sequence[str]) -> list[CollectJob]:
    allowed = set(collectors) if collectors else COLLECTORS
    unknown = sorted(allowed - COLLECTORS)
    if unknown:
        raise SystemExit(f"unknown collectors: {', '.join(unknown)}")
    return [CollectJob(collector, target) for target in targets for collector in target.collectors if collector in allowed]


def build_collectors(client: HttpClient, args: argparse.Namespace, config: Mapping[str, Any]) -> dict[str, Collector]:
    return {
        "auditor": AuditorCollector(client, args, config),
        "github": GitHubCollector(client, args, config),
        "legistar": LegistarCollector(client, args, config),
        "site": SiteCollector(client, args, config),
        "wayback": WaybackCollector(client, args, config),
    }


async def execute(args: argparse.Namespace) -> int:
    config, configured_targets = load_config(args.config)
    targets = select_targets(configured_targets, args.target)
    jobs = enumerate_jobs(targets, args.collector)
    if args.list:
        for target in targets:
            print(json.dumps(dataclasses.asdict(target), ensure_ascii=False, sort_keys=True))
        return 0
    if args.dry_run:
        for job in jobs:
            print(json.dumps({"collector": job.collector, "target_id": job.target.target_id, "title": job.target.title}, sort_keys=True))
        return 0
    client = HttpClient(delay=args.delay, timeout=args.timeout, github_token=os.environ.get("GITHUB_TOKEN"))
    writer = WriterActor(args.output)
    collectors = build_collectors(client, args, config)
    workers = [CollectorActor(collectors, writer) for _ in range(args.concurrency)]
    writer_task = asyncio.create_task(writer.run())
    worker_tasks = [asyncio.create_task(worker.run()) for worker in workers]
    for index, job in enumerate(jobs):
        await workers[index % len(workers)].send(job)
    for worker in workers:
        await worker.send(Stop())
    await asyncio.gather(*worker_tasks)
    await writer.send(Stop())
    await writer_task
    errors = [error for worker in workers for error in worker.errors]
    print(json.dumps({"jobs": len(jobs), "observations": writer.count, "errors": errors, "output": str(args.output)}, ensure_ascii=False, sort_keys=True))
    return 1 if errors and args.fail_on_error else 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enumerate and scrape WEF-Columbus Depth 7 public evidence surfaces")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--collector", action="append", default=[])
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fail-on-error", action="store_true")
    parser.add_argument("--ignore-robots", action="store_true")
    parser.add_argument("--archive-content", action="store_true")
    parser.add_argument("--auditor-download", action="store_true")
    parser.add_argument("--download-dir")
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--page-size", type=int, default=250)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--archive-limit", type=int, default=500)
    parser.add_argument("--github-file-limit", type=int, default=40)
    parser.add_argument("--auditor-hit-limit", type=int, default=250)
    parser.add_argument("--auditor-row-limit", type=int, default=2_000_000)
    parser.add_argument("--max-document-bytes", type=int, default=4_000_000)
    parser.add_argument("--max-dataset-bytes", type=int, default=128_000_000)
    args = parser.parse_args(argv)
    if args.concurrency < 1:
        parser.error("--concurrency must be at least 1")
    if args.max_pages < 1 or args.max_depth < 0 or args.auditor_row_limit < 1:
        parser.error("invalid crawl limits")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    return asyncio.run(execute(parse_args(argv)))
