# RobotStudio Smart Components Implementation Guide
## Project 18 — Digital Twin Commissioning: Automated Tray-to-Box Packing

---

## 1. Overview of Smart Components Architecture

In ABB RobotStudio, **Smart Components** provide the physics, sensor behavior, dynamic part generation, and actuator logic that transform a static 3D CAD station into an active, responsive **Digital Twin**.

This project implements four specialized Smart Components:
1. `SC_VacuumGripper`: Simulates pneumatic vacuum pickup, part attachment, release, and pressure switch feedback.
2. `SC_ConveyorSystem`: Drives infeed and outfeed box transport, stop-blade detection, and exit clearance.
3. `SC_FeederStation`: Handles automated part replenishment (4-slot 2×2 part instantiation) and cavity presence sensing.
4. `SC_BoxPacker`: Mechanically links placed parts to the box so all 4 parts travel solidly with the box during outfeed discharge.

---

## 2. Component 1: `SC_VacuumGripper`

### 2.1 Internal Sub-Components
- **PlaneSensor** (`Sensor_VacuumContact`): Detects workpiece within 4.0 mm of the suction cup lip.
  - Origin: `[0.0, 0.0, 105.0]` (at the TCP)
  - Axis: `[0.0, 0.0, 1.0]`
  - Length: `40.0 mm`, Width: `40.0 mm`, Depth: `4.0 mm`
- **Attacher** (`Attacher_Grip`): Mechanically parents the gripped workpiece to `tVacuumGripper`.
  - Parent: `tVacuumGripper`
  - Child: `[Sensor_VacuumContact.Part]`
  - Mount: `False` (Keeps workpiece in its exact current global orientation)
- **Detacher** (`Detacher_Release`): Frees the workpiece from the gripper.
  - Parent: `tVacuumGripper`
  - Child: `[Sensor_VacuumContact.Part]`
- **LogicGate_AND** (`Gate_GripTrigger`): Requires BOTH vacuum signal active AND part sensor tripped.
  - Input A: `doVacuumOn`
  - Input B: `Sensor_VacuumContact.Active`
- **Delay** (`Timer_PressureSwitch`): Simulates vacuum evacuation time (150 ms) before asserting pressure confirmation.
  - Delay Time: `0.150` seconds
- **LogicGate_NOT** (`Gate_VacuumOff`): Detects falling edge of vacuum signal to trigger detachment.
  - Input: `doVacuumOn`

### 2.2 Property & Signal Binding Table
| Source Object | Source Signal | Target Object | Target Signal | Function |
|---|---|---|---|---|
| Controller | `doVacuumOn` | `Gate_GripTrigger` | `InputA` | Solenoid energize request |
| `Sensor_VacuumContact`| `Active` | `Gate_GripTrigger` | `InputB` | Workpiece physical contact |
| `Gate_GripTrigger` | `Output` | `Attacher_Grip` | `Execute` | Attach part to gripper TCP |
| `Gate_GripTrigger` | `Output` | `Timer_PressureSwitch` | `Execute` | Start 150ms evacuation timer |
| `Timer_PressureSwitch` | `Executed` | Controller | `diGripConfirmed` | Pressure switch signal <-75 kPa |
| Controller | `doVacuumOn` | `Gate_VacuumOff` | `Input` | Invert vacuum state |
| `Gate_VacuumOff` | `Output` | `Detacher_Release` | `Execute` | Detach part on vacuum release |
| `Gate_VacuumOff` | `Output` | Controller | `diGripConfirmed` (Reset) | Immediate reset of grip flag |

---

## 3. Component 2: `SC_ConveyorSystem`

### 3.1 Internal Sub-Components
- **LinearMover** (`LinearMover_Infeed`): Drives empty packing boxes along +Y direction.
  - Direction: `[0.0, 1.0, 0.0]`
  - Speed: `150.0 mm/s`
  - Mechanism/Object: `[Source_Box.GeneratedPart]`
- **LinearMover** (`LinearMover_Outfeed`): Drives full packing boxes along +Y direction.
  - Direction: `[0.0, 1.0, 0.0]`
  - Speed: `200.0 mm/s`
  - Mechanism/Object: `[Source_Box.GeneratedPart]`
- **PlaneSensor** (`Sensor_BoxAtStop`): Optical sensor mounted at the packing station stop blade.
  - Center: `[350.0, 350.0, 455.0]`
  - Extents: `Width: 60 mm, Height: 40 mm, Depth: 10 mm`
- **PlaneSensor** (`Sensor_ExitClear`): Detects whether the outfeed conveyor exit zone is unobstructed.
  - Center: `[350.0, 850.0, 455.0]`
  - Extents: `Width: 260 mm, Height: 80 mm, Depth: 50 mm`
