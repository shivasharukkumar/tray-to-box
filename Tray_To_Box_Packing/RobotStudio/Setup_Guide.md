# ABB RobotStudio Work Cell Setup & Commissioning Guide
## Project 18 — Digital Twin Commissioning of a Robotic Work Cell: Tray-to-Box Packing

---

## 1. Executive Setup Overview

This document provides complete, step-by-step instructions for commissioning the **Tray-to-Box Automated Robotic Work Cell** in **ABB RobotStudio 2026 / 2024 / 2023 / 2022**.

### Work Cell Parameters
- **Robot Model**: ABB IRB 1200-7/0.7 (Payload: 7.0 kg, Reach: 703 mm)
- **Controller**: ABB IRC5 / OmniCore (RobotWare 6.x or 7.x)
- **Tool**: Custom Single-Bellows Vacuum Gripper (TCP Z = +105.0 mm, Mass = 0.820 kg)
- **Feeder Station**: 4-cavity 2×2 Tray (Pitch 90 mm, Center: X = 350 mm, Y = -350 mm, Z = 465 mm)
- **Packing Station**: 4-compartment 2×2 Box (Pitch 100 mm, Center: X = 350 mm, Y = +350 mm, Z = 435 mm)
- **Conveyor System**: Infeed & Outfeed Track (Width 320 mm, Length 2200 mm along Y axis)

---

## 2. Step-by-Step Commissioning Procedure

### Step 2.1 — Create New Station & Robot System
1. Open **ABB RobotStudio**.
2. Click **File -> New -> Station** (Create an Empty Station named `Tray_To_Box_Packing_Cell`).
3. Under the **Home** ribbon tab, click **ABB Library -> IRB 1200 -> IRB 1200-7/0.7**.
4. In the Layout tree, select the robot and verify its Base Frame is at `(0, 0, 0)` mm with zero rotation.
5. In the **Home** tab, click **Robot System -> From Layout**:
   - System Name: `IRB1200_Packing_Controller`
   - RobotWare: Select **6.15** or **7.x** (Standard 6-axis robot package).
   - Options: Check **English**, **Standard I/O**, and **PC Interface**.
   - Click **Finish** and wait for the Virtual Controller to boot (Status: `Green / 1/1 Running`).

---

### Step 2.2 — Import CAD Geometries into Station (From the Dedicated `STL/` Folder)
All 3D models are neatly organized into one single dedicated folder: `Tray_To_Box_Packing/STL/`.

> [!NOTE]
> **Why STL?** STL (Stereolithography) format is natively supported across all editions of ABB RobotStudio without requiring any optional CAD Converter Add-In license. Binary STL files provide high polygon fidelity and optimal simulation performance.

1. Under the **Home** tab, click **Import Geometry -> Browse**:
   - Navigate to `Tray_To_Box_Packing/STL/`
   - Select `STL/Vacuum_Gripper.stl`
   - Select `STL/Feeder_Tray.stl`
   - Select `STL/Packing_Box.stl`
   - Select `STL/Product.stl`
   - Select `STL/Conveyor_Components.stl`
   - Select `STL/Cell_Layout_Assembly.stl`
2. In the Layout tree, set the exact **World Coordinate Transforms** for each component:

| Component Name | Position X (mm) | Position Y (mm) | Position Z (mm) | Orientation (Rx, Ry, Rz) |
|---|---|---|---|---|
| `Cell_Layout_Assembly` | 0.0 | 0.0 | 0.0 | (0°, 0°, 0°) |
| `Conveyor_Components` | 0.0 | 0.0 | 0.0 | (0°, 0°, 0°) |
| `Feeder_Tray` | 350.0 | -350.0 | 465.0 | (0°, 0°, 0°) |
| `Packing_Box` (Master Template) | 350.0 | 350.0 | 435.0 | (0°, 0°, 0°) |
| `Product` (Master Part Template) | 305.0 | -395.0 | 500.0 | (0°, 0°, 0°) |
| `Vacuum_Gripper` | Attached to robot tool flange `tool0` (see Step 2.3) |

