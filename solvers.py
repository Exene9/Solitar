# solvers.py
import heapq
from models import Card
import game_logic as gl
import settings

# --- Heuristic for A* ---
def heuristic(pyramid):
    """
    Estimates the 'cost' to finish the game from the current state.
    Lower is better.
    """
    # Base: Minimum moves needed (cards / 2)
    cards_remaining = sum(1 for c in pyramid if c != "**")
    h = cards_remaining / 2.0
    
    # Refinement: Add a small penalty for "buried" cards.
    # This encourages the AI to pick cards that are blocking others (lower in the rows).
    rows = gl.pyramid_rows_from_list(pyramid)
    blocking_penalty = 0
    
    # Row 0 is top, Row 6 is bottom.
    # Cards in higher rows (0,1,2) are harder to reach.
    for r_idx, row in enumerate(rows):
        for card in row:
            if card != "**":
                # Add small weight: cards at top (row 0) add more "perceived cost"
                # because we really want to clear them.
                blocking_penalty += (7 - r_idx) * 0.1

    return h + blocking_penalty

# --- DFS Algorithm (Unchanged) ---
def find_solution_dfs(pyramid, stock, waste, foundation):
    visited = set()
    nodes = 0
    max_nodes = settings.DFS_MAX_NODES

    def dfs(p, s, w, f, path):
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes: return None
        if gl.is_pyramid_cleared(p): return path

        key = (gl.encode_list_for_state(p), gl.encode_list_for_state(s), gl.encode_list_for_state(w))
        if key in visited: return None
        visited.add(key)

        acc = gl.get_accessible_cards(p, s, w)
        cards = [c for c in acc if isinstance(c, Card)]

        # 1. Kings
        for c in cards:
            if c.rank == 13:
                p2, s2, w2, f2 = list(p), list(s), list(w), list(f)
                p2, s2, w2, f2 = gl.removeCards_obj(c, "none", p2, s2, w2, f2)
                res = dfs(p2, s2, w2, f2, path + [("king", c.number)])
                if res: return res

        # 2. Pairs
        for i in range(len(cards)):
            for j in range(i+1, len(cards)):
                a, b = cards[i], cards[j]
                if a.rank + b.rank == 13:
                    p2, s2, w2, f2 = list(p), list(s), list(w), list(f)
                    p2, s2, w2, f2 = gl.removeCards_obj(a, b, p2, s2, w2, f2)
                    res = dfs(p2, s2, w2, f2, path + [("pair", a.number, b.number)])
                    if res: return res

        # 3. Rotate
        if len(s) > 0 or (len(w) > 0 and w[0] != "**"):
            p2, s2, w2, f2 = list(p), list(s), list(w), list(f)
            s2, w2 = gl.stock_rotate(s2, w2)
            res = dfs(p2, s2, w2, f2, path + [("rotate",)])
            if res: return res
            
        return None

    return dfs(list(pyramid), list(stock), list(waste), list(foundation), [])

# --- A* Algorithm (Improved) ---
def find_solution_astar(pyramid, stock, waste, foundation):
    max_nodes = settings.ASTAR_MAX_NODES
    
    # HEURISTIC WEIGHT
    # 1.0 = Standard A* (Optimal path, but slow)
    # 1.5 - 2.0 = Weighted A* (Much faster, slightly sub-optimal path)
    H_WEIGHT = 2.5 

    start_node = (list(pyramid), list(stock), list(waste), list(foundation))
    start_h = heuristic(pyramid)
    
    # Priority Queue: (f_score, tie_breaker, g_score, state_tuple, path)
    counter = 0 
    pq = []
    
    # f = g + (h * weight)
    start_f = 0 + (start_h * H_WEIGHT)
    
    heapq.heappush(pq, (start_f, counter, 0, start_node, []))
    
    visited = set()
    nodes_visited = 0

    while pq:
        f, _, g, state, path = heapq.heappop(pq)
        p, s, w, fd = state
        
        nodes_visited += 1
        if nodes_visited > max_nodes: return None

        if gl.is_pyramid_cleared(p): return path

        state_key = (gl.encode_list_for_state(p), gl.encode_list_for_state(s), gl.encode_list_for_state(w))
        if state_key in visited: continue
        visited.add(state_key)

        acc = gl.get_accessible_cards(p, s, w)
        cards = [c for c in acc if isinstance(c, Card)]
        
        moves = []

        # 1. Kings
        for c in cards:
            if c.rank == 13:
                p2, s2, w2, f2 = list(p), list(s), list(w), list(fd)
                p2, s2, w2, f2 = gl.removeCards_obj(c, "none", p2, s2, w2, f2)
                moves.append((("king", c.number), (p2, s2, w2, f2)))

        # 2. Pairs
        for i in range(len(cards)):
            for j in range(i+1, len(cards)):
                a, b = cards[i], cards[j]
                if a.rank + b.rank == 13:
                    p2, s2, w2, f2 = list(p), list(s), list(w), list(fd)
                    p2, s2, w2, f2 = gl.removeCards_obj(a, b, p2, s2, w2, f2)
                    moves.append((("pair", a.number, b.number), (p2, s2, w2, f2)))

        # 3. Rotate
        if len(s) > 0 or (len(w) > 0 and w[0] != "**"):
             p2, s2, w2, f2 = list(p), list(s), list(w), list(fd)
             s2, w2 = gl.stock_rotate(s2, w2)
             moves.append((("rotate",), (p2, s2, w2, f2)))

        for move_action, next_state in moves:
            p_next = next_state[0]
            new_g = g + 1
            new_h = heuristic(p_next)
            
            # Apply Weight here
            new_f = new_g + (new_h * H_WEIGHT)
            
            counter += 1
            new_path = path + [move_action]
            heapq.heappush(pq, (new_f, counter, new_g, next_state, new_path))
            
    return None