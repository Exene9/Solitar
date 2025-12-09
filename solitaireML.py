import pygame
import random
import os
import sys

# Configurate the dimensions of the game
SCREEN_W, SCREEN_H = 1512, 900
CARD_W, CARD_H = 70, 100
PADDING_X = 10
PADDING_Y = 10
TOP_OFFSET = 30
SIDE_OFFSET = 40
BUTTON_W, BUTTON_H = 130, 36
FPS = 30

ASSET_DIR = "Carded"
AI_STEP_DELAY_MS = 500
# ---------------------------

# Card Class
class Card:
    def __init__(self, number, image_surface):
        self.number = number
        self.image = image_surface
        self.rect = self.image.get_rect()
        self.rank = ((number - 1) % 13) + 1
        self.suit_index = (number - 1) // 13
        self.selected = False
        self.removed = False

    def name(self):
        rank_lookup = {1: "A", 11: "J", 12: "Q", 13: "K"}
        suits = ["S", "H", "D", "C"]
        r = rank_lookup.get(self.rank, str(self.rank))
        return r + suits[self.suit_index]

# Logic Helpers
def cardLogic_obj(a: Card, b: Card):
    return (a is not None and b is not None and a.rank + b.rank == 13)

def is_king(card):
    return card.rank == 13

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

# Load Images
def load_card_images():
    images = {}
    for n in range(1, 53):
        path = os.path.join(ASSET_DIR, f"{n}.JPG")
        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
            surf = pygame.transform.smoothscale(surf, (CARD_W, CARD_H))
        else:
            # fallback simple card
            surf = pygame.Surface((CARD_W, CARD_H))
            surf.fill((250, 250, 250))
            f = pygame.font.SysFont(None, 26)
            txt = f.render(str(n), True, (0, 0, 0))
            surf.blit(txt, (5, 5))
        images[n] = surf

    back_path = os.path.join(ASSET_DIR, "Back.JPG")
    if os.path.exists(back_path):
        back = pygame.image.load(back_path).convert_alpha()
        back = pygame.transform.smoothscale(back, (CARD_W, CARD_H))
    else:
        back = pygame.Surface((CARD_W, CARD_H))
        back.fill((30, 120, 180))

    return images, back

def create_deck(card_images):
    deck = [Card(i, card_images[i]) for i in range(1, 53)]
    random.shuffle(deck)
    return deck

# Stock / Waste functions
def stock_rotate(stock, waste):
    if len(waste) > 0 and waste[0] == "**":
        waste.pop(0)

    if len(stock) != 0:
        waste.insert(0, stock.pop(0))
    else:
        if len(waste) > 0:
            stock.extend(reversed(waste))
            waste.clear()
        waste.append("**")
    return stock, waste

# Pyramid Helper
def pyramid_rows_from_list(p):
    """Return pyramid as list of rows"""
    return [
        [p[0]],
        p[1:3],
        p[3:6],
        p[6:10],
        p[10:15],
        p[15:21],
        p[21:28],
    ]

def get_accessible_cards(pyramid, stock, waste):
    acc = []

    # Stock top
    if len(stock) > 0 and stock[0] != "**":
        acc.append(stock[0])

    # Waste top
    if len(waste) > 0 and isinstance(waste[0], Card):
        acc.append(waste[0])

    rows = pyramid_rows_from_list(pyramid)

    # Bottom row is always accessible
    for c in rows[6]:
        if c != "**":
            acc.append(c)

    # Rows above bottom: only accessible if **entire row below is cleared**
    for r in range(5, -1, -1):
        if all(c == "**" for c in rows[r+1]):  # check entire row below
            for c in rows[r]:
                if c != "**":
                    acc.append(c)

    return acc



