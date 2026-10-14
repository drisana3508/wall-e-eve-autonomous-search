# WALL-E and EVE: Autonomous Search and Signal Detection Agent

## Project Overview
WALL-E and EVE is a Python-based autonomous search simulation. The agent explores a partially observable grid environment, gathers clues through scanning, estimates EVE's possible location, plans its movements, and manages battery resources.

## Features
- Autonomous grid exploration
- Scan-based signal detection
- Belief-state tracking for possible EVE locations
- Path planning using Breadth-First Search (BFS)
- Battery management and recharging
- Mission logging and JSON reports
- Automated multi-seed testing

## Technologies Used
- Python 3
- Search and path-planning algorithms
- Belief-state updates
- JSON for mission logs and reports

## Project Files
- `main.py` — starts the simulation
- `agent.py` — contains the agent's decision-making logic
- `environment.py` — simulates the environment
- `belief.py` — tracks possible EVE locations
- `mission_log.py` — records mission traces and reports
- `multi_seed_test.py` — runs multiple test seeds
- `mission_report.json` — mission summary
- `mission_trace.json` — detailed mission trace

## How to Run
1. Install Python 3.
2. Clone or download this repository.
3. Open a terminal in the project folder.
4. Run the simulation:

   `python main.py`

5. To run multi-seed testing, follow the configuration and instructions in `multi_seed_test.py`.

## Testing Results
- Initial 50-seed run: 48/50 successful missions (96%).
- Final 50-seed rerun after an agent improvement: 50/50 successful missions (100%).
- Additional test using seeds 101–200: 100/100 successful missions (100%).

These are observed results for the tested seed ranges and do not guarantee success in every possible environment.

## Documentation
The final project report and graphs should be added to the `reports/` folder.

