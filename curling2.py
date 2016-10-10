import pickle
import random
# import copy
import time

PRINT = True


class Card:
    def __init__(self, name, suit, player=None):
        self.name = str(name)
        if self.name == '10':
            self.name = '0'  # For spacing
        if name in ['*', 'Jkr', ' ']:
            self.value = 0
        elif name in ['J', 'Q', 'K']:
            self.value = 10
        elif name == 'A':
            self.value = 1
        else:
            self.value = int(name)
        self.suit = suit
        self.played = False
        self.discarded = False
        self.player = player

    def __repr__(self):
        return '{} {}'.format(self.name, self.suit)


class Joker(Card):
    def __init__(self):
        super().__init__('Jkr', '')
        self.played = True
        self.discarded = False

    def __repr__(self):
        return self.name


class BlankCard(Card):
    def __init__(self, pos):
        super().__init__(' ', ' ')
        self.played = True
        self.discarded = False
        self.pos = pos

    def __bool__(self):
        return False


class Board:
    def __init__(self, size=5, empty='Default'):
        self._final = 0
        self.size = size
        self.joker = Joker()
        self._cards = []
        for _ in range(size):
            self._cards.append([Card('*', '*')] * size)
        self.joker_pos = size // 2
        self._cards[self.joker_pos][self.joker_pos] = self.joker
        if empty == 'Default':
            empty = [(0, 0), (0, 1), (0, 3), (0, 4), (1, 0), (1, 4), (3, 0), (3, 4), (4, 0), (4, 1), (4, 3), (4, 4)]
        self.blanks = []
        for x, y in empty:
            blank = BlankCard((x + 1, y + 1))
            self._cards[x][y] = blank
            self.blanks.append(blank)
        self.scoring_pos = [(1, [(self.joker_pos - 1, self.joker_pos - 1), (self.joker_pos - 1, self.joker_pos + 1),
                                 (self.joker_pos + 1, self.joker_pos - 1), (self.joker_pos + 1, self.joker_pos + 1)]),
                            (2, [(self.joker_pos - 1, self.joker_pos), (self.joker_pos, self.joker_pos - 1),
                                 (self.joker_pos + 1, self.joker_pos), (self.joker_pos, self.joker_pos + 1)])]

    @property
    def cards(self):
        return [r[:] for r in self._cards]

    @cards.setter
    def cards(self, cards):
        self._cards = [r[:] for r in cards]

    def finalise(self):
        self._final = 1

    def unfinalise(self):
        self._final = 0

    def get_empty(self):
        if any(not blank.discarded for blank in self.blanks):
            return [blank.pos for blank in self.blanks if not blank.discarded]
        else:
            return []

    def score(self, player):
        out = 0
        if not self._final:
            for s, l in self.scoring_pos:
                for x, y in l:
                    if self._cards[x][y] and self._cards[x][y].suit == player.suit:
                        out += s * self._cards[x][y].value
        else:
            raise Exception('Trying to score points on a finalised board for {}'.format(player))
        return out

    def update(self, ply, test=False):
        """Starting from the outside left as column 0, top as row 0, place your card outside the space you want to
        insert it, e.g. 0, 2 to insert from the left into the second row"""
        card = ply.card
        error = ''
        empty = self.get_empty()
        if empty:
            if (ply.row, ply.column) not in empty:
                if PRINT:
                    print('Please choose from empty cells', empty)
                discarded = ''
                error = 'Please choose from empty cells {}'.format(empty)
                return discarded, error
            else:
                discarded, self._cards[ply.row - 1][ply.column - 1] = self._cards[ply.row - 1][ply.column - 1], card
        else:
            # Check insertion condition, determine if a row or column is being inserted to
            if 0 < ply.row <= self.size and ply.column in (0, self.size + 1):
                tempcards = self._cards
                ins_row = True  # row or column?
                ins_left = (ply.column == 0)  # left(top) or right(bottom)? (reverse if undoing)
                ins_pos = ply.row  # row(col) index
            elif 0 < ply.column <= self.size and ply.row in (0, self.size + 1):
                # treat row and column insertion the same by transposing the card list for one of them
                tempcards = list(map(list, zip(*self._cards)))
                # column insertion
                ins_row = False
                ins_left = (ply.row == 0)
                ins_pos = ply.column
            else:
                discarded = ''
                if PRINT:
                    print('Invalid row/column')
                error = 'Invalid row/column'
                return discarded, error

            # treat left and right insertion the same by reversing in one case
            if ins_left:
                card_row = tempcards[ins_pos - 1]
            else:
                card_row = tempcards[ins_pos - 1][::-1]

            discarded = card_row[-1]
            new_row = [card] + card_row[:-1]
            # put the joker back in the right place if we're in that row/col
            if ins_pos == self.joker_pos + 1:
                new_row.insert(self.joker_pos, new_row.pop(self.joker_pos + 1))

            # undo the row reverse and transpose
            if not ins_left:
                new_row.reverse()
            if ins_row:
                self._cards[ins_pos - 1] = new_row
            else:
                tempcards[ins_pos - 1] = new_row
                self._cards = [x for x in map(list, zip(*tempcards))]

        discarded.discarded = 1  # Set card attribute
        if not test and isinstance(discarded, BlankCard):
            self.blanks.remove(discarded)
        return discarded, error

    #    def is_setup_phase(self):
    #        return (len(self.get_empty()) > 0)

    def __repr__(self):
        out = []
        for row in self._cards:
            out.append(' | '.join(str(card) for card in row))
        return '\n'.join(out)
        #  return '\n'.join(' '.join(str(card) for card in rows) for rows in self._cards) + '\n'