# Remove cards function
def removeCards_obj(a, b, pyramid, stock, waste, foundation):
    accessible = get_accessible_cards(pyramid, stock, waste)

    def remove_card(c):
        if c not in accessible:
            return
        # Pyramid
        for i in range(len(pyramid)):
            if pyramid[i] == c:
                foundation.append(pyramid[i])
                pyramid[i] = "**"
        # Stock
        if len(stock) > 0 and stock[0] == c:
            foundation.append(stock.pop(0))
        # Waste
        if len(waste) > 0 and waste[0] == c:
            foundation.append(waste.pop(0))

    if a != "none":
        remove_card(a)
    if b != "none":
        remove_card(b)

    return pyramid, stock, waste, foundation




# DFS Helpers
def encode_list_for_state(lst):
    return tuple(x.number if isinstance(x, Card) else 0 for x in lst)

def is_pyramid_cleared(p):
    return all(c == "**" or c is None for c in p)

# How DFS Algorithm is being executed and displayed in Terminal
def find_solution_dfs(pyramid, stock, waste, foundation, max_nodes=200000):
    visited = set()
    nodes = 0

    def dfs(p, s, w, f, path):
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            return None

        if is_pyramid_cleared(p):
            return path

        key = (encode_list_for_state(p), encode_list_for_state(s), encode_list_for_state(w))
        if key in visited:
            return None
        visited.add(key)

        # Compute accessible cards for this state
        acc = get_accessible_cards(p, s, w)
        cards = [c for c in acc if isinstance(c, Card)]

        # Remove Kings
        for c in cards:
            if c.rank == 13:
                p2, s2, w2, f2 = list(p), list(s), list(w), list(f)
                p2, s2, w2, f2 = removeCards_obj(c, "none", p2, s2, w2, f2)
                res = dfs(p2, s2, w2, f2, path + [("king", c.number)])
                if res:
                    return res

        # Remove pairs
        for i in range(len(cards)):
            for j in range(i+1, len(cards)):
                a, b = cards[i], cards[j]
                if a.rank + b.rank == 13:
                    p2, s2, w2, f2 = list(p), list(s), list(w), list(f)
                    p2, s2, w2, f2 = removeCards_obj(a, b, p2, s2, w2, f2)
                    res = dfs(p2, s2, w2, f2, path + [("pair", a.number, b.number)])
                    if res:
                        return res

        # Rotate stock if possible
        if len(s) > 0 or (len(w) > 0 and w[0] != "**"):
            p2, s2, w2, f2 = list(p), list(s), list(w), list(f)
            s2, w2 = stock_rotate(s2, w2)
            res = dfs(p2, s2, w2, f2, path + [("rotate",)])
            if res:
                return res

        return None

    sol = dfs(list(pyramid), list(stock), list(waste), list(foundation), [])
    return sol


# Game Class
class PyramidGame:
    def __init__(self, screen):
        self.screen = screen
        self.images, self.back_img = load_card_images()
        self.font = pygame.font.SysFont(None, 22)
        self.init_new_game()
        

    def init_new_game(self):
        deck = create_deck(self.images)
        self.pyramid = deck[:28]
        self.stock = deck[28:]
        self.waste = ["**"]
        self.foundation = []
        self.selected = []
        self.compute_positions()
        self.message = ""
        self.elapsed_sec=0
        self.ai_moves = None
        self.ai_running = False
        self.ai_step_index = 0
        self.ai_last_step_time = 0
        
    def compute_positions(self):
        y = TOP_OFFSET
        self.pyramid_positions = []
        index = 0

        for row in [1,2,3,4,5,6,7]:
            row_w = row * CARD_W + (row - 1) * PADDING_X
            start_x = (SCREEN_W - row_w) // 2

            for col in range(row):
                rect = pygame.Rect(start_x + col*(CARD_W+PADDING_X), y, CARD_W, CARD_H)
                self.pyramid_positions.append(rect)
                index += 1
            y += CARD_H + PADDING_Y

        self.stock_rect = pygame.Rect(SIDE_OFFSET, TOP_OFFSET + 20, CARD_W, CARD_H)
        self.waste_rect = pygame.Rect(SIDE_OFFSET + CARD_W + 16, TOP_OFFSET + 20, CARD_W, CARD_H)

        self.rotate_button = pygame.Rect(SCREEN_W - BUTTON_W - 20, TOP_OFFSET+20, BUTTON_W, BUTTON_H)
        self.newgame_button = pygame.Rect(SCREEN_W - BUTTON_W - 20, TOP_OFFSET+20+BUTTON_H+10, BUTTON_W, BUTTON_H)

