"""Convert an NLCS Netbeheer XML file to a single map-ready GeoJSON (WGS84).

This is the conversion step of the "map-ready file hand-off" variant described in
docs/spec/03-system-architecture.md: the output GeoJSON file can be uploaded into
Dekart directly (Kepler.gl reads GeoJSON FeatureCollections natively).

Usage:
    python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
    .venv/bin/python scripts/nlcs2geojson.py data/enexis_voorbeeld_3092025_1554.xml out/enexis_voorbeeld_3092025_1554.geojson

Emits one GeoJSON FeatureCollection per drawing, containing every feature in the
file: the project boundary (AprojectReferentie) and all recognized asset categories
(LSkabel, MSkabel, Amantelbuis, LSmof, LSoverdrachtspunt, OVLoverdrachtspunt, LSkast,
MSstation), distinguished by each feature's `category` property.

Feature categories outside that set are counted as UNMAPPED and skipped, as are
features without geometry (e.g. AmantelbuisInhoud).
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from pyproj import Transformer

NS = {"n": "NS_NLCSnetbeheer", "gml": "http://www.opengis.net/gml/3.2"}
# EPSG:7415 is RD New + NAP height; planar part equals EPSG:28992.
TX = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)

COORD_PRECISION = 7

ASSET_CATS = {
    "LSkabel", "MSkabel", "Amantelbuis",
    "LSmof", "MSmof", "LSoverdrachtspunt", "OVLoverdrachtspunt",
    "LSkast", "MSstation",
}

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
    return [[round(lon, COORD_PRECISION), round(lat, COORD_PRECISION)] for lon, lat in pts]


def geometry_geojson(geom_el):
    for tag, kind in (("Point", "Point"), ("LineString", "LineString"), ("Polygon", "Polygon")):
        g = geom_el.find(f"gml:{tag}", NS)
        if g is None:
            continue
        dim = int(g.get("srsDimension", "2"))
        if kind == "Point":
            pts = parse_coords(g.find("gml:pos", NS).text, dim)
            return {"type": "Point", "coordinates": fmt(pts)[0]}
        if kind == "LineString":
            pts = parse_coords(g.find("gml:posList", NS).text, dim)
            return {"type": "LineString", "coordinates": fmt(pts)}
        ring = g.find("gml:exterior/gml:LinearRing/gml:posList", NS)
        pts = parse_coords(ring.text, dim)
        return {"type": "Polygon", "coordinates": [fmt(pts)]}
    return None


def main(xml_path, out_path):
    root = ET.parse(xml_path).getroot()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    features = []
    counts = {}
    skipped = 0
    for feat in root:
        cat = feat.tag.split("}")[-1]
        geom_el = feat.find("n:Geometry", NS)
        if geom_el is None:
            skipped += 1
            continue
        geometry = geometry_geojson(geom_el)
        if geometry is None:
            skipped += 1
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
        if cat not in ASSET_CATS:
            skipped += 1
            counts[f"UNMAPPED:{cat}"] = counts.get(f"UNMAPPED:{cat}", 0) + 1
            continue
        row = {"category": cat}
        for child in feat:
            key = ATTR_MAP.get(child.tag.split("}")[-1])
            if key and child.text:
                row[key] = child.text.strip()
        props = {c: row.get(c, "") for c in ATTR_COLS}
        features.append({"type": "Feature", "geometry": geometry, "properties": props})
        counts[cat] = counts.get(cat, 0) + 1

    with open(out, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False)

    for k in sorted(counts):
        print(f"{k}: {counts[k]}")
    print(f"skipped (no geometry): {skipped}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("xml_path", help="NLCS Netbeheer XML file to convert")
    parser.add_argument("out_path", help="output .geojson file path")
    args = parser.parse_args()
    main(args.xml_path, args.out_path)
