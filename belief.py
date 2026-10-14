
class EveBelief:

    def __init__(self, width, height, obstacles):
        self.width = width
        self.height = height
        self.obstacles = set(obstacles)

        # Store all possible starting locations for EVE.
        self.possible_locations = set()

        for x in range(width):
            for y in range(height):
                position = (x, y)

                if position in self.obstacles:
                    continue

                # EVE cannot start at WALL-E's start or charger.
                if position == (1, 1) or position == (0, 0):
                    continue

                # EVE must be at least 4 steps from WALL-E's start.
                distance_from_start = abs(x - 1) + abs(y - 1)

                if distance_from_start < 4:
                    continue

                self.possible_locations.add(position)

        self.confirmed_location = None
        self.scans_completed = 0

    def update_after_scan(self, position, eve_detected):
        """
        Positive signal: EVE is within Manhattan distance 1.
        Negative signal: EVE is farther than Manhattan distance 1.
        """

        if self.confirmed_location is not None:
            return

        self.scans_completed += 1

        x, y = position

        if eve_detected:
            self.possible_locations = {
                location
                for location in self.possible_locations
                if abs(location[0] - x) + abs(location[1] - y) <= 1
            }

        else:
            self.possible_locations = {
                location
                for location in self.possible_locations
                if abs(location[0] - x) + abs(location[1] - y) > 1
            }

    def update_after_move(self, position, eve_found):
        """
        Update candidates after WALL-E enters a cell.
        If EVE is not found there, remove that cell.
        """

        if eve_found:
            self.confirmed_location = position
            self.possible_locations = {position}

        elif self.confirmed_location is None:
            self.possible_locations.discard(position)

    def get_estimate(self):
        """Return a representative remaining candidate."""

        if self.confirmed_location is not None:
            return self.confirmed_location

        if not self.possible_locations:
            return None

        # Choose the candidate closest to all other candidates.
        best_location = None
        smallest_total_distance = float("inf")

        for candidate in self.possible_locations:
            total_distance = sum(
                abs(candidate[0] - other[0])
                + abs(candidate[1] - other[1])
                for other in self.possible_locations
            )

            if (
                total_distance < smallest_total_distance
                or (
                    total_distance == smallest_total_distance
                    and (
                        best_location is None
                        or candidate < best_location
                    )
                )
            ):
                smallest_total_distance = total_distance
                best_location = candidate

        return best_location

    def get_confidence(self):
        """
        Candidate-based score, not a calibrated probability.
        """

        if self.confirmed_location is not None:
            return 1.0

        if not self.possible_locations:
            return 0.0

        return 1.0 / len(self.possible_locations)

    def is_confirmed(self):
        return self.confirmed_location is not None
