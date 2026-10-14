
import json
from datetime import datetime


class MissionLogger:
    def __init__(self):
        # Store every mission event in a list.
        self.trace = []

        # Store when the mission begins.
        self.started_at = datetime.now().isoformat(timespec="seconds")

    def log_step(self, step, position, decision, observation, result, reason):
        # Create a record for this action.
        entry = {
            "step": step,
            "position": position,
            "decision": decision,
            "reason": reason,
            "observation": observation,
            "result": result
        }

        # Add the record to the mission trace.
        self.trace.append(entry)

    def save_trace(self, filename="mission_trace.json"):
        # Save all action records to a JSON file.
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(self.trace, file, indent=4, default=str)

    def save_report(self, report, filename="mission_report.json"):
        # Save the final mission report.
        report["started_at"] = self.started_at
        report["finished_at"] = datetime.now().isoformat(timespec="seconds")

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=4, default=str)
