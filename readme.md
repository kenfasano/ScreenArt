# ScreenArt Project Context

## Overview

ScreenArt is Kenny's personal generative art pipeline written in Python. It runs on a Mac M1 (primary) and an Arch Linux ARM64 VM under UTM (secondary). The pipeline fetches or generates source images, applies chains of raster transformers, grades each output A/B/C/F, and saves results to a watched directory. A companion SwiftUI screensaver app called **SASS** (Screen Art Slideshow) displays the output images across all connected monitors.

The project lives at `~/Scripts/ScreenArt/` on Mac and `~/mac/Scripts/ScreenArt/` on Arch. GitHub repo: `github.com/kenfasano/ScreenArt`. SASS lives at `~/Xcode/SASS/` with repo `github.com/kenfasano/SASS`.

---

## Architecture

### Pipeline flow

```
Generators → generators_in/ → ImageProcessingPipeline → transformers_out/ (A/B/C) or rejected_out/ (F)
```

The pipeline is invoked from `main.py`. Each generator writes images to its own subdirectory under `generators_in/`. The pipeline reads those images, samples 1–4 transformers using weighted-without-replacement selection, applies them in sequence, grades the result, and saves to `transformers_out/` or `rejected_out/`.

### Key files

| File | Role |
|---|---|
| `screenArt.py` | Base class: config loading, logging singleton, OS detection, path expansion, timer |
| `pipeline.py` | `ImageProcessingPipeline`: transformer sampling, grading, file routing |
| `main.py` | Entry point: instantiates generators and pipeline, runs everything |
| `screenArt.conf` | JSON config: paths, file counts, transformer list, weights |
| `grades.csv` | Accumulated grade data used to tune transformer weights |
| `parse_grades.py` | Parses log files into `grades.csv`; extracts transformer names, grades, source types |
| `logs/` | Timestamped run logs, trimmed to 10 most recent |

### Base classes

- `ScreenArt` — config, logging, OS detection (`darwin` / `linux`), `_expand_and_ensure_paths()`
- `Source(ScreenArt)` — base for network-fetching generators; shared session, retry logic
- `DrawGenerator(ScreenArt)` — base for procedural generators
- `RasterTransformer(ScreenArt)` — base for all transformers; `run(img_np) → img_np`, `metadata_dictionary`, `to_uint8()`, `to_float32()`

---

## Generators

All generators write JPEG files to `generators_in/<name>/`.

| Generator | Class | Source |
|---|---|---|
| `nasa.py` | `Nasa` | APOD pages (random dates since 2002) |
| `wiki.py` | `Wiki` | Wikimedia Commons (random or keyword search) |
| `goes.py` | `Goes` | NOAA GOES satellite imagery |
| `maps.py` | `Maps` | Map tile imagery |
| `lojong.py` | `Lojong` | Text: Tibetan lojong slogans |
| `bible.py` | `Bible` | Text: Psalms / Bible verses |
| `peace.py` | `Peace` | Text: "peace" in ~200 languages, themed color palettes |
| `bubbles.py` | `Bubbles` | Procedural: Numba JIT Lambert/Blinn-Phong sphere shading |
| `cubes.py` | `Cubes` | Procedural: isometric and perspective 3D projection |
| `kochSnowflake.py` | `KochSnowflake` | Procedural: Koch snowflake fractal |
| `hilbert.py` | `Hilbert` | Procedural: Hilbert curve |
| `peripheralDrift.py` | `PeripheralDrift` | Procedural: peripheral drift illusion |
| `staticMandala.py` | `StaticMandala` | Static: randomly picks from downloaded Wikimedia mandala JPEGs |
| `mandala_draw.py` | `MandalaDraw` | Procedural: rose curves, polygon rings, arc bursts, dot rings |

### `staticMandala.py` notes

- Input: `generators_in/static_mandalas/` — 24 downloaded Tibetan mandala JPEGs from Wikimedia Commons
- Output: a random sample copied to `generators_in/static_mandala_out/` (or similar)
- `input_dir` and `output_dir` must be **different** paths to avoid `shutil.rmtree` wiping the source

### `mandala_draw.py` notes

