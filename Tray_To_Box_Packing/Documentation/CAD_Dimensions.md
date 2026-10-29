# Engineering CAD Dimensions & Mechanical Specifications
## Project 18 — Digital Twin Commissioning: Automated Tray-to-Box Packing

---

## 1. Dimensional Summary & Component Overview

All mechanical components have been modeled in strict adherence to metric engineering standards (millimetres). The CAD models are exported in **ISO 10303-21 STEP** (`.step`) and **Binary STL** (`.stl`) formats.

```
       FEEDER TRAY (220 x 220 mm)                 PACKING BOX (240 x 240 mm)
       +-----------------------+                  +-------------------------+
       |   [Slot 3]   [Slot 4] |                  |   [Slot 3]    [Slot 4]  |
       |    (-45,45)   (45,45) |                  |    (-50,50)    (50,50)  |
       |                       |                  |                         |
       |       Center (0,0)    |                  |        Center (0,0)     |
       |                       |                  |                         |
       |   [Slot 1]   [Slot 2] |                  |   [Slot 1]    [Slot 2]  |
       |   (-45,-45)  (45,-45) |                  |   (-50,-50)   (50,-50)  |
       +-----------------------+                  +-------------------------+
             Pitch = 90 mm                              Pitch = 100 mm
```

---

## 2. Component 1: Feeder Tray (`Feeder_Tray.step`)

### 2.1 Dimensional Breakdown
- **Overall Dimensions**: `220.0 mm (L) × 220.0 mm (W) × 35.0 mm (H)`
- **Base Plate Floor Thickness**: `15.0 mm` solid base
- **Cavity Pockets**:
  - Number of Cavities: 4 arranged in a symmetrical 2×2 grid
  - Cavity Dimensions: `50.0 mm × 50.0 mm`
  - Cavity Depth: `20.0 mm` (Floor at Z = 15.0 mm, Top Rim at Z = 35.0 mm)
  - Slot Center Pitch: `90.0 mm` (Centers located at `X = ±45.0 mm, Y = ±45.0 mm`)
  - Pocket Wall Lead-in Chamfer: `2.0 mm × 45°` on top edges
- **Internal Cruciform Rib**: `40.0 mm` width separating cavities
- **Outer Perimeter Rim**: `40.0 mm` wall border
- **Sensor Mounting Bracket**:
  - Position: Mounted on the East (+X) exterior flange
  - Dimensions: `25.0 mm (Ext) × 50.0 mm (W) × 25.0 mm (H)`
  - Provision: M12 threaded through-hole for optical retro-reflective sensor barrel
- **Mounting Lugs**: 4 corner pads `(20.0 × 20.0 × 5.0 mm)` with M6 clearance holes

### 2.2 Material & Mass Properties
- **Material**: 6061-T6 Aluminum (Black hard-anodized, low surface reflectivity)
- **Calculated Volume**: `1,288,500 mm³`
- **Estimated Mass**: `3.48 kg`
- **Center of Gravity**: `(0.0 mm, 0.0 mm, 14.2 mm)` relative to tray base center

---

## 3. Component 2: Packing Box (`Packing_Box.step`)

### 3.1 Dimensional Breakdown
- **Overall Exterior Dimensions**: `240.0 mm (L) × 240.0 mm (W) × 65.0 mm (H)`
- **Bottom Floor Thickness**: `8.0 mm`
- **Exterior Wall Thickness**: `10.0 mm`
- **Internal Compartments**:
  - Number of Compartments: 4 arranged in a 2×2 grid
  - Compartment Opening: `50.0 mm × 50.0 mm`
  - Compartment Depth: `57.0 mm` (Floor at Z = 8.0 mm, Top Rim at Z = 65.0 mm)
  - Compartment Pitch: `100.0 mm` (Centers located at `X = ±50.0 mm, Y = ±50.0 mm`)
  - Top Rim Insertion Chamfer: `2.0 mm × 45°`
- **Internal Dividers (Cruciform Ribs)**:
  - Thickness: `8.0 mm` continuous partition walls
- **Stacking Lip**: `3.0 mm` perimeter overhang at base for transport rail guidance

