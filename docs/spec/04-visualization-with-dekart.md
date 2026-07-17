# Visualization Concept: Viewing Drawings in Dekart

## Why Dekart

[Dekart](https://dekart.xyz) is an open-source, self-hosted map analytics platform — a
self-hosted alternative to services like CARTO and Felt. It was chosen because:

- **Self-hosted.** Utility network data is sensitive; the whole stack can run inside the
  organisation's own environment, with the organisation's own authentication in front of it.
- **Query-driven.** Dekart turns queries against a connected data source into map layers.
  Since the ingestion pipeline lands NLCS++ content in exactly such a data source, no custom
  map application has to be built.
- **Proven rendering.** Maps are rendered with Kepler.gl, a mature WebGL engine that
  comfortably handles the volume of a drawing (hundreds to thousands of features) and far
  beyond.
- **Shareable reports.** A composed map is saved as a report with a link — a colleague opens
  the same view without redoing any work.

Licensing, at a mention level: Dekart is available under an open-source licence (AGPL) with a
commercial licence offered alongside; the choice between them is an adoption decision, not an
architectural one.

## How a drawing becomes a map

The unit of viewing is a **report**: a saved Dekart map composed of layers, where each layer
is fed by one query against the spatial data source.

For an NLCS++ drawing the natural composition is **one layer per asset category**, plus the
project boundary:

```mermaid
flowchart LR
    subgraph report ["Dekart report — one drawing"]
        b["Boundary layer<br/>project area (polygon)"]
        l1["Cable layers<br/>LSkabel, MSkabel (lines)"]
        l2["Point layers<br/>LSmof, overdrachtspunten"]
        l3["Structure layers<br/>LSkast, MSstation (polygons)"]
    end
    store[("Spatial data source")] --> report
```

- **The project boundary** is the orientation layer: it frames the initial view and shows the
  extent within which the drawing claims to describe the network.
- **Cables** render as lines; low-voltage and medium-voltage cables belong in separate layers
  so they can be styled and toggled independently.
- **Joints and transfer points** render as points on top of the cable lines.
- **Cabinets and stations** render as polygons (they are drawn to scale in the source data;
  at wide zoom they are effectively points, so a point-style rendering may serve better until
  the user zooms in).

Because each layer is just a query, this composition is a convention, not a build artifact:
a user can add, split, or filter layers ad hoc — for example, a layer showing only joints with
a particular function.

## Styling by attributes

The attributes carried by every asset (see the format document) drive the visual language:

- **Colour by Status** — the most useful default on revision drawings: existing (*BESTAAND*),
  new, and removed assets in clearly distinct colours shows at a glance what the project
  changed.
- **Colour by Bedrijfstoestand** — operational state, e.g. highlighting anything not
  *IN BEDRIJF*.
- **Distinguish network levels** — low-voltage vs medium-voltage assets in different hues,
  matching how engineers think about the network.
- **Tooltips** — hovering or clicking an asset shows its attributes (status, owner, function,
  construction date, identifiers), which is the viewer's answer to "what is this?".

## What the user can do

- **Explore**: pan, zoom, toggle layers, inspect any asset's attributes over a recognisable
  base map.
- **Filter**: narrow a layer by any attribute — only removed assets, only assets of a given
  owner, only cables laid after a date.
- **Compose and share**: save the composed map as a report and share the link; recipients see
  the same drawing without touching the upload flow.
- **Ask new questions**: because the data is queryable, questions nobody anticipated ("how
  many joints of this type are in the project area?") are a query away rather than a feature
  request.

## What Dekart does *not* do here

Developers should know where the platform's responsibility ends and custom work (or accepted
limitation) begins:

- **No file import.** Dekart never ingests XML/GML; the ingestion half of the architecture is
  irreplaceable.
- **No CAD symbology.** The NLCS drawing standard prescribes line types, symbols, and layer
  conventions for CAD sheets. Dekart renders generic map styling (colours, widths, point
  sizes) — the map is a faithful *data* view, not a facsimile of the CAD drawing. If
  NLCS-style symbology ever becomes a hard requirement, that is custom work outside Dekart.
- **No coordinate conversion.** Dekart expects web-map-ready coordinates; the RD-to-WGS84
  conversion must have happened in the pipeline.
- **No drawing management.** Dekart knows reports and queries, not "drawings" or "revisions".
  Any lifecycle around uploaded drawings (listing, replacing, deleting, comparing revisions)
  lives in the ingestion half or its data model.
