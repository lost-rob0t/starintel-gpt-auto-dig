from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from .model import Document, stable_id
from .validation import validate_document

_TSHARK_FIELDS = (
    "frame.number",
    "frame.time_epoch",
    "frame.len",
    "wlan.bssid",
    "wlan.sa",
    "wlan.da",
    "wlan.ssid",
    "wlan_radio.channel",
    "radiotap.channel.freq",
    "radiotap.dbm_antsignal",
    "eth.src",
    "eth.dst",
    "ip.src",
    "ip.dst",
    "ipv6.src",
    "ipv6.dst",
    "tcp.srcport",
    "tcp.dstport",
    "udp.srcport",
    "udp.dstport",
    "_ws.col.Protocol",
)


def _iso_epoch(value: str) -> str | None:
    if not value:
        return None
    stamp = float(value)
    return datetime.fromtimestamp(stamp, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _int(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _band(frequency_mhz: int | None) -> str:
    if frequency_mhz is None:
        return "unknown"
    if 2400 <= frequency_mhz < 2500:
        return "2.4ghz"
    if 4900 <= frequency_mhz < 5925:
        return "5ghz"
    if 5925 <= frequency_mhz <= 7125:
        return "6ghz"
    return "unknown"


def _pcap_format(path: Path) -> str:
    with path.open("rb") as stream:
        magic = stream.read(4)
    if magic == b"\x0a\x0d\x0d\x0a":
        return "pcapng"
    if magic in {
        b"\xa1\xb2\xc3\xd4",
        b"\xd4\xc3\xb2\xa1",
        b"\xa1\xb2\x3c\x4d",
        b"\x4d\x3c\xb2\xa1",
    }:
        return "pcap"
    return "unknown"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_mac(value: str) -> str:
    return value.strip().lower()


def _endpoint(
    *,
    mac: str = "",
    ipv4: str = "",
    ipv6: str = "",
    port: str = "",
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if mac:
        result["mac"] = _normalize_mac(mac)
    if ipv4:
        result["ipv4"] = ipv4
    if ipv6:
        result["ipv6"] = ipv6
    parsed_port = _int(port)
    if parsed_port is not None:
        result["port"] = parsed_port
    return result


def _conversation_key(row: dict[str, str]) -> tuple[str, str, str, dict[str, Any], dict[str, Any]] | None:
    if row["tcp.srcport"] or row["tcp.dstport"]:
        layer = "tcp"
        left = _endpoint(ipv4=row["ip.src"], ipv6=row["ipv6.src"], port=row["tcp.srcport"])
        right = _endpoint(ipv4=row["ip.dst"], ipv6=row["ipv6.dst"], port=row["tcp.dstport"])
    elif row["udp.srcport"] or row["udp.dstport"]:
        layer = "udp"
        left = _endpoint(ipv4=row["ip.src"], ipv6=row["ipv6.src"], port=row["udp.srcport"])
        right = _endpoint(ipv4=row["ip.dst"], ipv6=row["ipv6.dst"], port=row["udp.dstport"])
    elif row["ipv6.src"] or row["ipv6.dst"]:
        layer = "ipv6"
        left = _endpoint(ipv6=row["ipv6.src"])
        right = _endpoint(ipv6=row["ipv6.dst"])
    elif row["ip.src"] or row["ip.dst"]:
        layer = "ip"
        left = _endpoint(ipv4=row["ip.src"])
        right = _endpoint(ipv4=row["ip.dst"])
    elif row["eth.src"] or row["eth.dst"]:
        layer = "eth"
        left = _endpoint(mac=row["eth.src"])
        right = _endpoint(mac=row["eth.dst"])
    else:
        return None

    left_key = json.dumps(left, sort_keys=True, separators=(",", ":"))
    right_key = json.dumps(right, sort_keys=True, separators=(",", ":"))
    if left_key <= right_key:
        return layer, left_key, right_key, left, right
    return layer, right_key, left_key, right, left


def iter_tshark_rows(path: Path, *, tshark: str = "tshark") -> Iterator[dict[str, str]]:
    command = [
        tshark,
        "-n",
        "-r",
        str(path),
        "-T",
        "fields",
        "-E",
        "separator=/t",
        "-E",
        "quote=d",
        "-E",
        "occurrence=f",
    ]
    for field in _TSHARK_FIELDS:
        command.extend(("-e", field))

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None
    reader = csv.reader(process.stdout, delimiter="\t", quotechar='"')
    for values in reader:
        padded = list(values[: len(_TSHARK_FIELDS)])
        padded.extend("" for _ in range(len(_TSHARK_FIELDS) - len(padded)))
        yield dict(zip(_TSHARK_FIELDS, padded, strict=True))

    stderr = process.stderr.read() if process.stderr is not None else ""
    status = process.wait()
    if status != 0:
        raise RuntimeError(f"tshark failed with exit status {status}: {stderr.strip()}")


def _document(
    dtype: str,
    dataset: str,
    *,
    doc_id: str,
    data: dict[str, Any],
    title: str,
    related_ids: Sequence[str] = (),
    imported_from: str = "",
) -> dict[str, Any]:
    document = Document.create(
        dtype,
        dataset,
        doc_id=doc_id,
        title=title,
        data=data,
        related_ids=list(related_ids),
        provenance={
            "collector": "starintel-wardrive",
            "collector_type": "network-capture",
            "tool": "tshark",
            "pipeline": "wardrive-pcap",
            "imported_from": imported_from,
        },
    ).to_dict()
    validate_document(document)
    return document


def pcap_documents_from_rows(
    path: Path,
    rows: Iterable[dict[str, str]],
    *,
    dataset: str = "wardrive",
    file_uri: str | None = None,
) -> list[dict[str, Any]]:
    source = path.resolve()
    source_uri = file_uri or source.as_uri()
    file_sha256 = _sha256_file(source)
    capture_id = stable_id("pcap-capture", dataset, file_sha256)
    packet_count = 0
    capture_start: str | None = None
    capture_end: str | None = None

    networks: dict[str, dict[str, Any]] = {}
    stations: dict[str, dict[str, Any]] = {}
    conversations: dict[tuple[str, str, str], dict[str, Any]] = {}

    for row in rows:
        packet_count += 1
        timestamp = _iso_epoch(row["frame.time_epoch"])
        frame_number = _int(row["frame.number"]) or packet_count
        frame_len = _int(row["frame.len"]) or 0
        if timestamp:
            capture_start = capture_start or timestamp
            capture_end = timestamp

        bssid = _normalize_mac(row["wlan.bssid"]) if row["wlan.bssid"] else ""
        if bssid:
            network = networks.setdefault(
                bssid,
                {
                    "bssid": bssid,
                    "security": "unknown",
                    "band": "unknown",
                    "observations": 0,
                    "source_network_id": bssid,
                },
            )
            network["observations"] += 1
            if row["wlan.ssid"]:
                network["ssid"] = row["wlan.ssid"]
            channel = _int(row["wlan_radio.channel"])
            if channel is not None:
                network["channel"] = channel
            frequency = _int(row["radiotap.channel.freq"])
            if frequency is not None:
                network["frequency_mhz"] = frequency
                network["band"] = _band(frequency)
            signal = _int(row["radiotap.dbm_antsignal"])
            if signal is not None:
                network["signal_dbm"] = signal
            if timestamp:
                network["first_seen"] = min(network.get("first_seen", timestamp), timestamp)
                network["last_seen"] = max(network.get("last_seen", timestamp), timestamp)

        station_mac = _normalize_mac(row["wlan.sa"]) if row["wlan.sa"] else ""
        if station_mac:
            station = stations.setdefault(
                station_mac,
                {
                    "mac": station_mac,
                    "station_type": "unknown",
                    "observations": 0,
                    "packets": 0,
                    "data_bytes": 0,
                    "source_device_id": station_mac,
                },
            )
            station["observations"] += 1
            station["packets"] += 1
            station["data_bytes"] += frame_len
            if bssid:
                station["last_bssid"] = bssid
                observed_type = "ap" if station_mac == bssid else "station"
                current_type = station.get("station_type", "unknown")
                if current_type == "unknown":
                    station["station_type"] = observed_type
                elif current_type != observed_type:
                    station["station_type"] = "unknown"
            signal = _int(row["radiotap.dbm_antsignal"])
            if signal is not None:
                station["signal_dbm"] = signal
            if timestamp:
                station["first_seen"] = min(station.get("first_seen", timestamp), timestamp)
                station["last_seen"] = max(station.get("last_seen", timestamp), timestamp)

        conversation = _conversation_key(row)
        if conversation is None:
            continue
        layer, left_key, right_key, left_endpoint, right_endpoint = conversation
        key = (layer, left_key, right_key)
        record = conversations.setdefault(
            key,
            {
                "layer": layer,
                "a_endpoint": left_endpoint,
                "b_endpoint": right_endpoint,
                "protocols": [],
                "a_packets": 0,
                "b_packets": 0,
                "a_bytes": 0,
                "b_bytes": 0,
                "first_frame_num": frame_number,
                "last_frame_num": frame_number,
            },
        )
        original_left = _endpoint(
            mac=row["eth.src"],
            ipv4=row["ip.src"],
            ipv6=row["ipv6.src"],
            port=row["tcp.srcport"] or row["udp.srcport"],
        )
        original_left_key = json.dumps(original_left, sort_keys=True, separators=(",", ":"))
        if original_left_key == left_key:
            record["a_packets"] += 1
            record["a_bytes"] += frame_len
        else:
            record["b_packets"] += 1
            record["b_bytes"] += frame_len
        record["last_frame_num"] = frame_number
        if timestamp:
            record["started_at"] = min(record.get("started_at", timestamp), timestamp)
            record["ended_at"] = max(record.get("ended_at", timestamp), timestamp)
        protocol = row["_ws.col.Protocol"].strip().lower()
        for item in (layer, protocol):
            if item and item not in record["protocols"]:
                record["protocols"].append(item)

    capture_data: dict[str, Any] = {
        "capture_id": capture_id,
        "file_uri": source_uri,
        "file_sha256": file_sha256,
        "format": _pcap_format(source),
        "file_size_bytes": source.stat().st_size,
        "packet_count": packet_count,
        "capture_software": "tshark",
    }
    if capture_start:
        capture_data["capture_start"] = capture_start
    if capture_end:
        capture_data["capture_end"] = capture_end
    if capture_start and capture_end:
        started = datetime.fromisoformat(capture_start.replace("Z", "+00:00"))
        ended = datetime.fromisoformat(capture_end.replace("Z", "+00:00"))
        capture_data["duration_seconds"] = max(0.0, (ended - started).total_seconds())

    documents = [
        _document(
            "pcap-capture",
            dataset,
            doc_id=capture_id,
            data=capture_data,
            title=f"PCAP capture {source.name}",
            imported_from=source_uri,
        )
    ]

    for bssid, data in sorted(networks.items()):
        doc_id = stable_id("wireless-network", dataset, capture_id, bssid)
        documents.append(
            _document(
                "wireless-network",
                dataset,
                doc_id=doc_id,
                data=data,
                title=data.get("ssid") or bssid,
                related_ids=(capture_id,),
                imported_from=source_uri,
            )
        )

    for mac, data in sorted(stations.items()):
        doc_id = stable_id("wireless-station", dataset, capture_id, mac)
        documents.append(
            _document(
                "wireless-station",
                dataset,
                doc_id=doc_id,
                data=data,
                title=mac,
                related_ids=(capture_id,),
                imported_from=source_uri,
            )
        )

    for key, data in sorted(conversations.items(), key=lambda item: item[0]):
        layer, left_key, right_key = key
        conversation_id = stable_id("network-conversation", dataset, capture_id, layer, left_key, right_key)
        data["conversation_id"] = conversation_id
        data["capture_id"] = capture_id
        if data.get("started_at") and data.get("ended_at"):
            started = datetime.fromisoformat(data["started_at"].replace("Z", "+00:00"))
            ended = datetime.fromisoformat(data["ended_at"].replace("Z", "+00:00"))
            data["duration_seconds"] = max(0.0, (ended - started).total_seconds())
        documents.append(
            _document(
                "network-conversation",
                dataset,
                doc_id=conversation_id,
                data=data,
                title=f"{layer} conversation",
                related_ids=(capture_id,),
                imported_from=source_uri,
            )
        )

    return documents


def ingest_pcap(
    source: str | Path,
    *,
    dataset: str = "wardrive",
    tshark: str = "tshark",
    file_uri: str | None = None,
) -> list[dict[str, Any]]:
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(path)
    return pcap_documents_from_rows(
        path,
        iter_tshark_rows(path, tshark=tshark),
        dataset=dataset,
        file_uri=file_uri,
    )
