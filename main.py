
from environment import MissionEnvironment
from agent import WallEAgent
from belief import EveBelief
from mission_log import MissionLogger


# Configuration
SEED = 60
MAX_STEPS = 100


# 1. Create all mission components.
env = MissionEnvironment(seed=SEED)
agent = WallEAgent()

belief = EveBelief(
    env.width,
    env.height,
    env.obstacles
)

logger = MissionLogger()

print("WALL-E AND EVE: AUTONOMOUS SEARCH")
print("=" * 40)

env.display_map()

mission_result = "Action limit reached"
total_steps = 0


# 2. Run the autonomous mission.
for step in range(MAX_STEPS):

    total_steps = step + 1

    # Stop if mission time has run out.
    if env.time_remaining <= 0:
        mission_result = "Mission time exhausted"
        total_steps -= 1
        break

    # 3. Observe the environment before taking an action.
    observation = env.observe()
    position_before = env.position

    # 4. Ask WALL-E to choose an action.
    decision = agent.choose_action(
        observation,
        env,
        belief
    )

    action = decision["action"]
    reason = decision["reason"]

    print(f"\nStep {total_steps}")
    print("Position:", position_before)
    print("Action:", action)
    print("Reason:", reason)

    # 5. Stop if the agent chooses to finish.
    if action == "stop":
        mission_result = reason
        total_steps -= 1
        break

    # 6. Execute the selected action.
    if action == "scan":

        result = env.scan()

        if result.get("success", False):

            # Record a successfully scanned position.
            agent.scanned.add(position_before)

            # Update possible EVE locations.
            belief.update_after_scan(
                position_before,
                result.get("eve_detected", False)
            )

    elif action == "move":

        result = env.move(decision["direction"])

        if result.get("success", False):

            # Update the belief if EVE was found.
            belief.update_after_move(
                env.position,
                env.eve_found
            )

    elif action == "recharge":

        result = env.recharge()

    else:

        result = {
            "success": False,
            "message": "Unknown action"
        }

        mission_result = "Unknown action"
        total_steps -= 1
        break

    print(
        "Environment response:",
        result.get("message", "No message")
    )

    # 7. Display newly discovered clues.
    if "new_clues" in result:
        print("New clues:", result["new_clues"])

    # 8. Capture the observation after the action.
    observation_after = env.observe()

    signal_detected = None

    if action == "scan" and result.get("success", False):
        signal_detected = result.get("eve_detected", False)

    observation["signal_detected"] = signal_detected
    observation["position_after"] = env.position
    observation["observation_after"] = observation_after

    # 9. Save the action and observations.
    logger.log_step(
        step=total_steps,
        position=position_before,
        decision=decision,
        observation=observation,
        result=result,
        reason=reason
    )

    # 10. Display the current belief estimate.
    print(
        "Estimated EVE location:",
        belief.get_estimate()
    )

    print(
        "Estimate confidence:",
        round(belief.get_confidence() * 100, 2),
        "%"
    )

    print(
        "Possible locations:",
        len(belief.possible_locations)
    )

    # 11. Finish if EVE has been located.
    if env.eve_found:

        belief.update_after_move(
            env.position,
            True
        )

        mission_result = "EVE located successfully"

        print("\nEVE has been located!")
        break

    # Stop if mission time expires.
    if env.time_remaining <= 0:
        mission_result = "Mission time exhausted"
        break

else:
    mission_result = "Action limit reached"


# 12. Save the full action trace.
logger.save_trace()


# 13. Prepare the final mission report.
report = {
    "mission": "WALL-E and EVE's Signal",
    "seed": SEED,
    "status": mission_result,
    "eve_located": env.eve_found,
    "final_position": env.position,
    "estimated_eve_location": belief.get_estimate(),
    "confidence": round(belief.get_confidence(), 4),
    "battery_remaining": env.battery,
    "time_remaining": env.time_remaining,
    "clues_discovered": len(env.discovered_clues),
    "steps_executed": total_steps,
    "evidence_found": [
        list(clue)
        for clue in sorted(env.discovered_clues)
    ],
    "recommended_next_step": (
        "Confirm EVE's status and report the recovered signal."
        if env.eve_found
        else "Continue searching using new scans and observations."
    )
}


# 14. Save the final mission report.
logger.save_report(report)


# 15. Display the final mission report.
print("\n" + "=" * 40)
print("FINAL MISSION REPORT")
print("=" * 40)

for key, value in report.items():
    print(f"{key}: {value}")

print("\nFiles saved:")
print("- mission_trace.json")
print("- mission_report.json")