# The information a player gives to the game to make a ply (move)
class Ply:
    def __init__(self, card, row, column):
        self.card = card
        if self.card == '10':
            self.card = '0'
        self.row = row
        self.column = column

    def __repr__(self):
        return str(self.card) + " at " + str(self.row) + ", " + str(self.column)


class Player:
    def __init__(self, name, suit, card_options=1):
        self.score = 0
        self.name = name
        self.suit = suit
        # noinspection PyTypeChecker
        l = ['K', 'Q', 'J', 'A'] + list(range(2, 11))
        self.hand = sorted((Card(i, suit, self) for i in l), key=lambda x: -x.value)
        self.AI = False
        self.card_options = card_options

    def in_hand(self, card):
        """Tests if a card (by instance or name) is in player's hand and returns instance or False"""
        for c in self.hand:
            if c.name == card or c == card:
                return c
        return False
        # return any(c.name == card for c in self.hand) or card in self.hand

    def play(self, card):
        """Tells a player to remove a card from their hand"""
        if not self.in_hand(card):
            raise Exception('Card {} not in hand'.format(card))
        for i, c in enumerate(self.hand):
            if c.name == card or c == card:  # Either by name or card instance
                c.played = True
                del self.hand[i]
                return True
        raise Exception('Card not removed')

    # def unplay(self, card):
    #     if self.in_hand(card):
    #         raise Exception('Card {} already in hand during tree backtrack'.format(card))
    #     if card != '':
    #         card.played = False
    #     self.hand.append(card)
    #     return True

    def alter_score(self, delta):
        if delta > 500:
            raise Exception('Trying to add score above 500')
        self.score += delta
        return self.score

    @staticmethod
    def enum_plies(game, p_turn):
        """Given a game generates all potential moves for player indexed by p_turn"""

        # assuming we have cards left to play
        player = game.players[p_turn]
        # card_options = sorted(player.hand, key=lambda x: -x.value)  Player's hand is now sorted
        empty = game.board.get_empty()
        if empty:
            rowcol_options = empty
        else:
            bsize = game.board.size
            rowcol_options = [(0, i) for i in range(1, bsize + 1)] + \
                             [(bsize + 1, i) for i in range(1, bsize + 1)] + \
                             [(i, 0) for i in range(1, bsize + 1)] + \
                             [(i, bsize + 1) for i in range(1, bsize + 1)]

        # choose either the highest or lowest value card
        if len(player.hand) > 1 and player.card_options > 1:
            if player.card_options == 2:
                card_choices = [player.hand[0], player.hand[-1]]
            else:
                raise NotImplementedError
        else:
            # Pick maximum
            card_choices = [player.hand[0]]

        for card in card_choices:
            for rowcol in rowcol_options:
                yield Ply(card, rowcol[0], rowcol[1])

    # To be implemented by inheriting classes
    def make_move(self, game_state):
        raise NotImplementedError

    def __repr__(self):
        if self.AI:
            return 'AI - {} ({})'.format(self.name, self.suit)
        else:
            return '{} ({})'.format(self.name, self.suit)


class HumanPlayer(Player):
    def make_move(self, game_state):
        while 1:
            while 1:
                card = input('Pick a card:')
                if card == '10':
                    card = '0'
                card = self.in_hand(card)
                if self.in_hand(card):
                    break
            while 1:
                row = input('Pick row:')
                column = input('Pick column:')
                try:
                    row = int(row)
                    column = int(column)
                except ValueError:
                    # print('Please use integers')
                    continue
                else:
                    break
            # noinspection PyUnboundLocalVariable
            return Ply(card, row, column)


