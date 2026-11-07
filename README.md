# Battle Simulator

A pygame-ce map prototype with an infinite grid, mouse panning, cursor-centered zoom, and coordinate selection.

## Run

Requires Python 3.10 or newer. From this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

On Windows, use `py` instead of `python3` and activate with `.venv\Scripts\activate`.

## Controls

- Drag any mouse button to move the map.
- Scroll the wheel to zoom around the cursor.
- Click without dragging to mark a position and show its coordinates in meters in the top panel.
- Press Home to reset the view, or Escape to quit.

The origin is at the initial window center. X increases east (right); Y increases north (up). Grid spacing adapts to zoom and is displayed in meters. Selected positions stay attached to the map as you move or zoom. Resize the window freely.

`main.py` contains the camera transforms, grid drawing, and event loop. World coordinates remain independent of screen pixels so simulation units can later use meters directly.
