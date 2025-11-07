import os
import random

from game import Game


class GamesDB:
    # Set class variable file name to None until it is set in the init
    _file_name = None

    # Set up the context manager decorator that will be used on functions that need to open the database file
    # txt_context_manager takes a function as a required argument, the function it is decorating
    # wrapper takes in any args and kwargs of the function being decorated, it will require a method kwarg to properly
    # open and handle the database file
    def txt_context_manager(func):
        def wrapper(*args, **kwargs):
            if 'method' in kwargs:
                # Open the database file in the correct method
                f = open(GamesDB._file_name, kwargs['method'])
                # pass the file into the function being decorated as a kwarg
                kwargs['file'] = f
                # Execute the decorated function with the necessary args and kwargs
                rv = func(*args, **kwargs)
                # Close the file
                f.close()
                # Return any return value from the decorated function
                return rv
        return wrapper

    def __init__(self, db_name: str):
        # Set the class variable to the provided database file name, needs accessed by staticmethod context manager
        GamesDB._file_name = db_name

        self.max_id = 0

        # If the database file doesn't already exist, create it and print status to the console
        if GamesDB._file_name not in os.listdir():
            # TODO: dealing with reading/writing files needs a try/except around it
            with open(GamesDB._file_name, 'w') as f:
                print(f'Creating {GamesDB._file_name}')
            # TODO: if this is unnecessary, remove it
            # If there was no database file, starting max ID is 0
            # self.max_id = 0

        # Get all the games from the database file
        # KEY NOTE: CHANGED TO INTEGER ID VALUE INSTEAD OF STRING VALUE NAME
        self.games: {int: Game} = self.read_all_games(method='r')

    @txt_context_manager
    def read_all_games(self, **kwargs) -> {int: Game}:
        """
        Read all the games from the database txt file, expecting kwargs arguments with the file object

        Returns:
            {int: Game}, dictionary of games where key is id of the game
        """
        # File object should be passed in kwargs from the context manager function
        if 'file' in kwargs:
            # Read contents and split by line and commas
            # TODO: this could possibly be replaced with self._get_file_lines()
            contents = kwargs['file'].read()
            lines = [tuple(line.split(',')) for line in contents.split('\n') if line != '']
            if lines:
                # Set the max ID to the last ID found from the txt file
                self.max_id = lines[-1][0]
            return {int(line[0]): Game(*line) for line in lines}
        return {}

    def get_all_games(self) -> {int: Game}:
        """
        Return the dictionary of games as the contents of the database
        """
        return self.games

    @txt_context_manager
    def insert_game(self, game: Game, **kwargs) -> int:
        """
        Insert a game into the database, expecting file object in kwargs

        Args:
            game: Game, game object that is being written into the database file
            kwargs: expecting file object under key 'file'

        Returns:
             int: status of the insert, 201 success 40x failed
        """
        # File object should be passed in from the context manager
        if 'file' in kwargs:
            # Check to ensure game name isn't already in records by compiling names from records
            names = [game.name for key, game in self.games]
            if game.name not in names:
                # Ensure game ID is none as a new game
                if game.id is None:
                    # Increment max id and assign to current new game
                    self.max_id += 1
                    game.id = self.max_id
                # Write the new game to the file
                # TODO: This may cause issues, depending on whether it correctly uses __repr__ on the game object
                kwargs['file'].write(f'{game}\n')

                # Add the game to the dictionary of records
                self.games[game.id] = game
                return 201
            else:
                return 409  # Conflict, already exists
        else:
            return 400  # Bad request, text file was somehow not included to open

    def update_game(self, game: Game) -> int:
        """
        Update a game in the current records

        Args:
            game: Game, game object that is being updated

        Returns:
            int: value representing whether update was successful
        """
        # Get all the file lines from the database document
        lines = self._get_file_lines(method='r')

        # Iterate the lines to check for the game being updated
        for x in range(len(lines)):
            line = lines[x]
            if line:
                # Extract the game id from each line
                game_id = int(line[:line.index(',')])

                # If the line's id matches the updating game's id
                if game_id == game.id:
                    # Replace the line with the updated __repr__ information
                    lines[x] = f'{game.__repr__()}\n'
                    # Rewrite the updated list of lines to the database document
                    self._rewrite_file_lines(lines, method='w')

                    # Update the games dictionary attribute with the updated game information
                    self.games[game.id] = game
                    return 201  # Successfully updated game information
        return 404  # Error, could not find the updating game based on ID

    @txt_context_manager
    def _get_file_lines(self, **kwargs) -> [str]:
        """
        Helper function to get all the lines of the database document without creating Game objects

        Args:
            kwargs: expects file object to be passed in from context manager

        Returns:
            [str]: list of lines from the database document
        """
        # Ensure file object is passed in with kwargs
        if 'file' in kwargs:
            f = kwargs['file']
            # Return the lines from the file
            return f.readlines()
        return []

    @txt_context_manager
    def _rewrite_file_lines(self, file_lines: [str], **kwargs):
        """
        Helper function to rewrite lines into the database txt file

        Args:
            file_lines: [str], list of lines that are going to be rewritten to the txt file
            kwargs: expects the file object from the context manager
        """
        # Ensure the file object is passed in the kwargs
        if 'file' in kwargs:
            f = kwargs['file']
            # For each line, write it to the file
            for line in file_lines:
                f.write(line)

    def get_random_game(self, players: int, duration: int = 0, complexity: bool = False) -> Game | None:
        """
        Get a random game from the database given the provided parameters

        Args:
            players: int, number of players
            duration: int, default 0, preferred duration of a game
            complexity: bool, default False, whether games should be filtered for difficulty

        Returns:
            Game, a single game object of the selected game based on the parameters
        """
        _game_matches = []
        # Set the source of games to the top 25% most difficult
        if complexity:
            games_src = self._get_hardest_games()
        # Otherwise set it to the list of all games in records
        else:
            games_src = [value for key, value in self.games.items()]

        # For each game in the source, move it to the matches pool if it fits with the duration parameter
        for value in games_src:
            # If a duration value greater than 0 is provided, calculate how close a game is to the desired length
            if duration > 0:
                # This is just an arbitrary value saying look for games that are +/- 20 mins from given duration
                # Expand the time allowance if complex games are being used
                time_allowance = 20 if not complex else 30
                time_diff = abs(duration - value.duration)
                # If the time difference is within time allowance and players parameter fits, add to matches pool
                if time_diff <= time_allowance and value.min_players <= players <= value.max_players:
                    _game_matches.append(value)
            # If duration was left at 0, only check if numbers of players are a match and add to matches pool
            else:
                if value.min_players <= players <= value.max_players:
                    _game_matches.append(value)

        # If there are games in the matches pool
        if _game_matches:
            # Return a game randomly within the matches pool
            return _game_matches[random.randint(0, len(_game_matches) - 1)]
        # Otherwise print to console error message and return None
        else:
            print('Unfortunately, no games met the given criteria.')
            return None

    def _get_hardest_games(self) -> [Game]:
        """
        Helper function to return a pool of only the top 25% most difficult games from all records

        Returns:
            [Game]: list of game objects that represent the top 25% most difficult
        """
        # Sort all the games by their complexity in a reverse order with highest at the front
        sorted_items = sorted([value for key, value in self.games.items()], key=lambda g: g.complexity, reverse=True)

        # Calculate what the n value for top 25% of all games is
        top_n = max(1, len(sorted_items) // 4)

        # Return upto the n value for top 25% of games
        return sorted_items[:top_n]

