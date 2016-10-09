import pickle
import random


PRINT = False


class Card:
    def __init__(self, name, suit):
        self.name = str(name)
        if self.name == '10':
            self.name = '0'  # For spacing
        if name in ['*', 'Jkr']:
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

    # def __eq__(self, other):
    #     return self.name == other.name and self.suit == other.suit and self.value == other.value and \
    # self.played == other.played and self.discarded == other.discarded

    def __repr__(self):
        return '{} {}'.format(self.name, self.suit)


class Joker(Card):
    def __init__(self):
        super().__init__('Jkr', '')
        self.played = True
        self.discarded = False

    def __repr__(self):
        return self.name


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
            self._cards[x][y] = ''
        self.scoring_pos = {1: [(self.joker_pos - 1, self.joker_pos - 1), (self.joker_pos - 1, self.joker_pos + 1),
                                (self.joker_pos + 1, self.joker_pos - 1), (self.joker_pos + 1, self.joker_pos + 1)],
                            2: [(self.joker_pos - 1, self.joker_pos), (self.joker_pos, self.joker_pos - 1),
                                (self.joker_pos + 1, self.joker_pos), (self.joker_pos, self.joker_pos + 1)]}

    @property
    def cards(self):
        # Slice rows for copy of all lists
        return [r[:] for r in self._cards]

    def finalise(self):
        self._final = 1

    @property
    def final(self):
        return self._final

    def get_empty(self):
        if any(not x for r in self._cards for x in r):
            return [(r + 1, c + 1) for r in range(self.size) for c in range(self.size) if not self._cards[r][c]]
        else:
            return []

    def score(self, suit):
        out = 0
        if not self._final:
            for s, l in self.scoring_pos.items():
                for x, y in l:
                    if self._cards[x][y] and self._cards[x][y].suit == suit:
                        out += s * self._cards[x][y].value
        return out

    # noinspection PyUnboundLocalVariable
    def update(self, card, row, column):
        """Starting from the outside left as column 0, top as row 0, place your card outisde the space you want to
        insert it, e.g. 0, 2 to insert from the left into the second row"""
        error = ''
        if any(not x for row in self._cards for x in row):
            l = self.get_empty()
            if (row, column) not in l:
                if PRINT:
                    print('Please choose from empty cells', l)
                discarded = ''
                error = 'Please choose from empty cells {}'.format(l)
            else:
                self._cards[row - 1][column - 1] = card
                discarded = 'Insert'  # Evaluates True for move, no card actually discarded.
            # Return is important here
            return discarded, error

        if 0 < row <= self.size:
            card_row = self._cards[row - 1]
            if column == 0:
                discarded = card_row[-1]
                if row == self.joker_pos + 1:
                    new_row = [card] + card_row[:self.joker_pos - 1] + [self.joker] + [card_row[self.joker_pos - 1]] \
                              + card_row[self.joker_pos + 1:-1]
                else:
                    new_row = [card] + card_row[:-1]
            elif column == self.size + 1:
                discarded = card_row[0]
                if row == self.joker_pos + 1:
                    new_row = card_row[1:self.joker_pos] + [card_row[self.joker_pos + 1]] + [self.joker] + \
                              card_row[self.joker_pos + 2:] + [card]
                else:
                    new_row = card_row[1:] + [card]
            else:
                discarded = ''
                if PRINT:
                    print('Invalid row/column')
                error = 'Invalid row/column'
            if discarded:
                # noinspection PyUnboundLocalVariable
                self._cards[row - 1] = new_row
        elif 0 < column <= self.size:
            if row == 0:
                discarded = self._cards[self.size - 1][column - 1]
                if column == self.joker_pos + 1:
                    # Move cards down one row
                    for i, card_row in enumerate(self._cards[:self.joker_pos + 1:-1], start=2):
                        card_row[column - 1] = self._cards[self.size - i][column - 1]
                    self._cards[self.size - i][column - 1] = self._cards[self.size - i - 2][column - 1]  # Skip joker
                    for i, card_row in enumerate(self._cards[self.joker_pos - 1:0:-1], start=i + 3):
                        card_row[column - 1] = self._cards[self.size - i][column - 1]
                else:
                    for i, card_row in enumerate(self._cards[:0:-1], start=2):  # Move cards down one row
                        card_row[column - 1] = self._cards[self.size - i][column - 1]
                self._cards[0][column - 1] = card
            elif row == self.size + 1:
                discarded = self._cards[self.size - 1][0]
                if column == self.joker_pos + 1:
                    for i, card_row in enumerate(self._cards[:self.joker_pos - 1], start=1):  # Move cards up one row
                        card_row[column - 1] = self._cards[i][column - 1]
                    self._cards[i][column - 1] = self._cards[i + 2][column - 1]  # Skip joker
                    for i, card_row in enumerate(self._cards[self.joker_pos + 1:-1], start=i + 3):
                        card_row[column - 1] = self._cards[i][column - 1]
                else:
                    for i, card_row in enumerate(self._cards[:-1], start=1):  # Move cards up one row
                        card_row[column - 1] = self._cards[i][column - 1]
                self._cards[self.size - 1][column - 1] = card
            else:
                discarded = ''
                if PRINT:
                    print('Invalid row/column')
                error = 'Invalid row/column'
        else:
            if PRINT:
                print('Invalid row/column')
            error = 'Invalid row/column'
            discarded = ''
        if discarded:
            discarded.discarded = True  # Set card attribute
        return discarded, error

    def __repr__(self):
        out = []
        for row in self._cards:
            line = []
            for card in row:
                if not card:
                    line.append('   ')
                else:
                    line.append(str(card))
            out.append(' | '.join(line))
        return '\n'.join(out)
        #  return '\n'.join(' '.join(str(card) for card in rows) for rows in self._cards) + '\n'


