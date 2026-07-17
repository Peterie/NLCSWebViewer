"""Convert an NLCS Netbeheer XML file to map-ready CSVs (WGS84, WKT geometry).

This is the conversion step of the "map-ready file hand-off" variant described in
docs/spec/03-system-architecture.md: the output CSVs can be uploaded into Dekart
directly (each CSV has a lowercase `geometry` WKT column that Kepler.gl picks up).

Usage:
    python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
    .venv/bin/python scripts/nlcs2csv.py data/enexis_voorbeeld_3092025_1554.xml out/

Emits one CSV per layer group:
  boundary.csv  - project area polygon (AprojectReferentie)
  lines.csv     - LSkabel, MSkabel, Amantelbuis
  points.csv    - LSmof, LSoverdrachtspunt, OVLoverdrachtspunt
  areas.csv     - LSkast, MSstation

Feature categories not in the groups above are counted as UNMAPPED and skipped,
as are features without geometry (e.g. AmantelbuisInhoud).
"""

import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from pyproj import Transformer

NS = {"n": "NS_NLCSnetbeheer", "gml": "http://www.opengis.net/gml/3.2"}
# EPSG:7415 is RD New + NAP height; planar part equals EPSG:28992.
TX = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)

LINE_CATS = {"LSkabel", "MSkabel", "Amantelbuis"}
POINT_CATS = {"LSmof", "LSoverdrachtspunt", "OVLoverdrachtspunt"}
AREA_CATS = {"LSkast", "MSstation"}

ATTR_COLS = [
    "category", "handle", "status", "bedrijfstoestand", "functie",
    "subnettype", "eigenaar", "beheerder", "datum_aanleg",
    "netgekoppeld", "bovengronds", "asset_id", "feature_id",
]
ATTR_MAP = {
    "Handle": "handle", "Status": "status", "Bedrijfstoestand": "bedrijfstoestand",
    "Functie": "functie", "Subnettype": "subnettype", "Eigenaar": "eigenaar",
    "Beheerder": "beheerder", "DatumAanleg": "datum_aanleg",
    "NetGekoppeld": "netgekoppeld", "Bovengronds": "bovengronds",
    "AssetId": "asset_id", "ID": "feature_id",
}


def parse_coords(text, dim):
    vals = text.split()
    pts = [(float(vals[i]), float(vals[i + 1])) for i in range(0, len(vals), dim)]
    return [TX.transform(x, y) for x, y in pts]


def fmt(pts):
    return ", ".join(f"{lon:.7f} {lat:.7f}" for lon, lat in pts)


def geometry_wkt(geom_el):
    for tag, kind in (("Point", "POINT"), ("LineString", "LINESTRING"), ("Polygon", "POLYGON")):
        g = geom_el.find(f"gml:{tag}", NS)
        if g is None:
            continue
        dim = int(g.get("srsDimension", "2"))
        if kind == "POINT":
            pts = parse_coords(g.find("gml:pos", NS).text, dim)
            return f"POINT ({fmt(pts)})"
        if kind == "LINESTRING":
            pts = parse_coords(g.find("gml:posList", NS).text, dim)
            return f"LINESTRING ({fmt(pts)})"
        ring = g.find("gml:exterior/gml:LinearRing/gml:posList", NS)
        pts = parse_coords(ring.text, dim)
        return f"POLYGON (({fmt(pts)}))"
    return None


def main(xml_path, out_dir):
    root = ET.parse(xml_path).getroot()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    writers = {}
    files = {}
    for name in ("lines", "points", "areas"):
        f = open(out / f"{name}.csv", "w", newline="", encoding="utf-8")
        w = csv.writer(f)
        w.writerow(["geometry"] + ATTR_COLS)
        writers[name], files[name] = w, f

    bf = open(out / "boundary.csv", "w", newline="", encoding="utf-8")
    bw = csv.writer(bf)
    bw.writerow(["geometry", "projectnummer", "netbeheerder", "tekeningtype", "toelichting"])

    counts = {}
    skipped = 0
    for feat in root:
        cat = feat.tag.split("}")[-1]
        geom_el = feat.find("n:Geometry", NS)
        if geom_el is None:
            skipped += 1
            continue
        wkt = geometry_wkt(geom_el)
        if wkt is None:
            skipped += 1
            continue
        if cat == "AprojectReferentie":
            get = lambda k: (feat.findtext(f"n:{k}", "", NS) or "").strip()
            bw.writerow([wkt, get("Projectnummer"), get("Netbeheerder"), get("Tekeningtype"), get("Toelichting")])
            counts[cat] = counts.get(cat, 0) + 1
            continue
        group = "lines" if cat in LINE_CATS else "points" if cat in POINT_CATS else "areas" if cat in AREA_CATS else None
        if group is None:
            skipped += 1
            counts[f"UNMAPPED:{cat}"] = counts.get(f"UNMAPPED:{cat}", 0) + 1
            continue
        row = {"category": cat}
        for child in feat:
            key = ATTR_MAP.get(child.tag.split("}")[-1])
            if key and child.text:
                row[key] = child.text.strip()
        writers[group].writerow([wkt] + [row.get(c, "") for c in ATTR_COLS])
        counts[cat] = counts.get(cat, 0) + 1

    for f in files.values():
        f.close()
    bf.close()
    for k in sorted(counts):
        print(f"{k}: {counts[k]}")
    print(f"skipped (no geometry): {skipped}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
