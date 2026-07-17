"""Convert an NLCS Netbeheer XML file to a single map-ready GeoJSON (WGS84).

This is the conversion step of the "map-ready file hand-off" variant described in
docs/spec/03-system-architecture.md: the output GeoJSON file can be uploaded into
Dekart directly (Kepler.gl reads GeoJSON FeatureCollections natively).

Usage:
    python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
    .venv/bin/python scripts/nlcs2geojson.py data/enexis_voorbeeld_3092025_1554.xml out/enexis_voorbeeld_3092025_1554.geojson

Emits one GeoJSON FeatureCollection per drawing, containing every feature in the
file: the project boundary (AprojectReferentie) and every other feature that has a
convertible geometry, distinguished by each feature's `category` property. The
category set is open-ended (per docs/spec/02-nlcs-data-format.md) — nothing is
filtered by category name, only by whether its geometry can be converted.

Each feature's `properties` always carries the canonical attribute set (category,
handle, status, bedrijfstoestand, functie, subnettype, eigenaar, beheerder,
datum_aanleg, netgekoppeld, bovengronds, asset_id, feature_id), plus any other
simple-text child element the source feature has, snake_cased from its XML tag name
(e.g. `<Kabelopbouw>` -> `kabelopbouw`) — nothing is silently dropped.

Features without a `<Geometry>` element (e.g. AmantelbuisInhoud) are skipped, as are
features whose geometry uses a GML construct this converter can't convert (skipped,
never crashes the run). Every skip is counted and reported per category in the
conversion summary printed to stdout.
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from pyproj import Transformer

NS = {"n": "NS_NLCSnetbeheer", "gml": "http://www.opengis.net/gml/3.2"}
# EPSG:7415 is RD New + NAP height; planar part equals EPSG:28992.
TX = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)

COORD_PRECISION = 7

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

_SNAKE_RE1 = re.compile(r"(.)([A-Z][a-z]+)")
_SNAKE_RE2 = re.compile(r"([a-z0-9])([A-Z])")


def snake_case(tag):
    s = _SNAKE_RE1.sub(r"\1_\2", tag)
    s = _SNAKE_RE2.sub(r"\1_\2", s)
    return s.lower()


def parse_coords(text, dim):
    vals = text.split()
    pts = [(float(vals[i]), float(vals[i + 1])) for i in range(0, len(vals), dim)]
    return [TX.transform(x, y) for x, y in pts]


def fmt(pts):
    return [[round(lon, COORD_PRECISION), round(lat, COORD_PRECISION)] for lon, lat in pts]


def geometry_geojson(geom_el):
    """Returns (geometry, None) on success, or (None, reason) if unconvertible."""
    for tag, kind in (("Point", "Point"), ("LineString", "LineString"), ("Polygon", "Polygon")):
        g = geom_el.find(f"gml:{tag}", NS)
        if g is None:
            continue
        dim = int(g.get("srsDimension", "2"))
        if kind == "Point":
            pts = parse_coords(g.find("gml:pos", NS).text, dim)
            return {"type": "Point", "coordinates": fmt(pts)[0]}, None
        if kind == "LineString":
            pts = parse_coords(g.find("gml:posList", NS).text, dim)
            return {"type": "LineString", "coordinates": fmt(pts)}, None
        ring = g.find("gml:exterior/gml:LinearRing/gml:posList", NS)
        pts = parse_coords(ring.text, dim)
        return {"type": "Polygon", "coordinates": [fmt(pts)]}, None

    curve = geom_el.find("gml:Curve", NS)
    if curve is not None:
        segment_parent = curve.find("gml:segments", NS)
        segments = list(segment_parent) if segment_parent is not None else []
        if segments and all(s.tag.endswith("LineStringSegment") for s in segments):
            pts = []
            for seg in segments:
                dim = int(seg.get("srsDimension", "2"))
                seg_pts = parse_coords(seg.find("gml:posList", NS).text, dim)
                if pts and seg_pts and pts[-1] == seg_pts[0]:
                    pts.extend(seg_pts[1:])
                else:
                    pts.extend(seg_pts)
            return {"type": "LineString", "coordinates": fmt(pts)}, None
        return None, "Curve (non-straight segments)"

    children = list(geom_el)
    if not children:
        return None, "empty"
    return None, children[0].tag.split("}")[-1]


def extract_properties(cat, feat):
    row = {"category": cat}
    extra = {}
    for child in feat:
        tag = child.tag.split("}")[-1]
        if tag == "Geometry" or list(child):
            continue
        text = (child.text or "").strip()
        if not text:
            continue
        mapped = ATTR_MAP.get(tag)
        if mapped:
            row[mapped] = text
        else:
            extra[snake_case(tag)] = text
    props = {c: row.get(c, "") for c in ATTR_COLS}
    props.update(extra)
    return props


def main(xml_path, out_path):
    root = ET.parse(xml_path).getroot()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    features = []
    counts = {}
    skip_counts = {}

    def record_skip(cat, reason):
        key = (cat, reason)
        skip_counts[key] = skip_counts.get(key, 0) + 1

    for feat in root:
        cat = feat.tag.split("}")[-1]
        geom_el = feat.find("n:Geometry", NS)
        if geom_el is None:
            record_skip(cat, "no_geometry_element")
            continue
        geometry, reason = geometry_geojson(geom_el)
        if geometry is None:
            record_skip(cat, f"unsupported_geometry:{reason}")
            continue
        if cat == "AprojectReferentie":
            get = lambda k: (feat.findtext(f"n:{k}", "", NS) or "").strip()
            props = {
                "category": cat,
                "projectnummer": get("Projectnummer"),
                "netbeheerder": get("Netbeheerder"),
                "tekeningtype": get("Tekeningtype"),
                "toelichting": get("Toelichting"),
            }
            features.append({"type": "Feature", "geometry": geometry, "properties": props})
            counts[cat] = counts.get(cat, 0) + 1
            continue
        props = extract_properties(cat, feat)
        features.append({"type": "Feature", "geometry": geometry, "properties": props})
        counts[cat] = counts.get(cat, 0) + 1

    with open(out, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False)

    for cat in sorted(set(counts) | {c for c, _ in skip_counts}):
        converted = counts.get(cat, 0)
        skips = {reason: n for (c, reason), n in skip_counts.items() if c == cat}
        line = f"{cat}: {converted} converted"
        if skips:
            detail = ", ".join(f"{reason}={n}" for reason, n in sorted(skips.items()))
            line += f" | skipped: {detail}"
        print(line)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("xml_path", help="NLCS Netbeheer XML file to convert")
    parser.add_argument("out_path", help="output .geojson file path")
    args = parser.parse_args()
    main(args.xml_path, args.out_path)