class AiBoard(Board):
    def __init__(self, board):
        super().__init__(board.size)

    def test(self, board, card, row, column, suits):
        # Copys current actual board and tests an update
        self._cards = board.cards
        self.update(card, row, column)

        return [self.score(suit) for suit in suits]


class Player:
    # noinspection PyTypeChecker
    def __init__(self, name, suit, ai=False, gm=0):
        self.score = 0
        self.name = name
        self.suit = suit
        l = ['K', 'Q', 'J', 'A'] + list(range(2, 11))
        self.hand = [Card(i, suit) for i in l]
        self.ai = ai
        self.gm = gm

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

    def __repr__(self):
        if self.ai:
            return 'ai - {} ({})'.format(self.name, self.suit)
        else:
            return '{} ({})'.format(self.name, self.suit)


def dump(board, players, discarded, p_turn, statement, fname):
    with open(fname, 'wb') as f:
        pickle.dump(board, f)
        pickle.dump(players, f)
        pickle.dump(discarded, f)
        pickle.dump(p_turn, f)
        pickle.dump(statement, f)


def load(fname):
    with open(fname, 'rb') as f:
        board = pickle.load(f)
        players = pickle.load(f)
        discarded = pickle.load(f)
        p_turn = pickle.load(f)
        statement = pickle.load(f)
    return board, players, discarded, p_turn, statement


def setup(fname='curling.pi', save=1):
    names = ['Matt', 'F. Rob', 'Rob H.']
    suits = [chr(9829), chr(9830), chr(9827)]
    players = [Player(n, s) for n, s in zip(names, suits)]
    board = Board()
    discarded = []
    p_turn = 0
    player = players[p_turn]
    statement, score = statement_and_score(board, player)
    if save:
        dump(board, players, discarded, p_turn, statement, fname)
    return board, players, discarded, p_turn, statement