- Config block: `"mandala_draw": { "width": 1920, "height": 1280 }`
- File count: `"file_counts": { "mandala_draw": 3 }`
- N-fold symmetry options: `[8, 8, 12, 12, 16]` (weighted toward 8 and 12)
- Palette: base hue + hue step rotated around HSV wheel per layer
- Alpha compositing via RGBA — layers blend over dark background for luminous depth

---

## Transformers

All transformers accept and return `np.ndarray` float32 in `[0, 1]` range. Single dtype conversion happens at pipeline entry/exit.

**Active transformers** (as of recent runs):

`ChromaticAberrationTransformer`, `ColormapTransformer`, `DataMoshTransformer`, `FisheyeTransformer`, `FlipWilsonTransformer`, `FluidWarpTransformer`, `FractalWarpTransformer`, `GlitchWarpTransformer`, `HalftoneTransformer`, `KaleidoscopeTransformer`, `MeltMorphTransformer`, `OilPaintingTransformer`, `PixelSortTransformer`, `PosterizationTransformer`, `RadialWarpTransformer`, `SwirlWarpTransformer`, `ThermalImagingTransformer`, `VoronoiTransformer`, `WatercolorTransformer`, `WheelTransformer`

**Cut transformers** (poor grade data): `InvertRGBTransformer`, `DuotoneTransformer`, `TritoneTransformer`, `ThreeDExtrusionTransformer`, `XrayTransformer`, `AnamorphicTransformer`, `StippleTransformer`

### `KaleidoscopeTransformer` notes

- Folds image into N-fold radial symmetry via polar coordinate remap + `cv2.remap()`
- Segments: randomly chosen from `[4, 6, 8, 8, 12]` (8-fold weighted double)
- Centre offset: random `[-0.2, 0.2]` fraction of image dims
- Spectacular on: bubbles, cubes, peripheral_drift, static_mandalas, mandala_draw
- Config key: `"kaleidoscopetransformer"` with optional `segments`, `cx_offset`, `cy_offset`

---

## Grading

`_calculate_grade()` in `pipeline.py` scores each output on:
- **Sharpness** (Laplacian variance, peak at 150, log-penalized above)
- **Contrast** (std dev of grayscale, clipped to [0,1])
- **Highlight penalty** (tanh-based, penalizes washed-out images)
- **Clip multiplier** (0.35× if near-black or near-white with low std dev)
- **Hue diversity penalty** (caps at B if >80% of vivid pixels share a 5° hue bin)

Grade thresholds: A ≥ 0.65, B ≥ 0.50, C ≥ 0.35, F < 0.35

---

## Transformer weights

`screenArt.conf` → `"transformer_weights"` section:
- `"enabled": true/false` — set false for uniform baseline run
- `"default"` — base weights for all source types
- Per-source overrides: `"lojong"`, `"psalms"`, `"bubbles"`, `"cubes"`, `"peripheral_drift"`, `"peace"`, `"static_mandala"`, `"nasa_earth"`, `"noaa_goes"`, `"photo"`
- `"#comment"` keys are ignored by `_get_transformer_weights()` (filter: `not k.startswith('#')`)
- Source type is derived from the generator output folder name via `_SOURCE_TYPE_MAP` in `pipeline.py`

### Important config pitfall

The `mandala_draw` width/height config block belongs at the **top level** of `screenArt.conf`, **not** inside `transformer_weights`. Nesting it inside `transformer_weights` causes `_get_transformer_weights()` to attempt `float()` on a dict, throwing an error.

---

## OS / path handling

`screenArt.py` detects OS via `platform.system().lower()`. On Linux, `_expand_and_ensure_paths()` rewrites `~/Scripts/` → `~/mac/Scripts/` so all path config written for Mac resolves correctly over the sshfs mount.

Mac alias: `sa` not available in shell scripts — use `$OSTYPE` detection in `run_sa.sh` to select the correct venv.

Arch venv: `~/.venvs/screenart/` (not on the sshfs mount for performance).

---

## SASS (Screen Art Slideshow)

SwiftUI macOS screensaver-like app displaying ScreenArt output across all connected monitors.