> [!TIP]
> Setting individual colors enhances visual realism: Feeder Tray = Dark Anodized Gray (#4A4A4A), Packing Box = Kraft Brown (#C49A6C), Product = Gloss Cobalt Blue (#0055A5), Vacuum Gripper = Aluminum/Black (#2B2B2B), Conveyor Frame = Traffic Yellow / Galvanized Steel (#E5A91A).

---

### Step 2.3 — Create Robot Tool Mechanism (`tVacuumGripper`)
1. In the **Modeling** ribbon tab, click **Create Tool**:
   - Tool Name: `tVacuumGripper`
   - Use Existing Part: Select `Vacuum_Gripper`
   - Weight: `0.820` kg
   - Center of Gravity: `X=0.0, Y=0.0, Z=38.5` mm
   - Tool Center Point (TCP) Values:
     - `X = 0.0` mm
     - `Y = 0.0` mm
     - `Z = 105.0` mm (at the suction lip)
     - Orientation: `Rx = 0°, Ry = 0°, Rz = 0°`
2. Click **Done**.
3. In the Layout tree, drag `tVacuumGripper` onto `IRB1200_7_07`.
4. RobotStudio will prompt: *"Do you want to attach tVacuumGripper to IRB1200_7_07 and update its position?"* -> Click **Yes**.
5. Verify in 3D that the gripper flange mates flush with Axis 6 tool plate.

---

### Step 2.4 — Configure Virtual Controller I/O Signals
1. Switch to the **Controller** ribbon tab.
2. Click **Configuration -> Load Parameters**.
3. Browse and select `RAPID/EIO.cfg`.
4. RobotStudio will display: *"Configuration parameters loaded successfully. A restart is required to apply changes."*
5. Click **Restart -> Warmstart** (10-second reboot).
6. Verify signals in the **I/O Simulator** pane:
   - Inputs: `diTrayReady`, `diPartPresent`, `diBoxPresent`, `diGripConfirmed`, `diBoxExitClear`
   - Outputs: `doVacuumOn`, `doInfeedRun`, `doOutfeedRun`, `doBoxFull`, `doCycleComplete`, `doReplenishTray`, `doRobotInHome`, `doRobotInFeederZone`, `doRobotInBoxZone`

---

### Step 2.5 — Load RAPID Program Modules
1. In the **RAPID** ribbon tab, expand `RAPID -> T_ROB1`.
2. Right-click `T_ROB1` and select **Load Module**:
   - Load `RAPID/PickPlace.mod`
   - Load `RAPID/Main.mod`
3. Click **Apply -> Apply All**.
4. Verify the syntax check reports **0 Errors, 0 Warnings**.

---

### Step 2.6 — Reachability & Kinematic Singularity Verification
1. IRB 1200-7/0.7 has maximum horizontal reach of `703.0 mm`.
2. Check radial distances from robot origin `(0, 0, 0)`:
   - Feeder Tray Center: `sqrt(350^2 + (-350)^2) = 494.97 mm`
   - Feeder Slot 1: `(305, -395) -> 499.0 mm`
   - Feeder Slot 2: `(395, -395) -> 558.6 mm`
   - Feeder Slot 3: `(305, -305) -> 431.3 mm`
   - Feeder Slot 4: `(395, -305) -> 499.0 mm`
   - Packing Box Center: `sqrt(350^2 + 350^2) = 494.97 mm`
   - Box Slot 1: `(300, 300) -> 424.3 mm`
   - Box Slot 2: `(400, 300) -> 500.0 mm`
   - Box Slot 3: `(300, 400) -> 500.0 mm`
   - Box Slot 4: `(400, 400) -> 565.7 mm`
3. **Conclusion**: All 8 targets lie well within the `424 mm to 566 mm` sweet spot:
   - Well clear of outer reach boundary (>137 mm safety margin).
   - Well clear of the inner cylindrical dead zone (`< 180 mm`).
   - Wrist Axis 5 maintains an angle of ~45° to 60°, completely eliminating Axis 5 singularity (`J5 = 0°`).

---

### Step 2.7 — Set Up Collision Detection Sets
1. In the **Simulation** tab, click **Collision Setup**.
2. Create **Collision Set 1**:
   - Object A: `IRB1200_7_07` + `tVacuumGripper`
   - Object B: `Feeder_Tray` + `Conveyor_Components` + `Cell_Layout_Assembly`
3. Check **Log collision warnings to Output window**.
4. Check **Highlight colliding objects in Red**.
