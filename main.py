import pygame
import sys
import os

IS_MOBILE = False
try:
    import android
    IS_MOBILE = True
except ImportError:
    IS_MOBILE = False

try:
    from tictactoe_neural import TicTacToeGame, MonteCarloLearner
except ImportError:
    print("Файл tictactoe_neural.py не найден!")
    sys.exit(1)

THEME = {
    "bg": (15, 15, 25),
    "grid": (40, 40, 40),
    "x": (255, 80, 80),
    "x_flash": (255, 140, 140),
    "o": (80, 220, 80),
    "o_flash": (140, 255, 140),
    "text": (240, 240, 250),
    "highlight": (255, 255, 100),
    "button": (60, 60, 60),
    "button_hover": (80, 80, 80),
    "button_text": (255, 255, 255),
    "panel": (30, 35, 50),
    "x_width": 18,
    "o_width": 18,
    "win_line_width": 18,
    "grid_width": 6,
}

class TicTacToeGUI:
    def __init__(self):
        pygame.init()
        
        if IS_MOBILE:
            # ФИКСИРОВАННАЯ ПОРТРЕТНАЯ ОРИЕНТАЦИЯ
            # Получаем размеры экрана
            info = pygame.display.Info()
            
            # ПРОВЕРЯЕМ ориентацию и принудительно устанавливаем портретную
            screen_width = min(info.current_w, info.current_h)
            screen_height = max(info.current_w, info.current_h)
            
            # Создаем окно с портретной ориентацией
            self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
            self.screen_width, self.screen_height = screen_width, screen_height
            
            self.grid_size = int(min(self.screen_width * 0.85, self.screen_height * 0.35))
            self.cell_size = self.grid_size // 3
            self.grid_top = int(self.screen_height * 0.45)
            self.grid_left = (self.screen_width - self.grid_size) // 2
            
            self.title_size = int(self.screen_height * 0.045)
            self.large_size = int(self.screen_height * 0.04)
            self.medium_size = int(self.screen_height * 0.035)
            self.small_size = int(self.screen_height * 0.03)
        else:
            self.screen_width = 800
            self.screen_height = 1000
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            self.grid_size = int(min(self.screen_width * 0.8, self.screen_height * 0.35))
            self.cell_size = self.grid_size // 3
            self.grid_top = int(self.screen_height * 0.45)
            self.grid_left = (self.screen_width - self.grid_size) // 2
            
            self.title_size = 40
            self.large_size = 36
            self.medium_size = 32
            self.small_size = 28
        
        pygame.display.set_caption("Крестики-Нолики с Нейросетью")
        
        self.font_title = pygame.font.Font(None, self.title_size)
        self.font_large = pygame.font.Font(None, self.large_size)
        self.font_medium = pygame.font.Font(None, self.medium_size)
        self.font_small = pygame.font.Font(None, self.small_size)
        
        self.game = TicTacToeGame()
        self.nn = MonteCarloLearner("fast_player")
        self.nn.load_memory()
        
        self.player_x_wins = 0
        self.player_o_wins = 0
        self.ai_wins = 0
        self.human_wins = 0
        self.draws = 0
        self.score_updated = False
        
        self.running = True
        self.thinking = False
        self.game_mode = "ai"
        self.win_animation = 0
        
        self.animation_start_time = {}
        self.flash_effects = {}
        self.flash_cooldowns = {}
        self.winning_cells = []
        self.win_flash_chain_active = False
        self.win_flash_index = 0
        self.win_flash_timer = 0
        
        self.current_time = pygame.time.get_ticks()
        
        self.highlight_surfaces = self.create_highlight_surfaces()
        self.win_highlight_surfaces = self.create_win_highlight_surfaces()
        
        self.create_buttons()
        
        if self.game.current_player == 1 and self.game_mode == "ai":
            self.thinking = True
    
    def create_highlight_surfaces(self):
        surfaces = {}
        perimeter_width = max(8, self.cell_size // 10)
        
        empty_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        for i in range(perimeter_width):
            alpha = int(255 * (1 - i / perimeter_width) * 0.9)
            if alpha > 0:
                color = (255, 255, 255, alpha)
                pygame.draw.rect(empty_surface, color,
                               (i, i, self.cell_size - 2*i, self.cell_size - 2*i), width=2)
        surfaces[0] = empty_surface
        
        x_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        for i in range(perimeter_width):
            alpha = int(255 * (1 - i / perimeter_width) * 0.9)
            if alpha > 0:
                color = (255, 80, 80, alpha)
                pygame.draw.rect(x_surface, color,
                               (i, i, self.cell_size - 2*i, self.cell_size - 2*i), width=2)
        surfaces[1] = x_surface
        
        o_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        for i in range(perimeter_width):
            alpha = int(255 * (1 - i / perimeter_width) * 0.9)
            if alpha > 0:
                color = (80, 220, 80, alpha)
                pygame.draw.rect(o_surface, color,
                               (i, i, self.cell_size - 2*i, self.cell_size - 2*i), width=2)
        surfaces[-1] = o_surface
        
        return surfaces
    
    def create_win_highlight_surfaces(self):
        surfaces = {}
        perimeter_width = max(12, self.cell_size // 7)
        
        x_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        for i in range(perimeter_width):
            alpha = int(255 * (1 - i / perimeter_width) * 1.0)
            if alpha > 0:
                color = (255, 100, 100, alpha)
                pygame.draw.rect(x_surface, color,
                               (i, i, self.cell_size - 2*i, self.cell_size - 2*i), width=3)
        surfaces[1] = x_surface
        
        o_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        for i in range(perimeter_width):
            alpha = int(255 * (1 - i / perimeter_width) * 1.0)
            if alpha > 0:
                color = (100, 255, 100, alpha)
                pygame.draw.rect(o_surface, color,
                               (i, i, self.cell_size - 2*i, self.cell_size - 2*i), width=3)
        surfaces[-1] = o_surface
        
        return surfaces
    
    def create_buttons(self):
        """Верхние кнопки опускаем, нижние оставляем как было"""
        if IS_MOBILE:
            top_btn_width = int(self.screen_width * 0.45)
            top_btn_height = int(self.screen_height * 0.07)
            top_btn_y = int(self.screen_height * 0.25)
            top_btn_spacing = int(self.screen_width * 0.02)
            
            bottom_btn_width = int(self.screen_width * 0.45)
            bottom_btn_height = int(self.screen_height * 0.07)
            bottom_btn_y = int(self.screen_height * 0.85)
            bottom_btn_spacing = int(self.screen_width * 0.02)
        else:
            top_btn_width = 220
            top_btn_height = 60
            top_btn_y = 250
            top_btn_spacing = 20
            
            bottom_btn_width = 220
            bottom_btn_height = 60
            bottom_btn_y = 850
            bottom_btn_spacing = 20
        
        self.buttons = {
            "train": {
                "rect": pygame.Rect(
                    self.screen_width//2 - top_btn_width - top_btn_spacing//2,
                    top_btn_y, top_btn_width, top_btn_height
                ),
                "text": "Тренировать",
                "action": self.quick_train
            },
            "exit": {
                "rect": pygame.Rect(
                    self.screen_width//2 + top_btn_spacing//2,
                    top_btn_y, top_btn_width, top_btn_height
                ),
                "text": "Выход",
                "action": self.exit_game
            },
            "pvp": {
                "rect": pygame.Rect(
                    self.screen_width//2 - bottom_btn_width - bottom_btn_spacing//2,
                    bottom_btn_y, bottom_btn_width, bottom_btn_height
                ),
                "text": "PvP" if self.game_mode == "ai" else "AI",
                "action": self.toggle_mode
            },
            "new_game": {
                "rect": pygame.Rect(
                    self.screen_width//2 + bottom_btn_spacing//2,
                    bottom_btn_y, bottom_btn_width, bottom_btn_height
                ),
                "text": "Новая игра",
                "action": self.new_game
            }
        }
    
    def toggle_mode(self):
        if self.game_mode == "ai":
            self.game_mode = "pvp"
            self.buttons["pvp"]["text"] = "AI"
        else:
            self.game_mode = "ai"
            self.buttons["pvp"]["text"] = "PvP"
        
        self.player_x_wins = 0
        self.player_o_wins = 0
        self.ai_wins = 0
        self.human_wins = 0
        self.draws = 0
        
        self.new_game()
    
    def new_game(self):
        self.game.reset()
        self.thinking = False
        self.win_animation = 0
        self.animation_start_time = {}
        self.flash_effects = {}
        self.flash_cooldowns = {}
        self.winning_cells = []
        self.win_flash_chain_active = False
        self.win_flash_index = 0
        self.win_flash_timer = 0
        self.score_updated = False
        
        if self.game_mode == "ai" and self.game.current_player == 1:
            self.thinking = True
    
    def quick_train(self):
        old_thinking = self.thinking
        self.thinking = False
        self.nn.quick_train(100)
        self.thinking = old_thinking
        self.new_game()
    
    def exit_game(self):
        self.nn.save_memory()
        self.running = False
    
    def get_winning_line_cells(self):
        if not self.game.winner:
            return []
        
        win_patterns = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        
        for pattern in win_patterns:
            if all(self.game.board[i] == self.game.winner for i in pattern):
                return pattern
        
        return []
    
    def start_winning_flashes(self):
        self.winning_cells = self.get_winning_line_cells()
        if not self.winning_cells:
            return
        
        if self.game.winner != 0:
            self.flash_effects = {}
            self.flash_cooldowns = {}
        
        self.win_flash_chain_active = True
        self.win_flash_index = 0
        self.win_flash_timer = self.current_time
    
    def get_symbol_color(self, cell_idx, symbol, appearance_progress):
        if cell_idx in self.animation_start_time:
            elapsed = self.current_time - self.animation_start_time[cell_idx]
            if elapsed < 150:
                flash_progress = min(1.0, elapsed / 150)
                
                start_color = (255, 255, 255)
                if symbol == 1:
                    end_color = THEME["x"]
                else:
                    end_color = THEME["o"]
                
                t = flash_progress
                eased_progress = t * t * (3.0 - 2.0 * t)
                
                r = int(start_color[0] + (end_color[0] - start_color[0]) * eased_progress)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * eased_progress)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * eased_progress)
                return (r, g, b)
        
        if cell_idx in self.flash_effects:
            elapsed = self.current_time - self.flash_effects[cell_idx]["start_time"]
            flash_progress = min(1.0, elapsed / 800)
            
            t = flash_progress
            eased_progress = t * t * (3.0 - 2.0 * t)
            
            if eased_progress < 0.5:
                progress = eased_progress * 2
                start_color = (255, 255, 255)
                if symbol == 1:
                    end_color = THEME["x_flash"]
                else:
                    end_color = THEME["o_flash"]
                
                r = int(start_color[0] + (end_color[0] - start_color[0]) * progress)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * progress)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * progress)
            else:
                progress = (eased_progress - 0.5) * 2
                if symbol == 1:
                    start_color = THEME["x_flash"]
                    end_color = THEME["x"]
                else:
                    start_color = THEME["o_flash"]
                    end_color = THEME["o"]
                
                r = int(start_color[0] + (end_color[0] - start_color[0]) * progress)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * progress)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * progress)
            
            return (r, g, b)
        
        return THEME["x"] if symbol == 1 else THEME["o"]
    
    def draw_grid(self):
        pygame.draw.rect(self.screen, THEME["panel"], 
                        (self.grid_left - 10, self.grid_top - 10, 
                         self.grid_size + 20, self.grid_size + 20),
                        border_radius=10)
        
        for i in range(9):
            row = i // 3
            col = i % 3
            cell_left = self.grid_left + col * self.cell_size
            cell_top = self.grid_top + row * self.cell_size
            
            symbol = self.game.board[i]
            
            if i in self.winning_cells and self.game.game_over:
                win_surface = self.win_highlight_surfaces[symbol]
                self.screen.blit(win_surface, (cell_left, cell_top))
            else:
                highlight_surface = self.highlight_surfaces[symbol]
                self.screen.blit(highlight_surface, (cell_left, cell_top))
        
        for i in range(1, 3):
            x = self.grid_left + i * self.cell_size
            pygame.draw.line(self.screen, THEME["grid"], 
                           (x, self.grid_top), (x, self.grid_top + self.grid_size), 
                           THEME["grid_width"])
        
        for i in range(1, 3):
            y = self.grid_top + i * self.cell_size
            pygame.draw.line(self.screen, THEME["grid"], 
                           (self.grid_left, y), (self.grid_left + self.grid_size, y), 
                           THEME["grid_width"])
    
    def draw_symbol(self, cell_idx, symbol):
        row = cell_idx // 3
        col = cell_idx % 3
        
        center_x = self.grid_left + col * self.cell_size + self.cell_size // 2
        center_y = self.grid_top + row * self.cell_size + self.cell_size // 2
        
        appearance_progress = 1.0
        if cell_idx in self.animation_start_time:
            elapsed = self.current_time - self.animation_start_time[cell_idx]
            if elapsed < 150:
                appearance_progress = min(1.0, elapsed / 150)
                t = appearance_progress
                appearance_progress = t * t * (3.0 - 2.0 * t)
        
        color = self.get_symbol_color(cell_idx, symbol, appearance_progress)
        
        if cell_idx in self.animation_start_time and appearance_progress < 1.0:
            size = (self.cell_size * 0.4) * appearance_progress
        else:
            size = self.cell_size * 0.4
        
        if symbol == 1:
            line_width = int(THEME["x_width"] * (0.5 + 0.5 * appearance_progress))
            if line_width < 1:
                line_width = 1
            
            offset = size * 0.7
            
            pygame.draw.line(self.screen, color, 
                           (center_x - offset, center_y - offset),
                           (center_x + offset, center_y + offset), 
                           line_width)
            pygame.draw.line(self.screen, color, 
                           (center_x + offset, center_y - offset),
                           (center_x - offset, center_y + offset), 
                           line_width)
        elif symbol == -1:
            line_width = int(THEME["o_width"] * (0.5 + 0.5 * appearance_progress))
            if line_width < 1:
                line_width = 1
            
            pygame.draw.circle(self.screen, color, 
                             (center_x, center_y), int(size), 
                             line_width)
    
    def draw_win_line(self):
        if not self.game.winner:
            return
        
        win_patterns = [
            ([0,1,2], ((0,0), (2,0))),
            ([3,4,5], ((0,1), (2,1))),
            ([6,7,8], ((0,2), (2,2))),
            ([0,3,6], ((0,0), (0,2))),
            ([1,4,7], ((1,0), (1,2))),
            ([2,5,8], ((2,0), (2,2))),
            ([0,4,8], ((0,0), (2,2))),
            ([2,4,6], ((2,0), (0,2)))
        ]
        
        for pattern, coords in win_patterns:
            if all(self.game.board[i] == self.game.winner for i in pattern):
                start_x = self.grid_left + coords[0][0] * self.cell_size + self.cell_size // 2
                start_y = self.grid_top + coords[0][1] * self.cell_size + self.cell_size // 2
                end_x = self.grid_left + coords[1][0] * self.cell_size + self.cell_size // 2
                end_y = self.grid_top + coords[1][1] * self.cell_size + self.cell_size // 2
                
                self.win_animation = min(1.0, self.win_animation + 0.25)
                
                t = self.win_animation
                eased_progress = t * t * (3.0 - 2.0 * t)
                
                anim_x = start_x + (end_x - start_x) * eased_progress
                anim_y = start_y + (end_y - start_y) * eased_progress
                
                pygame.draw.line(self.screen, THEME["highlight"], 
                               (start_x, start_y), (anim_x, anim_y), 
                               THEME["win_line_width"])
                break
    
    def draw_scoreboard(self):
        if self.game_mode == "ai":
            x_wins = self.ai_wins
            o_wins = self.human_wins
        else:
            x_wins = self.player_x_wins
            o_wins = self.player_o_wins
        
        score_y = self.grid_top - 120
        
        score_bg_width = 450 if IS_MOBILE else 400
        score_bg = pygame.Rect(
            self.screen_width//2 - score_bg_width//2,
            score_y - 15,
            score_bg_width, 60
        )
        pygame.draw.rect(self.screen, THEME["panel"], score_bg, border_radius=10)
        pygame.draw.rect(self.screen, THEME["grid"], score_bg, 2, border_radius=10)
        
        symbol_size = self.large_size
        number_size = self.medium_size
        
        x_symbol = pygame.font.Font(None, symbol_size).render("X", True, THEME["x"])
        o_symbol = pygame.font.Font(None, symbol_size).render("O", True, THEME["o"])
        
        x_width, x_height = x_symbol.get_size()
        # УМЕНЬШАЕМ КВАДРАТИК: 80% от высоты X
        square_size = int(x_height * 0.8)
        square_surface = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
        # УВЕЛИЧИВАЕМ ТОЛЩИНУ ЛИНИЙ: было 4, стало 6
        border_width = 6
        pygame.draw.rect(square_surface, THEME["text"], 
                        (0, 0, square_size, square_size), 
                        width=border_width)
        
        x_text = pygame.font.Font(None, number_size).render(str(x_wins), True, THEME["x"])
        o_text = pygame.font.Font(None, number_size).render(str(o_wins), True, THEME["o"])
        square_text = pygame.font.Font(None, number_size).render(str(self.draws), True, THEME["text"])
        
        spacing = 140 if IS_MOBILE else 130
        
        start_x = self.screen_width // 2 - spacing * 1.5
        
        self.screen.blit(x_symbol, (start_x, score_y))
        self.screen.blit(x_text, (start_x + 55, score_y + 5))
        
        self.screen.blit(o_symbol, (start_x + spacing, score_y))
        self.screen.blit(o_text, (start_x + spacing + 55, score_y + 5))
        
        square_x = start_x + spacing * 2
        # Центрируем уменьшенный квадратик по вертикали относительно X и O
        square_y = score_y + (x_height - square_size) // 2
        self.screen.blit(square_surface, (square_x, square_y))
        
        # СДВИГАЕМ ЦИФРУ ПРАВЕЕ: было +55, стало +60
        self.screen.blit(square_text, (square_x + 60, score_y + 5))
    
    def draw_nn_stats(self):
        stats_y = 80 if IS_MOBILE else 70
        
        stats_bg_width = 400 if IS_MOBILE else 350
        stats_bg = pygame.Rect(
            self.screen_width//2 - stats_bg_width//2,
            stats_y - 10,
            stats_bg_width, 50
        )
        pygame.draw.rect(self.screen, THEME["panel"], stats_bg, border_radius=10)
        pygame.draw.rect(self.screen, THEME["grid"], stats_bg, 2, border_radius=10)
        
        stats_text = f"Игр: {self.nn.games_played} | Позиций: {self.nn.unique_positions_seen}"
        stats_surface = self.font_small.render(stats_text, True, THEME["text"])
        
        self.screen.blit(stats_surface, 
                        (self.screen_width//2 - stats_surface.get_width()//2, stats_y))
    
    def draw_mode_text(self):
        mode_y = self.grid_top - 50
        
        mode_text = "Режим: против AI" if self.game_mode == "ai" else "Режим: человек vs человек"
        mode_surface = self.font_small.render(mode_text, True, THEME["text"])
        self.screen.blit(mode_surface, (self.screen_width//2 - mode_surface.get_width()//2, mode_y))
    
    def draw_buttons(self):
        mouse_pos = pygame.mouse.get_pos()
        
        for btn_data in self.buttons.values():
            rect = btn_data["rect"]
            
            if not IS_MOBILE and rect.collidepoint(mouse_pos):
                color = THEME["button_hover"]
                border_color = THEME["highlight"]
            else:
                color = THEME["button"]
                border_color = THEME["button_text"]
            
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, rect, 3, border_radius=10)
            
            text = self.font_medium.render(btn_data["text"], True, THEME["button_text"])
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)
    
    def draw_status(self):
        status_y = self.grid_top + self.grid_size + 40
        
        if self.game.game_over:
            if self.game.winner == 1:
                if self.game_mode == "ai":
                    status = "AI победила!"
                else:
                    status = "Игрок X победил!"
                color = THEME["x"]
            elif self.game.winner == -1:
                if self.game_mode == "ai":
                    status = "Вы победили!"
                else:
                    status = "Игрок O победил!"
                color = THEME["o"]
            else:
                status = "Ничья!"
                color = (180, 180, 180)
        else:
            if self.game_mode == "ai" and self.thinking:
                status = "AI думает..."
                color = THEME["text"]
            else:
                if self.game_mode == "pvp":
                    status = f"Ход игрока {'X' if self.game.current_player == 1 else 'O'}"
                else:
                    status = "Ваш ход (нолики)"
                color = THEME["o"] if self.game.current_player == -1 else THEME["x"]
        
        status_text = self.font_large.render(status, True, color)
        self.screen.blit(status_text, 
                        (self.screen_width//2 - status_text.get_width()//2, status_y))
    
    def draw(self):
        self.screen.fill(THEME["bg"])
        
        self.draw_nn_stats()
        
        self.draw_scoreboard()
        
        self.draw_mode_text()
        
        self.draw_grid()
        
        for i in range(9):
            if self.game.board[i] != 0:
                self.draw_symbol(i, self.game.board[i])
        
        if self.game.game_over and self.game.winner != 0:
            self.draw_win_line()
        
        self.draw_status()
        
        self.draw_buttons()
        
        pygame.display.flip()
    
    def handle_click(self, pos):
        for btn_name, btn_data in self.buttons.items():
            if btn_data["rect"].collidepoint(pos):
                btn_data["action"]()
                return
        
        if not self.game.game_over and not self.thinking:
            if self.game_mode == "pvp" or (self.game_mode == "ai" and self.game.current_player == -1):
                if (self.grid_left <= pos[0] <= self.grid_left + self.grid_size and 
                    self.grid_top <= pos[1] <= self.grid_top + self.grid_size):
                    
                    col = int((pos[0] - self.grid_left) // self.cell_size)
                    row = int((pos[1] - self.grid_top) // self.cell_size)
                    cell_idx = row * 3 + col
                    
                    if 0 <= col < 3 and 0 <= row < 3 and self.game.board[cell_idx] == 0:
                        self.game.make_move(cell_idx)
                        self.animation_start_time[cell_idx] = self.current_time
                        
                        self.flash_effects[cell_idx] = {"start_time": self.current_time}
                        self.flash_cooldowns[cell_idx] = self.current_time + 5000
                        
                        if self.game_mode == "ai" and not self.game.game_over:
                            self.thinking = True
                        elif self.game.game_over:
                            self.start_winning_flashes()
                            if not self.score_updated:
                                self.update_score()
                                self.score_updated = True
    
    def update_score(self):
        if self.game.game_over:
            if self.game.winner == 1:
                if self.game_mode == "ai":
                    self.ai_wins += 1
                else:
                    self.player_x_wins += 1
            elif self.game.winner == -1:
                if self.game_mode == "ai":
                    self.human_wins += 1
                else:
                    self.player_o_wins += 1
            else:
                self.draws += 1
            
            # ВАЖНОЕ ИСПРАВЛЕНИЕ: Нейросеть учится на ВСЕХ играх
            # И в режиме AI, и в режиме PvP
            self.nn.learn_from_game(self.game.move_history, self.game.winner)
            
            self.score_updated = True
    
    def update(self):
        self.current_time = pygame.time.get_ticks()
        
        self.update_animations()
        
        if self.thinking and not self.game.game_over and self.game_mode == "ai":
            self.ai_move()
    
    def update_animations(self):
        if self.game.game_over and self.game.winner != 0:
            keys_to_remove = []
            for cell_idx in self.flash_effects:
                if cell_idx not in self.winning_cells:
                    keys_to_remove.append(cell_idx)
            for cell_idx in keys_to_remove:
                del self.flash_effects[cell_idx]
        
        to_remove = []
        for cell_idx, effect in self.flash_effects.items():
            if cell_idx in self.winning_cells and self.win_flash_chain_active:
                continue
                
            elapsed = self.current_time - effect["start_time"]
            if elapsed >= 800:
                to_remove.append(cell_idx)
        
        for cell_idx in to_remove:
            del self.flash_effects[cell_idx]
        
        to_remove_anim = []
        for cell_idx, start_time in self.animation_start_time.items():
            if self.current_time - start_time >= 150:
                to_remove_anim.append(cell_idx)
        
        for cell_idx in to_remove_anim:
            del self.animation_start_time[cell_idx]
        
        if not self.game.game_over or self.game.winner == 0:
            for cell_idx in list(self.flash_cooldowns.keys()):
                if cell_idx in self.winning_cells:
                    continue
                    
                if self.game.board[cell_idx] != 0:
                    if self.current_time >= self.flash_cooldowns[cell_idx]:
                        if cell_idx not in self.flash_effects:
                            self.flash_effects[cell_idx] = {
                                "start_time": self.current_time
                            }
                        self.flash_cooldowns[cell_idx] = self.current_time + 5000
                else:
                    del self.flash_cooldowns[cell_idx]
        
        if self.game.game_over and self.game.winner != 0 and self.winning_cells:
            if self.win_flash_chain_active:
                if self.win_flash_index < len(self.winning_cells):
                    if self.current_time - self.win_flash_timer >= 300:
                        cell_idx = self.winning_cells[self.win_flash_index]
                        self.flash_effects[cell_idx] = {"start_time": self.current_time}
                        self.win_flash_index += 1
                        self.win_flash_timer = self.current_time
                else:
                    if self.current_time - self.win_flash_timer >= 1300:
                        for cell_idx in self.winning_cells:
                            if cell_idx in self.flash_effects:
                                del self.flash_effects[cell_idx]
                        self.win_flash_index = 0
                        self.win_flash_timer = self.current_time
            else:
                self.win_flash_chain_active = True
                self.win_flash_index = 0
                self.win_flash_timer = self.current_time
    
    def ai_move(self):
        if not self.thinking or self.game.game_over:
            return
        
        move = self.nn.get_move(self.game.board, temperature=0.1)
        
        if move is not None and 0 <= move < 9 and self.game.board[move] == 0:
            self.game.make_move(move)
            self.animation_start_time[move] = self.current_time
            
            self.flash_effects[move] = {"start_time": self.current_time}
            self.flash_cooldowns[move] = self.current_time + 5000
            
            if self.game.game_over:
                self.start_winning_flashes()
                if not self.score_updated:
                    self.update_score()
                    self.score_updated = True
            
            self.thinking = False
    
    def run(self):
        clock = pygame.time.Clock()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.exit_game()
                    elif event.key == pygame.K_r:
                        self.new_game()
                    elif event.key == pygame.K_t:
                        self.quick_train()
                    elif event.key == pygame.K_m:
                        self.toggle_mode()
                    elif IS_MOBILE and event.key in [pygame.K_AC_BACK, 27]:
                        self.exit_game()
            
            self.update()
            self.draw()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()

def main():
    game = TicTacToeGUI()
    game.run()

if __name__ == "__main__":
    main()