- **Source dir**: `~/Scripts/ScreenArt/Images/TransformedImages/`
- **Slots**: 21 concurrent independent async image slots per screen
- **Timing**: Fibonacci values `[1, 2, 3, 5, 8, 13]` seconds for image lifetime and appearance intervals
- **Size**: 10–55% of shorter screen dimension
- **Blend mode**: `.blendMode(.screen)` — black backgrounds render transparent
- **Transitions**: per-layer random asymmetric insertion/removal from a catalog of 15 transitions
- **Build**: `build.sh` using `swiftc` directly (Xcode 26.4 `xcodebuild` hangs on clang probe step)
- **Sync**: `sync.sh` for git add/commit/push
- **Planned**: IOKit display sleep prevention (`IOPMAssertionCreateWithName`), runtime config file

---

## Coding conventions

- Python with type hints throughout; no `# type: ignore` except PIL tuple coercions
- All image arrays: `np.float32` in `[0, 1]`; `to_uint8()` / `to_float32()` helpers in `RasterTransformer`
- JPEG output at quality=95 everywhere
- Filenames: `{stem}-{grade}[-{mode_tag}]_{4hex}.jpeg` — 4-hex suffix prevents collision across runs
- Logging: timestamped files in `logs/`, trimmed to 10 most recent; singleton pattern
- Config comments: use `"#comment"` or `"#note"` keys (filtered at parse time, not stripped from file)
- Reformatting `screenArt.conf`: `python3 -c "import json; ...json.dump(data, f, indent=4)"`

