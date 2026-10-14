
import random


class MissionEnvironment:
    def __init__(self, seed=42):
        # Use a fixed seed to make missions reproducible.
        self.random = random.Random(seed)

        # Map dimensions.
        self.width = 10
        self.height = 10

        # WALL-E's starting position and charger.
        self.position = (1, 1)
        self.charger = (0, 0)

        # Mission resources.
        self.battery = 100
        self.time_remaining = 150

        # Action costs.
        self.move_cost = 1
        self.scan_cost = 3

        # Obstacles on the map.
        self.obstacles = {
            (3, 2), (3, 3), (3, 4),
            (5, 5), (6, 5), (7, 5),
            (7, 6), (2, 7), (3, 7)
        }

        # Place EVE at least four grid steps from WALL-E.
        self.eve_location = self.random_empty_cell(
            min_distance=4
        )

        # Place six clues without revealing them to WALL-E.
        self.clues = set()

        while len(self.clues) < 6:
            clue = self.random_empty_cell()

            if clue != self.eve_location:
                self.clues.add(clue)

        # Store only the clues that WALL-E has discovered.
        self.discovered_clues = set()

        # Mission completion status.
        self.eve_found = False

    def random_empty_cell(self, min_distance=0):
        """Choose a valid cell, optionally far from WALL-E."""

        while True:
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)

            cell = (x, y)

            distance = (
                abs(x - self.position[0])
                + abs(y - self.position[1])
            )

            if (
                cell not in self.obstacles
                and cell != self.position
                and cell != self.charger
                and distance >= min_distance
            ):
                return cell

    def in_bounds(self, position):
        """Check whether a cell is inside the map."""

        x, y = position

        return (
            0 <= x < self.width
            and 0 <= y < self.height
        )

    def observe(self):
        """Return information available to WALL-E."""

        return {
            "position": self.position,
            "battery": self.battery,
            "time_remaining": self.time_remaining,
            "discovered_clues": sorted(
                self.discovered_clues
            ),
            "eve_found": self.eve_found
        }

    def move(self, direction):
        """Move one cell in a selected direction."""

        if self.time_remaining <= 0:
            return {
                "success": False,
                "message": "Mission time exhausted.",
                "observation": self.observe()
            }

        directions = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0)
        }

        if direction not in directions:
            return {
                "success": False,
                "message": "Unknown direction.",
                "observation": self.observe()
            }

        if self.battery < self.move_cost:
            return {
                "success": False,
                "message": "Not enough battery to move.",
                "observation": self.observe()
            }

        dx, dy = directions[direction]
        x, y = self.position

        next_position = (x + dx, y + dy)

        if not self.in_bounds(next_position):
            return {
                "success": False,
                "message": "Map boundary reached.",
                "observation": self.observe()
            }

        if next_position in self.obstacles:
            return {
                "success": False,
                "message": "Obstacle detected.",
                "observation": self.observe()
            }

        # Execute the movement.
        self.position = next_position
        self.battery -= self.move_cost
        self.time_remaining -= 1

        # EVE is confirmed only at her exact location.
        if self.position == self.eve_location:
            self.eve_found = True

        return {
            "success": True,
            "message": "Movement completed.",
            "observation": self.observe()
        }

    def scan(self):
        """Find nearby clues and detect EVE's signal."""

        if self.time_remaining <= 0:
            return {
                "success": False,
                "message": "Mission time exhausted.",
                "observation": self.observe()
            }

        if self.battery < self.scan_cost:
            return {
                "success": False,
                "message": "Not enough battery to scan.",
                "observation": self.observe()
            }

        # Pay the scanning costs.
        self.battery -= self.scan_cost
        self.time_remaining -= 1

        x, y = self.position
        found_now = []

        # Discover clues within scanning radius two.
        for clue_x, clue_y in self.clues:
            distance = (
                abs(x - clue_x)
                + abs(y - clue_y)
            )

            if (
                distance <= 2
                and (clue_x, clue_y)
                not in self.discovered_clues
            ):
                self.discovered_clues.add(
                    (clue_x, clue_y)
                )
                found_now.append((clue_x, clue_y))

        # Detect EVE's signal within distance one.
        eve_distance = (
            abs(x - self.eve_location[0])
            + abs(y - self.eve_location[1])
        )

        eve_detected = eve_distance <= 1

        # Signal detection does not reveal EVE's exact location.
        # Exact confirmation happens only when WALL-E reaches her.
        if self.position == self.eve_location:
            self.eve_found = True

        return {
            "success": True,
            "message": "Scan completed.",
            "new_clues": found_now,
            "eve_detected": eve_detected,
            "observation": self.observe()
        }

    def recharge(self):
        """Recharge at the designated station."""

        if self.time_remaining <= 0:
            return {
                "success": False,
                "message": "Mission time exhausted.",
                "observation": self.observe()
            }

        if self.position != self.charger:
            return {
                "success": False,
                "message": "Move to the charger first.",
                "observation": self.observe()
            }

        # Recharging costs one time unit.
        self.time_remaining -= 1
        self.battery = 100

        return {
            "success": True,
            "message": "Battery fully recharged.",
            "observation": self.observe()
        }

    def display_map(self):
        """Display known information without exposing hidden cells."""

        print("\nMission Map")
        print("W = WALL-E, C = Charger, # = Obstacle")
        print("? = Discovered clue, . = Unknown cell\n")

        for y in range(self.height):
            row = []

            for x in range(self.width):
                cell = (x, y)

                if cell == self.position:
                    symbol = "W"
                elif cell == self.charger:
                    symbol = "C"
                elif cell in self.obstacles:
                    symbol = "#"
                elif cell in self.discovered_clues:
                    symbol = "?"
                else:
                    symbol = "."

                row.append(symbol)

            print(" ".join(row))

        print("\nBattery:", self.battery)
        print("Time remaining:", self.time_remaining)
        print("Clues found:", len(self.discovered_clues))
        print("EVE located:", self.eve_found)