### 3.2 Insertion Clearance Analysis
- Workpiece Dimensions: `45.0 mm × 45.0 mm`
- Compartment Dimensions: `50.0 mm × 50.0 mm`
- **Total Clearance**: `5.0 mm` total (`2.5 mm` nominal clearance per side)
- **Robotic Precision Factor**:
  - IRB 1200 Repeatability: `±0.02 mm`
  - Clear-to-Tolerance Ratio: `2.5 mm / 0.02 mm = 125:1`
  - Guarantees 100% collision-free insertion even under maximum path deviation!

---

## 4. Component 3: Product / Workpiece (`Product.step`)

### 4.1 Dimensional Breakdown
- **Overall Dimensions**: `45.0 mm (L) × 45.0 mm (W) × 30.0 mm (H)`
- **Top Suction Interface Face**:
  - Planar Contact Land: Flat planar face at `Z = 30.0 mm`
  - Target Ring Diameter: `Ø24.0 mm` centered circular contact zone
  - Top Rim Chamfer: `2.0 mm × 45°` around top perimeter
- **Bottom Locating Relief**:
  - Recess: `15.0 mm × 15.0 mm × 3.0 mm` deep cavity on bottom face

### 4.2 Material & Mass Properties
- **Material**: Engineering Thermoplastic (POM Acetal / Delrin) or Solid Aluminum
- **Mass per Part**: `0.150 kg` (Total 4 parts = `0.600 kg`)
- **Seated Height in Box**:
  - Box floor = `8.0 mm`, Part height = `30.0 mm`
  - Seated top surface = `38.0 mm` from box bottom (`27.0 mm` below box top rim)

---

## 5. Component 4: Custom Vacuum Gripper (`Vacuum_Gripper.step`)

### 5.1 Mechanical Stack-Up & TCP Calibration
The gripper has been engineered so that the suction cup lip lies at **exactly Z = 105.0 mm** from the robot tool mounting flange face:

```
  +-----------------------------------+  Z = 0.0 mm (Robot Flange Face)
  |  ISO 9409-1-50-4-M6 Tool Flange   |  Thickness: 10.0 mm, OD: 63.0 mm
  +-----------------------------------+  Z = 10.0 mm
  |   Pneumatic Manifold Block        |  Height: 35.0 mm (45 x 45 mm)
  +-----------------------------------+  Z = 45.0 mm
  |      Extension Stem Tube          |  Length: 35.0 mm (Ø20.0 mm)
  +-----------------------------------+  Z = 80.0 mm
  |    1.5-Fold Bellows Suction Cup   |  Height: 25.0 mm (Ø32.0 mm Cup)
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Z = 105.0 mm (TCP Contact Plane)
```

### 5.2 Tool Data Definition in RAPID
```rapid
PERS tooldata tVacuumGripper := [TRUE,
    [[0.0, 0.0, 105.0], [1.0, 0.0, 0.0, 0.0]],
    [0.820, [0.0, 0.0, 38.5], [1.0, 0.0, 0.0, 0.0], 0.001, 0.001, 0.001]];
```
- **Tool Center Point (TCP)**: `X = 0.0 mm, Y = 0.0 mm, Z = 105.0 mm`
- **Total Gripper Mass**: `0.820 kg`
- **Center of Gravity**: `X = 0.0 mm, Y = 0.0 mm, Z = 38.5 mm`

---

## 6. Component 5: Conveyor System (`Conveyor_Components.step`)

### 6.1 Dimensional Breakdown
- **Overall Span**: `2200.0 mm` continuous dual-belt bed running along Y axis
- **Centerline Position**: `X = 350.0 mm`
- **Conveyor Belt Width**: `320.0 mm`
- **Working Bed Surface Height**: `Z = 435.0 mm` (Places box top rim at `Z = 500.0 mm`)
- **Guide Rails**:
  - Height above belt: `45.0 mm`
  - Spacing between rails: `246.0 mm` (Providing `3.0 mm` clearance for `240 mm` box)
- **Pneumatic Box Stop Blade**:
  - Station Center: `Y = +350.0 mm`
  - Stop Blade Position: `Y = +470.0 mm` (Stops box front edge at `350 + 120 = 470 mm`)
  - Blade Stroke: `30.0 mm` vertical pneumatic retract
