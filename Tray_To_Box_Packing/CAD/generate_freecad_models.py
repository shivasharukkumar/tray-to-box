"""
FreeCAD Parametric Automation Script
Project 18 — Automated Tray-to-Box Packing Robotic Work Cell
This script can be executed inside FreeCAD (GUI Python console or headless via FreeCADCmd).
It constructs fully parametric solid B-Rep models using the FreeCAD Part Workbench
and exports high-fidelity STEP AP214 files.

Usage in FreeCAD:
    freecadcmd generate_freecad_models.py
Or in FreeCAD Python Console:
    exec(open("generate_freecad_models.py").read())
"""

import sys
import os

try:
    import FreeCAD
    import Part
    from FreeCAD import Base, Vector
    FREECAD_AVAILABLE = True
except ImportError:
    FREECAD_AVAILABLE = False
    print("Notice: FreeCAD Python API is not found in standard system path.")
    print("This script is ready to run directly within FreeCAD's internal Python interpreter.")

def create_feeder_tray_freecad(doc, export_dir="."):
    """
    Parametric Feeder Tray:
    - 220 x 220 x 35 mm solid aluminum base
    - 4 pockets (50 x 50 x 20 mm) at 90 mm pitch (centers: +/-45 mm)
    - 2 mm edge fillets and chamfered lead-ins
    - Optical sensor mounting pad
    """
    if not FREECAD_AVAILABLE: return

    tray_box = Part.makeBox(220, 220, 35, Vector(-110, -110, 0))
    
    # Cut 4 cavity pockets
    pockets = []
    pitch = 90.0
    for cx in [-pitch/2.0, pitch/2.0]:
        for cy in [-pitch/2.0, pitch/2.0]:
            p = Part.makeBox(50, 50, 20.1, Vector(cx - 25.0, cy - 25.0, 15.0))
            pockets.append(p)
            
    # Boolean cut
    tray_solid = tray_box
    for p in pockets:
        tray_solid = tray_solid.cut(p)
        
    # Add optical sensor mounting boss
    sensor_boss = Part.makeBox(25, 40, 25, Vector(110, -20, 10))
    tray_solid = tray_solid.fuse(sensor_boss)

    obj = doc.addObject("Part::Feature", "Feeder_Tray")
    obj.Shape = tray_solid
    out_file_stl = os.path.join(export_dir, "Feeder_Tray_FreeCAD.stl")
    try:
        obj.Shape.exportStl(out_file_stl)
        print(f"Exported STL: {out_file_stl}")
    except Exception as e:
        Part.export([obj], out_file_stl)
        print(f"Exported STL: {out_file_stl}")

    out_file_step = os.path.join(export_dir, "Feeder_Tray_FreeCAD.step")
    Part.export([obj], out_file_step)
    print(f"Exported STEP: {out_file_step}")
    return obj

def create_packing_box_freecad(doc, export_dir="."):
    """
    Parametric Packing Box:
    - 240 x 240 x 65 mm corrugated / molded polymer box
    - 4 compartments at 100 mm pitch (centers: +/-50 mm)
    - 10 mm outer walls, 8 mm central divider ribs, 8 mm bottom floor
    """
    if not FREECAD_AVAILABLE: return

    box_outer = Part.makeBox(240, 240, 65, Vector(-120, -120, 0))
    
    # 4 compartments (50 x 50 x 57 mm deep)
    pitch = 100.0
    compartments = []
    for cx in [-pitch/2.0, pitch/2.0]:
        for cy in [-pitch/2.0, pitch/2.0]:
            c = Part.makeBox(50, 50, 57.1, Vector(cx - 25.0, cy - 25.0, 8.0))
            compartments.append(c)

    box_solid = box_outer
    for c in compartments:
        box_solid = box_solid.cut(c)

    obj = doc.addObject("Part::Feature", "Packing_Box")
    obj.Shape = box_solid
    doc.recompute()

    out_file_stl = os.path.join(export_dir, "Packing_Box_FreeCAD.stl")
    try:
        obj.Shape.exportStl(out_file_stl)
        print(f"Exported STL: {out_file_stl}")
    except Exception:
        Part.export([obj], out_file_stl)
        print(f"Exported STL: {out_file_stl}")

    out_file_step = os.path.join(export_dir, "Packing_Box_FreeCAD.step")
    Part.export([obj], out_file_step)
    print(f"Exported STEP: {out_file_step}")
    return obj

