Smart Bank Service Simulation System
=====================================
EE367 – Data Structures and Algorithms
King Abdulaziz University – 202602

FOUR SCENARIOS
--------------
  Scenario 1 → Simple Queue  + Insertion Sort   (baseline)
  Scenario 2 → Min-Heap      + Insertion Sort
  Scenario 3 → Simple Queue  + Binary Search
  Scenario 4 → Min-Heap      + Binary Search    (fully optimized)

USAGE
-----
- Select a scenario from the dropdown and click "Run Scenario"
- Or click "Run All 4 Scenarios" to run them back-to-back automatically
- Adjust Speed slider to speed up the simulation
- KPI results are exported to the Results/ folder after each full run

OUTPUT FILES (auto-generated in Results/)
-----------------------------------------
  Performance_Data.csv          – raw KPI data
  Performance_Data.xlsx         – formatted Excel file
  KPI_Comparison_Charts.png     – bar chart comparing all 4 scenarios

PROJECT STRUCTURE
-----------------
Code/
  main.py                       – entry point
  gui.py                        – full CustomTkinter GUI
  modules/
    abstracts.py                – AbstractEntity, AbstractResource
    entities.py                 – Customer, ServiceCounter
    data_structures.py          – SimpleQueue, MinHeap, HeapNode
    algorithms.py               – InsertionSortScheduler, BinarySearchScheduler
    simulation_engine.py        – SimulationEngine, BankSimulation
    performance_tracker.py      – PerformanceTracker
    exporter.py                 – CSV and Excel export

TEAM
----
1. Mustafa Abdelrahman Mohamed  : 2342671
2. 
3. 
4.
5.
