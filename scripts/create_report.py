"""Convert an NLCS++ XML file and publish it as a styled Dekart report.

Formalizes the flow that was previously done by hand (see CLAUDE.md "Existing demo
reports"): convert -> upload -> style -> verify -> print the report URL. Reuses
scripts/nlcs2geojson.py for conversion and dekart/map-style.json for the layer
style and tooltip fields (see dekart/README.md for what that file captures).

Every run creates a brand-new report — there is no dataset-id tracking to update an
existing one, so re-running this on the same file leaves the previous report in
place (clean up stray reports via the Dekart UI, per CLAUDE.md).

Usage:
    .venv/bin/python scripts/create_report.py data/enexis_voorbeeld_3092025_1554.xml

Prints the report URL to stdout on success; progress goes to stderr. Non-zero exit
with a message on stderr on any failure (conversion, upload, styling, or snapshot
verification).
"""

import json
import math
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
import nlcs2geojson  # noqa: E402

STYLE_PATH = REPO_ROOT / "dekart" / "map-style.json"
RESOURCES_DIR = REPO_ROOT / "resources"

SNAPSHOT_TIMEOUT = 120


def log(msg):
    print(msg, file=sys.stderr)


def fail(msg):
    log(f"error: {msg}")
    sys.exit(1)


def dekart_call(name, args):
    proc = subprocess.run(
        ["dekart", "call", "--name", name, "--args", json.dumps(args), "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        fail(f"dekart call {name} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    try:
        return json.loads(proc.stdout)["result"]
    except (json.JSONDecodeError, KeyError) as e:
        fail(f"dekart call {name} returned unexpected output: {e}\n{proc.stdout}")


def upload_file(file_id, path, mime_type="application/geo+json"):
    proc = subprocess.run(
        ["dekart", "upload-file", "--file", str(path), "--file-id", file_id,
         "--name", path.name, "--mime-type", mime_type, "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        fail(f"dekart upload-file failed: {proc.stderr.strip() or proc.stdout.strip()}")
    payload = json.loads(proc.stdout)
    status = payload.get("complete", {}).get("status")
    if status != "completed":
        fail(f"upload did not complete (status={status!r})")


def compute_view(features, width_px=1600, height_px=900, padding=1.25):
    lons, lats = [], []
    for feat in features:
        coords = feat["geometry"]["coordinates"]

        def collect(c):
            if isinstance(c[0], (int, float)):
                lons.append(c[0])
                lats.append(c[1])
            else:
                for x in c:
                    collect(x)
        collect(coords)
    if not lons:
        fail("no coordinates found in converted GeoJSON; cannot compute a viewport")
    minlon, maxlon = min(lons), max(lons)
    minlat, maxlat = min(lats), max(lats)
    lon_span = max(maxlon - minlon, 1e-6) * padding
    lat_span = max(maxlat - minlat, 1e-6) * padding
    zoom_lon = math.log2(360 * width_px / (256 * lon_span))
    zoom_lat = math.log2(180 * height_px / (256 * lat_span))
    zoom = max(1, min(min(zoom_lon, zoom_lat), 19))
    return (minlat + maxlat) / 2, (minlon + maxlon) / 2, zoom


def build_map_config(dataset_id, label, latitude, longitude, zoom):
    style = json.loads(STYLE_PATH.read_text())
    template_layer = json.loads(json.dumps(style["config"]["visState"]["layers"][0]))
    template_layer["id"] = "main"
    template_layer["config"]["dataId"] = dataset_id
    template_layer["config"]["label"] = label
    template_layer["config"]["isVisible"] = True

    tooltip_fields = next(iter(
        style["config"]["visState"]["interactionConfig"]["tooltip"]["fieldsToShow"].values()
    ))

    map_config = {
        "version": "v1",
        "config": {
            "visState": {
                "layers": [template_layer],
                "interactionConfig": {
                    "tooltip": {
                        "enabled": True,
                        "fieldsToShow": {dataset_id: tooltip_fields},
                    }
                },
            },
            "mapState": {"latitude": latitude, "longitude": longitude, "zoom": zoom},
            "mapStyle": style["config"]["mapStyle"],
        },
    }
    return json.dumps(map_config)


def main(xml_path):
    xml_path = Path(xml_path)
    if not xml_path.exists():
        fail(f"{xml_path} does not exist")
    if not STYLE_PATH.exists():
        fail(f"{STYLE_PATH} not found — see dekart/README.md")

    name = xml_path.stem
    out_path = RESOURCES_DIR / f"{name}.geojson"

    log(f"converting {xml_path} -> {out_path}")
    try:
        nlcs2geojson.main(str(xml_path), str(out_path))
    except Exception as e:
        fail(f"conversion failed: {e}")
    geojson = json.loads(out_path.read_text())
    if not geojson["features"]:
        fail("conversion produced zero features")

    latitude, longitude, zoom = compute_view(geojson["features"])
    log(f"computed viewport: lat={latitude:.5f} lon={longitude:.5f} zoom={zoom:.1f}")

    log("creating report")
    report_id = dekart_call("create_report", {})["report"]["id"]

    log("creating dataset")
    dataset_id = dekart_call("create_dataset", {"report_id": report_id})["id"]
    dekart_call("update_dataset_name", {"dataset_id": dataset_id, "name": name})

    log("creating file and uploading")
    file_id = dekart_call("create_file", {"dataset_id": dataset_id})["file_id"]
    upload_file(file_id, out_path)

    log("applying map style")
    map_config = build_map_config(dataset_id, name, latitude, longitude, zoom)
    dekart_call("update_report_map_config", {"report_id": report_id, "map_config": map_config})
    dekart_call("update_report_title", {"report_id": report_id, "title": name})

    log("verifying via snapshot")
    proc = subprocess.run(
        ["dekart", "snapshot", "--report-id", report_id, "--out", "/dev/null",
         "--lat", str(latitude), "--lon", str(longitude), "--zoom", str(zoom),
         "--timeout", str(SNAPSHOT_TIMEOUT), "--json"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        fail(f"snapshot verification failed: {proc.stderr.strip() or proc.stdout.strip()}")

    url_proc = subprocess.run(
        ["dekart", "report-url", "--report-id", report_id, "--json"],
        capture_output=True, text=True,
    )
    if url_proc.returncode != 0:
        fail(f"could not resolve report url: {url_proc.stderr.strip()}")
    report_url = json.loads(url_proc.stdout)["report_url"]

    print(report_url)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("xml_path", help="NLCS Netbeheer XML file to convert and publish")
    args = parser.parse_args()
    main(args.xml_path)