def information(fname='curling.pi'):
    board, players, discarded, p_turn, statement = load(fname)
    if not any(x.hand for x in players):
        statement = final(fname)
    elif players[p_turn].ai:
        random_ai_turn(players[p_turn], board, players, discarded, p_turn, statement)
        # For more ai
        information(fname)
        board, players, discarded, p_turn, statement = load(fname)
        if PRINT:
            print(board)
            print('\n'.join('{}: {}'.format(player, player.score) for player in players))
            print(statement)

    return board, '\n'.join('{}: {}'.format(player, player.score) for player in players), statement


def statement_and_score(board, next_player):
    score = board.score(next_player.suit)
    statement = "{}'s turn\nThey score {} points\nThey have in their hand:\n{}".format(next_player, score,
                                                                                       str([c.name for c in
                                                                                            next_player.hand]))

    return statement, score


def turn(card, row, column, save=1, fname='curling.pi', data=None):
    if data:
        board, players, discarded, p_turn, statement = data
    else:
        board, players, discarded, p_turn, statement = load(fname)
    player = players[p_turn]
    # #print('Statement')
    # while 1:
    #    card = input('Pick a card:')
    if card == '10':
        card = '0'
    card = player.in_hand(card)
    if not card:
        return 'Please pick card again'
    # while 1:
    #    row = input('Pick row:')
    #    column = input('Pick column:')
    #    try:
    #        row = int(row)
    #        column = int(column)
    #    except ValueError:
    #        #print('Please use integers')
    #        continue
    discard, error = board.update(card, row, column)
    if discard:
        if discard != 'Insert':
            discarded.append(discard)
        player.play(card)

        for p_turn, p in enumerate(players):
            if p.name == player.name:
                break
        if p_turn == len(players) - 1:
            p_turn = 0
        else:
            p_turn += 1
        next_player = players[p_turn]

        statement, score = statement_and_score(board, next_player)
        next_player.score += score

        if save:
            dump(board, players, discarded, p_turn, statement, fname)
        return 'Done'
    return error


def final(fname='curling.pi', data=None, save=1):
    if not data:
        data = load(fname)
    board, players, discarded, p_turn, statement = data
    if not board.final:
        if PRINT:
            print('\n'.join('{}: {}'.format(player, player.score) for player in players))
        for player in players:
            score = board.score(player.suit)
            player.score += score
    statement = "Final score:\n" + '\n'.join('{}: {}'.format(player, player.score) for player in players) + \
                "\n{} Wins!".format(max((p for p in players), key=lambda x: x.score).name)
    board.finalise()
    if PRINT:
        print(statement)
    if save:
        dump(board, players, discarded, p_turn, statement, fname)
    return statement


def text_turn(player, board, players, discarded, p_turn, statement):
    while 1:
        while 1:
            card = input('Pick a card:')
            if card == '10':
                card = '0'
            # card = player.in_hand(card)
            if player.in_hand(card):
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
        message = turn(card, row, column, save=0, data=[board, players, discarded, p_turn, statement])
        if message == "Done":
            return "Done"


# Random AI
def random_ai_turn(player, board, players, discarded, p_turn, statement, save=1):
    if player.hand:
        # card = random.choice(player.hand)
        card = max(player.hand, key=lambda x: x.value)
    else:
        raise Exception("Empty Hand")
    # print(card)
    empty = board.get_empty()
    min_choice = 2 if player.gm == "r2" else 1
    if player.gm == "r1":
        max_choice = 3
    elif player.gm == "r2":
        max_choice = 4
    else:
        max_choice = board.size
    if empty:
        # An initial choice, may be overridden
        row, column = random.choice(empty)
        if player.gm:
            e1 = [(r, c) for (r, c) in empty if min_choice <= r <= max_choice and min_choice <= c <= max_choice]
            if e1:
                row, column = random.choice(e1)
            else:
                ec = [(r, c) for (r, c) in empty if min_choice <= c <= max_choice]
                er = [(r, c) for (r, c) in empty if min_choice <= r <= max_choice]
                insert = random.choice(('R', 'C'))
                if er and (insert == 'R' or not ec):
                    row, column = random.choice(er)
                elif ec:
                    row, column = random.choice(ec)

    else:
        insert = random.choice(('R', 'C'))
        if insert == "R":
            row = random.choice((0, board.size + 1))
            column = random.randint(min_choice, max_choice)
        else:
            column = random.choice((0, board.size + 1))
            row = random.randint(min_choice, max_choice)

    message = turn(card, row, column, save=save, data=[board, players, discarded, p_turn, statement])
    if message != "Done":
        raise Exception("ai error")


