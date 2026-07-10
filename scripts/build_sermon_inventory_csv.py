#!/usr/bin/env python3
"""Build BIC-Sermon-Inventory.csv with YouTube metadata and all pack paths."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

EDITOR = Path("/Users/praison/praisonai-audio-editor")
YAML_DIR = Path("/Users/praison/praisonaippt/examples")
PACK1 = Path("/Users/praison/Downloads/BIC-Sermon-Deck-Pack")
PACK2 = Path("/Users/praison/Downloads/BIC-Sermon-Deck-Pack-2")
OUT = Path("/Users/praison/Downloads/BIC-Sermon-Inventory.csv")

PACK1_ROWS = [
    ("Mt1NZPzalvo", "5m42_to_49m22", "00:05:42", "00:49:22", "authority_over_death.yaml"),
    ("STWhp-VPVbY", "full", "00:00:00", "end", "god_is_good_all_the_time.yaml"),
    ("TLnGSLAINBw", "24m26_to_1h02m08", "00:24:26", "01:02:08", "freedom_in_spirit.yaml"),
    ("thB7DNrrfrI", "1h02m34_to_1h46m41", "01:02:34", "01:46:41", "job_sickness.yaml"),
    ("_11xTbG4wzo", "1h00m47_to_1h58m32", "01:00:47", "01:58:32", "reign_in_life.yaml"),
    ("TBq3EM8vm0U", "1h03m21_to_2h15m26", "01:03:21", "02:15:26", "love_of_god.yaml"),
    ("i-NGDkTeI6E", "54m46_to_2h00m43", "00:54:46", "02:00:43", "receive_a_hundredfold_now.yaml"),
    ("gOrYG7pDcbk", "1h28m34_to_2h27m34", "01:28:34", "02:27:34", "they_didnt_wait_for_god.yaml"),
    ("beKvRRD_b3c", "1h25m46_to_2h24m14", "01:25:46", "02:24:14", "how_to_come_out_of_testing_and_trials.yaml"),
    ("OTEB4s6GyEY", "36m56_to_1h34m50", "00:36:56", "01:34:50", "freedom_from_all_your_troubles.yaml"),
    ("oclDCqUsFM8", "1h14m13_to_2h07m59", "01:14:13", "02:07:59", "100_fold_blessing.yaml"),
]

PACK2_CROP = {
    "z3z1BsilJbA": ("00:49:07", "01:14:23"),
    "2HvVrE698Po": ("00:53:18", "01:20:58"),
    "3-oz3g2foCY": ("00:39:17", "01:14:07"),
    "pgYkdVyj7R4": ("00:47:21", "01:28:26"),
    "aaq6bWK0kSs": ("00:54:46", "01:32:16"),
    "LLZhFYDUXRI": ("00:52:17", "01:38:14"),
    "mw7d4zY75LU": ("00:51:03", "01:41:27"),
    "DF46Ce8Qp0s": ("01:01:00", "01:43:33"),
    "RXcnbvcXkYU+kVGjQRlLZxk": ("42:42→end | 0→12:54", "merged"),
    "VjjYOKni7vY": ("00:22:54", "end"),
    "BrHrmowpAUg": ("00:05:19", "00:39:33"),
    "2mdU9czZ2E8+eHq2f86DyrI": ("6:18→end | full", "merged"),
    "_scM90efH1E": ("00:00:00", "end"),
    "oMe-lhWDsdg": ("00:00:00", "end"),
    "cppgcxw-C_Y": ("00:40:53", "01:10:14"),
}

FIELDS = [
    "pack",
    "pack_name",
    "video_id",
    "source_url",
    "source_title",
    "upload_date",
    "channel",
    "full_video_duration_sec",
    "crop_start",
    "crop_end",
    "merged",
    "clip_duration_sec",
    "word_count",
    "yaml_title",
    "yaml_file",
    "yaml_path",
    "stem",
    "m4a_path",
    "transcript_txt",
    "transcript_json",
    "full_download_path",
]


def read_yaml_title(yaml_name: str) -> str:
    for line in (YAML_DIR / yaml_name).read_text(encoding="utf-8").splitlines():
        if line.startswith("presentation_title:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return yaml_name.replace(".yaml", "")


def yt_meta(video_id: str) -> dict:
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "python3",
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--no-warnings",
        "--print",
        "%(id)s\t%(title)s\t%(upload_date)s\t%(duration)s\t%(channel)s\t%(webpage_url)s",
        url,
    ]
    try:
        parts = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip().split("\t")
        if len(parts) >= 6:
            raw_date = parts[2]
            date_fmt = (
                f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if len(raw_date) == 8 else raw_date
            )
            return {
                "video_id": parts[0],
                "source_title": parts[1],
                "upload_date": date_fmt,
                "full_video_duration_sec": parts[3],
                "channel": parts[4],
                "source_url": parts[5],
            }
    except Exception:
        pass
    return {
        "video_id": video_id,
        "source_title": "",
        "upload_date": "",
        "full_video_duration_sec": "",
        "channel": "",
        "source_url": url,
    }


def combined_meta(video_ids: str, cache: dict) -> dict:
    ids = video_ids.split("+")
    for vid in ids:
        if vid not in cache:
            cache[vid] = yt_meta(vid)
    if len(ids) == 1:
        return cache[ids[0]]
    metas = [cache[i] for i in ids]
    return {
        "video_id": video_ids,
        "source_title": " | ".join(m["source_title"] for m in metas),
        "upload_date": " | ".join(m["upload_date"] for m in metas),
        "full_video_duration_sec": " | ".join(str(m["full_video_duration_sec"]) for m in metas),
        "channel": metas[0]["channel"],
        "source_url": " | ".join(m["source_url"] for m in metas),
    }


def ffprobe_duration(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nokey=1:noprint_wrappers=1",
                str(path),
            ],
            text=True,
        ).strip()
    except Exception:
        return ""


def word_count(stem: str) -> str:
    txt = EDITOR / f"{stem}.transcript.txt"
    if txt.exists():
        return str(len(txt.read_text(encoding="utf-8").split()))
    return ""


def clip_m4a(stem: str, video_id: str) -> Path:
    p = EDITOR / f"{stem}.m4a"
    if p.exists():
        return p
    vid = video_id.split("+")[0]
    dl = Path("/Users/praison/Downloads") / f"{vid}_full.m4a"
    return dl if dl.exists() else p


def full_downloads(video_id: str) -> str:
    paths = []
    for vid in video_id.split("+"):
        p = Path("/Users/praison/Downloads") / f"{vid}_full.m4a"
        if p.exists():
            paths.append(str(p))
    return " | ".join(paths)


def pack_paths(pack_dir: Path, pack_name: str, stem: str) -> dict:
    def pick(ext: str, fallback: Path) -> str:
        p = pack_dir / f"{pack_name}{ext}"
        return str(p) if p.exists() else str(fallback)

    return {
        "m4a_path": pick(".m4a", clip_m4a(stem, stem.split("_")[0])),
        "transcript_txt": pick(".transcript.txt", EDITOR / f"{stem}.transcript.txt"),
        "transcript_json": pick(".transcript.json", EDITOR / f"{stem}.transcript.json"),
    }


def main() -> None:
    cache: dict[str, dict] = {}
    rows: list[dict] = []

    for vid, crop_label, start, end, yaml_name in PACK1_ROWS:
        stem = f"{vid}_full" if crop_label == "full" else f"{vid}_{crop_label}"
        title = read_yaml_title(yaml_name)
        meta = combined_meta(vid, cache)
        paths = pack_paths(PACK1, title, stem)
        rows.append(
            {
                "pack": "BIC-Sermon-Deck-Pack-1",
                "pack_name": title,
                "video_id": vid,
                "source_url": meta["source_url"],
                "source_title": meta["source_title"],
                "upload_date": meta["upload_date"],
                "channel": meta["channel"],
                "full_video_duration_sec": meta["full_video_duration_sec"],
                "crop_start": start,
                "crop_end": end,
                "merged": "no",
                "clip_duration_sec": ffprobe_duration(Path(paths["m4a_path"])),
                "word_count": word_count(stem),
                "yaml_title": title,
                "yaml_file": yaml_name,
                "yaml_path": str(YAML_DIR / yaml_name),
                "stem": stem,
                "full_download_path": full_downloads(vid),
                **paths,
            }
        )

    pack2 = json.loads((PACK2 / "sermon_video_map.json").read_text(encoding="utf-8"))
    for item in pack2:
        vid = item["video_id"]
        stem = item["stem"]
        yaml_path = Path(item["yaml_source"])
        yaml_name = yaml_path.name
        title = read_yaml_title(yaml_name)
        meta = combined_meta(vid, cache)
        crop = PACK2_CROP.get(vid, ("", ""))
        rows.append(
            {
                "pack": "BIC-Sermon-Deck-Pack-2",
                "pack_name": item["pack_name"],
                "video_id": vid,
                "source_url": meta["source_url"],
                "source_title": meta["source_title"],
                "upload_date": meta["upload_date"],
                "channel": meta["channel"],
                "full_video_duration_sec": meta["full_video_duration_sec"],
                "crop_start": crop[0],
                "crop_end": crop[1],
                "merged": "yes" if "+" in vid else "no",
                "clip_duration_sec": ffprobe_duration(Path(item["m4a"])),
                "word_count": word_count(stem),
                "yaml_title": title,
                "yaml_file": yaml_name,
                "yaml_path": str(yaml_path),
                "stem": stem,
                "m4a_path": item["m4a"],
                "transcript_txt": item["transcript_txt"],
                "transcript_json": item["transcript_json"],
                "full_download_path": full_downloads(vid),
            }
        )

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