# This is where the GUI of the Pyramid Solitaire is made
    def draw(self):
        self.screen.fill((34,90,55))
        
        # Pyramid
        for i, pos in enumerate(self.pyramid_positions):
            c = self.pyramid[i]
            if c == "**":
                pygame.draw.rect(self.screen, (50,110,70), pos, border_radius=6)
            else:
                self.screen.blit(c.image, pos)

        # Stock
        if len(self.stock) > 0 and self.stock[0] != "**":
            self.screen.blit(self.back_img, self.stock_rect)
        else:
            pygame.draw.rect(self.screen, (180,180,180), self.stock_rect)

        # Waste
        if len(self.waste) > 0 and isinstance(self.waste[0], Card):
            self.screen.blit(self.waste[0].image, self.waste_rect)
        else:
            pygame.draw.rect(self.screen, (120,120,120), self.waste_rect)

        # Buttons
        pygame.draw.rect(self.screen, (230,230,230), self.rotate_button)
        pygame.draw.rect(self.screen, (230,230,230), self.newgame_button)

        rt = self.font.render("Rotate", True, (0,0,0))
        ng = self.font.render("New Game", True, (0,0,0))
        self.screen.blit(rt, (self.rotate_button.x+25, self.rotate_button.y+8))
        self.screen.blit(ng, (self.newgame_button.x+15, self.newgame_button.y+8))

        # Message
        msg = self.font.render(self.message, True, (255,255,0))
        self.screen.blit(msg, (20, SCREEN_H - 30))

        # --- Display DFS Move List ---
        if self.ai_moves:
            list_x = self.newgame_button.x
            list_y = self.newgame_button.y + BUTTON_H + 20
            
            # Calculate remaining moves
            remaining = len(self.ai_moves) - self.ai_step_index
            header = self.font.render(f"Moves Left: {remaining}", True, (255, 255, 0))
            self.screen.blit(header, (list_x, list_y))
            list_y += 25
            
            # Slice the list to show only upcoming moves (limit to 20 lines to fit screen)
            upcoming_moves = self.ai_moves[self.ai_step_index : self.ai_step_index + 20]
            
            for m in upcoming_moves:
                txt_str = get_move_string(m)
                surf = self.font.render(txt_str, True, (220, 220, 220))
                self.screen.blit(surf, (list_x, list_y))
                list_y += 20
    # Find card
    def find_card(self, num):
        for c in self.pyramid:
            if isinstance(c, Card) and c.number == num:
                return c
        for c in self.stock:
            if isinstance(c, Card) and c.number == num:
                return c
        for c in self.waste:
            if isinstance(c, Card) and c.number == num:
                return c
        return None

    # Interactive system with the user
    def click_at(self, pos):
        if self.ai_running:
            return

        # New Game
        if self.newgame_button.collidepoint(pos):
            self.init_new_game()
            return

        # Rotate
        if self.rotate_button.collidepoint(pos):
            self.stock, self.waste = stock_rotate(self.stock, self.waste)
            return

        # Pyramid click
        for i, rect in enumerate(self.pyramid_positions):
            if rect.collidepoint(pos):
                c = self.pyramid[i]
                if c == "**":
                    return
                if c not in get_accessible_cards(self.pyramid, self.stock, self.waste):
                    self.message = "That card is blocked."
                    return
                self.toggle_select(c)
                return

        # Stock click
        if self.stock_rect.collidepoint(pos):
            if len(self.stock)>0 and isinstance(self.stock[0], Card):
                self.toggle_select(self.stock[0])
            return

        # Waste click
        if self.waste_rect.collidepoint(pos):
            if len(self.waste)>0 and isinstance(self.waste[0], Card):
                self.toggle_select(self.waste[0])
            return

    def toggle_select(self, c):
        if c in self.selected:
            self.selected.clear()
            self.message = ""
            return

        self.selected.append(c)

        if is_king(c):
            self.pyramid, self.stock, self.waste, self.foundation = removeCards_obj(
                c, "none", self.pyramid, self.stock, self.waste, self.foundation
            )
            self.selected.clear()
            self.message = f"Removed King {c.name()}"
            return

        if len(self.selected) == 2:
            a, b = self.selected
            if a.rank + b.rank == 13:
                self.pyramid, self.stock, self.waste, self.foundation = removeCards_obj(
                    a, b, self.pyramid, self.stock, self.waste, self.foundation
                )
                self.message = f"Removed {a.name()} + {b.name()}"
            else:
                self.message = "Not 13."
            self.selected.clear()

    # Part where DFS algorithm si implementing
    def start_ai_solve(self):
        self.message = "AI: DFS searching..."
        pygame.display.flip()

        start_time = pygame.time.get_ticks()
        sol = find_solution_dfs(self.pyramid, self.stock, self.waste, self.foundation)
        end_time = pygame.time.get_ticks()
        elapsed_sec = (end_time - start_time) / 1000.0
        self.elapsed_sec = elapsed_sec

        if not sol:
            self.message = f"AI: No solution. (search took {elapsed_sec:.3f}s)"
            return

        # Store solution but DO NOT execute yet
        self.ai_moves = sol
        self.ai_step_index = 0
        self.ai_running = False  # important

        # Ask user for confirmation
        self.awaiting_ai_confirm = True

        self.message = f"AI found a solution in {elapsed_sec:.3f}s. Execute? (Y/N)"


    def update_ai(self):
        if not self.ai_running or not self.ai_moves:
            return

        now = pygame.time.get_ticks()
        if now - self.ai_last_step_time < AI_STEP_DELAY_MS:
            return

        self.ai_last_step_time = now

        if self.ai_step_index >= len(self.ai_moves):
            self.ai_running = False
            self.message = f"AI: Done! (search took {self.elapsed_sec:.3f}s)"
            return

        m = self.ai_moves[self.ai_step_index]
        self.ai_step_index += 1

        if m[0] == "king":
            card = self.find_card(m[1])
            if card:
                self.pyramid, self.stock, self.waste, self.foundation = removeCards_obj(
                    card, "none", self.pyramid, self.stock, self.waste, self.foundation
                )
                self.message = f"AI removed King {card.name()}"

        elif m[0] == "pair":
            _, a, b = m
            c1 = self.find_card(a)
            c2 = self.find_card(b)
            if c1 and c2:
                self.pyramid, self.stock, self.waste, self.foundation = removeCards_obj(
                    c1, c2, self.pyramid, self.stock, self.waste, self.foundation
                )
                self.message = f"AI removed {c1.name()} + {c2.name()}"

        elif m[0] == "rotate":
            self.stock, self.waste = stock_rotate(self.stock, self.waste)
            self.message = "AI rotated stock"

# Main
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Pyramid Solitaire - DFS AI")
    clock = pygame.time.Clock()

    game = PyramidGame(screen)
    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if getattr(game, 'awaiting_ai_confirm', False):

                    
                    if event.key == pygame.K_y:
                        game.awaiting_ai_confirm = False
                        game.ai_running = True
                        game.ai_last_step_time = pygame.time.get_ticks()
                        game.message = "AI: Executing solution..."

                    
                    elif event.key == pygame.K_n:
                        game.awaiting_ai_confirm = False
                        game.ai_running = False
                        game.message = "AI: Execution canceled."

                    
                    continue

        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    game.init_new_game()

                if event.key == pygame.K_s:
                    game.start_ai_solve()  

                if event.key == pygame.K_r and not game.ai_running:
                    game.stock, game.waste = stock_rotate(game.stock, game.waste)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not getattr(game, 'awaiting_ai_confirm', False):
                    # Disable clicking cards while deciding (Y/N)
                    game.click_at(event.pos)

        game.update_ai()
        game.draw()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
