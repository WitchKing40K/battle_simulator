# Battle Simulator

A real-time pygame-ce battle prototype with a bordered 4 km × 4 km grass field, camera panning,
cursor-centered zoom, and ten 50 m × 50 m test units (eight friendly, two enemy).
Each block represents about 500 medieval infantry. Units march at up to
10 meters per second.
The battlefield runs from -2,000 m to +2,000 m on each axis. Movement orders
shift formations inside the border, keeping the whole unit footprint on the field.

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

- Left-click a blue friendly unit to select it; a gold outline marks selection.
- Ctrl + left-click a friendly unit to add it to the selection or remove it.
  Ctrl-clicking empty space or enemies preserves the selection.
- Left-click empty space to deselect. Drag from empty space to box-select friendly
  units, including squares intersecting the box. Red enemy units cannot be selected.
- Right-click to move selected units into a rectangular formation centered on the
  clicked location, facing the direction of travel. Hold and drag the right button to preview a custom formation,
  then release to issue the order. The drag line sets its width and orientation;
  the formation is centered on the line midpoint, with extra units in parallel
  rows. Facing is to the left of the drag direction (drag east to face north,
  or drag north to face west); arrows preview it. Longer drags fit more columns, up to a single line of units. Green outlines
  preview destinations. Losing window focus cancels the pending gesture.
  Orders can be replaced while moving.
- Selected units always show their active movement destinations, order lines,
  and ordered facing. Hold Space to show orders for all friendly units; release
  Space to return to selected units only.
- Drag the middle mouse button to pan. Scroll to zoom around the cursor.
- Press Home to fit the whole field into the view, or Escape to quit. Resize the window freely.

Positions and destinations are in meters, with X east and Y north. Selection and
orders use the same camera transforms as the map. Grass detail stays anchored to the field as you pan and zoom.
At extreme zoom-out, units can
be smaller than a pixel and precise clicking is difficult; box selection still
uses their actual world bounds. Simulation continues during camera and selection
operations.

## Coordinated movement

Groups preserve their ranks and files relative to their current facing when
assigning destination slots. Across open ground, blocks advance together at the
slowest member's pace and maintain their relative positions. They wheel around a
shared pivot to change direction; outer blocks travel farther, while inner blocks
move more slowly. No block exceeds its own marching speed.

Orders use an assembly point behind the destination before deployment. When the
whole body cannot fit a route or a wheel, it moves in a column. Followers follow
the preceding block's trail, and the head waits for stragglers. Column spacing aims
for a 2 m gap; local maneuvering may use any nonnegative gap. The 15 m interval is
only the target spacing in the completed formation, not a movement restriction.

At deployment, blocks advance together, sharing progress so they reach their
slots together even when their approach distances differ. There is no arrival
queue. Units can overlap during free movement. Nearby orders deploy directly.
The HUD reports marching, wheeling, column movement, deployment, or engagement.
Facing arrows show block orientation. Rotated final layouts preserve at least
15 m of spacing. Map boundaries still constrain movement.

Opponents automatically engage when the gap between their square edges is at most
50 m. The nearest opponents are matched first. A free unit can also engage an enemy
that is already fighting. The newcomer closes to contact and faces that enemy;
the existing combatants retain their original engagement and facing.
Both units cancel their orders, leave any formation, and close at their movement
speeds until their axis-aligned squares touch. They stop translating at contact
and rotate to face each other using the normal turn rate. Move orders are ignored
for engaged units; other selected units can still receive orders. Engagements
persist indefinitely. There is no damage, health, morale, or attack animation.

`combat.py` owns engagement acquisition, contact movement, and facing.
`maneuvers.py` coordinates group orders. `pathfinding.py` provides rectangle routing;
free-moving units do not contribute obstacles. Engaged enemies are solid to
individual, formation, and combat movement. Contact movement stops at square
boundaries, including when additional units join an existing fight.
`units.py` owns selection, formation slots, and simulation; `selection.py` handles
mouse gestures, and `main.py` renders the field, facing, and movement orders.

## Verification

```sh
python -m unittest discover -s tests -v
```

Tests cover selection, enemies, drag threshold, box intersection, formation
spacing, retargeting, frame-rate independence, and camera transforms across zooms.
Maneuver tests cover shared pace, wheels, movement through other troops,
concurrent deployment, synchronized arrival, overlapping destinations, and final facing.

Combat tests cover range, nearest pairing, independent engagements, exact contact,
facing, unequal sizes and speeds, formation interruption, order priority, and frame-rate independence.