## Transformer weights

    "transformer_weights": {
        "#comment": "Set enabled=false for a uniform baseline run. Set true to apply weights.",
        "enabled": true,
        "default": {
            "ChromaticAberrationTransformer": 1.0,
            "ColormapTransformer": 1.0,
            "DataMoshTransformer": 1.0,
            "FisheyeTransformer": 0.8,
            "FlipWilsonTransformer": 1.0,
            "FluidWarpTransformer": 1.0,
            "FractalWarpTransformer": 1.2,
            "GlitchWarpTransformer": 1.0,
            "HalftoneTransformer": 1.0,
            "KaleidoscopeTransformer": 1.0,
            "MeltMorphTransformer": 1.0,
            "OilPaintingTransformer": 1.0,
            "PixelSortTransformer": 1.0,
            "PosterizationTransformer": 1.0,
            "RadialWarpTransformer": 1.0,
            "SwirlWarpTransformer": 1.0,
            "ThermalImagingTransformer": 1.0,
            "VoronoiTransformer": 1.0,
            "WatercolorTransformer": 0.6,
            "WheelTransformer": 1.2
        },
        "photo": {
            "FractalWarpTransformer": 1.0,
            "WheelTransformer": 1.2
        },
        "lojong": {
            "#comment": "n=260. Halftone/Chromatic/Voronoi/Fractal lead; MeltMorph/Oil/Thermal suppress.",
            "ChromaticAberrationTransformer": 1.08,
            "ColormapTransformer": 1.04,
            "DataMoshTransformer": 1.01,
            "FisheyeTransformer": 0.91,
            "FlipWilsonTransformer": 1.04,
            "FluidWarpTransformer": 0.97,
            "FractalWarpTransformer": 1.06,
            "GlitchWarpTransformer": 0.95,
            "HalftoneTransformer": 1.09,
            "KaleidoscopeTransformer": 0.0,
            "MeltMorphTransformer": 0.87,
            "OilPaintingTransformer": 0.89,
            "PixelSortTransformer": 1.04,
            "PosterizationTransformer": 1.0,
            "RadialWarpTransformer": 0.98,
            "SwirlWarpTransformer": 1.02,
            "ThermalImagingTransformer": 0.87,
            "VoronoiTransformer": 1.07,
            "WatercolorTransformer": 1.01,
            "WheelTransformer": 1.04
        },
        "psalms": {
            "#comment": "n=258. Voronoi/Fluid/Poster/Wheel lead; Oil/Fisheye/Swirl/Thermal suppress. Kaleidoscope n=3 (noise) \u2192 capped at 1.2.",
            "ChromaticAberrationTransformer": 1.07,
            "ColormapTransformer": 0.98,
            "DataMoshTransformer": 0.91,
            "FisheyeTransformer": 0.8,
            "FlipWilsonTransformer": 1.05,
            "FluidWarpTransformer": 1.09,
            "FractalWarpTransformer": 0.95,
            "GlitchWarpTransformer": 1.01,
            "HalftoneTransformer": 1.06,
            "KaleidoscopeTransformer": 1.2,
            "MeltMorphTransformer": 0.9,
            "OilPaintingTransformer": 0.77,
            "PixelSortTransformer": 1.02,
            "PosterizationTransformer": 1.09,
            "RadialWarpTransformer": 0.9,
            "SwirlWarpTransformer": 0.86,
            "ThermalImagingTransformer": 0.84,
            "VoronoiTransformer": 1.13,
            "WatercolorTransformer": 0.89,
            "WheelTransformer": 1.07
        },
        "bubbles": {
            "#comment": "n=260. Halftone/DataMosh/PixelSort/Thermal lead; Chromatic/Swirl/Oil/Radial suppress. Kaleidoscope+Voronoi excluded (0.0) \u2014 intentional.",
            "ChromaticAberrationTransformer": 0.64,
            "ColormapTransformer": 1.07,
            "DataMoshTransformer": 1.16,
            "FisheyeTransformer": 1.04,
            "FlipWilsonTransformer": 1.01,
            "FluidWarpTransformer": 1.08,
            "FractalWarpTransformer": 1.02,
            "GlitchWarpTransformer": 1.03,
            "HalftoneTransformer": 1.19,
            "KaleidoscopeTransformer": 0.0,
            "MeltMorphTransformer": 1.01,
            "OilPaintingTransformer": 0.79,
            "PixelSortTransformer": 1.15,
            "PosterizationTransformer": 1.02,
            "RadialWarpTransformer": 0.83,
            "SwirlWarpTransformer": 0.79,
            "ThermalImagingTransformer": 1.07,
            "VoronoiTransformer": 0.0,
            "WatercolorTransformer": 0.83,
            "WheelTransformer": 1.02
        },
        "cubes": {
            "#comment": "n=156. Kaleidoscope/Fisheye/PixelSort lead; Wheel/Water/Voronoi suppress. Voronoi excluded (0.0) \u2014 intentional.",
            "ChromaticAberrationTransformer": 1.02,
            "ColormapTransformer": 1.0,
            "DataMoshTransformer": 1.03,
            "FisheyeTransformer": 1.08,
            "FlipWilsonTransformer": 0.99,
            "FluidWarpTransformer": 0.98,
            "FractalWarpTransformer": 1.02,
            "GlitchWarpTransformer": 1.02,
            "HalftoneTransformer": 1.03,
            "KaleidoscopeTransformer": 1.15,
            "MeltMorphTransformer": 0.99,
            "OilPaintingTransformer": 0.96,
            "PixelSortTransformer": 1.06,
            "PosterizationTransformer": 1.01,
            "RadialWarpTransformer": 0.94,
            "SwirlWarpTransformer": 1.03,
            "ThermalImagingTransformer": 0.97,
            "VoronoiTransformer": 0.0,
            "WatercolorTransformer": 0.92,
            "WheelTransformer": 0.89
        },
        "peripheral_drift": {
            "#comment": "n=520. Kaleidoscope/Water/Fisheye/Halftone lead; Thermal suppressed strongly (0.74).",
            "ChromaticAberrationTransformer": 1.04,
            "ColormapTransformer": 0.99,
            "DataMoshTransformer": 0.99,
            "FisheyeTransformer": 1.11,
            "FlipWilsonTransformer": 1.05,
            "FluidWarpTransformer": 1.01,
            "FractalWarpTransformer": 0.96,
            "GlitchWarpTransformer": 0.94,
            "HalftoneTransformer": 1.08,
            "KaleidoscopeTransformer": 1.17,
            "MeltMorphTransformer": 0.97,
            "OilPaintingTransformer": 0.93,
            "PixelSortTransformer": 1.02,
            "PosterizationTransformer": 0.95,
            "RadialWarpTransformer": 0.97,
            "SwirlWarpTransformer": 0.98,
            "ThermalImagingTransformer": 0.74,
            "VoronoiTransformer": 1.04,
            "WatercolorTransformer": 1.17,
            "WheelTransformer": 0.89
        },
        "peace": {
            "#comment": "n=104. Kaleidoscope/Water/Fractal/Chromatic lead; Thermal/Glitch/Fisheye/Voronoi suppress.",
            "ChromaticAberrationTransformer": 1.1,
            "ColormapTransformer": 1.08,
            "DataMoshTransformer": 1.01,
            "FisheyeTransformer": 0.78,
            "FlipWilsonTransformer": 1.09,
            "FluidWarpTransformer": 0.98,
            "FractalWarpTransformer": 1.15,
            "GlitchWarpTransformer": 0.76,
            "HalftoneTransformer": 1.09,
            "KaleidoscopeTransformer": 1.29,
            "MeltMorphTransformer": 0.98,
            "OilPaintingTransformer": 0.93,
            "PixelSortTransformer": 1.09,
            "PosterizationTransformer": 0.9,
            "RadialWarpTransformer": 0.94,
            "SwirlWarpTransformer": 1.03,
            "ThermalImagingTransformer": 0.72,
            "VoronoiTransformer": 0.79,
            "WatercolorTransformer": 1.25,
            "WheelTransformer": 1.06
        },
        "static_mandala": {
            "#comment": "n=156. Kaleidoscope/Chromatic/Fisheye/Halftone lead; Glitch/Thermal suppress.",
            "ChromaticAberrationTransformer": 1.12,
            "ColormapTransformer": 0.95,
            "DataMoshTransformer": 1.0,
            "FisheyeTransformer": 1.1,
            "FlipWilsonTransformer": 1.03,
            "FluidWarpTransformer": 1.06,
            "FractalWarpTransformer": 1.05,
            "GlitchWarpTransformer": 0.84,
            "HalftoneTransformer": 1.07,
            "KaleidoscopeTransformer": 1.2,
            "MeltMorphTransformer": 0.96,
            "OilPaintingTransformer": 0.94,
            "PixelSortTransformer": 1.01,
            "PosterizationTransformer": 0.95,
            "RadialWarpTransformer": 0.96,
            "SwirlWarpTransformer": 0.99,
            "ThermalImagingTransformer": 0.87,
            "VoronoiTransformer": 0.97,
            "WatercolorTransformer": 0.96,
            "WheelTransformer": 0.97
        },
        "nasa_earth": {
            "#comment": "n=104. Watercolor/Voronoi/DataMosh/Kaleidoscope lead; MeltMorph/Fractal suppress.",
            "ChromaticAberrationTransformer": 0.98,
            "ColormapTransformer": 0.9,
            "DataMoshTransformer": 1.17,
            "FisheyeTransformer": 1.09,
            "FlipWilsonTransformer": 1.05,
            "FluidWarpTransformer": 0.99,
            "FractalWarpTransformer": 0.82,
            "GlitchWarpTransformer": 0.99,
            "HalftoneTransformer": 0.95,
            "KaleidoscopeTransformer": 1.1,
            "MeltMorphTransformer": 0.79,
            "OilPaintingTransformer": 0.9,
            "PixelSortTransformer": 0.9,
            "PosterizationTransformer": 0.91,
            "RadialWarpTransformer": 1.08,
            "SwirlWarpTransformer": 1.01,
            "ThermalImagingTransformer": 0.92,
            "VoronoiTransformer": 1.23,
            "WatercolorTransformer": 1.33,
            "WheelTransformer": 0.88
        },
        "noaa_goes": {
            "#comment": "n=26. Chromatic/Halftone/Colormap lead clearly; Kaleidoscope/Thermal suppress. Many transformers n<3 so left near-neutral.",
            "ChromaticAberrationTransformer": 1.36,
            "ColormapTransformer": 1.12,
            "DataMoshTransformer": 1.0,
            "FisheyeTransformer": 0.98,
            "FlipWilsonTransformer": 0.88,
            "FluidWarpTransformer": 1.0,
            "FractalWarpTransformer": 1.0,
            "GlitchWarpTransformer": 1.02,
            "HalftoneTransformer": 1.24,
            "KaleidoscopeTransformer": 0.59,
            "MeltMorphTransformer": 0.95,
            "OilPaintingTransformer": 0.91,
            "PixelSortTransformer": 1.0,
            "PosterizationTransformer": 0.88,
            "RadialWarpTransformer": 1.0,
            "SwirlWarpTransformer": 1.0,
            "ThermalImagingTransformer": 0.59,
            "VoronoiTransformer": 0.89,
            "WatercolorTransformer": 1.0,
            "WheelTransformer": 0.97
        }
    }
