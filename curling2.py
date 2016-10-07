import pickle
import random
import copy

PRINT = True


class Card:
    def __init__(self, name, suit):
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
    def __init__(self):
        super().__init__(' ', ' ')
        self.played = True
        self.discarded = False

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
        for x, y in empty:
            self._cards[x][y] = BlankCard()
        self.scoring_pos = [(1, [(self.joker_pos - 1, self.joker_pos - 1), (self.joker_pos - 1, self.joker_pos + 1),
                                 (self.joker_pos + 1, self.joker_pos - 1), (self.joker_pos + 1, self.joker_pos + 1)]),
                            (2, [(self.joker_pos - 1, self.joker_pos), (self.joker_pos, self.joker_pos - 1),
                                 (self.joker_pos + 1, self.joker_pos), (self.joker_pos, self.joker_pos + 1)])]

        self.first_turn = False

    @property
    def cards(self):
        return [r[:] for r in self._cards]

    def finalise(self):
        self._final = 1

    def unfinalise(self):
        self._final = 0

    def get_empty(self):
        if any(not x for r in self._cards for x in r):
            return [(r + 1, c + 1) for r in range(self.size) for c in range(self.size) if not self._cards[r][c]]
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
            raise Exception('Trying to score points on a finalised board for {}'.format(player.name))
        return out

    def update(self, ply, undo=False, undiscard=''):
        '''Starting from the outside left as column 0, top as row 0, place your card outisde the space you want to
        insert it, e.g. 0, 2 to insert from the left into the second row'''
        if undo and undiscard == '':
            raise Exception('Trying to undo a ply without a card to reinstate')
        if undo:
            card = undiscard
        else:
            card = ply.card

        error = ''
        empty = self.get_empty()
        if empty and not undo:
            if (ply.row, ply.column) not in empty:
                if PRINT:
                    print('Please choose from empty cells', empty)
                discarded = ''
                error = 'Please choose from empty cells {}'.format(empty)
            else:
                discarded, self._cards[ply.row - 1][ply.column - 1] = self._cards[ply.row - 1][ply.column - 1], card
                if len(self.get_empty()) == 0:
                    self.first_turn = True
                # discarded = 'Insert'  # Evaluates True for move, no card actually discarded.
            # Return is important here
            return discarded, error
        elif undo and isinstance(undiscard, BlankCard):
            self._cards[ply.row - 1][ply.column - 1] = undiscard
            self.first_turn = False
            return 'undo', error

        # Check insertion condition, determine if a row or column is being inserted to
        if 0 < ply.row <= self.size and ply.column in (0, self.size + 1):
            tempcards = self._cards
            ins_row = True  # row or column?
            ins_left = (ply.column == 0) ^ undo  # left(top) or right(bottom)? (reverse if undoing)
            ins_pos = ply.row  # row(col) index
        elif 0 < ply.column <= self.size and ply.row in (0, self.size + 1):
            # treat row and column insertion the same by transposing the card list for one of them
            tempcards = [x for x in map(list, zip(*self._cards))]
            # column insertion
            ins_row = False
            ins_left = (ply.row == 0) ^ undo
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

        discarded.discarded = (not undo)  # Set card attribute
        self.first_turn = False
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
        return repr(self.card) + " at " + str(self.row) + ", " + str(self.column)


class Player:
    def __init__(self, name, suit):
        self.score = 0
        self.name = name
        self.suit = suit
        l = ['K', 'Q', 'J', 'A'] + list(range(2, 11))
        self.hand = [Card(i, suit) for i in l]

        self.AI = False

        self.postinit()  # hook for inheriting classes

    def postinit(self):
        pass

    def in_hand(self, card):
        for c in self.hand:
            if c.name == card or c == card:
                return c
                # return any(c.name == card for c in self.hand) or card in self.hand

    def play(self, card):
        if not self.in_hand(card):
            raise Exception('Card {} not in hand'.format(card))
        for i, c in enumerate(self.hand):
            if c.name == card or c == card:  # Either by name or card instance
                c.played = True
                del self.hand[i]
                return True
        raise Exception('Card not removed')

    def unplay(self, card):
        if self.in_hand(card):
            raise Exception('Card {} already in hand during tree backtrack'.format(card))
        if card != '':
            card.played = False
        self.hand.append(card)
        return True

    def alter_score(self, delta):
        if delta > 500:
            raise Exception('Trying to add score above 500')
        self.score += delta
        return self.score

    # To be implemented by inheriting classes
    def make_move(self, board, players, discarded, p_turn, statement):
        pass

    def __repr__(self):
        return '{} ({})'.format(self.name, self.suit)


class HumanPlayer(Player):
    def postinit(self):
        self.AI = False

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
            return Ply(card, row, column)


