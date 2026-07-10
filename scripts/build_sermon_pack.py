#!/usr/bin/env python3
"""Assemble a sermon deck pack directory from editor session artefacts."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

EDITOR = Path.home() / "praisonai-audio-editor"
YAML_DIR = Path(__file__).resolve().parents[1] / "examples"
DOWNLOADS = Path.home() / "Downloads"

# BIC pack-2 job list — override via future pack protocol YAML if needed
JOBS = [
    ("z3z1BsilJbA_49m07_to_1h14m23", "god_is_good_all_the_time.yaml", "z3z1BsilJbA"),
    ("2HvVrE698Po_53m18_to_1h20m58", "how_to_become_heir_of_the_world.yaml", "2HvVrE698Po"),
    ("3-oz3g2foCY_39m17_to_1h14m07", "first_adam_vs_last_adam.yaml", "3-oz3g2foCY"),
    ("pgYkdVyj7R4_47m21_to_1h28m26", "miracles_are_easy.yaml", "pgYkdVyj7R4"),
    ("aaq6bWK0kSs_54m46_to_1h32m16", "freedom_from_all_your_troubles.yaml", "aaq6bWK0kSs"),
    ("LLZhFYDUXRI_52m17_to_1h38m14", "full_restoration.yaml", "LLZhFYDUXRI"),
    ("mw7d4zY75LU_51m03_to_1h41m27", "be_fruitful_and_multiply.yaml", "mw7d4zY75LU"),
    ("DF46Ce8Qp0s_1h01m00_to_1h43m33", "why_delay.yaml", "DF46Ce8Qp0s"),
    ("RXcnbvcXkYU_42m42_to_end__kVGjQRlLZxk_start_to_12m54", "gospel.yaml", "RXcnbvcXkYU+kVGjQRlLZxk"),
    ("VjjYOKni7vY_22m54_to_end", "freedom_in_spirit.yaml", "VjjYOKni7vY"),
    ("BrHrmowpAUg_5m19_to_39m33", "why_listen_word_of_god.yaml", "BrHrmowpAUg"),
    ("2mdU9czZ2E8_6m18_to_end__eHq2f86DyrI_full", "how_to_become_heir_of_the_world.yaml", "2mdU9czZ2E8+eHq2f86DyrI"),
    ("_scM90efH1E_full", "only_one_reason_sickness.yaml", "_scM90efH1E"),
    ("oMe-lhWDsdg_full", "miracles_are_easy.yaml", "oMe-lhWDsdg"),
    ("cppgcxw-C_Y_40m53_to_1h10m14", "great_faith.yaml", "cppgcxw-C_Y"),
]


def read_title(yaml_name: str) -> str:
    for line in (YAML_DIR / yaml_name).read_text(encoding="utf-8").splitlines():
        if line.startswith("presentation_title:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return yaml_name.replace(".yaml", "")


def m4a_path(stem: str, vid: str) -> Path:
    p = EDITOR / f"{stem}.m4a"
    if p.exists():
        return p
    for part in vid.split("+"):
        d = DOWNLOADS / f"{part}_full.m4a"
        if d.exists():
            return d
    return p


def build_pack(pack_dir: Path) -> None:
    pack_dir.mkdir(parents=True, exist_ok=True)
    used: dict[str, bool] = {}
    manifest = []

    for stem, yaml_name, vid in JOBS:
        title = read_title(yaml_name)
        base = title if title not in used else f"{title} [{vid}]"
        used[base] = True

        m4a = m4a_path(stem, vid)
        json_f = EDITOR / f"{stem}.transcript.json"
        txt_f = EDITOR / f"{stem}.transcript.txt"
        yaml_f = YAML_DIR / yaml_name

        missing = [str(x) for x in (m4a, json_f, txt_f, yaml_f) if not x.exists()]
        if missing:
            raise FileNotFoundError(f"{stem}: missing {missing}")

        for src, ext in (
            (m4a, ".m4a"),
            (yaml_f, ".yaml"),
            (json_f, ".transcript.json"),
            (txt_f, ".transcript.txt"),
        ):
            shutil.copy2(src, pack_dir / f"{base}{ext}")

        manifest.append(
            {
                "pack_name": base,
                "video_id": vid,
                "stem": stem,
                "yaml_source": str(yaml_f),
                "m4a": str(pack_dir / f"{base}.m4a"),
                "yaml": str(pack_dir / f"{base}.yaml"),
                "transcript_txt": str(pack_dir / f"{base}.transcript.txt"),
                "transcript_json": str(pack_dir / f"{base}.transcript.json"),
            }
        )

    (pack_dir / "sermon_video_map.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Pack: {pack_dir}")
    print(f"Sermons: {len(manifest)}  Files: {len(list(pack_dir.iterdir()))}")
    for m in manifest:
        print(f"  • {m['pack_name']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build sermon deck pack directory")
    parser.add_argument(
        "--pack-dir",
        default=str(DOWNLOADS / "BIC-Sermon-Deck-Pack-2"),
        help="Output pack directory",
    )
    args = parser.parse_args()
    build_pack(Path(args.pack_dir).expanduser())


if __name__ == "__main__":
    main()
