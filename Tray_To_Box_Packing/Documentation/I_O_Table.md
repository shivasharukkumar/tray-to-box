# Industrial Digital I/O Interface Specification & Timing Diagrams
## Project 18 — Digital Twin Commissioning: Automated Tray-to-Box Packing

---

## 1. Master Signal Dictionary

The work cell operates using an industrial 24 VDC PNP digital I/O architecture mapped onto the ABB Virtual Controller Local Bus (`Virtual_IO_Board`).

### 1.1 Digital Inputs (Sensors -> Controller)
| Signal Name | Address | Logic Type | Voltage | Debounce | Functional Description |
|---|---|---|---|---|---|
| `diTrayReady` | DI 0 | Active HIGH | 24 VDC | 15 ms | Feeder tray clamped and populated with parts. |
| `diPartPresent` | DI 1 | Active HIGH | 24 VDC | 10 ms | Optical sensor detects part in active pick slot. |
| `diBoxPresent` | DI 2 | Active HIGH | 24 VDC | 20 ms | Packing box seated against mechanical stop blade. |
| `diGripConfirmed` | DI 3 | Active HIGH | 24 VDC | 5 ms | Vacuum switch threshold reached (<-75 kPa). |
| `diBoxExitClear` | DI 4 | Active HIGH | 24 VDC | 20 ms | Outfeed conveyor discharge zone unobstructed. |
| `diEmergencyStop`| DI 5 | Active HIGH (NC)| 24 VDC | 2 ms | Dual-channel safety loop (1 = Healthy, 0 = E-Stop).|
| `diCellGateClosed`| DI 6 | Active HIGH (NC)| 24 VDC | 2 ms | Perimeter safety door locked (1 = Closed). |

### 1.2 Digital Outputs (Controller -> Actuators / Smart Components)
| Signal Name | Address | Logic Type | Voltage | Current | Functional Description |
|---|---|---|---|---|---|
| `doVacuumOn` | DO 0 | Active HIGH | 24 VDC | 0.5 A | Energizes 5/2 vacuum ejector solenoid valve. |
| `doInfeedRun` | DO 1 | Active HIGH | 24 VDC | 2.0 A | Drives infeed conveyor motor (150 mm/s). |
| `doOutfeedRun` | DO 2 | Active HIGH | 24 VDC | 2.0 A | Drives outfeed conveyor motor (200 mm/s). |
| `doBoxFull` | DO 3 | Active HIGH | 24 VDC | 0.1 A | Status bit indicating 4 parts packed in box. |
| `doCycleComplete`| DO 4 | Pulse (300ms)| 24 VDC | 0.1 A | Strobe signal indicating completed box cycle. |
| `doReplenishTray`| DO 5 | Pulse (500ms)| 24 VDC | 0.5 A | Triggers feeder Smart Component to spawn 4 parts.|
| `doRobotInHome` | DO 6 | Active HIGH | 24 VDC | 0.1 A | Safety bit: robot confirmed at pHome standby. |
| `doRobotInFeederZone`| DO 7| Active HIGH | 24 VDC | 0.1 A | Safety bit: robot arm inside feeder perimeter. |
| `doRobotInBoxZone`| DO 8 | Active HIGH | 24 VDC | 0.1 A | Safety bit: robot arm inside box conveyor zone.|
| `doStopBladeLower`| DO 9 | Active HIGH | 24 VDC | 0.5 A | Retracts pneumatic box stop blade. |
| `doCellAlarm` | DO 10| Active HIGH | 24 VDC | 1.0 A | Cell fault strobe for visual/acoustic beacon. |

---

## 2. Signal Timing Sequence Diagrams

### 2.1 Empty Box Infeed & Registration Sequence
```
Time (s)        0.0    0.5    1.0    1.5    2.0    2.5    3.0    3.5
doInfeedRun      [___________ON________________________] OFF
diBoxPresent     OFF --------------------------[________ON__________]
doRobotInBoxZone OFF -----------------------------------------------
```
1. Controller checks `diBoxPresent = 0`.
2. Controller asserts `doInfeedRun = 1` while verifying `doRobotInBoxZone = 0`.
3. Infeed conveyor advances empty box forward at 150 mm/s.
4. Box contacts stop blade at packing station -> `diBoxPresent` asserts.
5. Controller de-asserts `doInfeedRun = 0` within 10 ms.
6. 200 ms mechanical damping delay occurs before robot enters box zone.

---

### 2.2 Vacuum Pick & Pressure Confirmation Handshake
```
Time (s)         0.0    0.2    0.4    0.6    0.8    1.0    1.2
Robot Path       [--- Descent ---][Contact][--- Lift ---]
doVacuumOn       OFF -------------[_________ON__________]
diGripConfirmed  OFF -------------------[_______ON______]
                                  <150ms>
```
1. Robot executes `MoveL` to pick target with `zStop` (fine point).
2. Robot asserts `doVacuumOn = 1`.
3. Vacuum generator evacuates cup volume; pressure switch detects <-75 kPa after 150 ms.
4. `diGripConfirmed` transitions to HIGH.
5. RAPID `WaitDI diGripConfirmed, 1 \MaxTime:=1.5` validates grip.
6. Robot executes smooth vertical retreat with part securely held.

---

### 2.3 Vacuum Release & Box Parenting Handshake
```
Time (s)         0.0    0.1    0.2    0.3    0.4    0.5
Robot Path       [--- Descent ---][Dwell][--- Lift ---]
doVacuumOn       ON --------------[OFF__________________]
diGripConfirmed  ON --------------[OFF__________________]
Parent To Box    OFF -------------[_PULSE_] OFF --------
```
1. Robot descends into box compartment to placement depth.
2. Robot de-asserts `doVacuumOn = 0`.
3. Vacuum breaks; `diGripConfirmed` drops to LOW.
4. Detach strobe triggers `SC_BoxPacker` to link workpiece to `Packing_Box`.
5. Robot dwells for 100 ms to guarantee complete pneumatic decay.
6. Robot retreats vertically along Z axis.

---

### 2.4 Box Full & Outfeed Discharge Handshake
```
Time (s)         0.0    0.5    1.0    1.5    2.0    2.5    3.0    3.5
doBoxFull        [____________________ON____________________] OFF
doRobotInHome    [____________________ON____________________]
doStopBladeLower OFF ---[_____________ON____________________] OFF
doOutfeedRun     OFF -------[_________ON____________________] OFF
diBoxPresent     ON --------[___OFF___] ----------------------
doCycleComplete  OFF ---------------------------------------[_PULSE_]
```
1. 4th part placement completed -> Controller asserts `doBoxFull = 1`.
2. Robot moves to `pHome` (`doRobotInHome = 1`, `doRobotInBoxZone = 0`).
3. Stop blade cylinder retracts (`doStopBladeLower = 1`).
4. Outfeed conveyor runs (`doOutfeedRun = 1`), carrying full box + 4 parts toward outfeed sink.
5. Box departs stop station -> `diBoxPresent` transitions to LOW.
6. Once box reaches outfeed sink, outfeed conveyor stops, stop blade resets, and `doCycleComplete` pulses.
