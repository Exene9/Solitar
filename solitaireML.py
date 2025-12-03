"""
pyramid_pygame.py
Single-file Pygame implementation of your Pyramid solitaire logic.
Requires a folder 'cards' containing 1.png..52.png and back.png
"""

import pygame
import random
import os
import sys

# --------- CONFIG ----------
# Tuned for 14" MacBook Pro (default scaled resolution)
SCREEN_W, SCREEN_H = 1512, 900
CARD_W, CARD_H = 70, 100
PADDING_X = 10
PADDING_Y = 10
TOP_OFFSET = 30
SIDE_OFFSET = 40
BUTTON_W, BUTTON_H = 130, 36
FPS = 30

ASSET_DIR = "Carded"   # folder with 1.JPG .. 52.JPG and Back.JPG
# ---------------------------

# ---------- Card class ----------
class Card:
    def __init__(self, number, image_surface):
        """
        number: 1..52
        image_surface: pygame.Surface already scaled to CARD_W x CARD_H
        """
        self.number = number
        self.image = image_surface
        self.rect = self.image.get_rect()
        # compute rank 1..13 and suit index 0..3
        self.rank = ((number - 1) % 13) + 1
        self.suit_index = (number - 1) // 13  # 0..3
        self.selected = False
        self.removed = False  # removed from pyramid/stock/waste (like "**")

    def name(self):
        rank_lookup = {1: "A", 11: "J", 12: "Q", 13: "K"}
        r = rank_lookup.get(self.rank, str(self.rank))
        suits = ["S", "H", "D", "C"]
        return r + suits[self.suit_index]

# ---------- Helper functions (logic) ----------
def cardLogic_obj(a: Card, b: Card):
    """Return True if two cards sum to 13 by rank"""
    if a is None or b is None:
        return False
    return (a.rank + b.rank) == 13

def is_king(card: Card):
    return card.rank == 13

# ---------- Deck / load images ----------
def load_card_images():
    images = {}
    for n in range(1, 53):
        path = os.path.join(ASSET_DIR, f"{n}.JPG")  # or .png if you changed it
        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
            surf = pygame.transform.smoothscale(surf, (CARD_W, CARD_H))
        else:
            # fallback: make a plain colored surface with rank + suit text
            surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            surf.fill((245, 245, 245))
            f = pygame.font.SysFont(None, 24)

            # compute rank and suit for display
            rank = ((n - 1) % 13) + 1
            suit_index = (n - 1) // 13  # 0..3
            rank_lookup = {1: "A", 11: "J", 12: "Q", 13: "K"}
            r = rank_lookup.get(rank, str(rank))
            suits = ["♠", "♥", "♦", "♣"]
            s = suits[suit_index]

            txt = f.render(f"{r}{s}", True, (0, 0, 0))
            surf.blit(txt, (6, 6))
        images[n] = surf
    # back image
    back_path = os.path.join(ASSET_DIR, "Back.JPG")  # or Back.png if you changed it
    if os.path.exists(back_path):
        back = pygame.image.load(back_path).convert_alpha()
        back = pygame.transform.smoothscale(back, (CARD_W, CARD_H))
    else:
        back = pygame.Surface((CARD_W, CARD_H))
        back.fill((30, 120, 180))
    return images, back

def create_deck(card_images):
    deck = []
    for i in range(1, 53):
        deck.append(Card(i, card_images[i]))
    random.shuffle(deck)
    return deck

# ---------- Stock/Waste functions ----------
def stock_rotate(stock, waste):
    # remove placeholder if present at waste[0] as original used "**"
    if len(waste) > 0 and waste[0] == "**":
        waste.pop(0)

    if len(stock) != 0:
        # move top stock card to top of waste
        waste.insert(0, stock[0])
        # remove that element from stock
        stock.pop(0)
    else:
        # refill stock from waste reversed (but we want to preserve Card objects)
        # original code used: stock becomes reverse of waste, then waste reset to ["**"]
        if len(waste) > 0:
            new_stock = []
            # reverse waste into stock
            for i in range(len(waste)):
                new_stock.insert(0, waste[i])  # reverse
            stock.extend(new_stock)
            waste.clear()
        # mimic original placeholder
        waste.append("**")
    return stock, waste

