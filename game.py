class Game:
    def __init__(self, game_id: int, name: str, min_players: int, max_players: int, duration: int, complexity: float):
        # ID will be set when inserting into or read from the database
        self.id = int(game_id) if game_id is not None else None

        self.name = name
        self.min_players = int(min_players)
        self.max_players = int(max_players)
        self.duration = int(duration)
        self.complexity = float(complexity)

    def __repr__(self):
        return f'{self.id},{self.name},{self.min_players},{self.max_players},{self.duration},{self.complexity}'
