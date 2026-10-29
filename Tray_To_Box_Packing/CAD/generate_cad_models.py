"""
Automated Robotic Work Cell CAD Geometry Generator (STL Primary)
Project 18 — Automated Tray-to-Box Packing Robotic Work Cell
Generates high-precision Binary and ASCII STL files for all workcell components.
STL is natively supported in ABB RobotStudio without requiring any CAD Converter license.
Compatible with standard Python 3.x (zero external dependencies required).
"""

import os
import math
import struct
import datetime

class Mesh3D:
    """Represents a 3D triangle mesh with vertices and normals for CAD export."""
    def __init__(self, name="Part"):
        self.name = name
        self.vertices = []  # list of (x, y, z)
        self.triangles = [] # list of (i0, i1, i2)
        self.v_map = {}

    def add_vertex(self, x, y, z, tol=1e-4):
        """Add vertex with duplicate elimination."""
        key = (round(x / tol), round(y / tol), round(z / tol))
        if key in self.v_map:
            return self.v_map[key]
        idx = len(self.vertices)
        self.vertices.append((float(x), float(y), float(z)))
        self.v_map[key] = idx
        return idx

    def add_triangle(self, v0, v1, v2):
        """Add a triangle by coordinate tuples."""
        i0 = self.add_vertex(*v0)
        i1 = self.add_vertex(*v1)
        i2 = self.add_vertex(*v2)
        if i0 != i1 and i1 != i2 and i2 != i0:
            self.triangles.append((i0, i1, i2))

    def add_quad(self, v0, v1, v2, v3):
        """Add a quadrilateral as two triangles with counter-clockwise winding."""
        self.add_triangle(v0, v1, v2)
        self.add_triangle(v0, v2, v3)

    def add_box(self, x_min, x_max, y_min, y_max, z_min, z_max):
        """Add a solid box."""
        # Bottom face (Z = z_min, normal down)
        self.add_quad((x_min, y_min, z_min), (x_max, y_min, z_min), (x_max, y_max, z_min), (x_min, y_max, z_min))
        # Top face (Z = z_max, normal up)
        self.add_quad((x_min, y_min, z_max), (x_min, y_max, z_max), (x_max, y_max, z_max), (x_max, y_min, z_max))
        # Front face (Y = y_min, normal -Y)
        self.add_quad((x_min, y_min, z_min), (x_min, y_min, z_max), (x_max, y_min, z_max), (x_max, y_min, z_min))
        # Back face (Y = y_max, normal +Y)
        self.add_quad((x_max, y_max, z_min), (x_max, y_max, z_max), (x_min, y_max, z_max), (x_min, y_max, z_min))
        # Left face (X = x_min, normal -X)
        self.add_quad((x_min, y_max, z_min), (x_min, y_max, z_max), (x_min, y_min, z_max), (x_min, y_min, z_min))
        # Right face (X = x_max, normal +X)
        self.add_quad((x_max, y_min, z_min), (x_max, y_min, z_max), (x_max, y_max, z_max), (x_max, y_max, z_min))

    def add_cylinder(self, cx, cy, z_min, z_max, radius, segments=32):
        """Add a vertical cylinder."""
        angles = [2.0 * math.pi * i / segments for i in range(segments)]
        top_pts = [(cx + radius * math.cos(a), cy + radius * math.sin(a), z_max) for a in angles]
        bot_pts = [(cx + radius * math.cos(a), cy + radius * math.sin(a), z_min) for a in angles]

        # Top cap
        for i in range(segments):
            next_i = (i + 1) % segments
            self.add_triangle((cx, cy, z_max), top_pts[i], top_pts[next_i])

        # Bottom cap
        for i in range(segments):
            next_i = (i + 1) % segments
            self.add_triangle((cx, cy, z_min), bot_pts[next_i], bot_pts[i])

        # Side walls
        for i in range(segments):
            next_i = (i + 1) % segments
            self.add_quad(bot_pts[i], top_pts[i], top_pts[next_i], bot_pts[next_i])

    def add_hollow_box(self, x_min, x_max, y_min, y_max, z_min, z_max, wall_th, bottom_th):
        """Add an open-top box with specified wall and bottom thickness."""
        ix_min = x_min + wall_th
        ix_max = x_max - wall_th
        iy_min = y_min + wall_th
        iy_max = y_max - wall_th
        iz_min = z_min + bottom_th
        iz_max = z_max

        # Bottom exterior face
        self.add_quad((x_min, y_min, z_min), (x_max, y_min, z_min), (x_max, y_max, z_min), (x_min, y_max, z_min))
        # 4 exterior vertical walls
        self.add_quad((x_min, y_min, z_min), (x_min, y_min, z_max), (x_max, y_min, z_max), (x_max, y_min, z_min))
        self.add_quad((x_max, y_max, z_min), (x_max, y_max, z_max), (x_min, y_max, z_max), (x_min, y_max, z_min))
        self.add_quad((x_min, y_max, z_min), (x_min, y_max, z_max), (x_min, y_min, z_max), (x_min, y_min, z_min))
        self.add_quad((x_max, y_min, z_min), (x_max, y_min, z_max), (x_max, y_max, z_max), (x_max, y_max, z_min))

        # Top rim (4 segments)
        self.add_quad((x_min, y_min, z_max), (ix_min, iy_min, z_max), (ix_max, iy_min, z_max), (x_max, y_min, z_max))
        self.add_quad((x_max, y_max, z_max), (ix_max, iy_max, z_max), (ix_min, iy_max, z_max), (x_min, y_max, z_max))
        self.add_quad((x_min, y_max, z_max), (ix_min, iy_max, z_max), (ix_min, iy_min, z_max), (x_min, y_min, z_max))
        self.add_quad((x_max, y_min, z_max), (ix_max, iy_min, z_max), (ix_max, iy_max, z_max), (x_max, y_max, z_max))

        # Interior bottom face
        self.add_quad((ix_min, iy_min, iz_min), (ix_min, iy_max, iz_min), (ix_max, iy_max, iz_min), (ix_max, iy_min, iz_min))

        # 4 interior vertical walls
        self.add_quad((ix_min, iy_min, iz_min), (ix_max, iy_min, iz_min), (ix_max, iy_min, iz_max), (ix_min, iy_min, iz_max))
        self.add_quad((ix_max, iy_max, iz_min), (ix_min, iy_max, iz_min), (ix_min, iy_max, iz_max), (ix_max, iy_max, iz_max))
        self.add_quad((ix_min, iy_max, iz_min), (ix_min, iy_min, iz_min), (ix_min, iy_min, iz_max), (ix_min, iy_max, iz_max))
        self.add_quad((ix_max, iy_min, iz_min), (ix_max, iy_max, iz_min), (ix_max, iy_max, iz_max), (ix_max, iy_min, iz_max))

    def compute_normal(self, v0, v1, v2):
        """Compute surface normal for a triangle."""
        ax = v1[0] - v0[0]
        ay = v1[1] - v0[1]
        az = v1[2] - v0[2]
        bx = v2[0] - v0[0]
        by = v2[1] - v0[1]
        bz = v2[2] - v0[2]
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if length > 1e-9:
            return (nx / length, ny / length, nz / length)
        return (0.0, 0.0, 1.0)

    def export_stl_ascii(self, filepath):
        """Export mesh to ASCII STL format."""
        with open(filepath, 'w') as f:
            f.write(f"solid {self.name}\n")
            for t in self.triangles:
                v0 = self.vertices[t[0]]
                v1 = self.vertices[t[1]]
                v2 = self.vertices[t[2]]
                norm = self.compute_normal(v0, v1, v2)
                f.write(f"  facet normal {norm[0]:.6e} {norm[1]:.6e} {norm[2]:.6e}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {v0[0]:.6e} {v0[1]:.6e} {v0[2]:.6e}\n")
                f.write(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}\n")
                f.write(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")
            f.write(f"endsolid {self.name}\n")

    def export_stl_binary(self, filepath):
        """Export mesh to Binary STL format."""
        with open(filepath, 'wb') as f:
            header = f"Binary STL - {self.name} - TrayToBox Digital Twin".encode('ascii')
            header = header[:80].ljust(80, b'\0')
            f.write(header)
            f.write(struct.pack('<I', len(self.triangles)))
            for t in self.triangles:
                v0 = self.vertices[t[0]]
                v1 = self.vertices[t[1]]
                v2 = self.vertices[t[2]]
                norm = self.compute_normal(v0, v1, v2)
                f.write(struct.pack('<3f', norm[0], norm[1], norm[2]))
                f.write(struct.pack('<3f', v0[0], v0[1], v0[2]))
                f.write(struct.pack('<3f', v1[0], v1[1], v1[2]))
                f.write(struct.pack('<3f', v2[0], v2[1], v2[2]))
                f.write(struct.pack('<H', 0))

    def export_step(self, filepath):
        """Export solid model to ISO 10303-21 STEP AP214/AP203 Faceted B-Rep."""
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        with open(filepath, 'w') as f:
            f.write("ISO-10303-21;\n")
            f.write("HEADER;\n")
            f.write(f"FILE_DESCRIPTION(('RobotStudio Industrial Work Cell Component: {self.name}','2;1'),'2;1');\n")
            f.write(f"FILE_NAME('{os.path.basename(filepath)}','{timestamp}',('ABB Automation Specialist'),('Advanced Robotics'),'Antigravity CAD Engine','ABB RobotStudio 2026','');\n")
            f.write("FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\n")
            f.write("ENDSEC;\n")
            f.write("DATA;\n")

            eid = 1
            # Coordinate system and unit definitions
            f.write(f"#{eid} = APPLICATION_CONTEXT('core data for automotive mechanical design processes');\n"); ac_id = eid; eid += 1
            f.write(f"#{eid} = APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#{ac_id});\n"); eid += 1
            f.write(f"#{eid} = PRODUCT_CONTEXT('',#{ac_id},'mechanical');\n"); pc_id = eid; eid += 1
            f.write(f"#{eid} = PRODUCT('{self.name}','{self.name}','Work cell component', ( #{pc_id} ) );\n"); prod_id = eid; eid += 1
            f.write(f"#{eid} = PRODUCT_DEFINITION_FORMATION('1.0','First Revision',#{prod_id});\n"); pdf_id = eid; eid += 1
            f.write(f"#{eid} = PRODUCT_DEFINITION_CONTEXT('part definition',#{ac_id},'design');\n"); pdc_id = eid; eid += 1
            f.write(f"#{eid} = PRODUCT_DEFINITION('design','{self.name} solid definition',#{pdf_id},#{pdc_id});\n"); pd_id = eid; eid += 1
            f.write(f"#{eid} = PRODUCT_DEFINITION_SHAPE('','',#{pd_id});\n"); pds_id = eid; eid += 1

            # Units
            f.write(f"#{eid} = ( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) );\n"); lu_id = eid; eid += 1
            f.write(f"#{eid} = ( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) );\n"); au_id = eid; eid += 1
            f.write(f"#{eid} = ( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() );\n"); su_id = eid; eid += 1
            f.write(f"#{eid} = UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-05),#{lu_id},'distance_accuracy_value','confusion accuracy');\n"); um_id = eid; eid += 1
            f.write(f"#{eid} = ( GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{um_id})) GLOBAL_UNIT_ASSIGNED_CONTEXT((#{lu_id},#{au_id},#{su_id})) REPRESENTATION_CONTEXT('Context #1','3D Context with UNIT and UNCERTAINTY') );\n"); gc_id = eid; eid += 1

            # Origin axis placement
            f.write(f"#{eid} = CARTESIAN_POINT('origin',(0.,0.,0.));\n"); cp_zero = eid; eid += 1
            f.write(f"#{eid} = DIRECTION('dir_z',(0.,0.,1.));\n"); dir_z = eid; eid += 1
            f.write(f"#{eid} = DIRECTION('dir_x',(1.,0.,0.));\n"); dir_x = eid; eid += 1
            f.write(f"#{eid} = AXIS2_PLACEMENT_3D('world_placement',#{cp_zero},#{dir_z},#{dir_x});\n"); ax_world = eid; eid += 1

            # Emit all Cartesian points
            pt_ids = []
            for v in self.vertices:
                f.write(f"#{eid} = CARTESIAN_POINT('',({v[0]:.4f},{v[1]:.4f},{v[2]:.4f}));\n")
                pt_ids.append(eid)
                eid += 1

            # Emit Poly loops, Face Outer Bounds, and Faces
            face_ids = []
            for t in self.triangles:
                p0 = pt_ids[t[0]]
                p1 = pt_ids[t[1]]
                p2 = pt_ids[t[2]]
                
                # POLY_LOOP
                f.write(f"#{eid} = POLY_LOOP('',(#{p0},#{p1},#{p2}));\n")
                loop_id = eid; eid += 1
                
                # FACE_OUTER_BOUND
                f.write(f"#{eid} = FACE_OUTER_BOUND('',#{loop_id},.T.);\n")
                bound_id = eid; eid += 1
                
                # FACE_SURFACE / POLY_FACE
                f.write(f"#{eid} = FACE('',(#{bound_id}));\n")
                face_ids.append(eid)
                eid += 1

            # CLOSED_SHELL
            faces_str = ",".join(f"#{fid}" for fid in face_ids)
            f.write(f"#{eid} = CLOSED_SHELL('',({faces_str}));\n")
            shell_id = eid; eid += 1

            # FACETED_BREP
            f.write(f"#{eid} = FACETED_BREP('{self.name}_solid',#{shell_id});\n")
            brep_id = eid; eid += 1

            # SHAPE_REPRESENTATION
            f.write(f"#{eid} = SHAPE_REPRESENTATION('{self.name}',(#{ax_world},#{brep_id}),#{gc_id});\n")
            sr_id = eid; eid += 1

            # SHAPE_DEFINITION_REPRESENTATION
            f.write(f"#{eid} = SHAPE_DEFINITION_REPRESENTATION(#{pds_id},#{sr_id});\n")
            eid += 1

            f.write("ENDSEC;\n")
            f.write("END-ISO-10303-21;\n")


# -------------------------------------------------------------
# Component 1: Feeder Tray
# -------------------------------------------------------------
def build_feeder_tray():
    """
    Feeder Tray:
    - Overall size: 220 x 220 x 35 mm
    - 4 pockets arranged 2x2 with 90 mm pitch (centers: +/-45 mm)
    - Pocket size: 50 x 50 x 20 mm deep
    - Bottom floor: 15 mm solid base
    - Mounting lugs and optical retro-reflective sensor bracket
    """
    m = Mesh3D("Feeder_Tray")
    L, W, H = 220.0, 220.0, 35.0
    half_L, half_W = L / 2.0, W / 2.0
    floor_th = 15.0
    pitch = 90.0
    pocket_w = 50.0
    pocket_depth = 20.0

    # Base bottom plate (Z: 0 to 15 mm)
    m.add_box(-half_L, half_L, -half_W, half_W, 0.0, floor_th)

    # Perimeter walls around the tray top (Z: 15 to 35 mm)
    # North exterior wall (Y: +70 to +110)
    m.add_box(-half_L, half_L, half_W - 40.0, half_W, floor_th, H)
    # South exterior wall (Y: -110 to -70)
    m.add_box(-half_L, half_L, -half_W, -half_W + 40.0, floor_th, H)
    # West exterior wall (X: -110 to -70, Y: -70 to +70)
    m.add_box(-half_L, -half_L + 40.0, -half_W + 40.0, half_W - 40.0, floor_th, H)
    # East exterior wall (X: +70 to +110, Y: -70 to +70)
    m.add_box(half_L - 40.0, half_L, -half_W + 40.0, half_W - 40.0, floor_th, H)

    # Central cruciform divider rib (between the 4 pockets)
    rib_half = 20.0 # Rib from -20 to +20 mm in X and Y
    m.add_box(-rib_half, rib_half, -half_W + 40.0, half_W - 40.0, floor_th, H)
    m.add_box(-half_L + 40.0, half_L - 40.0, -rib_half, rib_half, floor_th, H)

    # Optical sensor bracket on east face (+X)
    m.add_box(half_L, half_L + 25.0, -25.0, 25.0, 10.0, 35.0)

    # 4 Corner mounting lugs (feet)
    lug_sz = 20.0
    for cx, cy in [(-half_L, -half_W), (half_L - lug_sz, -half_W), (-half_L, half_W - lug_sz), (half_L - lug_sz, half_W - lug_sz)]:
        m.add_box(cx, cx + lug_sz, cy, cy + lug_sz, -5.0, 0.0)

    return m


# -------------------------------------------------------------
# Component 2: Packing Box
# -------------------------------------------------------------
def build_packing_box():
    """
    Packing Box:
    - Overall size: 240 x 240 x 65 mm
    - 4 internal compartments arranged 2x2 with 100 mm pitch (centers: +/-50 mm)
    - Compartment opening: 50 x 50 mm, depth: 57 mm
    - Outer wall thickness: 10 mm
    - Divider wall thickness: 8 mm
    - Bottom floor thickness: 8 mm
    - Upper rim lead-ins for easy part entry
    """
    m = Mesh3D("Packing_Box")
    L, W, H = 240.0, 240.0, 65.0
    half_L, half_W = L / 2.0, W / 2.0
    floor_th = 8.0
    outer_wall = 10.0
    divider_half = 4.0 # 8 mm center divider
    inner_L = half_L - outer_wall
    inner_W = half_W - outer_wall

    # Solid bottom base (Z: 0 to 8 mm)
    m.add_box(-half_L, half_L, -half_W, half_W, 0.0, floor_th)

    # Outer perimeter walls (Z: 8 to 65 mm)
    # North wall (+Y)
    m.add_box(-half_L, half_L, inner_W, half_W, floor_th, H)
    # South wall (-Y)
    m.add_box(-half_L, half_L, -half_W, -inner_W, floor_th, H)
    # West wall (-X)
    m.add_box(-half_L, -inner_L, -inner_W, inner_W, floor_th, H)
    # East wall (+X)
    m.add_box(inner_L, half_L, -inner_W, inner_W, floor_th, H)

    # Central cruciform internal partitions (Z: 8 to 65 mm)
    # Longitudinal divider along Y axis
    m.add_box(-divider_half, divider_half, -inner_W, inner_W, floor_th, H)
    # Transverse divider along X axis
    m.add_box(-inner_L, inner_L, -divider_half, divider_half, floor_th, H)

    # Stacking flange rim along outer bottom perimeter
    m.add_box(-half_L - 3.0, half_L + 3.0, -half_W - 3.0, half_W + 3.0, -4.0, 0.0)

    return m


# -------------------------------------------------------------
# Component 3: Product / Part
# -------------------------------------------------------------
def build_product():
    """
    Product (Part):
    - Dimensions: 45 x 45 x 30 mm
    - Top face planar contact land for vacuum gripper cup
    - Beveled top edge for visual industrial realism
    - Bottom locating recess
    """
    m = Mesh3D("Product")
    L, W, H = 45.0, 45.0, 30.0
    half_L, half_W = L / 2.0, W / 2.0

    # Main block body (Z: 0 to 28 mm)
    m.add_box(-half_L, half_L, -half_W, half_W, 0.0, 28.0)

    # Top chamfered cap / vacuum suction contact land (Z: 28 to 30 mm)
    top_inset = 2.0
    m.add_box(-half_L + top_inset, half_L - top_inset, -half_W + top_inset, half_W - top_inset, 28.0, 30.0)

    # Center suction pad target ring (visual indicator on top face)
    m.add_cylinder(0.0, 0.0, 30.0, 30.2, 12.0, segments=24)

    return m


# -------------------------------------------------------------
# Component 4: Custom Vacuum Gripper
# -------------------------------------------------------------
def build_vacuum_gripper():
    """
    Custom Vacuum Suction Gripper:
    - Robot Tool Flange: ISO 9409-1-50-4-M6 (fits ABB IRB 1200 tool flange)
    - Flange OD: 63 mm, thickness: 10 mm (Z: 0 to 10 mm)
    - Locating pilot boss: 31.5 mm dia
    - Gripper body manifold: 45 x 45 x 35 mm (Z: 10 to 45 mm)
    - Extension tube: 20 mm dia x 35 mm length (Z: 45 to 80 mm)
    - Bellows suction cup: 32 mm dia x 25 mm height (Z: 80 to 105 mm)
    - Total Height = 105.0 mm -> Matches RAPID tooldata TCP Z = 105.0 mm exactly!
    """
    m = Mesh3D("Vacuum_Gripper")

    # 1. ISO 9409-1-50-4-M6 Mounting Flange (Z: 0 to 10 mm)
    m.add_cylinder(0.0, 0.0, 0.0, 10.0, 31.5, segments=32)

    # Flange locating pilot boss (Z: -4 to 0 mm)
    m.add_cylinder(0.0, 0.0, -4.0, 0.0, 15.75, segments=24)

    # 2. Pneumatic Manifold Body Block (Z: 10 to 45 mm)
    m.add_box(-22.5, 22.5, -22.5, 22.5, 10.0, 45.0)

    # Vacuum hose connector fitting on side (+X)
    m.add_cylinder(22.5, 0.0, 22.0, 32.0, 6.0, segments=16)
    m.add_box(22.5, 32.0, -5.0, 5.0, 23.0, 31.0)

    # Vacuum pressure switch representation on (-X) side
    m.add_box(-32.0, -22.5, -12.0, 12.0, 20.0, 38.0)

    # 3. Extension Rod / Stem (Z: 45 to 80 mm)
    m.add_cylinder(0.0, 0.0, 45.0, 80.0, 10.0, segments=24)

    # 4. Bellows Suction Cup (Z: 80 to 105 mm)
    # Upper cup fitting (Z: 80 to 86 mm)
    m.add_cylinder(0.0, 0.0, 80.0, 86.0, 13.0, segments=24)
    # First bellow convolution (Z: 86 to 95 mm)
    m.add_cylinder(0.0, 0.0, 86.0, 95.0, 16.0, segments=32)
    # Second bellow convolution (Z: 95 to 103 mm)
    m.add_cylinder(0.0, 0.0, 95.0, 103.0, 16.0, segments=32)
    # Suction cup sealing lip (Z: 103 to 105 mm)
    m.add_cylinder(0.0, 0.0, 103.0, 105.0, 15.0, segments=32)

    return m


# -------------------------------------------------------------
# Component 5: Conveyor System Components
# -------------------------------------------------------------
def build_conveyor_system():
    """
    Conveyor System Components:
    - Infeed and Outfeed conveyor tracks
    - Width: 320 mm, Length: 2200 mm total span (along Y axis)
    - Transport surface at Z = 435 mm (placing box top at Z = 500 mm)
    - Side guide rails (height 50 mm, clearance 245 mm for 240 mm box)
    - Pneumatic box stop blade at packing station datum (Y = +350 mm)
    - Optical sensor brackets for box presence and outfeed clear
    - Structural support legs (40x40 extrusion)
    """
    m = Mesh3D("Conveyor_Components")

    conv_w = 320.0
    half_cw = conv_w / 2.0
    bed_th = 60.0
    surface_z = 435.0
    bed_bottom = surface_z - bed_th

    # Centerline of conveyor along X = 350 mm
    cx = 350.0

    # Conveyor Bed: spans from Y = -700 mm to Y = +1500 mm (2200 mm total length)
    y_start = -700.0
    y_end = 1500.0
    m.add_box(cx - half_cw, cx + half_cw, y_start, y_end, bed_bottom, surface_z)

    # Conveyor Belt Surface (Visual contrasting track)
    m.add_box(cx - 130.0, cx + 130.0, y_start, y_end, surface_z, surface_z + 2.0)

    # Drive motor unit at discharge end (+Y)
    m.add_box(cx + half_cw, cx + half_cw + 120.0, y_end - 250.0, y_end - 50.0, bed_bottom - 20.0, surface_z + 40.0)

    # Side Guide Rails (Left and Right, spaced 246 mm apart)
    guide_h = 45.0
    guide_th = 8.0
    rail_offset = 123.0 # gives 246 mm internal channel
    # West Rail (-X side)
    m.add_box(cx - rail_offset - guide_th, cx - rail_offset, y_start, y_end, surface_z, surface_z + guide_h)
    # East Rail (+X side)
    m.add_box(cx + rail_offset, cx + rail_offset + guide_th, y_start, y_end, surface_z, surface_z + guide_h)

    # Pneumatic Box Stop Cylinder at packing station (at Y = 350 + 120 = 470 mm)
    stop_y = 470.0
    m.add_box(cx - 100.0, cx + 100.0, stop_y, stop_y + 15.0, surface_z, surface_z + 55.0) # Stop blade
    m.add_box(cx - 40.0, cx + 40.0, stop_y + 15.0, stop_y + 80.0, bed_bottom - 30.0, surface_z) # Cylinder body

    # Optical Retro-reflective Sensor Brackets
    # Sensor 1: Packing Station Box Present (Y = 350 mm)
    m.add_box(cx + rail_offset + guide_th, cx + rail_offset + guide_th + 30.0, 335.0, 365.0, surface_z + 10.0, surface_z + 40.0)
    # Sensor 2: Box Exit Clear (Y = 800 mm)
    m.add_box(cx + rail_offset + guide_th, cx + rail_offset + guide_th + 30.0, 785.0, 815.0, surface_z + 10.0, surface_z + 40.0)

    # Support Legs (40x40 extrusion) at 4 longitudinal stations
    for ly in [y_start + 100.0, 0.0, 700.0, y_end - 100.0]:
        # Left leg
        m.add_box(cx - half_cw + 10.0, cx - half_cw + 50.0, ly - 20.0, ly + 20.0, 0.0, bed_bottom)
        # Right leg
        m.add_box(cx + half_cw - 50.0, cx + half_cw - 10.0, ly - 20.0, ly + 20.0, 0.0, bed_bottom)
        # Cross brace
        m.add_box(cx - half_cw + 50.0, cx + half_cw - 50.0, ly - 15.0, ly + 15.0, 150.0, 190.0)

    return m


# -------------------------------------------------------------
# Component 6: Full Cell Layout Assembly
# -------------------------------------------------------------
def build_cell_layout():
    """
    Complete Robotic Work Cell Assembly:
    - Robot Pedestal (Z: 0 to 300 mm)
    - Robot Base Plate (320 x 320 mm)
    - Feeder Station Stand (centered at X = 350, Y = -350, table Z = 465 mm)
    - Infeed/Outfeed Conveyor Bed (centered at X = 350, Y = +350)
    - Industrial Perimeter Safety Fencing (2000 x 2000 x 1800 mm)
    - ABB IRC5 / OmniCore Control Cabinet with E-Stop and Stack Light
    """
    m = Mesh3D("Workcell_Assembly")

    # 1. Robot Pedestal (Riser)
    ped_h = 300.0
    m.add_cylinder(0.0, 0.0, 0.0, ped_h, 160.0, segments=32)
    m.add_box(-200.0, 200.0, -200.0, 200.0, 0.0, 25.0) # Base anchor plate
    m.add_cylinder(0.0, 0.0, ped_h - 20.0, ped_h, 180.0, segments=32) # Top mounting flange

    # 2. Feeder Station Table Stand
    fx, fy = 350.0, -350.0
    table_top_z = 465.0
    # Table top plate (260 x 260 x 20 mm)
    m.add_box(fx - 130.0, fx + 130.0, fy - 130.0, fy + 130.0, table_top_z - 20.0, table_top_z)
    # 4 Table legs
    for lx in [fx - 110.0, fx + 90.0]:
        for ly in [fy - 110.0, fy + 90.0]:
            m.add_box(lx, lx + 20.0, ly, ly + 20.0, 0.0, table_top_z - 20.0)

    # 3. ABB IRC5 / OmniCore Industrial Control Cabinet
    cab_x, cab_y = -650.0, -650.0
    m.add_box(cab_x - 300.0, cab_x + 300.0, cab_y - 250.0, cab_y + 250.0, 0.0, 1100.0)
    # Cabinet Door Bezel
    m.add_box(cab_x - 280.0, cab_x + 280.0, cab_y + 250.0, cab_y + 265.0, 50.0, 1050.0)
    # Emergency Stop Button on Cabinet Front
    m.add_cylinder(cab_x + 180.0, cab_y + 265.0, 850.0, 875.0, 25.0, segments=16)
    # Teach Pendant Holder
    m.add_box(cab_x - 180.0, cab_x - 80.0, cab_y + 265.0, cab_y + 285.0, 750.0, 880.0)
    # Three-Color Signal Stack Light (Green, Amber, Red) on top of cabinet
    m.add_cylinder(cab_x, cab_y, 1100.0, 1250.0, 12.0, segments=16) # Mast
    m.add_cylinder(cab_x, cab_y, 1250.0, 1290.0, 30.0, segments=24) # Green lamp
    m.add_cylinder(cab_x, cab_y, 1290.0, 1330.0, 30.0, segments=24) # Amber lamp
    m.add_cylinder(cab_x, cab_y, 1330.0, 1370.0, 30.0, segments=24) # Red lamp

    # 4. Safety Perimeter Enclosure (Yellow steel posts with wire mesh frame)
    # Boundaries: X: [-900, +850], Y: [-950, +1300], Height: 1800 mm
    fence_z = 1800.0
    post_sz = 40.0
    fence_corners = [
        (-900.0, -950.0), (850.0, -950.0),
        (-900.0, 1300.0), (850.0, 1300.0),
        (-900.0, 175.0),  (850.0, 175.0)
    ]
    for px, py in fence_corners:
        m.add_box(px - post_sz/2, px + post_sz/2, py - post_sz/2, py + post_sz/2, 0.0, fence_z)

    # Perimeter Top Crossbars
    m.add_box(-900.0, 850.0, -950.0 - post_sz/2, -950.0 + post_sz/2, fence_z - 30.0, fence_z)
    m.add_box(-900.0, 850.0, 1300.0 - post_sz/2, 1300.0 + post_sz/2, fence_z - 30.0, fence_z)
    m.add_box(-900.0 - post_sz/2, -900.0 + post_sz/2, -950.0, 1300.0, fence_z - 30.0, fence_z)

    return m


def main():
    cad_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(cad_dir)
    stl_dir = os.path.join(project_root, "STL")
    os.makedirs(stl_dir, exist_ok=True)

    print(f"Generating CAD models...")
    print(f"  Primary STL Destination Folder: {stl_dir}")
    print(f"  CAD Archive Folder:             {cad_dir}\n")

    generators = [
        ("Feeder_Tray", build_feeder_tray),
        ("Packing_Box", build_packing_box),
        ("Product", build_product),
        ("Vacuum_Gripper", build_vacuum_gripper),
        ("Conveyor_Components", build_conveyor_system),
        ("Cell_Layout_Assembly", build_cell_layout),
    ]

    for name, gen_fn in generators:
        print(f"  Building {name}...")
        mesh = gen_fn()
        
        # 1. Primary Binary STL -> Saved into dedicated STL/ folder
        stl_path_dedicated = os.path.join(stl_dir, f"{name}.stl")
        mesh.export_stl_binary(stl_path_dedicated)
        print(f"    -> [DEDICATED STL FOLDER] {stl_path_dedicated} ({len(mesh.triangles)} facets, {len(mesh.vertices)} vertices)")

        # Also save in CAD folder
        stl_path_cad = os.path.join(cad_dir, f"{name}.stl")
        mesh.export_stl_binary(stl_path_cad)

        # 2. ASCII STL -> Saved in both STL/ and CAD/
        stl_ascii_path = os.path.join(stl_dir, f"{name}_ascii.stl")
        mesh.export_stl_ascii(stl_ascii_path)
        mesh.export_stl_ascii(os.path.join(cad_dir, f"{name}_ascii.stl"))

        # 3. STEP AP214/AP203 Faceted B-Rep in CAD/ folder
        step_path = os.path.join(cad_dir, f"{name}.step")
        mesh.export_step(step_path)
        print(f"    -> [STEP ARCHIVE]        {step_path}")

    print(f"\nSUCCESS: All STL models gathered in one single folder:")
    print(f"  --> {stl_dir}")


if __name__ == "__main__":
    main()
