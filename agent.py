
from collections import deque


class WallEAgent:
    def __init__(self):
        self.visited = set()
        self.scanned = set()
        self.directions = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0),
        }
        self.steps = 0
        self.last_scan_position = None

    def choose_action(self, observation, environment, belief):
        self.steps += 1

        position = tuple(observation["position"])
        battery = observation["battery"]
        time_remaining = observation["time_remaining"]

        self.visited.add(position)

        # Stop if the mission is finished or time has run out.
        if observation.get("eve_found", False):
            return {
                "action": "stop",
                "reason": "EVE has been located successfully."
            }

        if time_remaining <= 0:
            return {
                "action": "stop",
                "reason": "Mission time has run out."
            }

        # Read the environment's map information.
        charger = tuple(environment.charger)
        obstacles = set(environment.obstacles)

        # Find the shortest route back to the charger.
        distance_to_charger = self.shortest_distance(
            position, charger, environment
        )

        if distance_to_charger is None:
            distance_to_charger = 999

        # Keep enough battery to return to the charger.
        # Add a small safety reserve for unexpected situations.
        if position != charger and battery <= distance_to_charger + 5:
            next_position = self.next_step(
                position, charger, environment
            )

            if next_position is not None:
                return {
                    "action": "move",
                    "direction": self.direction_between(
                        position, next_position
                    ),
                    "reason": "Return to the charger before battery gets too low."
                }

        # Recharge whenever WALL-E reaches the charger
        # with less than a full battery.
        if position == charger and battery < 100:
            return {
                "action": "recharge",
                "reason": "Recharge the battery before continuing."
            }

        possible = set(belief.possible_locations)

        # If the belief system has confirmed EVE's location,
        # travel directly to that location.
        if belief.is_confirmed():
            target = tuple(belief.confirmed_location)

            if position == target:
                return {
                    "action": "stop",
                    "reason": "EVE's location has been confirmed."
                }

            next_position = self.next_step(
                position, target, environment
            )

            if next_position is not None:
                return {
                    "action": "move",
                    "direction": self.direction_between(
                        position, next_position
                    ),
                    "reason": "Move to the confirmed EVE location."
                }

        # When few candidates remain, investigate the nearest
        # candidate first instead of wasting time on distant scans.
                # Investigate candidates directly when only a few remain.
        # This gives WALL-E more time to reach EVE before the
        # action limit is reached.
        if possible and len(possible) <= 15:

            target = self.nearest_candidate(
                position, possible, environment
            )

            if target is not None:

                # If WALL-E is already at this candidate,
                # it should have found EVE if EVE were there.
                if position == target:
                    belief.update_after_move(position, False)
                    possible = set(belief.possible_locations)

                else:
                    next_position = self.next_step(
                        position, target, environment
                    )

                    if next_position is not None:
                        return {
                            "action": "move",
                            "direction": self.direction_between(
                                position, next_position
                            ),
                            "reason": (
                                "Investigate a remaining possible "
                                "EVE location: " + str(target)
                            )
                        }

            elif position not in self.scanned and battery >= 3:
                return {
                    "action": "scan",
                    "reason": "Scan the selected informative location."
                }

        # If scanning cannot help, move toward the nearest
        # remaining candidate.
        if possible:
            target = self.nearest_candidate(
                position, possible, environment
            )

            if target is not None and target != position:
                next_position = self.next_step(
                    position, target, environment
                )

                if next_position is not None:
                    return {
                        "action": "move",
                        "direction": self.direction_between(
                            position, next_position
                        ),
                        "reason": "Move toward the nearest possible EVE location."
                    }

        # Explore an unvisited cell if no useful candidate
        # or scan target is available.
        target = self.find_unvisited_cell(
            position, environment
        )

        if target is not None:
            next_position = self.next_step(
                position, target, environment
            )

            if next_position is not None:
                return {
                    "action": "move",
                    "direction": self.direction_between(
                        position, next_position
                    ),
                    "reason": "Explore an unvisited cell."
                }

        return {
            "action": "stop",
            "reason": "No reachable search target remains."
        }

    def scan_information_score(self, scan_position, possible_locations):
        """
        Estimate how informative a scan could be.

        A scan can detect EVE when Manhattan distance is at most 1.
        A useful scan divides the remaining candidates into
        detectable and non-detectable groups.
        """
        if not possible_locations:
            return 0

        x, y = scan_position
        detectable = 0

        for candidate in possible_locations:
            distance = (
                abs(candidate[0] - x)
                + abs(candidate[1] - y)
            )

            if distance <= 1:
                detectable += 1

        not_detectable = len(possible_locations) - detectable

        # Prefer scans that divide candidates into two useful groups.
        return min(detectable, not_detectable)

    def best_scan_target(self, position, possible_locations, environment):
        """
        Choose a reachable, unscanned cell with a useful scan score.
        Distance is considered so WALL-E does not travel too far
        for a small amount of information.
        """
        if not possible_locations:
            return None

        width = environment.width
        height = environment.height
        obstacles = set(environment.obstacles)

        best_target = None
        best_score = 0
        best_distance = float("inf")

        for x in range(width):
            for y in range(height):
                candidate = (x, y)

                if candidate in obstacles:
                    continue

                if candidate in self.scanned:
                    continue

                distance = self.shortest_distance(
                    position, candidate, environment
                )

                if distance is None:
                    continue

                information = self.scan_information_score(
                    candidate, possible_locations
                )

                # Favor useful scans close to WALL-E.
                adjusted_score = information / (distance + 1)

                if (
                    adjusted_score > best_score
                    or (
                        adjusted_score == best_score
                        and information > 0
                        and distance < best_distance
                    )
                ):
                    best_score = adjusted_score
                    best_distance = distance
                    best_target = candidate

        return best_target

    def nearest_candidate(self, position, candidates, environment):
        """Return the closest reachable possible EVE location."""
        best_target = None
        best_distance = float("inf")

        for candidate in sorted(candidates):
            distance = self.shortest_distance(
                position, candidate, environment
            )

            if distance is not None and distance < best_distance:
                best_distance = distance
                best_target = candidate

        return best_target

    def shortest_distance(self, start, goal, environment):
        """Calculate the shortest path length using BFS."""
        start = tuple(start)
        goal = tuple(goal)

        if start == goal:
            return 0

        obstacles = set(environment.obstacles)
        width = environment.width
        height = environment.height

        queue = deque([(start, 0)])
        visited = {start}

        while queue:
            current, distance = queue.popleft()

            for dx, dy in self.directions.values():
                neighbor = (current[0] + dx, current[1] + dy)

                if not (0 <= neighbor[0] < width):
                    continue

                if not (0 <= neighbor[1] < height):
                    continue

                if neighbor in obstacles or neighbor in visited:
                    continue

                if neighbor == goal:
                    return distance + 1

                visited.add(neighbor)
                queue.append((neighbor, distance + 1))

        return None

    def next_step(self, start, goal, environment):
        """Return the next cell on the shortest path to the goal."""
        start = tuple(start)
        goal = tuple(goal)

        if start == goal:
            return start

        obstacles = set(environment.obstacles)
        width = environment.width
        height = environment.height

        queue = deque([start])
        parent = {start: None}

        while queue:
            current = queue.popleft()

            if current == goal:
                break

            for dx, dy in self.directions.values():
                neighbor = (current[0] + dx, current[1] + dy)

                if not (0 <= neighbor[0] < width):
                    continue

                if not (0 <= neighbor[1] < height):
                    continue

                if neighbor in obstacles or neighbor in parent:
                    continue

                parent[neighbor] = current
                queue.append(neighbor)

        if goal not in parent:
            return None

        current = goal

        while parent[current] != start:
            current = parent[current]

            if current is None:
                return None

        return current

    def direction_between(self, start, next_position):
        """Convert two adjacent cells into a movement direction."""
        dx = next_position[0] - start[0]
        dy = next_position[1] - start[1]

        for direction, (move_x, move_y) in self.directions.items():
            if (dx, dy) == (move_x, move_y):
                return direction

        raise ValueError("The target cell is not adjacent to WALL-E.")

    def find_unvisited_cell(self, position, environment):
        """Find the nearest reachable cell that has not been visited."""
        best_target = None
        best_distance = float("inf")

        for x in range(environment.width):
            for y in range(environment.height):
                candidate = (x, y)

                if candidate in environment.obstacles:
                    continue

                if candidate in self.visited:
                    continue

                distance = self.shortest_distance(
                    position, candidate, environment
                )

                if distance is not None and distance < best_distance:
                    best_distance = distance
                    best_target = candidate

        return best_target
