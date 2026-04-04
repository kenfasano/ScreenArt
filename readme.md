# SASS — Screen Art Slideshow
## Claude Project Instructions

### What is SASS?
SASS (Screen Art Slideshow) is a personal macOS SwiftUI app by Kenny Fasano (kenfasano) that displays generative art images from ScreenArt across all connected monitors. It is a non-sandboxed app for personal use only, built for Mac M1 (arm64), targeting macOS 14.0+.

### Repository
- GitHub: `git@github.com:kenfasano/SASS.git`
- Local: `~/Xcode/SASS/`
- Sync script: `~/Xcode/SASS/sync.sh` (stages, commits with prompt, pushes)
- Build script: `~/Xcode/SASS/build.sh` (compiles with swiftc, assembles .app bundle)

### Build Situation
Xcode 26.4 (the current release as of April 2026) has a bug where `xcodebuild` hangs on "Discovering version info for clang". `swiftc` itself works fine. **All builds are done via `build.sh`**, which calls `swiftc` directly and assembles a proper `.app` bundle with ad-hoc code signing. Do not attempt to fix the Xcode build system hang — work around it with `build.sh`.

```bash
cd ~/Xcode/SASS
./build.sh           # debug build
./build.sh release   # optimized build
cp -r build/SASS.app /Applications/
```

### Project Structure
```
~/Xcode/SASS/
  SASS/
    SASSApp.swift        — app entry point, AppDelegate, menu bar setup
    ScreenWindow.swift   — full-screen NSWindow per monitor, quit on click/keypress
    ImageLoader.swift    — loads image URLs from TransformedImages, sorted newest-first
    SlideshowView.swift  — SwiftUI ZStack view + SlideshowController
    Info.plist
    SASS.entitlements    — sandbox explicitly disabled
    SASS.icns            — app icon (generated from ScreenArt mandala image)
  SASS.xcodeproj/
  build/                 — compiled output, git-ignored
  build.sh
  sync.sh
  .gitignore
```

### Image Source
```
/Users/kenfasano/Scripts/ScreenArt/Images/TransformedImages
```
Images are JPEG, sorted newest-first. The directory is read at startup and refreshed occasionally (1-in-20 chance per slot cycle) to pick up new ScreenArt output automatically.

### Architecture — SlideshowView.swift

**ImageLayer struct**: holds `NSImage`, `position: CGPoint`, `size: CGSize`, `opacity: Double`, `transition: AnyTransition`. Each layer is independent.

**SlideshowController (@MainActor, ObservableObject)**:
- `slotCount = 21` independent async Task slots, each running `runSlot()` concurrently
- Slots are staggered at launch so they don't all fire simultaneously
- Each slot independently: waits (random Fibonacci seconds) → picks random image → fades in → holds (random Fibonacci seconds) → fades out → repeats
- Fibonacci timing: `[1, 2, 3, 5, 8, 13]` seconds, picked randomly and independently for wait interval and hold duration
- Image sizes: 10%–55% of screen's shorter dimension, aspect-ratio preserved, capped to view bounds
- Position: random, guaranteed fully on-screen (safe range guards prevent Range crash)

**Transitions**: each layer gets a random `.asymmetric(insertion:removal:)` transition chosen independently from catalog arrays (`insertionTransitions`, `removalTransitions`). Animation curves also chosen randomly from separate insertion/removal catalogs (spring/bouncy for insertion, easeOut/linear for removal).

**Blend mode**: `.screen` on each image layer — makes pure black pixels transparent so black-background ScreenArt images don't occlude layers beneath them.

**Crash fix**: `makeLayer()` returns `Optional<ImageLayer>` — returns nil if `viewSize` is zero or if computed ranges would be invalid. `runSlot()` skips nil layers with `guard let`.

### ScreenWindow.swift
- One `NSWindow` per `NSScreen.screens`
- `NSWindow.Level.screenSaver` — covers Dock and menu bar
- `collectionBehavior`: `.canJoinAllSpaces`, `.fullScreenPrimary`, `.stationary`
- Quit on any keypress or mouse click
- `super.init` does NOT pass `screen:` parameter (causes error on macOS 26.4)

### Known Issues / Quirks
- Xcode 26.4 `xcodebuild` hangs — use `build.sh` workaround
- `.move` and `.slide` transitions clip to ZStack bounds — images near edges look correct, center images slide from further away
- Memory growth possible with 21 slots at full resolution — monitor with Activity Monitor

### Planned / In Progress
- IOKit display sleep prevention (prevent monitors sleeping while SASS runs)
- Runtime config file (adjust slot count, Fibonacci values, size fractions without recompiling)
- Possibly: per-image transition logging for tuning

### TransitionSampler Playground
A SwiftUI Playground at `TransitionSampler.playground` exists for previewing transitions interactively. Platform must be set to **macOS** in playground settings or it will be very slow. Space bar toggles the preview, auto-cycle available.

### Style / Conventions
- Swift with type safety, no `// type: ignore`
- `@MainActor` on controller classes
- Async/await with structured concurrency (Task slots)
- No storyboards, no NIBs — pure SwiftUI + AppKit
- Kenny's machine: Mac mini M1, 16GB, macOS 26.4, two 1080p Dell monitors