def one_set_ai(player, board, players, discarded, p_turn, statement, save=1):
    ai_board = AiBoard(board)
    suits = [p.suit for p in players]
    if player.hand:
        # Card don't score immediately, might as well be high
        cards = [max(player.hand, key=lambda x: x.value)]
        # cards = [c for c in player.hand if c.value != 10]
        # c10 = [c for c in player.hand if c.value == 10]
        # #  Only one value 10 card to evaluate later
        # if c10:
        #     cards.append(c10[0])
    else:
        raise Exception("Empty Hand")
    empty = board.get_empty()
    if empty:
        choices = empty
    else:
        choices = [(0, i + 1) for i in range(board.size)] + [(6, i + 1) for i in range(board.size)] + \
                  [(i + 1, 0) for i in range(board.size)] + [(i + 1, 6) for i in range(board.size)]
    best = [(cards[0], choices[0][0], choices[0][1])]
    best_score = 0
    for card in cards:
        for r, c in choices:
            scores = ai_board.test(board, card, r, c, suits)
            score = 2 * scores[p_turn] - sum(scores)
            if score > best_score:
                best = [(card, r, c)]
                best_score = score
            elif score == best_score:
                best.append((card, r, c))
    card, row, column = random.choice(best)
    message = turn(card, row, column, save=save, data=[board, players, discarded, p_turn, statement])
    if message != "Done":
        raise Exception("ai error")


def ai_on_off(player_n, ai_on, fname='curling.pi'):
    board, players, discarded, p_turn, statement = load(fname)
    players[player_n].ai = ai_on
    dump(board, players, discarded, p_turn, statement, fname)


def main(ai=(0, 0, 0), gm=(0, 0, 0), fname='curling.pi'):
    board, players, discarded, p_turn, statement = setup(fname, save=0)
    players[0].ai = ai[0]
    players[1].ai = ai[1]
    players[2].ai = ai[2]
    players[0].gm = gm[0]
    players[1].gm = gm[1]
    players[2].gm = gm[2]
    while players[0].hand:
        if PRINT:
            print('\n'.join('{}: {}'.format(player, player.score) for player in players))
        for player in players:
            for p_turn, p in enumerate(players):
                if p.name == player.name:
                    break
            if PRINT:
                print(board)
                print(statement_and_score(board, player)[0])
            if not player.ai:
                text_turn(player, board, players, discarded, p_turn, statement)
            else:
                if "r" in player.gm:
                    random_ai_turn(player, board, players, discarded, p_turn, statement, save=0)
                else:
                    one_set_ai(player, board, players, discarded, p_turn, statement, save=0)
    final(data=[board, players, discarded, p_turn, statement], save=0)
    return [p.score for p in players]


def averages(runs, gm=(0, 0, 0)):
    global PRINT
    PRINT = False
    results = []
    for _ in range(runs):
        results.append(main((1, 1, 1), gm))

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

    print("Wins", end)
    print("Av score")
    for i in range(3):
        diff[i] /= runs
    for i in range(len(results[0])):
        print(sum(x[i] for x in results) / runs)

    print("Margins:", diff)
    print("Av winning score:", sum(av_m) / runs)
    print()


if __name__ == '__main__':
    for _ in range(5):
        averages(1000, ("", "", ""))
        # gm_l = [("r", "", "r"), ("r", "", ""), ("", "", "r"), ("r", "r", ""), ("", "r", ""), ("", "r", "r")]
        # for gm in gm_l:
        #     print(gm)
        #     averages(1000, gm)
    # PRINT = 1
    # main((1,0,1), ("", "", ""))
