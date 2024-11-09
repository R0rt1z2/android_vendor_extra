import os
import argparse
import json

from hashlib import md5
from re import search, sub
from glob import glob
from pathlib import Path
from datetime import datetime as dt

def get_prop(key, fallback=None, file="system/build.prop"):
    try:
        with open(file, "r") as f:
            data = f.read()
            match = search(rf"(?<={key}=).*", data)
            if match:
                return match.group(0)
            if fallback:
                match_fallback = search(rf"(?<={fallback}=).*", data)
                return match_fallback.group(0) if match_fallback else None
    except FileNotFoundError:
        print(f"Error: {file} not found.")
    return None


def find_latest_zip(version, work_dir):
    files = glob(str(Path(work_dir) / f"lineage-{version}*.zip"))
    return max(files, key=os.path.getctime) if files else None


def md5_hash(file_path):
    with open(file_path, "rb") as f:
        return md5(f.read()).hexdigest()


def build_url(code, date, fname):
    return f"https://github.com/r0rt1z2-releases/LineageOS_{code}/releases/download/{date}/{fname}"


def main(work_dir):
    build_prop = Path(work_dir) / "system/build.prop"

    version = get_prop("ro.lineage.build.version", "ro.cm.build.version",
                       build_prop)
    timestamp = get_prop("ro.build.date.utc", file=build_prop)
    incr = get_prop("ro.build.version.incremental", file=build_prop)
    code = get_prop("ro.lineage.device", "ro.cm.device", build_prop)

    if not all([version, timestamp, incr, code]):
        print("Error: Missing required properties in build.prop")
        return

    zip_path = find_latest_zip(version, work_dir)
    if not zip_path:
        print(f"Error: No zip file found for version {version} in {work_dir}")
        return

    fname = Path(zip_path).name
    file_id = md5_hash(zip_path)
    size = Path(zip_path).stat().st_size
    url = build_url(code,
                    dt.utcfromtimestamp(int(timestamp)).strftime("%Y%m%d"),
                    fname)

    ota_data = {
        "response": [{
            "datetime": int(timestamp),
            "filename": fname,
            "id": file_id,
            "romtype": "unofficial",
            "size": size,
            "url": url,
            "version": version
        }]
    }

    print(json.dumps(ota_data, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate OTA JSON for LineageOS builds.")
    parser.add_argument(
        "--work-dir",
        type=str,
        default=".",
        help=
        "Specify the working directory for build.prop and zip files (default: current directory)"
    )
    args = parser.parse_args()
    main(args.work_dir)
