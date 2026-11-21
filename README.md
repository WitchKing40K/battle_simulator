# Battle Simulator

A real-time pygame-ce battle prototype with a bordered 4 km × 4 km grass field, camera panning,
cursor-centered zoom, and ten 50 m × 50 m test units (eight friendly, two enemy).
Each block starts with 500 medieval infantry. Units march at up to
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
- Hover over a unit to see how many men are alive and its vigour. Drag the middle mouse
  button to pan. Scroll to zoom around the cursor.
- Use the bottom-right controls to run at 1×, 2×, or 5× speed, or pause the
  battle. You can still select units and give orders while paused. Choose a
  speed to resume and carry out those orders.
- Press Home to fit the whole field into the view, or Escape to quit. Resize the window freely.

Positions and destinations are in meters, with X east and Y north. Selection and
orders use the same camera transforms as the map. Grass detail stays anchored to the field as you pan and zoom.
At extreme zoom-out, units can
be smaller than a pixel and precise clicking is difficult; box selection still
uses their actual world bounds. Camera and selection operations work at every
speed, including while paused.

## Group movement

Group orders assign destination slots to minimize the sum of straight-line
distances from the units' current positions. Each unit takes its own direct
route at its own speed, so units can arrive at different times. Friendly units
can overlap while moving. The final formation keeps its requested shape and
orientation.

Each unit turns toward its direction of travel while moving and toward the
ordered facing after arrival. Angular speed is the marching speed divided by
the distance from the center to an outer corner. For a 50 m block moving at
10 m/s, a 90-degree turn takes about 5.6 seconds. The same turn rate applies
during engagements.

Blocks, selection outlines, and order previews rotate freely to any facing angle.
Right-drag at any angle to choose the final orientation; individual units finish
turning after arrival. Facing arrows show block orientation. Rotated final layouts preserve at least
15 m between rotated square edges. Right-drag formation spacing stays
the same at every angle. Map boundaries still constrain movement.

Opponents automatically engage when the gap between their rotated square edges is at most
50 m. The nearest opponents are matched first. A free unit can also engage an enemy
that is already engaged. Closing units stop at square-edge contact with free
allies. If the primary pair stalls, a reinforcement that gets within fighting
range can take over the fight. Either member of the primary pair can use its
available movement to close the gap. Reinforcements hold their facing while
in fighting range.
Both units cancel their orders and close at their movement speeds until the gap
between their rotated square footprints is 8 m. The primary pair turns to face
each other using the normal turn rate, adjusting spacing as their footprints
rotate. Move orders are ignored
for engaged units; other selected units can still receive orders. Each fighting
unit inflicts a base of one casualty per simulated second, split evenly among its opponents
in fighting range. Each unit accumulates fractional losses until they add up to
whole casualties. Units disappear when their count reaches zero. Casualties
follow simulation speed and stop while paused.

Units start with 100 vigour. Marching drains 0.1 vigour per simulated second
spent moving, and fighting drains 1 per simulated second regardless of opponent
count. At zero vigour, units deal 50% less damage and take 50% more. Both
modifiers scale linearly with vigour lost and multiply when applied to the
same attack.

The HUD distinguishes units closing on an enemy, units within fighting range, and passively engaged reinforcements. Fighting and passively
engaged allies are solid to units moving freely.
A unit that reaches the rear or side of a solid ally stops at contact,
cancels its order, and joins the engagement passively. It then settles toward
its ally. While closing, fighting, or providing passive support, engaged allies
can share up to 20% of the smaller unit’s footprint area, measured from the
intersection of their rotated squares. More units can
pile up against the reinforcement.
Passive units turn toward the enemy as clearance allows, become
fighters within 8 m of an opposing footprint, and become free if they lose their chain of
contact to the fight.

`combat.py` owns engagement acquisition, contact movement, and facing.
`maneuvers.py` provides turning helpers. `pathfinding.py` provides routing, minimum-cost
slot assignment, and swept movement checks.
`units.py` owns selection, formation slots, and simulation; `selection.py` handles
mouse gestures, and `main.py` renders the field, facing, and movement orders.

## Verification

```sh
python -m unittest discover -s tests -v
```

Tests cover selection, enemies, drag threshold, box intersection, formation
spacing, retargeting, frame-rate independence, and camera transforms across zooms.
Movement tests cover independent speeds, minimum-distance slot assignment,
overlapping destinations, and final facing.

Combat tests cover range, nearest pairing, independent engagements, exact fighting range,
facing, unequal sizes and speeds, formation interruption, order priority, and frame-rate independence.
