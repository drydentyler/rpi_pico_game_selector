from games_db import GamesDB
from game import Game


class DBWrapper:
    def __init__(self, db_name: str):
        """
        Given a name for the database file, create the file passing it into the GamesDB class

        Args:
            db_name: str, name of the file to be used as the database, allows for testing
        """
        self.db = GamesDB(db_name)

    def get_games(self) -> [Game]:
        """
        Wrapper function for getting all current games in the database

        Returns:
            [Game]: list of game objects
        """
        # For every value in the database dictionary, return list comprehension of all the values
        return [value for key, value in self.db.games.items()]

    def insert_game(self, game: Game):
        """
        Wrapper function for inserting a game into the database

        Args:
            game: Game, provided game object that is to be inserted into the database
        """
        # Insert the game using the 'a' (append) method for writing to the txt file
        return self.db.insert_game(game=game, method='a')

    def update_game(self, game: Game):
        """
        Wrapper function for updating a game that is currently in the database

        Args:
            game: Game, provided game object that is to be updated in the database
        """
        return self.db.update_game(game=game)

    def get_random_game(self, players: int, duration: int=0, complexity: bool=False) -> Game:
        """
        Get a random game from the database that matches with the provided criteria

        Args:
            players: int, number of players
            duration: int, preferred duration of game
            complexity: bool, whether the games should be filtered for the top 25% difficulty

        Returns:
            Game: a single game object that matched the given criteria
        """
        return self.db.get_random_game(players, duration, complexity)

