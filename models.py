# cars class for game
import random

class Card:
    def __init__(self, number):
        self.number = number
        self.rank = ((number - 1) % 13) + 1
        self.suit_index = (number - 1) // 13
        
        # UI State
        self.selected = False
        self.removed = False

    def name(self):
        rank_lookup = {1: "A", 11: "J", 12: "Q", 13: "K"}
        suits = ["S", "H", "D", "C"]
        r = rank_lookup.get(self.rank, str(self.rank))
        return r + suits[self.suit_index]
    
    def get_color(self):
        # 0=Spades, 1=Hearts, 2=Diamonds, 3=Clubs
        return "red" if self.suit_index in [1, 2] else "black"

    def get_display_rank(self):
        rank_lookup = {1: "A", 11: "J", 12: "Q", 13: "K"}
        return rank_lookup.get(self.rank, str(self.rank))

    def get_suit_symbol(self):
        return ["♠", "♥", "♦", "♣"][self.suit_index]
    
    def __repr__(self):
        return f"<{self.name()}>"

def create_deck():
    deck = [Card(i) for i in range(1, 53)]
    random.shuffle(deck)
    return deck