class AIPlayer(Player):
    def __init__(self, name, suit):
        super().__init__(name, suit)
        self.AI = True

    def make_move(self, game_state):
        """Selects max card and random valid row/column"""
        if self.hand:
            card = max(self.hand, key=lambda x: x.value)
        else:
            raise Exception("Empty Hand")
        # print(card)
        empty = game_state.board.get_empty()
        # print(empty)
        if empty:
            row, column = random.choice(empty)
        else:
            insert = random.choice(('R', 'C'))
            if insert == "R":
                row = random.choice((0, game_state.board.size + 1))
                column = random.randint(1, 5)
            else:
                column = random.choice((0, game_state.board.size + 1))
                row = random.randint(1, 5)
        return Ply(card, row, column)


class AITreeSearch(Player):
    def __init__(self, name, suit, depth=2, card_options=1):
        super().__init__(name, suit, card_options)
        self.AI = True
        self.depth = depth  # tree search depth (plies)
        self.t_game = []  # to hold the local version of the game

    def make_move(self, game_state):
        """Runs a tree search to find out best move"""
        # entry point
        global PRINT
        PRINT = False
        print("Enter AITree make_move")
        # create local version of the game without letting it enter its game loop
        self.t_game = Game(game_state, autostart=False)  # copy.deepcopy(Game(game_state, autostart = False))

        # do a tree search recursively to find the best ply and its expected scores
        alter_scores = {player: 0 for player in self.t_game.players}
        bestscores, bestply = self.tree_search(self.t_game, self.depth, self.t_game.p_turn, alter_scores)

        # point the resulting card object to the actual card in the real game
        for card in self.hand:
            if card.name == bestply.card.name:
                bestply.card = card
        print("Exit AITree make_move, best scores: ", bestscores)
        PRINT = True
        return bestply

    # recursive search of future moves to the given depth
    def tree_search(self, game, depth, p_turn, alter_scores):
        # p_turn = game.p_turn
        player = game.players[p_turn]
        plies = player.enum_plies(game, p_turn)
        best = ''
        # Store a copy of board cards
        stored_cards = game.board.cards
        for ply in plies:
            new_alter_scores, new_p_turn, gameover, discard = game.test_move(ply, p_turn, alter_scores.copy())
            if gameover or depth == 0:
                node_values = self.heuristic_eval(game, new_alter_scores, new_p_turn, gameover)
            else:
                node_values = self.tree_search(game, depth - 1, new_p_turn, new_alter_scores)[0]

            # Undo move by
            ply.card.played = False
            discard.discarded = False
            # Restore the board's cards
            game.board.cards = stored_cards
            # unply = game.unmake_move()
            # assert ply == unply, 'Mismatch plies {} {}'.format(ply, unply)
            # assert stored_cards == game.board.cards, "Game board cards don't match\n{}\n{}".format(stored_cards,
            # game.board.cards)
            if best == '' or node_values[player] > best[player]:
                best = node_values
                bestplies = [ply]
            elif node_values[player] == best[player]:
                # noinspection PyUnboundLocalVariable
                bestplies.append(ply)
        bestply = random.choice(bestplies)
        return best, bestply

    # returns the value of the current game for each player in a three-item list
    # trying to take into account immediate future moves without doing a tree search
    # (so that this evaluation doesn't favour the player who just played)

    @staticmethod
    def heuristic_eval(game, alter_scores, p_turn, gameover):
        if not gameover:
            num_players = len(game.players)
            values = {p: 0 for p in game.players}
            # Catch non player cards
            values[None] = 0
            # add some value for cards not currently in scoring positions
            central = (game.board.size // 2 - 1, game.board.size // 2, game.board.size // 2 + 1)
            # TODO: Work out scoring for other sized boards - where are scoring pos etc.
            # Only worry about outer rows here, inner is counted by score
            rows = [0, game.board.size - 1]
            columns = [0, game.board.size - 1]
            for r in rows:
                for c in columns:
                    card = game.board._cards[r][c]
                    values[card.player] += 0.2 * card.value
                for c in central:
                    card = game.board._cards[r][c]
                    values[card.player] += 0.5 * card.value
            for c in columns:
                for r in central:
                    card = game.board._cards[r][c]
                    values[card.player] += 0.5 * card.value
            del values[None]
            # for row, x in enumerate(game.board._cards):
            #     for column, card in enumerate(x):
            #         if row in central or column in central:
            #             values[card.player] += 0.5 * card.value
            #         else:
            #             values[card.player] += 0.2 * card.value
            for i, player in enumerate(game.players):
                waittime = (i - p_turn) % num_players  # plies until your next ply
                score = player.score + alter_scores[player]
                boardscore = game.board.score(player) * (1 + num_players - waittime)  # how good the board is
                hand_potential = sum(c.value for c in player.hand if not c.played)
                values[player] += score + 0.4 * boardscore + 0.4 * hand_potential
            s = sum(values.values())
            for k, v in values.items():
                values[k] = 2 * v - s  # I.e. subtract others
        else:
            # TODO: Should we differentiate between winning states? E.g probability of winning, margin of winning?
            # losers have a large negative score
            values = {p: -500 for p in game.players}
            maxscore = 0
            winners = []
            for player in game.players:
                if player.score + alter_scores[player] > maxscore:
                    maxscore = player.score  + alter_scores[player]
                    winners = [player]
                elif player.score + alter_scores[player] == maxscore:
                    winners.append(player)

            # winner has a large positive score
            winning_bonus = 10000 / len(winners)
            for player in winners:
                values[player] += winning_bonus

        return values


# the information which players are sent to make their move
class GameState:
    def __init__(self, board, players, plyhistory, p_turn, gameover):
        self.board = board
        self.players = players
        self.plyhistory = plyhistory
        self.p_turn = p_turn
        self.next_player = self.players[self.p_turn]
        self.gameover = gameover

    def statement(self):
        if not self.gameover:
            return "{}'s turn\nThey scored {} points\nThey have in their hand:\n{}".format(self.next_player,
                                                                                           self.board.score(
                                                                                               self.next_player),
                                                                                           str([c.name for c in
                                                                                                self.next_player.hand]))
        else:
            return "Final score:\n" + '\n'.join('{}: {}'.format(player, player.score) for player in self.players) + \
                   "\n{} Wins!".format(max((p for p in self.players), key=lambda x: x.score).name)

    def __repr__(self):
        return str(self.board) + "\n\n" + self.statement()


class StartGameState(GameState):
    def __init__(self, board=None, players=None):
        if board is None:
            board = Board(empty="Default")
        if players is None:
            players = [HumanPlayer('Matt', chr(9829)),
                       HumanPlayer('F. Rob', chr(9830)),
                       HumanPlayer('Rob H.', chr(9827))]
        super().__init__(board, players, [], 0, False)


class Game:
    def __init__(self, game_state, fname='', save=1, load=1, autostart=True):
        if fname != '':
            self.fname = fname
            self.save = save
            if load:
                try:
                    game_state = self.load()
                except FileNotFoundError:
                    print('No file {} found. Using input GameState'.format(fname))
        else:
            self.save = 0
            self.fname = 'err.pi'

        self.board = game_state.board
        self.players = game_state.players
        self.plyhistory = game_state.plyhistory
        self.p_turn = game_state.p_turn
        self.gameover = game_state.gameover

        self.plyhistory = []

        if self.save:
            self.dump()

        if autostart:
            self.gameloop()

    def gameloop(self):
        while not self.gameover:
            if PRINT:
                print()
                print('\n'.join('{}: {}'.format(player, player.score) for player in self.players))
                print(self.get_game_state())
            self.turn()

    def turn(self):
        self.gameover = False

        player = self.players[self.p_turn]

        while True:
            ply = player.make_move(self.get_game_state())

            card = player.in_hand(ply.card)
            if not card:
                return 'Please pick card again'
            else:
                break

        if PRINT:
            # noinspection PyUnboundLocalVariable
            print(ply)

        error = self.make_move(ply)
        return error

    def online_turn(self, card, row, column):
        t = time.time()
        self.gameover = False

        player = self.players[self.p_turn]
        if not player.AI:
            card = player.in_hand(card)
            if not card:
                return 'Please pick card again'
            ply = Ply(card, row, column)
            error = self.make_move(ply)
        else:
            # Catch and procede when starting from AI player.
            error = "Done"

        # Loop through AI turns
        while error == "Done" and self.players[self.p_turn].AI and not self.gameover:
            player = self.players[self.p_turn]
            print(player, 'turn')
            ply = player.make_move(self.get_game_state())
            error = self.make_move(ply)
            # Timeout
            if time.time() - t > 5:
                break

        return error

    def make_move(self, ply):
        player = self.players[self.p_turn]
        discard, error = self.board.update(ply)
        self.plyhistory.append((ply, discard))
        if error:
            if player.AI:
                raise Exception("AI error: {} trying {} in\n{}".format(error, ply, self.board))
            else:
                return error
        else:
            player.play(ply.card)

            self.p_turn = (self.p_turn + 1) % len(self.players)

            next_player = self.players[self.p_turn]

            if not next_player.hand:
                self.final()
            else:
                next_player.alter_score(self.board.score(next_player))

            if self.save:
                self.dump()
            return 'Done'

    def test_move(self, ply, p_turn, alter_scores):
        player = self.players[p_turn]
        discard, error = self.board.update(ply, test=1)
        # self.plyhistory.append((ply, discard))
        if error:
            if player.AI:
                raise Exception("AI error: {} trying {} in\n{}".format(error, ply, self.board))
            else:
                return error
        else:
            # player.play(ply.card)
            ply.card.played = True
            p_turn = (p_turn + 1) % len(self.players)

            next_player = self.players[p_turn]

            if not next_player.hand or not any(not c.played for c in next_player.hand):
                for player in self.players:
                    alter_scores[player] += self.board.score(player)
                gameover = 1
            else:
                alter_scores[next_player] += self.board.score(next_player)
                gameover = 0

            # if self.save:
            #     self.dump()
            return alter_scores, p_turn, gameover, discard

    # def unmake_move(self):
    #     player = self.players[self.p_turn]
    #     (unply, undiscard) = self.plyhistory.pop()
    #     if self.gameover:
    #         self.unfinal()
    #     else:
    #         player.alter_score(-self.board.score(player))
    #
    #     self.p_turn = (self.p_turn - 1) % len(self.players)
    #     lastplayer = self.players[self.p_turn]
    #
    #     lastplayer.unplay(unply.card)
    #     undiscard, error = self.board.update(unply, True, undiscard)
    #     if error:
    #         raise Exception("Unmake move error")
    #     if self.save:
    #         self.dump()
    #     return unply

    def final(self):
        self.gameover = True
        if PRINT:
            print('\n'.join('{}: {}'.format(player, player.score) for player in self.players))
        for player in self.players:
            score = self.board.score(player)
            player.alter_score(score)

        self.board.finalise()
        if PRINT:
            print('Final score:')
            print('\n'.join('{}: {}'.format(player, player.score) for player in self.players))
        if self.save:
            self.dump()
        return self.get_game_state().statement()

    def unfinal(self):
        self.gameover = False
        self.board.unfinalise()
        for player in self.players:
            score = self.board.score(player)
            player.alter_score(-score)
        if self.save:
            self.dump()
        return True

    def get_game_state(self):
        return GameState(self.board, self.players, self.plyhistory, self.p_turn, self.gameover)

    def dump(self):
        with open(self.fname, 'wb') as f:
            pickle.dump(self.get_game_state(), f)

    def load(self):
        with open(self.fname, 'rb') as f:
            return pickle.load(f)


#
# def AI_on_off(player_n, ai_on, self.fname='curling.pi'):
#     board, players, discarded, p_turn, statement = load(self.fname)
#     players[player_n].AI = ai_on
#     dump(board, players, discarded, p_turn, statement, self.fname)
#
#


def main(fname='curling.pi'):
    t = time.time()
    board = Board(empty="Default")
    players = [AITreeSearch('Matt', chr(9829), 2),
               AITreeSearch('F. Rob', chr(9830), 2),
               AITreeSearch('Rob H.', chr(9827), 2)]
    game_state = StartGameState(board, players)
    Game(game_state, fname=fname, save=0, load=0)
    print("\nTime is:", time.time() - t)


def averages(runs):
    global PRINT
    PRINT = False
    results = []
    for _ in range(runs):
        results.append(main())

    end = [0, 0, 0]
    diff = [0, 0, 0]
    av_m = []
    for a, b, c in results:
        m = max(a, b, c)
        if a == m:
            end[0] += 1
        if b == m:
            end[1] += 1
        if c == m:
            end[2] += 1

        diff[0] += a - b
        diff[1] += b - c
        diff[2] += c - a
        av_m.append(m)

    print(end)
    for i in range(3):
        diff[i] /= runs
    for i in range(len(results[0])):
        print(sum(x[i] for x in results) / runs)

    print(diff)
    print(sum(av_m) / runs)


if __name__ == '__main__':
    PRINT = True
    main()
