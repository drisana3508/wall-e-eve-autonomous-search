
import json
import re
import subprocess
import sys
import statistics
from pathlib import Path

# ------------------------------------------
# SETTINGS
# ------------------------------------------

SEEDS = list(range(101, 201))

PROJECT_FOLDER = Path(__file__).resolve().parent
MAIN_FILE = PROJECT_FOLDER / "main.py"
REPORT_FILE = PROJECT_FOLDER / "mission_report.json"
TRACE_FILE = PROJECT_FOLDER / "mission_trace.json"
RESULTS_FOLDER = PROJECT_FOLDER / "multi_seed_results"

# ------------------------------------------
# HELPER: READ A JSON REPORT
# ------------------------------------------

def read_report(filename):
    if not filename.exists():
        return None

    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return None


# ------------------------------------------
# MAIN TEST
# ------------------------------------------

def main():
    if not MAIN_FILE.exists():
        print("ERROR: main.py was not found.")
        return

    original_main = MAIN_FILE.read_text(encoding="utf-8")

    seed_pattern = re.compile(
        r"^(\s*SEED\s*=\s*)\d+(\s*(?:#.*)?)$",
        re.MULTILINE
    )

    if not seed_pattern.search(original_main):
        print("ERROR: Could not find a line like SEED = 60 in main.py.")
        return

    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    results = []

    print("=" * 60)
    print("WALL-E AND EVE: 100-SEED EVALUATION")
    print("=" * 60)

    try:
        for index, seed in enumerate(SEEDS, start=1):
            print(f"\n[{index}/{len(SEEDS)}] Running seed {seed}...")

            updated_main = seed_pattern.sub(
                lambda match: (
                    match.group(1) + str(seed) + match.group(2)
                ),
                original_main,
                count=1
            )

            MAIN_FILE.write_text(updated_main, encoding="utf-8")

            # Remove old output to prevent stale results.
            for old_file in (REPORT_FILE, TRACE_FILE):
                if old_file.exists():
                    old_file.unlink()

            try:
                process = subprocess.run(
                    [sys.executable, str(MAIN_FILE)],
                    cwd=str(PROJECT_FOLDER),
                    capture_output=True,
                    text=True,
                    timeout=180
                )

                console_file = (
                    RESULTS_FOLDER / f"console_seed_{seed}.txt"
                )
                console_file.write_text(
                    process.stdout + "\n" + process.stderr,
                    encoding="utf-8"
                )

                if process.returncode != 0:
                    print("Python error. Check", console_file.name)
                    results.append({
                        "seed": seed,
                        "run_error": True,
                        "error": "Python process failed"
                    })
                    continue

                report = read_report(REPORT_FILE)

                if report is None:
                    print("No valid report was produced.")
                    results.append({
                        "seed": seed,
                        "run_error": True,
                        "error": "Missing or invalid report"
                    })
                    continue

                # Save a separate report and trace for this seed.
                (RESULTS_FOLDER / f"report_seed_{seed}.json").write_text(
                    json.dumps(report, indent=4),
                    encoding="utf-8"
                )

                if TRACE_FILE.exists():
                    (RESULTS_FOLDER / f"trace_seed_{seed}.json").write_text(
                        TRACE_FILE.read_text(encoding="utf-8"),
                        encoding="utf-8"
                    )

                status_value = str(
                    report.get("status", "")
                ).strip().lower()

                located_value = report.get("eve_located", False)

                success = (
                    located_value is True
                    or status_value in {
                        "eve located successfully",
                        "success",
                        "successful"
                    }
                )

                result = {
                    "seed": seed,
                    "success": success,
                    "steps": report.get("steps_executed"),
                    "battery": report.get("battery_remaining"),
                    "time": report.get("time_remaining"),
                    "run_error": False
                }

                results.append(result)

                print(
                    f"{'SUCCESS' if success else 'NOT LOCATED'} | "
                    f"Steps: {result['steps']} | "
                    f"Battery: {result['battery']} | "
                    f"Time: {result['time']}"
                )

            except subprocess.TimeoutExpired:
                print("TIMEOUT: this mission exceeded 180 seconds.")
                results.append({
                    "seed": seed,
                    "run_error": True,
                    "error": "Timeout after 180 seconds"
                })

            except OSError as error:
                print("Could not run mission:", error)
                results.append({
                    "seed": seed,
                    "run_error": True,
                    "error": str(error)
                })

    finally:
        # Restore the original main.py even if testing fails.
        MAIN_FILE.write_text(original_main, encoding="utf-8")
        print("\nOriginal main.py has been restored.")

    # ------------------------------------------
    # SUMMARY AND METRICS
    # ------------------------------------------

    completed = [
        result for result in results
        if not result.get("run_error", False)
    ]

    successful = [
        result for result in completed
        if result["success"]
    ]

    failed_missions = [
        result for result in completed
        if not result["success"]
    ]

    summary = {
        "seeds_requested": len(SEEDS),
        "runs_with_reports": len(completed),
        "run_errors": len(results) - len(completed),
        "successful_missions": len(successful),
        "failed_missions": len(failed_missions),
        "success_rate_percent": (
            round(len(successful) / len(completed) * 100, 2)
            if completed else None
        )
    }

    print("\n" + "=" * 60)
    print("FINAL EVALUATION")
    print("=" * 60)

    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    for field, label in [
        ("steps", "Average steps on successful missions"),
        ("battery", "Average battery remaining on successful missions"),
        ("time", "Average time remaining on successful missions")
    ]:
        values = [
            result[field]
            for result in successful
            if isinstance(result.get(field), (int, float))
        ]

        if values:
            average = statistics.mean(values)
            summary[f"average_{field}"] = round(average, 2)
            print(f"{label}: {average:.2f}")

    # Save the complete results for later analysis.
    summary["individual_results"] = results

    summary_file = RESULTS_FOLDER / "summary_50_seeds.json"
    summary_file.write_text(
        json.dumps(summary, indent=4),
        encoding="utf-8"
    )

    print("\nSummary saved to:")
    print(summary_file)

    print("\nTesting complete.")
    print("Review failed seeds and their traces before optimizing.")


if __name__ == "__main__":
    main()
