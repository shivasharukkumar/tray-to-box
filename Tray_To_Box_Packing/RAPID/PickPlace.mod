MODULE PickPlaceData
    !**********************************************************************************
    ! Project 18 — Automated Tray-to-Box Packing Robotic Work Cell
    ! Module: PickPlaceData.mod
    ! Description: Kinematics, Tool Definition, Work Objects, Targets, and Offsets
    ! Robot Model: ABB IRB 1200-7/0.7 (Payload 7kg, Reach 703mm)
    !**********************************************************************************

    ! ---------------------------------------------------------------------------------
    ! 1. TOOL DATA DEFINITION
    ! Custom Vacuum Suction Gripper with ISO 9409-1-50-4-M6 interface
    ! TCP: X = 0.0 mm, Y = 0.0 mm, Z = 105.0 mm (at the suction cup sealing lip)
    ! ---------------------------------------------------------------------------------
    PERS tooldata tVacuumGripper := [TRUE, 
        [[0.0, 0.0, 105.0], [1.0, 0.0, 0.0, 0.0]], 
        [0.820, [0.0, 0.0, 38.5], [1.0, 0.0, 0.0, 0.0], 0.001, 0.001, 0.001]];

    ! ---------------------------------------------------------------------------------
    ! 2. WORK OBJECT DEFINITIONS
    ! User coordinate frames for Feeder Station and Packing Station
    ! ---------------------------------------------------------------------------------
    ! Feeder Tray Datum: Center of tray table surface (X=350, Y=-350, Z=465 mm)
    PERS wobjdata wobj_FeederTray := [FALSE, TRUE, "", 
        [[350.0, -350.0, 465.0], [1.0, 0.0, 0.0, 0.0]], 
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]];

    ! Packing Box Datum: Center of box locked at conveyor stop blade (X=350, Y=+350, Z=435 mm)
    PERS wobjdata wobj_PackingBox := [FALSE, TRUE, "", 
        [[350.0, 350.0, 435.0], [1.0, 0.0, 0.0, 0.0]], 
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]];

    ! ---------------------------------------------------------------------------------
    ! 3. SPEED AND ZONE DATA
    ! ---------------------------------------------------------------------------------
    ! Rapid transit speeds for high-efficiency packing
    CONST speeddata vTransit := [800, 500, 5000, 1000];   ! Free travel between stations
    CONST speeddata vApproach := [400, 300, 3000, 800];   ! Descending to clearance height
    CONST speeddata vContact := [80, 50, 1000, 400];      ! Controlled contact during pick/place
    CONST speeddata vRetreat := [300, 200, 2000, 600];    ! Vertical lift after vacuum engage

    ! Zone data: smooth continuous transitions vs precise positioning
    CONST zonedata zFly := z50;                           ! Fly-by for high-speed transit
    CONST zonedata zNear := z10;                          ! Approach waypoint smoothing
    CONST zonedata zStop := fine;                         ! Fine contact for seal engagement

    ! ---------------------------------------------------------------------------------
    ! 4. ROBOT TARGET DEFINITIONS
    ! Orientation quaternion [0.0, 0.0, 1.0, 0.0] points Tool Z vertically downward
    ! ---------------------------------------------------------------------------------
    ! Safe Home Standby Position (in World Coordinates)
    CONST robtarget pHome := [
        [300.0, 0.0, 650.0], 
        [0.0, 0.0, 1.0, 0.0], 
        [0, 0, 0, 0], 
        [9E+09, 9E+09, 9E+09, 9E+09, 9E+09, 9E+09]];

    ! Safe Intermediate Transit Waypoint between Feeder and Box
    CONST robtarget pTransitMid := [
        [350.0, 0.0, 620.0], 
        [0.0, 0.0, 1.0, 0.0], 
        [0, 0, 0, 0], 
        [9E+09, 9E+09, 9E+09, 9E+09, 9E+09, 9E+09]];

    ! Safe Standby Point above Conveyor Movement Envelope
    CONST robtarget pConveyorClear := [
        [350.0, 180.0, 620.0], 
        [0.0, 0.0, 1.0, 0.0], 
        [0, 0, 0, 0], 
        [9E+09, 9E+09, 9E+09, 9E+09, 9E+09, 9E+09]];

    ! Reference Datum Targets in Local Work Objects
    ! Base Pick target at Feeder Tray center surface (offset will be applied per slot)
    CONST robtarget pFeederBasePick := [
        [0.0, 0.0, 35.0], 
        [0.0, 0.0, 1.0, 0.0], 
        [0, 0, 0, 0], 
        [9E+09, 9E+09, 9E+09, 9E+09, 9E+09, 9E+09]];

    ! Base Place target at Packing Box bottom pocket floor
    CONST robtarget pBoxBasePlace := [
        [0.0, 0.0, 38.0], 
        [0.0, 0.0, 1.0, 0.0], 
        [0, 0, 0, 0], 
        [9E+09, 9E+09, 9E+09, 9E+09, 9E+09, 9E+09]];

    ! ---------------------------------------------------------------------------------
    ! 5. INDEXED SLOT COORDINATE OFFSETS
    ! 2x2 Array configurations for 4 feeder pockets and 4 box compartments
    ! ---------------------------------------------------------------------------------
    ! Feeder Pitch = 90 mm (+/-45 mm from center)
    ! Slot 1: [-45, -45], Slot 2: [+45, -45], Slot 3: [-45, +45], Slot 4: [+45, +45]
    CONST pos slotFeederOffset{4} := [
        [-45.0, -45.0, 0.0], 
        [ 45.0, -45.0, 0.0], 
        [-45.0,  45.0, 0.0], 
        [ 45.0,  45.0, 0.0]];

    ! Packing Box Pitch = 100 mm (+/-50 mm from center)
    ! Slot 1: [-50, -50], Slot 2: [+50, -50], Slot 3: [-50, +50], Slot 4: [+50, +50]
    CONST pos slotBoxOffset{4} := [
        [-50.0, -50.0, 0.0], 
        [ 50.0, -50.0, 0.0], 
        [-50.0,  50.0, 0.0], 
        [ 50.0,  50.0, 0.0]];

    ! Vertical Clearances
    CONST num nApproachHeight := 90.0;   ! Clearance above tray/box during approach
    CONST num nLiftHeight     := 110.0;  ! Vertical lift distance before horizontal transfer

ENDMODULE
