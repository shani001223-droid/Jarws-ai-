"""Task 49: reproducible, offline-only Hoshi Game Studio design contract.

This is a proposed mini-game design, NOT a playable build or owner approval.
No external assets, filesystem writes, network, accounts or paid services.
"""
from collections import deque
from hashlib import sha256
import json

TITLE = "Hoshi Star Trail"
VERSION = "gdd-v1"
MAX_MOVES = 30
LEVELS = (
    ("#######", "#S...E#", "#.....#", "#..C..#", "#.....#", "#.....#", "#######"),
    ("#######", "#S.#.E#", "#..#..#", "#..C..#", "#.....#", "#.....#", "#######"),
    ("#######", "#S....#", "#.#.#.#", "#C....#", "#.#.#.#", "#...CE#", "#######"),
    ("#######", "#S...C#", "#.#.#.#", "#...#.#", "#.#...#", "#C...E#", "#######"),
    ("#######", "#S...C#", "#.#.#.#", "#C..#.#", "#.#...#", "#C...E#", "#######"),
    ("#######", "#S.C..#", "#.#.#.#", "#C....#", "#.#.#.#", "#..C.E#", "#######"),
)


def solve_level(rows):
    """Validate a 7x7 layout and BFS all collectible states; return shortest moves."""
    if len(rows) != 7 or any(len(row) != 7 for row in rows):
        raise ValueError("invalid_dimensions")
    if any(ch not in "#.SCE" for row in rows for ch in row):
        raise ValueError("invalid_tile")
    if any(rows[y][x] != "#" for y in range(7) for x in range(7)
           if x in (0, 6) or y in (0, 6)):
        raise ValueError("open_boundary")
    locate = lambda ch: [(x, y) for y, row in enumerate(rows)
                         for x, value in enumerate(row) if value == ch]
    starts, exits, stars = locate("S"), locate("E"), locate("C")
    if len(starts) != 1 or len(exits) != 1 or not 1 <= len(stars) <= 3:
        raise ValueError("invalid_entities")
    star_bits = {pos: 1 << i for i, pos in enumerate(stars)}
    full = (1 << len(stars)) - 1
    queue = deque([(starts[0][0], starts[0][1], 0, 0)])
    visited = {(starts[0][0], starts[0][1], 0)}
    while queue:
        x, y, mask, moves = queue.popleft()
        if (x, y) == exits[0] and mask == full:
            if moves > MAX_MOVES:
                raise ValueError("move_budget_exceeded")
            return moves
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < 7 and 0 <= ny < 7) or rows[ny][nx] == "#":
                continue
            new_mask = mask | star_bits.get((nx, ny), 0)
            state = (nx, ny, new_mask)
            if state not in visited:
                visited.add(state)
                queue.append((nx, ny, new_mask, moves + 1))
    raise ValueError("unsolvable_level")


def design_manifest():
    """Return a fresh, finite JSON-compatible proposed design and proof metadata."""
    levels = [{"id": i, "rows": list(rows), "stars": sum(r.count("C") for r in rows),
               "minimum_moves": solve_level(rows)} for i, rows in enumerate(LEVELS, 1)]
    payload = {
        "title": TITLE, "version": VERSION, "status": "design_only_not_playable",
        "approval": "proposed_not_owner_approved", "platform": "offline_mobile_web",
        "engine_plan": "free_html5_canvas_in_existing_hoshi_repo",
        "levels": levels, "max_moves_per_level": MAX_MOVES,
        "network_required": False, "accounts_required": False,
        "paid_assets_required": False, "real_build_created": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["sha256"] = sha256(canonical.encode("utf-8")).hexdigest()
    return payload


if __name__ == "__main__":
    print(json.dumps(design_manifest(), indent=2, ensure_ascii=False))