# ---------- Validity check (accessible cards) ----------
def pyramid_rows_from_list(pyramid_list):
    rows = [
        [pyramid_list[0]],
        pyramid_list[1:3],
        pyramid_list[3:6],
        pyramid_list[6:10],
        pyramid_list[10:15],
        pyramid_list[15:21],
        pyramid_list[21:28],
    ]
    return rows

def get_accessible_cards(pyramid, stock, waste):
    cardAccess = []
    # top of stock
    if len(stock) > 0:
        if stock[0] != "**":
            cardAccess.append(stock[0])
        else:
            cardAccess.append("**")
    else:
        cardAccess.append("**")
    # top of waste
    if len(waste) > 0:
        if waste[0] != "**":
            cardAccess.append(waste[0])
        else:
            cardAccess.append("**")
    else:
        cardAccess.append("**")

    rows = pyramid_rows_from_list(pyramid)
    # always add 7th row (bottom row) accessible if not removed
    for c in rows[6]:
        if c != "**":
            cardAccess.append(c)

    # for rows 0..5, a card is accessible if both cards below are removed/"**"
    for row in range(len(rows) - 1):
        if row != 0:
            for idx in range(len(rows[row])):
                below_left = rows[row+1][idx]
                below_right = rows[row+1][idx+1]
                if (below_left == "**" or below_left is None) and (below_right == "**" or below_right is None):
                    if rows[row][idx] != "**" and rows[row][idx] is not None:
                        cardAccess.append(rows[row][idx])
        else:
            # for the top single card row: check its two children
            if rows[1][0] == "**" or rows[1][0] is None:
                if rows[1][1] == "**" or rows[1][1] is None:
                    if rows[0][0] != "**" and rows[0][0] is not None:
                        cardAccess.append(rows[0][0])
    return cardAccess

# ---------- Remove cards ----------
def removeCards_obj(firstCard, secondCard, pyramid, stock, waste, foundation):
    for i in range(len(pyramid)):
        if pyramid[i] == firstCard or pyramid[i] == secondCard:
            foundation.append(pyramid[i])
            pyramid[i] = "**"

    if len(stock) > 0:
        if stock[0] == firstCard or stock[0] == secondCard:
            foundation.append(stock[0])
            stock.pop(0)
    if len(waste) > 0:
        if waste[0] == firstCard or waste[0] == secondCard:
            foundation.append(waste[0])
            waste.pop(0)
    return pyramid, stock, waste, foundation