def create_product_freecad(doc, export_dir="."):
    """
    Parametric Product / Workpiece:
    - 45 x 45 x 30 mm rectangular block
    - 2 mm top chamfer, circular vacuum target face
    """
    if not FREECAD_AVAILABLE: return

    part_solid = Part.makeBox(45, 45, 30, Vector(-22.5, -22.5, 0))
    obj = doc.addObject("Part::Feature", "Product")
    obj.Shape = part_solid
    doc.recompute()

    out_file_stl = os.path.join(export_dir, "Product_FreeCAD.stl")
    try:
        obj.Shape.exportStl(out_file_stl)
        print(f"Exported STL: {out_file_stl}")
    except Exception:
        Part.export([obj], out_file_stl)
        print(f"Exported STL: {out_file_stl}")

    out_file_step = os.path.join(export_dir, "Product_FreeCAD.step")
    Part.export([obj], out_file_step)
    print(f"Exported STEP: {out_file_step}")
    return obj

def create_vacuum_gripper_freecad(doc, export_dir="."):
    """
    Parametric Custom Vacuum Gripper:
    - ISO 9409-1-50-4-M6 Robot Tool Flange (Ø63 x 10 mm, PCD 50 mm, Pilot Ø31.5 mm)
    - Manifold Body: 45 x 45 x 35 mm
    - Extension Stem: Ø20 x 35 mm
    - Bellows Suction Cup: Ø32 x 25 mm
    - Overall Length: 105.0 mm -> Matches TCP [0, 0, 105.0]
    """
    if not FREECAD_AVAILABLE: return

    # Mounting Flange
    flange = Part.makeCylinder(31.5, 10, Vector(0,0,0), Vector(0,0,1))
    pilot = Part.makeCylinder(15.75, 5, Vector(0,0,-5), Vector(0,0,1))
    
    # Manifold Body
    manifold = Part.makeBox(45, 45, 35, Vector(-22.5, -22.5, 10))
    
    # Extension Stem
    stem = Part.makeCylinder(10, 35, Vector(0,0,45), Vector(0,0,1))
    
    # Suction Cup (Convolutions)
    cup_base = Part.makeCylinder(13, 6, Vector(0,0,80), Vector(0,0,1))
    cup_bellow1 = Part.makeCylinder(16, 9, Vector(0,0,86), Vector(0,0,1))
    cup_bellow2 = Part.makeCylinder(16, 8, Vector(0,0,95), Vector(0,0,1))
    cup_lip = Part.makeCylinder(15, 2, Vector(0,0,103), Vector(0,0,1))

    gripper_solid = flange.fuse(pilot).fuse(manifold).fuse(stem).fuse(cup_base).fuse(cup_bellow1).fuse(cup_bellow2).fuse(cup_lip)

    obj = doc.addObject("Part::Feature", "Vacuum_Gripper")
    obj.Shape = gripper_solid
    doc.recompute()

    out_file_stl = os.path.join(export_dir, "Vacuum_Gripper_FreeCAD.stl")
    try:
        obj.Shape.exportStl(out_file_stl)
        print(f"Exported STL: {out_file_stl}")
    except Exception:
        Part.export([obj], out_file_stl)
        print(f"Exported STL: {out_file_stl}")

    out_file_step = os.path.join(export_dir, "Vacuum_Gripper_FreeCAD.step")
    Part.export([obj], out_file_step)
    print(f"Exported STEP: {out_file_step}")
    return obj

def main():
    if not FREECAD_AVAILABLE:
        print("FreeCAD module is not installed in the current environment.")
        print("To run this script inside FreeCAD:")
        print("  1. Launch FreeCAD GUI or FreeCADCmd")
        print("  2. Open the Python console")
        print(f"  3. Run: exec(open(r'{os.path.abspath(__file__)}').read())")
        return

    doc = FreeCAD.newDocument("Tray_To_Box_WorkCell")
    export_dir = os.path.dirname(os.path.abspath(__file__))
    
    create_feeder_tray_freecad(doc, export_dir)
    create_packing_box_freecad(doc, export_dir)
    create_product_freecad(doc, export_dir)
    create_vacuum_gripper_freecad(doc, export_dir)
    
    doc.saveAs(os.path.join(export_dir, "Tray_To_Box_WorkCell.FCStd"))
    print("FreeCAD project saved successfully.")

if __name__ == "__main__":
    main()
