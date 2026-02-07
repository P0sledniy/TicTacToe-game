import numpy as np
import random
import time
import os
import json
from collections import defaultdict

print("=" * 60)
print("ЧИСТАЯ НЕЙРОСЕТЬ: УЧИМСЯ С НУЛЯ")
print("=" * 60)

class TicTacToeGame:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.board = [0] * 9
        self.current_player = 1
        self.game_over = False
        self.winner = 0
        self.move_history = []
        return self.board.copy()
    
    def get_legal_moves(self):
        return [i for i in range(9) if self.board[i] == 0]
    
    def make_move(self, position):
        if self.board[position] != 0 or self.game_over:
            return False
        
        board_before = self.board.copy()
        self.move_history.append((self.current_player, position, board_before))
        
        self.board[position] = self.current_player
        
        win_patterns = [
            [0,1,2], [3,4,5], [6,7,8],
            [0,3,6], [1,4,7], [2,5,8],
            [0,4,8], [2,4,6]
        ]
        
        for pattern in win_patterns:
            if all(self.board[i] == self.current_player for i in pattern):
                self.game_over = True
                self.winner = self.current_player
                return True
        
        if 0 not in self.board:
            self.game_over = True
            self.winner = 0
            return True
        
        self.current_player *= -1
        return True

class MonteCarloLearner:
    def __init__(self, player_id="default"):
        self.player_id = player_id
        
        self.experience = defaultdict(lambda: {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'moves': defaultdict(lambda: [0, 0.0])
        })
        
        self.best_moves_cache = {}
        
        self.games_played = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        
        self.total_games_played = 0
        self.unique_positions_seen = 0
        
        self.win_patterns = set()
        self.loss_patterns = set()
        
        print(f"Создана нейросеть для игрока: {player_id}")
    
    # Свойства для совместимости
    @property
    def mcts_stats(self):
        stats = {}
        for board_key, pos_data in self.experience.items():
            stats[board_key] = {}
            for move, move_data in pos_data['moves'].items():
                stats[board_key][move] = [move_data[0], move_data[1]]
        return stats
    
    @property
    def best_moves(self):
        return self.best_moves_cache
    
    @property
    def move_values(self):
        return self.experience
    
    def load_memory(self):
        return self.load_knowledge()
    
    def save_memory(self):
        return self.save_knowledge()
    
    def quick_train(self, num_games=100):
        return self.quick_self_learn(num_games)
    
    def learn_from_game(self, game_history, result):
        winner = result
        # ВАЖНОЕ ИСПРАВЛЕНИЕ: Обучение на реальных играх
        return self.analyze_game(game_history, winner)
    
    def get_blank_slate_move(self, board):
        legal_moves = [i for i in range(9) if board[i] == 0]
        if legal_moves:
            return random.choice(legal_moves)
        return None
    
    def learn_from_experience(self, board, move, result):
        board_key = tuple(board)
        
        if board_key not in self.experience:
            self.unique_positions_seen += 1
        
        pos_data = self.experience[board_key]
        pos_data['total_games'] += 1
        
        if result > 0:
            pos_data['wins'] += 1
        elif result < 0:
            pos_data['losses'] += 1
        else:
            pos_data['draws'] += 1
        
        move_data = pos_data['moves'][move]
        move_data[0] += 1
        move_data[1] += result
        
        if board_key in self.best_moves_cache:
            del self.best_moves_cache[board_key]
    
    def analyze_game(self, game_history, winner):
        # ВАЖНОЕ ИСПРАВЛЕНИЕ: Всегда обновляем статистику
        self.total_games_played += 1
        self.games_played += 1  # Исправлено: эта переменная теперь используется
        
        if winner == 1:
            self.wins += 1
        elif winner == -1:
            self.losses += 1
        else:
            self.draws += 1
        
        # Обновляем рейтинги на основе результата игры
        x_reward = 1.0 if winner == 1 else (-1.0 if winner == -1 else 0.0)
        o_reward = -x_reward
        
        print(f"\n📊 Обучение на игре #{self.total_games_played}")
        print(f"   Результат: {'X победил' if winner == 1 else 'O победил' if winner == -1 else 'ничья'}")
        print(f"   Ходов в игре: {len(game_history)}")
        
        for i, (player, move, board_before) in enumerate(game_history):
            reward = x_reward if player == 1 else o_reward
            self.learn_from_experience(board_before, move, reward)
            
            # Дополнительное обучение для победивших ходов
            if (player == 1 and winner == 1) or (player == -1 and winner == -1):
                self.learn_from_experience(board_before, move, reward * 0.5)
        
        print(f"   Новая статистика: Игр={self.games_played}, Позиций={self.unique_positions_seen}")
        
        return True
    
    def get_learned_move(self, board, exploration_rate=0.3):
        board_key = tuple(board)
        legal_moves = [i for i in range(9) if board[i] == 0]
        
        if not legal_moves:
            return None
        
        if board_key not in self.experience or random.random() < exploration_rate:
            return random.choice(legal_moves)
        
        if board_key in self.best_moves_cache:
            cached_move = self.best_moves_cache[board_key]
            if cached_move in legal_moves and random.random() > exploration_rate/2:
                return cached_move
        
        pos_data = self.experience[board_key]
        best_move = None
        best_value = -float('inf')
        
        for move in legal_moves:
            if move in pos_data['moves']:
                uses, total_reward = pos_data['moves'][move]
                if uses > 0:
                    avg_reward = total_reward / uses
                    confidence = np.sqrt(uses) / (1 + uses)
                    value = avg_reward + 0.1 * confidence
                    
                    if value > best_value:
                        best_value = value
                        best_move = move
        
        if best_move is not None:
            self.best_moves_cache[board_key] = best_move
            return best_move
        
        return random.choice(legal_moves)
    
    def get_move(self, board, temperature=0.1):
        if self.total_games_played == 0:
            exploration = 1.0
        elif self.total_games_played < 5:
            exploration = 0.7
        elif self.total_games_played < 10:
            exploration = 0.4
        elif self.total_games_played < 20:
            exploration = 0.2
        else:
            exploration = 0.1
        
        exploration = min(1.0, exploration + temperature)
        
        return self.get_learned_move(board, exploration)
    
    def quick_self_learn(self, num_games=100):
        print(f"\n🧠 САМООБУЧЕНИЕ ({num_games} случайных игр)")
        print("Нейросеть играет сама с собой случайными ходами")
        
        start_time = time.time()
        
        for game_num in range(num_games):
            game = TicTacToeGame()
            
            while not game.game_over:
                legal_moves = game.get_legal_moves()
                if legal_moves:
                    move = random.choice(legal_moves)
                    game.make_move(move)
                else:
                    break
            
            self.analyze_game(game.move_history, game.winner)
            
            if (game_num + 1) % 20 == 0:
                print(f"   Пройдено {game_num + 1}/{num_games} игр...")
        
        elapsed = time.time() - start_time
        
        print(f"\n✅ Самообучение завершено за {elapsed:.2f} сек")
        print(f"   Всего игр: {self.total_games_played}")
        print(f"   Уникальных позиций: {self.unique_positions_seen}")
        print(f"   Текущая статистика: Игр={self.games_played}")
    
    def save_knowledge(self):
        try:
            save_data = {
                'player_id': self.player_id,
                'total_games': self.total_games_played,
                'games_played': self.games_played,
                'wins': self.wins,
                'losses': self.losses,
                'draws': self.draws,
                'unique_positions': self.unique_positions_seen,
                'win_patterns': [str(p) for p in self.win_patterns],
                'loss_patterns': [str(p) for p in self.loss_patterns],
                'experience': {}
            }
            
            for board_key, pos_data in self.experience.items():
                board_str = str(board_key)
                save_data['experience'][board_str] = {
                    'total_games': pos_data['total_games'],
                    'wins': pos_data['wins'],
                    'losses': pos_data['losses'],
                    'draws': pos_data['draws'],
                    'moves': {str(k): v for k, v in pos_data['moves'].items()}
                }
            
            filename = f"pure_experience_{self.player_id}.json"
            with open(filename, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            print(f"\n💾 Опыт сохранен: {self.games_played} игр, {self.unique_positions_seen} позиций")
            return True
            
        except Exception as e:
            print(f"\n❌ Ошибка сохранения: {e}")
            return False
    
    def load_knowledge(self):
        try:
            filename = f"pure_experience_{self.player_id}.json"
            if not os.path.exists(filename):
                print(f"\n📝 Файл опыта не найден. Начинаем с чистого листа.")
                return False
            
            with open(filename, 'r') as f:
                save_data = json.load(f)
            
            self.experience.clear()
            self.best_moves_cache.clear()
            
            self.player_id = save_data.get('player_id', self.player_id)
            self.total_games_played = save_data.get('total_games', 0)
            self.games_played = save_data.get('games_played', 0)  # Исправлено: загружаем games_played
            self.wins = save_data.get('wins', 0)
            self.losses = save_data.get('losses', 0)
            self.draws = save_data.get('draws', 0)
            self.unique_positions_seen = save_data.get('unique_positions', 0)
            
            win_patterns_data = save_data.get('win_patterns', [])
            for pattern_str in win_patterns_data:
                self.win_patterns.add(tuple(eval(pattern_str)))
            
            loss_patterns_data = save_data.get('loss_patterns', [])
            for pattern_str in loss_patterns_data:
                self.loss_patterns.add(tuple(eval(pattern_str)))
            
            exp_data = save_data.get('experience', {})
            for board_str, pos_data in exp_data.items():
                board_key = tuple(eval(board_str))
                
                self.experience[board_key] = {
                    'total_games': pos_data['total_games'],
                    'wins': pos_data['wins'],
                    'losses': pos_data['losses'],
                    'draws': pos_data['draws'],
                    'moves': defaultdict(lambda: [0, 0.0])
                }
                
                moves_data = pos_data.get('moves', {})
                for move_str, stats in moves_data.items():
                    self.experience[board_key]['moves'][int(move_str)] = stats
            
            print(f"\n📂 Загружен опыт из {self.total_games_played} игр")
            print(f"   Статистика: Игр={self.games_played}, Позиций={self.unique_positions_seen}")
            return True
            
        except Exception as e:
            print(f"\n❌ Ошибка загрузки: {e}")
            return False