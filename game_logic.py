# game_logic.py
from models import Card

def is_king(card):
    return card.rank == 13
# Returns a string description of the move
def get_move_string(move):
    def n_str(n):
        rank = ((n - 1) % 13) + 1
        suits = ["S", "H", "D", "C"]
        r_s = {1: "A", 11: "J", 12: "Q", 13: "K"}.get(rank, str(rank))
        return r_s + suits[(n - 1) // 13]

    if move[0] == "king":
        return f"Remove K: {n_str(move[1])}"
    elif move[0] == "pair":
        return f"Pair: {n_str(move[1])} & {n_str(move[2])}"
    elif move[0] == "rotate":
        return "Rotate Stock"
    return ""
# Rotates the stock and waste piles according to game rules
def stock_rotate(stock, waste):
    stock = list(stock)
    waste = list(waste)

    # Remove empty marker if present at top of waste
    if len(waste) > 0 and waste[0] == "**":
        waste.pop(0)

    if len(stock) != 0:
        # Move top of Stock (Face Down) to top of Waste (Face Up)
        card = stock.pop(0)
        waste.insert(0, card)
    else:
        # Recycle Waste back to Stock
        if len(waste) > 0:
            stock.extend(reversed(waste))
            waste.clear()
        waste.append("**")
    
    return stock, waste

def pyramid_rows_from_list(p):
    return [
        [p[0]], p[1:3], p[3:6], p[6:10], p[10:15], p[15:21], p[21:28],
    ]

def get_accessible_cards(pyramid, stock, waste):
    acc = []
    
 
    # Waste Top
    if len(waste) > 0 and isinstance(waste[0], Card):
        acc.append(waste[0])

    # Stock Top

    rows = pyramid_rows_from_list(pyramid)

    # Bottom Row
    for c in rows[6]:
        if c != "**": acc.append(c)

    # Upper Rows (only if row below is cleared)
    for r in range(5, -1, -1):
        if all(c == "**" for c in rows[r+1]):
            for c in rows[r]:
                if c != "**": acc.append(c)
    return acc

def is_valid_source_pair(a, b, pyramid):
   
    a_in_pyr = (a in pyramid)
    b_in_pyr = (b in pyramid)
    
    if not a_in_pyr and not b_in_pyr:
        return False
        
    return True

def removeCards_obj(a, b, pyramid, stock, waste, foundation):
    accessible = get_accessible_cards(pyramid, stock, waste)

    def remove_card(c):
        if c not in accessible: return
        
        for i in range(len(pyramid)):
            if pyramid[i] == c:
                foundation.append(pyramid[i])
                pyramid[i] = "**"
        
        if len(stock) > 0 and stock[0] == c:
            foundation.append(stock.pop(0))
        
        if len(waste) > 0 and waste[0] == c:
            foundation.append(waste.pop(0))

    if a != "none": remove_card(a)
    if b != "none": remove_card(b)

    return pyramid, stock, waste, foundation

def encode_list_for_state(lst):
    return tuple(x.number if isinstance(x, Card) else 0 for x in lst)

def is_pyramid_cleared(p):
    return all(c == "**" or c is None for c in p)