class AIPlayer(Player):
    def postinit(self):
        self.AI = True

    def make_move(self, game_state):
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
    def postinit(self):
        self.AI = True
        self.depth = 4  # tree search depth (plies)
        self.t_game = []  # to hold the local version of the game

    def make_move(self, game_state):
        # entry point
        global PRINT
        PRINT = False
        print("Enter AITree make_move")
        # create local version of the game without letting it enter its game loop
        self.t_game = Game(game_state, autostart=False)  # copy.deepcopy(Game(game_state, autostart = False))

        # do a tree search recursively to find the best ply and its expected scores
        bestscores, bestply = self.tree_search(self.t_game, 2)

        # point the resulting card object to the actual card in the real game
        for card in self.hand:
            if card.name == bestply.card.name:
                bestply.card = card
        print("Exit AITree make_move, best scores: ", bestscores)
        PRINT = True
        return bestply

    # given a game state, generate all the moves the current player could make
    def enum_plies(self, game):
        # assuming we have cards left to play
        player = game.players[game.p_turn]
        card_options = sorted(player.hand, key=lambda x: -x.value)  # cards ordered high-low
        empty = game.board.get_empty()
        if empty:
            rowcol_options = empty
        else:
            bsize = game.board.size
            rowcol_options = [(0, i) for i in range(1, bsize + 1)] + \
                             [(bsize + 1, i) for i in range(1, bsize + 1)] + \
                             [(i, 0) for i in range(1, bsize + 1)] + \
                             [(i, bsize + 1) for i in range(1, bsize + 1)]

        # just choose the highest value card for now
        card_choice = card_options[0]

        for rowcol in rowcol_options:
            yield Ply(card_choice, rowcol[0], rowcol[1])

    # recursive search of future moves to the given depth
    def tree_search(self, game, depth):
        plyvalues = []
        p_turn = game.p_turn
        plies = self.enum_plies(game)
        best = ''
        bestply = ''
        for ply in plies:
            stored_cards = game.board.cards
            game.make_move(ply)
            if game.gameover:
                depth = 0

            if depth == 0:
                node_value = self.heuristic_eval(game)
            else:
                node_value = self.tree_search(game, depth - 1)[0]

            unply = game.unmake_move()
            assert ply == unply, 'Mismatch plies {} {}'.format(ply, unply)
            assert stored_cards == game.board.cards, "Game board cards don't match\n{}\n{}".format(stored_cards, game.board.cards)
            if best == '' or node_value[p_turn] > best[p_turn]:
                best = node_value
                bestply = ply

        return best, bestply

    # returns the value of the current game for each player in a three-item list
    # trying to take into account immediate future moves without doing a tree search
    # (so that this evaluation doesn't favour the player who just played)
    def heuristic_eval(self, game):
        if not game.gameover:
            values = [0] * len(game.players)
            for i, player in enumerate(game.players):
                waittime = (i - game.p_turn) % len(game.players)  # plies until your next ply
                score = player.score
                boardscore = game.board.score(player) * (4 - waittime)  # how good the board is
                # add some value for cards not currently in scoring positions
                for row, x in enumerate(game.board.cards):
                    for column, card in enumerate(x):
                        if card != '' and card.suit == player.suit:
                            if row in (2, 3, 4) or column in (2, 3, 4):
                                boardscore += 0.5 * card.value
                            else:
                                boardscore += 0.2 * card.value

                # point difference with the best player other than yourself
                pointdiff = score - max([x.score for x in game.players if x.name != player.name])

                hand_potential = sum([c.value for c in player.hand])
                values[i] = pointdiff + 0.2 * boardscore + 0.5 * hand_potential
        else:
            maxscore = 0
            winner_ids = []
            for i, player in enumerate(game.players):
                if player.score > maxscore:
                    maxscore = player.score
                    winner_ids = [i]
                elif player.score == maxscore:
                    winner_ids.append(i)
            # losers have a large negative score
            values = [-10000] * len(game.players)
            # winner has a large positive score
            # TODO: Should joint winners have lower score?
            for i in winner_ids:
                values[i] = 10000

        return values


# the information which players are sent to make their move
class GameState:
    def __init__(self, board, players, discarded, p_turn, gameover):
        self.board = board
        self.players = players
        self.discarded = discarded
        self.p_turn = p_turn
        self.next_player = self.players[self.p_turn]
        self.gameover = gameover

    def statement(self):
        if not self.gameover:
            return "{}'s turn\nThey scored {} points\nThey have in their hand:\n{}".format(self.next_player,
                        self.board.score(self.next_player),
                        str([c.name for c in self.next_player.hand]))
        else:
            return "Final score:\n" + '\n'.join('{}: {}'.format(player, player.score) for player in self.players) + \
                   "\n{} Wins!".format(max((p for p in self.players), key=lambda x: x.score).name)

    def __repr__(self):
        return repr(self.board) + "\n\n" + self.statement()


class StartGameState(GameState):
    def __init__(self, board, players):
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
                    print('No file {} found. Using input GameState')
        else:
            self.save = 0
            self.fname = 'err.pi'

        self.board = game_state.board
        self.players = game_state.players
        self.discarded = game_state.discarded
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
                print('\n'.join('{}: {}'.format(player, player.score) for player in self.players))
            if PRINT:
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
            print(ply)

        error = self.make_move(ply)
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
            self.discarded.append(discard)
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

    def unmake_move(self):
        player = self.players[self.p_turn]
        (unply, undiscard) = self.plyhistory.pop()
        self.discarded.pop()
        if self.gameover:
            self.unfinal()
        else:
            player.alter_score(-self.board.score(player))

        self.p_turn = (self.p_turn - 1) % len(self.players)
        lastplayer = self.players[self.p_turn]

        lastplayer.unplay(unply.card)
        undiscard, error = self.board.update(unply, True, undiscard)
        if error:
            raise Exception("Unmake move error")
        if self.save:
            self.dump()
        return unply

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
        return GameState(self.board, self.players, self.discarded, self.p_turn, self.gameover)

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
    board = Board(empty="Default")
    players = [AITreeSearch('Matt', chr(9829)),
               AITreeSearch('F. Rob', chr(9830)),
               AITreeSearch('Rob H.', chr(9827))]
    game_state = StartGameState(board, players)
    game = Game(game_state, fname=fname, save=0, load=0)


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
