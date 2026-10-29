# PROJECT 18 — AUTOMATED TRAY-TO-BOX PACKING ROBOTIC WORK CELL
## Digital Twin Commissioning in ABB RobotStudio

---

## 1. Project Directory Structure

```
Tray_To_Box_Packing/
├── STL/                             # ALL WORKCELL 3D MODELS IN ONE DEDICATED FOLDER
│   ├── Feeder_Tray.stl              # 4-cavity 2x2 tray (220 x 220 x 35 mm, pitch 90 mm)
│   ├── Packing_Box.stl              # 4-compartment 2x2 box (240 x 240 x 65 mm, pitch 100 mm)
│   ├── Product.stl                  # Workpiece (45 x 45 x 30 mm, top chamfer, vacuum face)
│   ├── Vacuum_Gripper.stl           # Custom vacuum gripper (ISO 9409-1-50-4-M6, TCP Z = 105 mm)
│   ├── Conveyor_Components.stl      # Infeed/Outfeed dual conveyor bed, stop blade, rails
│   └── Cell_Layout_Assembly.stl     # Full cell assembly (Pedestal, Fence, Cabinet, Feeder Stand)
├── CAD/
│   ├── Feeder_Tray.step             # STEP archive models
│   ├── Packing_Box.step
│   ├── Product.step
│   ├── Vacuum_Gripper.step
│   ├── Conveyor_Components.step
│   ├── Cell_Layout_Assembly.step
│   ├── generate_cad_models.py       # Standalone Python 3 geometry generator (AP214 STEP & STL)
│   └── generate_freecad_models.py   # Parametric FreeCAD automation script
├── RAPID/
│   ├── Main.mod                     # Production executive control, 10-cycle loop, error recovery
│   ├── PickPlace.mod                # Kinematics, tooldata, workobjects, targets, indexed offsets
│   ├── Signals_Configuration.txt    # Industrial digital signal dictionary & handshake manual
│   └── EIO.cfg                      # Standard ABB Virtual Controller I/O configuration file
├── RobotStudio/
│   ├── Setup_Guide.md               # Step-by-step station setup, CAD import, tool & workobject setup
│   ├── Smart_Components_Guide.md    # Smart component blueprints (Gripper, Conveyor, Feeder, Packer)
│   └── Station_Logic_Guide.md       # Station logic signal wiring, safety interlocks, Pack & Go export
└── Documentation/
    ├── Project_Overview.md          # Technical report, layout, sequence diagrams, safety specs
    ├── CAD_Dimensions.md            # Mechanical dimension drawings, tolerances, TCP stack-up
    ├── I_O_Table.md                 # Signal dictionary, electrical specs, timing diagrams
    ├── Testing_Checklist.md         # 10-Cycle (40-part) test log, singularity audit, clearance audit
    └── Cycle_Time_Analysis.md       # Baseline vs optimized cycle times (42.8% cycle time reduction)
```

---

## 2. Quick-Start Guide for ABB RobotStudio

1. **Launch RobotStudio** and create an empty station:
   - Add **ABB IRB 1200-7/0.7** robot from the ABB Library.
   - Create a Virtual Controller from the layout (`RobotWare 6.x` or `7.x`).
2. **Import CAD Geometry (From the `STL/` Folder)**:
   - In RobotStudio, click **Import Geometry** and select the `.stl` files from `STL/` (no CAD converter license required).
   - Place them at the coordinates specified in [Setup_Guide.md](file:///d:/projects/tray%20to%20box/Tray_To_Box_Packing/RobotStudio/Setup_Guide.md).
3. **Configure End-Effector Tool**:
   - Create Tool `tVacuumGripper` from `STL/Vacuum_Gripper.stl`.
   - Set TCP to `X = 0.0, Y = 0.0, Z = 105.0 mm` and attach it to the robot flange.
4. **Load Virtual Controller Signals**:
   - Under Controller tab -> Configuration -> **Load Parameters** -> Select [EIO.cfg](file:///d:/projects/tray%20to%20box/Tray_To_Box_Packing/RAPID/EIO.cfg).
   - Perform a **Warmstart**.
5. **Load RAPID Programs**:
   - In the RAPID tab, load [PickPlace.mod](file:///d:/projects/tray%20to%20box/Tray_To_Box_Packing/RAPID/PickPlace.mod) and [Main.mod](file:///d:/projects/tray%20to%20box/Tray_To_Box_Packing/RAPID/Main.mod).
6. **Set Up Smart Components**:
   - Follow [Smart_Components_Guide.md](file:///d:/projects/tray%20to%20box/Tray_To_Box_Packing/RobotStudio/Smart_Components_Guide.md) and [Station_Logic_Guide.md](file:///d:/projects/tray%20to%20box/Tray_To_Box_Packing/RobotStudio/Station_Logic_Guide.md) to wire the virtual physics and sensor signals.
7. **Run the Simulation**:
   - Press **Play** in the Simulation tab.
   - Watch the robot autonomously execute 10 consecutive box cycles (40 parts transferred) with zero manual intervention!