# ---------- Game GUI ----------
class PyramidGame:
    def __init__(self, screen):
        self.screen = screen
        self.images, self.back_image = load_card_images()
        self.font = pygame.font.SysFont(None, 22)
        self.init_new_game()

    def init_new_game(self):
        deck = create_deck(self.images)
        self.pyramid = deck[0:28]
        self.stock = deck[28:52]
        self.waste = ["**"]
        self.foundation = []
        self.selected = []
        self.compute_positions()
        self.message = ""

    def compute_positions(self):
        total_pyramid_width = 7 * CARD_W + 6 * PADDING_X
        y = TOP_OFFSET
        self.pyramid_positions = []  # index -> rect
        index = 0
        for row_len in [1, 2, 3, 4, 5, 6, 7]:
            row_width = row_len * CARD_W + (row_len - 1) * PADDING_X
            row_start_x = (SCREEN_W - row_width) // 2
            for col in range(row_len):
                rect = pygame.Rect(
                    row_start_x + col * (CARD_W + PADDING_X),
                    y,
                    CARD_W, CARD_H
                )
                self.pyramid_positions.append(rect)
                index += 1
            y += CARD_H + PADDING_Y

        # stock & waste positions (left)
        self.stock_rect = pygame.Rect(SIDE_OFFSET, TOP_OFFSET + 20, CARD_W, CARD_H)
        self.waste_rect = pygame.Rect(SIDE_OFFSET + CARD_W + 16, TOP_OFFSET + 20, CARD_W, CARD_H)

        # buttons (right side)
        self.rotate_button_rect = pygame.Rect(
            SCREEN_W - BUTTON_W - 20, TOP_OFFSET + 20, BUTTON_W, BUTTON_H
        )
        self.newgame_button_rect = pygame.Rect(
            SCREEN_W - BUTTON_W - 20,
            TOP_OFFSET + 20 + BUTTON_H + 12,
            BUTTON_W,
            BUTTON_H,
        )

    def draw(self):
        self.screen.fill((34, 90, 55))
        # draw pyramid cards
        for i, pos in enumerate(self.pyramid_positions):
            card = self.pyramid[i]
            if card == "**" or card is None:
                # draw empty placeholder
                pygame.draw.rect(self.screen, (50, 110, 70), pos, border_radius=6)
            else:
                # draw card image
                self.screen.blit(card.image, pos)
                if card in self.selected:
                    # highlight selection
                    pygame.draw.rect(self.screen, (255, 215, 0), pos, 4, border_radius=6)

        # draw stock
        if len(self.stock) > 0:
            top = self.stock[0]
            if top != "**":
                self.screen.blit(self.back_image, self.stock_rect)
            else:
                # placeholder
                pygame.draw.rect(self.screen, (200, 200, 200), self.stock_rect)
        else:
            # empty stock draw placeholder
            pygame.draw.rect(self.screen, (60, 60, 60), self.stock_rect)

        # draw waste
        if len(self.waste) > 0:
            topw = self.waste[0]
            if topw == "**":
                pygame.draw.rect(self.screen, (100, 100, 100), self.waste_rect)
            else:
                if isinstance(topw, Card):
                    self.screen.blit(topw.image, self.waste_rect)
                    if topw in self.selected:
                        pygame.draw.rect(self.screen, (255, 215, 0), self.waste_rect, 4, border_radius=6)
                else:
                    pygame.draw.rect(self.screen, (120, 120, 120), self.waste_rect)
        else:
            pygame.draw.rect(self.screen, (60, 60, 60), self.waste_rect)

        # draw rotate / new game buttons
        pygame.draw.rect(self.screen, (200, 200, 200), self.rotate_button_rect, border_radius=6)
        pygame.draw.rect(self.screen, (200, 200, 200), self.newgame_button_rect, border_radius=6)
        rt = self.font.render("Rotate Stock", True, (0, 0, 0))
        ng = self.font.render("New Game", True, (0, 0, 0))
        self.screen.blit(rt, (self.rotate_button_rect.x + 12, self.rotate_button_rect.y + 8))
        self.screen.blit(ng, (self.newgame_button_rect.x + 28, self.newgame_button_rect.y + 8))

        # draw top labels
        lbl = self.font.render("Stock", True, (255, 255, 255))
        lbl2 = self.font.render("Waste", True, (255, 255, 255))
        self.screen.blit(lbl, (self.stock_rect.x, self.stock_rect.y - 18))
        self.screen.blit(lbl2, (self.waste_rect.x, self.waste_rect.y - 18))

        # message
        msgsurf = self.font.render(self.message, True, (255, 255, 0))
        self.screen.blit(msgsurf, (20, SCREEN_H - 30))

        # draw foundation count
        fnt = self.font.render(
            f"Foundation: {len([x for x in self.foundation if x != '**'])}",
            True,
            (255, 255, 255),
        )
        self.screen.blit(fnt, (SCREEN_W - 220, SCREEN_H - 30))

    def click_at(self, pos):
        x, y = pos
        # check pyramid
        for i, rect in enumerate(self.pyramid_positions):
            if rect.collidepoint(pos):
                card = self.pyramid[i]
                if card == "**" or card is None:
                    return
                # check accessibility: only allow selecting accessible cards
                accessible = get_accessible_cards(self.pyramid, self.stock, self.waste)
                if card not in accessible:
                    self.message = "That pyramid card is covered"
                    return
                self.toggle_select(card)
                return

        # check stock
        if self.stock_rect.collidepoint(pos):
            # clicking stock: allow selecting top of stock if present
            if len(self.stock) > 0 and self.stock[0] != "**":
                if self.stock[0] in get_accessible_cards(self.pyramid, self.stock, self.waste):
                    self.toggle_select(self.stock[0])
                else:
                    self.message = "Stock top not available"
            else:
                self.message = "Stock empty or placeholder"
            return

        # waste
        if self.waste_rect.collidepoint(pos):
            if len(self.waste) > 0 and self.waste[0] != "**":
                if self.waste[0] in get_accessible_cards(self.pyramid, self.stock, self.waste):
                    self.toggle_select(self.waste[0])
                else:
                    self.message = "Waste top not available"
            else:
                self.message = "Waste empty"
            return

        # rotate button
        if self.rotate_button_rect.collidepoint(pos):
            self.stock, self.waste = stock_rotate(self.stock, self.waste)
            self.selected.clear()
            self.message = "Rotated stock"
            self.check_loss()
            return

        # new game
        if self.newgame_button_rect.collidepoint(pos):
            self.init_new_game()
            self.message = "New game"
            return

    def toggle_select(self, card):
        # if card already selected, deselect
        if card in self.selected:
            self.selected.remove(card)
            self.message = ""
            return

        # add selection
        self.selected.append(card)
        # if we selected a king, remove it instantly
        if is_king(card):
            self.pyramid, self.stock, self.waste, self.foundation = removeCards_obj(
                card, "none", self.pyramid, self.stock, self.waste, self.foundation
            )
            self.selected.clear()
            self.message = f"Removed King {card.name()}"
            self.check_win()
            self.check_loss()
            return

        # if two cards selected, check combination
        if len(self.selected) == 2:
            a, b = self.selected
            if cardLogic_obj(a, b):
                self.pyramid, self.stock, self.waste, self.foundation = removeCards_obj(
                    a, b, self.pyramid, self.stock, self.waste, self.foundation
                )
                self.message = f"Removed {a.name()} + {b.name()}"
            else:
                self.message = f"{a.name()} + {b.name()} do not sum to 13"
            self.selected.clear()
            self.check_win()
            self.check_loss()

    def check_win(self):
        all_removed = all((c == "**" or c is None) for c in self.pyramid)
        if all_removed:
            self.message = "You removed the pyramid! You win!"

    def check_loss(self):
        # If already won, don't override the win message
        if all((c == "**" or c is None) for c in self.pyramid):
            return False

        accessible = get_accessible_cards(self.pyramid, self.stock, self.waste)
        cards = [c for c in accessible if isinstance(c, Card)]

        # Any accessible king?
        for c in cards:
            if c.rank == 13:
                return False

        # Any accessible pair summing to 13?
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                if cards[i].rank + cards[j].rank == 13:
                    return False

        # No kings, no pairs among accessible cards → no immediate moves
        self.message = "No moves left! Game over."
        return True

# ---------- Main ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Pyramid Solitaire - Pygame")
    clock = pygame.time.Clock()

    game = PyramidGame(screen)
    running = True

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.click_at(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.stock, game.waste = stock_rotate(game.stock, game.waste)
                    game.selected.clear()
                    game.message = "Rotated stock"
                    game.check_loss()
                if event.key == pygame.K_n:
                    game.init_new_game()

        game.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
