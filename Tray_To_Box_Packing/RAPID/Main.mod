MODULE MainModule
    !**********************************************************************************
    ! Project 18 — Automated Tray-to-Box Packing Robotic Work Cell
    ! Module: Main.mod
    ! Description: Production Executive Control, Indexed Cycle Routines, Error Handling
    ! Robot: ABB IRB 1200-7/0.7 on IRC5 / OmniCore Controller
    !**********************************************************************************

    ! Cycle and Packing Counters
    VAR num nCycleCount := 0;             ! Completed box counter (Target >= 10 cycles)
    VAR num nCurrentSlot := 1;            ! Current indexed slot (1 to 4)
    VAR num nPartsInCurrentBox := 0;      ! Verification tally of parts packed
    VAR bool bCellInitialized := FALSE;   ! Cell initialization status flag
    VAR clock clkCycleTimer;              ! Stopwatch for precision cycle time measurement
    VAR num nMeasuredCycleTime := 0.0;    ! Elapsed seconds per completed box

    ! Error Codes
    CONST num ERR_VACUUM_FAILED := 101;
    CONST num ERR_BOX_MISSING   := 102;
    CONST num ERR_TRAY_EMPTY    := 103;
    CONST num ERR_OUTFEED_BLOCKED := 104;
    CONST num ERR_SAFETY_TRIPPED  := 105;

    ! Maximum Consecutive Production Cycles
    CONST num MAX_PRODUCTION_CYCLES := 10;

    ! ---------------------------------------------------------------------------------
    ! MAIN ENTRY POINT
    ! ---------------------------------------------------------------------------------
    PROC main()
        TPWrite "==================================================";
        TPWrite " ABB TRAY-TO-BOX AUTOMATED PACKING CELL STARTING ";
        TPWrite " Project 18 — Digital Twin Commissioning          ";
        TPWrite " Target: 10 Full Box Cycles (40 Indexed Parts)   ";
        TPWrite "==================================================";

        ! Step 1: Initialize System Hardware, Signals, and Homing
        InitializeCell();

        ! Step 2: Continuous Automatic Production Loop (At least 10 full box cycles)
        WHILE (nCycleCount < MAX_PRODUCTION_CYCLES) DO
            ClkReset clkCycleTimer;
            ClkStart clkCycleTimer;

            TPWrite "--------------------------------------------------";
            TPWrite " STARTING PRODUCTION CYCLE " \Num:= (nCycleCount + 1);
            TPWrite "--------------------------------------------------";

            ! Stage 1 & 2: Wait for Infeed Box and Feeder Tray Ready
            WaitForBox();
            WaitForTray();

            ! Reset parts count for the new empty box
            nPartsInCurrentBox := 0;

            ! Stage 3 & 4: Sequential 4-Slot Indexed Pick and Place Operation
            FOR slotIndex FROM 1 TO 4 DO
                nCurrentSlot := slotIndex;
                TPWrite ">>> Processing Part " \Num:= nCurrentSlot \NoNewLine;
                TPWrite " (Slot " \Num:= nCurrentSlot \NoNewLine;
                TPWrite " of 4)";

                ! Pick part from feeder tray slot
                PickPart(nCurrentSlot);

                ! Place part into packing box slot
                PlacePart(nCurrentSlot);

                ! Update tally
                nPartsInCurrentBox := nPartsInCurrentBox + 1;
            ENDFOR

            ! Stage 5: Box Full Verification
            CheckBoxFull();

            ! Stage 6: Safe Outfeed Release & Automated Replacement Handshake
            ReleaseFullBox();

            ! Stop and record cycle time
            ClkStop clkCycleTimer;
            nMeasuredCycleTime := ClkRead(clkCycleTimer);
            nCycleCount := nCycleCount + 1;

            TPWrite ">>> CYCLE " \Num:= nCycleCount \NoNewLine;
            TPWrite " COMPLETE! Elapsed Time: " \Num:= nMeasuredCycleTime \NoNewLine;
            TPWrite " seconds.";

            ! Reset Cycle Signals & Prepare for Next Box
            ResetCycle();
        ENDWHILE

        ! End of 10-Cycle Validation Run
        TPWrite "==================================================";
        TPWrite " PRODUCTION BATCH COMPLETE! 10 Boxes (40 Parts)  ";
        TPWrite " System returning to Home and entering Standby.  ";
        TPWrite "==================================================";
        
        MoveJ pHome, vTransit, zStop, tVacuumGripper;
        SetDO doRobotInHome, 1;
        SetDO doCycleComplete, 1;
    ERROR
        HandleFault(ERRNO);
    ENDPROC


    ! ---------------------------------------------------------------------------------
    ! ROUTINE 1: InitializeCell
    ! Resets actuators, checks safety circuits, homes robot arm, and confirms signals
    ! ---------------------------------------------------------------------------------
    PROC InitializeCell()
        TPWrite "Initializing Work Cell Hardware and Safety...";

        ! Deactivate all output actuators
        SetDO doVacuumOn, 0;
        SetDO doInfeedRun, 0;
        SetDO doOutfeedRun, 0;
        SetDO doBoxFull, 0;
        SetDO doCycleComplete, 0;
        SetDO doReplenishTray, 0;
        SetDO doRobotInFeederZone, 0;
        SetDO doRobotInBoxZone, 0;
        SetDO doStopBladeLower, 0;
        SetDO doCellAlarm, 0;

        ! Verify Safety Interlocks (E-Stop and Perimeter Gates)
        IF (diEmergencyStop = 0) THEN
            HandleFault(ERR_SAFETY_TRIPPED);
        ENDIF

        ! Move Robot to Verified Home Standby Position
        MoveJ pHome, vApproach, zStop, tVacuumGripper;
        SetDO doRobotInHome, 1;

        ! Trigger Initial Part Replenishment for Feeder Tray
        PulseDO \PLength:=0.5, doReplenishTray;

        ! Staggered delay for physical settling
        WaitTime 0.5;

        bCellInitialized := TRUE;
        TPWrite "System Initialization Complete. Ready for automatic cycle.";
    ENDPROC


    ! ---------------------------------------------------------------------------------
    ! ROUTINE 2: WaitForTray
    ! Verifies feeder tray is seated and workpiece is present before attempting pick
    ! ---------------------------------------------------------------------------------
    PROC WaitForTray()
        TPWrite "Verifying Feeder Tray Status...";

        ! Check if feeder tray fixture is clamped and ready
        IF (diTrayReady = 0) THEN
            TPWrite "Tray not ready. Triggering replenishment...";
            PulseDO \PLength:=0.5, doReplenishTray;
            WaitDI diTrayReady, 1 \MaxTime:=5.0 \TimeFlag:=bCellInitialized;
            IF (bCellInitialized = FALSE) THEN
                HandleFault(ERR_TRAY_EMPTY);
            ENDIF
        ENDIF

        ! Check if workpiece is present in active feeder slot
        IF (diPartPresent = 0) THEN
            TPWrite "Waiting for workpiece sensor in slot...";
            WaitDI diPartPresent, 1 \MaxTime:=3.0 \TimeFlag:=bCellInitialized;
            IF (bCellInitialized = FALSE) THEN
                HandleFault(ERR_TRAY_EMPTY);
            ENDIF
        ENDIF

        TPWrite "Feeder Tray and Workpiece Confirmed Ready.";
    ENDPROC


    ! ---------------------------------------------------------------------------------
    ! ROUTINE 3: WaitForBox
    ! Coordinates infeed conveyor to advance an empty packing box into the station
    ! ---------------------------------------------------------------------------------
    PROC WaitForBox()
        TPWrite "Checking for Empty Packing Box at Station...";

        ! If box is already locked at stop blade, proceed immediately
        IF (diBoxPresent = 1) THEN
            TPWrite "Box detected at packing station.";
            RETURN;
        ENDIF

        ! Ensure stop blade is raised to catch incoming box
        SetDO doStopBladeLower, 0;

        ! Confirm robot is safely outside conveyor movement envelope
        IF (doRobotInBoxZone = 1) THEN
            MoveJ pHome, vTransit, zStop, tVacuumGripper;
            SetDO doRobotInBoxZone, 0;
            SetDO doRobotInHome, 1;
        ENDIF

        ! Turn on infeed conveyor to index empty box forward
        TPWrite "Running Infeed Conveyor (Empty Box Feeding)...";
        SetDO doInfeedRun, 1;

        ! Wait for optical sensor at stop blade to confirm box arrival (12s timeout)
        WaitDI diBoxPresent, 1 \MaxTime:=12.0 \TimeFlag:=bCellInitialized;
        
        ! Immediately halt conveyor once box arrives
        SetDO doInfeedRun, 0;

        IF (bCellInitialized = FALSE) THEN
            HandleFault(ERR_BOX_MISSING);
        ENDIF

        ! Allow 200ms mechanical settling time against the stop blade
        WaitTime 0.2;
        TPWrite "Empty Packing Box Locked and Registered.";
    ENDPROC


    ! ---------------------------------------------------------------------------------
    ! ROUTINE 4: PickPart(num nSlot)
    ! Indexed approach, vacuum engagement, confirmation, and retreat from feeder tray
    ! ---------------------------------------------------------------------------------
    PROC PickPart(num nSlot)
        VAR robtarget pPickTarget;
        VAR robtarget pApproachTarget;
        VAR robtarget pRetreatTarget;
        VAR pos currentOffset;

        ! Retrieve indexed 2x2 coordinate offset for the active slot
        currentOffset := slotFeederOffset{nSlot};

        ! Calculate 3D Targets relative to Feeder Work Object
        pPickTarget := Offs(pFeederBasePick, currentOffset.x, currentOffset.y, currentOffset.z);
        pApproachTarget := Offs(pPickTarget, 0.0, 0.0, nApproachHeight);
        pRetreatTarget := Offs(pPickTarget, 0.0, 0.0, nLiftHeight);

        ! Announce entering feeder zone
        SetDO doRobotInHome, 0;
        SetDO doRobotInFeederZone, 1;

        ! 1. Rapid move to Approach position above active feeder cavity
        MoveJ pApproachTarget, vTransit, zNear, tVacuumGripper \WObj:=wobj_FeederTray;

        ! 2. Controlled vertical descent to contact the workpiece top surface
        MoveL pPickTarget, vContact, zStop, tVacuumGripper \WObj:=wobj_FeederTray;

        ! 3. Energize vacuum ejector solenoid valve
        SetDO doVacuumOn, 1;

        ! 4. Wait for vacuum pressure switch feedback (diGripConfirmed <-75 kPa)
        WaitDI diGripConfirmed, 1 \MaxTime:=1.5 \TimeFlag:=bCellInitialized;
        IF (bCellInitialized = FALSE) THEN
            TPWrite "ERROR: Vacuum attachment failed on Slot " \Num:= nSlot;
            SetDO doVacuumOn, 0;
            HandleFault(ERR_VACUUM_FAILED);
        ENDIF

        ! Dwell for vacuum stabilization
        WaitTime 0.1;

        ! 5. Smooth vertical lift out of feeder cavity to safe retreat height
        MoveL pRetreatTarget, vRetreat, zNear, tVacuumGripper \WObj:=wobj_FeederTray;

        ! Exit feeder zone
        SetDO doRobotInFeederZone, 0;
    ENDPROC


    ! ---------------------------------------------------------------------------------
    ! ROUTINE 5: PlacePart(num nSlot)
    ! Transfer, indexed alignment, insertion, vacuum release, and detachment into box
    ! ---------------------------------------------------------------------------------
    PROC PlacePart(num nSlot)
        VAR robtarget pPlaceTarget;
        VAR robtarget pApproachTarget;
        VAR robtarget pRetreatTarget;
        VAR pos currentOffset;

        ! Retrieve indexed 2x2 coordinate offset for the target box compartment
        currentOffset := slotBoxOffset{nSlot};

        ! Calculate 3D Targets relative to Packing Box Work Object
        pPlaceTarget := Offs(pBoxBasePlace, currentOffset.x, currentOffset.y, currentOffset.z);
        pApproachTarget := Offs(pPlaceTarget, 0.0, 0.0, nApproachHeight);
        pRetreatTarget := Offs(pPlaceTarget, 0.0, 0.0, nLiftHeight);

        ! Verify box is still locked in position before entering box zone
        IF (diBoxPresent = 0) THEN
            HandleFault(ERR_BOX_MISSING);
        ENDIF

        ! 1. High-speed fly-by transit through intermediate safe waypoint
        MoveJ pTransitMid, vTransit, zFly, tVacuumGripper;

        ! Announce entering packing conveyor zone
        SetDO doRobotInBoxZone, 1;

        ! 2. Move to Approach position above destination compartment
        MoveJ pApproachTarget, vTransit, zNear, tVacuumGripper \WObj:=wobj_PackingBox;

        ! 3. Smooth vertical descent into compartment to seating depth
        MoveL pPlaceTarget, vContact, zStop, tVacuumGripper \WObj:=wobj_PackingBox;

        ! 4. Deactivate vacuum solenoid valve to release part
        SetDO doVacuumOn, 0;

        ! 5. Wait for vacuum decay confirmation
        WaitDI diGripConfirmed, 0 \MaxTime:=1.0 \TimeFlag:=bCellInitialized;

        ! Dwell 100ms for atmospheric equalization & Smart Component box attachment
        WaitTime 0.1;

        ! 6. Vertical retreat to clear the box upper rim
        MoveL pRetreatTarget, vRetreat, zNear, tVacuumGripper \WObj:=wobj_PackingBox;

        ! Exit box zone
        SetDO doRobotInBoxZone, 0;
    ENDPROC


    ! ---------------------------------------------------------------------------------
    ! ROUTINE 6: CheckBoxFull
    ! Validates that all 4 compartments have been filled before releasing conveyor
    ! ---------------------------------------------------------------------------------
    PROC CheckBoxFull()
        TPWrite "Validating Box Contents (4 of 4 Slots)...";

        IF (nPartsInCurrentBox = 4) THEN
            SetDO doBoxFull, 1;
            TPWrite "Box-Full Verified: 4 Workpieces Packed Successfully.";
        ELSE
            TPWrite "FATAL: Incomplete pack tally: " \Num:= nPartsInCurrentBox;
            HandleFault(ERR_TRAY_EMPTY);
        ENDIF
    ENDPROC


    ! ---------------------------------------------------------------------------------
    ! ROUTINE 7: ReleaseFullBox
    ! Retreats robot to safe clearance, opens stop blade, runs outfeed conveyor,
    ! and carries completed box with all 4 attached parts out of the work cell.
    ! ---------------------------------------------------------------------------------
    PROC ReleaseFullBox()
        TPWrite "Initiating Full Box Discharge Sequence...";

        ! 1. Ensure robot moves completely clear of the conveyor movement envelope
        MoveJ pConveyorClear, vTransit, zNear, tVacuumGripper;
        MoveJ pHome, vTransit, zStop, tVacuumGripper;
        SetDO doRobotInBoxZone, 0;
        SetDO doRobotInHome, 1;

        ! 2. Verify outfeed conveyor path is unobstructed
        IF (diBoxExitClear = 0) THEN
            TPWrite "Outfeed conveyor blocked. Waiting for path to clear...";
            WaitDI diBoxExitClear, 1 \MaxTime:=10.0 \TimeFlag:=bCellInitialized;
            IF (bCellInitialized = FALSE) THEN
                HandleFault(ERR_OUTFEED_BLOCKED);
            ENDIF
        ENDIF

        ! 3. Lower / retract pneumatic stop blade to allow box passage
        SetDO doStopBladeLower, 1;
        WaitTime 0.15; ! Pneumatic cylinder stroke time

        ! 4. Start outfeed conveyor motor
        SetDO doOutfeedRun, 1;
        TPWrite "Outfeed Conveyor Running — Transporting Box + 4 Parts...";

        ! 5. Wait for box to clear the packing station optical sensor
        WaitDI diBoxPresent, 0 \MaxTime:=8.0 \TimeFlag:=bCellInitialized;
        
        ! Allow box to travel into the exit sink zone (approx 2.5 seconds at 200 mm/s)
        WaitTime 2.5;

        ! 6. Stop outfeed conveyor and raise stop blade for next box
        SetDO doOutfeedRun, 0;
        SetDO doStopBladeLower, 0;
        SetDO doBoxFull, 0;

        TPWrite "Full Box Discharged Successfully to Outfeed Sink.";
    ENDPROC


    ! ---------------------------------------------------------------------------------
    ! ROUTINE 8: ResetCycle
    ! Pulses cycle complete strobe and replenishes feeder tray with 4 new workpieces
    ! ---------------------------------------------------------------------------------
    PROC ResetCycle()
        ! Strobe cycle complete output for PLC / SCADA tracking
        PulseDO \PLength:=0.3, doCycleComplete;

        ! Trigger Smart Component to replenish 4 parts in Feeder Tray
        TPWrite "Replenishing Feeder Tray with 4 new workpieces...";
        PulseDO \PLength:=0.5, doReplenishTray;

        ! Reset internal registers
        nCurrentSlot := 1;
        nPartsInCurrentBox := 0;

        WaitTime 0.2;
    ENDPROC


    ! ---------------------------------------------------------------------------------
    ! ROUTINE 9: HandleFault(num nFaultCode)
    ! Diagnostic handler for hardware exceptions, sensor timeouts, and safety trips
    ! ---------------------------------------------------------------------------------
    PROC HandleFault(num nFaultCode)
        ! Immediately activate cell alarm annunciator
        SetDO doCellAlarm, 1;

        ! Halt conveyors and vacuum
        SetDO doInfeedRun, 0;
        SetDO doOutfeedRun, 0;
        SetDO doVacuumOn, 0;

        TPWrite "**************************************************";
        TPWrite " WORKCELL FAULT ENCOUNTERED! Code: " \Num:= nFaultCode;

        TEST nFaultCode
            CASE ERR_VACUUM_FAILED:
                TPWrite "FAULT: Vacuum Pressure Switch timeout or seal lost.";
                TPWrite "Check suction cup, compressed air supply, and workpiece seating.";
            CASE ERR_BOX_MISSING:
                TPWrite "FAULT: Empty Box infeed timeout.";
                TPWrite "Check infeed conveyor magazine, box sensor, or mechanical jam.";
            CASE ERR_TRAY_EMPTY:
                TPWrite "FAULT: Feeder Tray empty or part presence sensor unasserted.";
                TPWrite "Check feeder gravity feed, magazine replenishment, or optics.";
            CASE ERR_OUTFEED_BLOCKED:
                TPWrite "FAULT: Outfeed discharge zone obstructed.";
                TPWrite "Clear palletizing station / downstream accumulation line.";
            CASE ERR_SAFETY_TRIPPED:
                TPWrite "FAULT: Emergency Stop or Perimeter Safety Gate Tripped!";
            DEFAULT:
                TPWrite "FAULT: General Unhandled System Exception.";
        ENDTEST
        TPWrite "**************************************************";

        ! Attempt safe retreat to Home if physically possible
        IF (doRobotInHome = 0) THEN
            MoveJ pHome, vContact, zStop, tVacuumGripper;
            SetDO doRobotInHome, 1;
        ENDIF

        ! Suspend execution until operator intervention
        Stop;
    ENDPROC

ENDMODULE