- **Source** (`Source_Box`): Generates a new empty box at the infeed conveyor entrance.
  - Source Part: `Packing_Box` template
  - Position: `[350.0, -600.0, 435.0]`
  - Orientation: `[0.0, 0.0, 0.0]`
- **Sink** (`Sink_Box`): Automatically removes completed boxes reaching the outfeed discharge terminal.
  - Target Part: `[Source_Box.GeneratedPart]`
  - Trigger Area: Box bounding envelope at `Y > 1400.0 mm`
- **LogicGate_NOT** (`Gate_StopConveyorOnArrival`): Shuts off infeed drive once box reaches stop blade.
  - Input: `Sensor_BoxAtStop.Active`

### 3.2 Property & Signal Binding Table
| Source Object | Source Signal | Target Object | Target Signal | Function |
|---|---|---|---|---|
| Controller | `doInfeedRun` | `LinearMover_Infeed` | `Execute` | Run infeed drive motor |
| `Sensor_BoxAtStop` | `Active` | Controller | `diBoxPresent` | Inform robot box is clamped |
| `Sensor_BoxAtStop` | `Active` | `Gate_StopConveyorOnArrival` | `Input` | Box arrived at stop blade |
| `Gate_StopConveyorOnArrival` | `Output` | `LinearMover_Infeed` | `Reset` | Auto-stop infeed conveyor |
| Controller | `doOutfeedRun`| `LinearMover_Outfeed`| `Execute` | Run outfeed drive motor |
| `Sensor_ExitClear` | `Active` | Controller | `diBoxExitClear` | Inverted exit clear status |
| Controller | `doInfeedRun` (Rising)| `Source_Box` | `Execute` | Generate new empty box |

---

## 4. Component 3: `SC_FeederStation`

### 4.1 Internal Sub-Components
- **Multi-Source Generator** (`Source_FeederParts`):
  Spawns 4 distinct workpiece instances into the feeder tray cavities at 90 mm pitch:
  - Part 1: Position `[305.0, -395.0, 480.0]` (Slot 1: -45, -45)
  - Part 2: Position `[395.0, -395.0, 480.0]` (Slot 2: +45, -45)
  - Part 3: Position `[305.0, -305.0, 480.0]` (Slot 3: -45, +45)
  - Part 4: Position `[395.0, -305.0, 480.0]` (Slot 4: +45, +45)
- **LineSensor** (`Sensor_TrayLoaded`): Optical retro-reflective sensor verifying tray presence.
  - Start Point: `[460.0, -350.0, 490.0]`
  - End Point:   `[240.0, -350.0, 490.0]`
- **LogicGate_AND** (`Gate_TrayReady`): Asserts `diTrayReady` when both tray fixture is clamped and parts are sensed.

### 4.2 Property & Signal Binding Table
| Source Object | Source Signal | Target Object | Target Signal | Function |
|---|---|---|---|---|
| Controller | `doReplenishTray` | `Source_FeederParts` | `Execute` | Spawn 4 parts in feeder |
| `Sensor_TrayLoaded` | `Active` | Controller | `diTrayReady` | Feeder tray confirmed full |
| `Sensor_TrayLoaded` | `Active` | Controller | `diPartPresent` | Part available for pick |

---

## 5. Component 4: `SC_BoxPacker` (Multi-Part Rigid Parent Linking)

### 5.1 Working Principle
When the robot places each part into the box and shuts off `doVacuumOn`, the part is detached from the gripper. To prevent the parts from sliding or floating away when the box moves on the outfeed conveyor, `SC_BoxPacker` contains 4 dedicated `Attacher` components that rigidly parent each placed part to the active `Packing_Box`.

### 5.2 Internal Sub-Components
- **Attacher** (`Attach_Part_To_Box_1`): Parents Workpiece 1 to `Packing_Box`.
- **Attacher** (`Attach_Part_To_Box_2`): Parents Workpiece 2 to `Packing_Box`.
- **Attacher** (`Attach_Part_To_Box_3`): Parents Workpiece 3 to `Packing_Box`.
- **Attacher** (`Attach_Part_To_Box_4`): Parents Workpiece 4 to `Packing_Box`.
- **Demux / Slot Selector**: Routes the `PlacePart` detachment strobe to the corresponding Attacher (1 to 4).

### 5.3 Behavior During Outfeed Conveyor Movement
Because all 4 parts are children of `Packing_Box` in the RobotStudio scene tree, when `LinearMover_Outfeed` moves `Packing_Box`, all four parts move in exact mathematical synchrony with zero slip, replicating real physical friction inside the box compartments!
