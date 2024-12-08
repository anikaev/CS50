import itertools
import random


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        # Если число мин равно количеству ячеек, то все ячейки — мины.
        if len(self.cells) == self.count and self.count > 0:
            return set(self.cells)
        return set()

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        # Если count == 0, то все ячейки безопасны
        if self.count == 0:
            return set(self.cells)
        return set()

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell in self.cells:
            self.cells.remove(cell)



class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        if cell in self.mines:
            return
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        if cell in self.safes:
            return
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.

        This function should:
            1) mark the cell as a move that has been made
            2) mark the cell as safe
            3) add a new sentence to the AI's knowledge base
               based on the value of cell and count
            4) mark any additional cells as safe or as mines
               if it can be concluded based on the AI's knowledge base
            5) add any new sentences to the AI's knowledge base
               if they can be inferred from existing knowledge
        """
        # 1) Mark cell as move made
        self.moves_made.add(cell)
        # 2) Mark cell as safe
        self.mark_safe(cell)

        # Determine neighbors
        (i, j) = cell
        neighbors = set()
        for r in range(i - 1, i + 2):
            for c in range(j - 1, j + 2):
                if (r, c) != (i, j) and 0 <= r < self.height and 0 <= c < self.width:
                    neighbors.add((r, c))

        # Adjust for known mines and safes
        adjusted_count = count
        adjusted_neighbors = set()
        for n in neighbors:
            if n in self.mines:
                adjusted_count -= 1
            elif n not in self.safes:
                adjusted_neighbors.add(n)

        # 3) Add new sentence
        if len(adjusted_neighbors) > 0:
            new_sentence = Sentence(adjusted_neighbors, adjusted_count)
            self.knowledge.append(new_sentence)

        # Обновляем знания, пока можем
        self.update_knowledge()

    def update_knowledge(self):
        changed = True
        while changed:
            changed = False

            # Сначала попробуем вывести известные мины и безопасные клетки
            known_mines = set()
            known_safes = set()

            for sentence in self.knowledge:
                # Если предложение пустое, пропускаем
                if len(sentence.cells) == 0:
                    continue

                # Определяем известные мины и безопасные клетки
                for m in sentence.known_mines():
                    known_mines.add(m)
                for s in sentence.known_safes():
                    known_safes.add(s)

            # Помечаем найденные мины и безопасные клетки
            if known_mines:
                for m in known_mines:
                    if m not in self.mines:
                        self.mark_mine(m)
                        changed = True
            if known_safes:
                for s in known_safes:
                    if s not in self.safes:
                        self.mark_safe(s)
                        changed = True

            # Удаляем пустые или повторяющиеся предложения
            temp_knowledge = []
            for s in self.knowledge:
                if len(s.cells) > 0 and s not in temp_knowledge:
                    temp_knowledge.append(s)
            self.knowledge = temp_knowledge

            # Теперь пытаемся вывести новые предложения через подмножества
            new_sentences = []
            for s1 in self.knowledge:
                for s2 in self.knowledge:
                    if s1 == s2:
                        continue
                    # Проверяем, что s1 - подмножество s2
                    if s1.cells.issubset(s2.cells):
                        diff = s2.cells - s1.cells
                        diff_count = s2.count - s1.count
                        if len(diff) > 0:
                            new_s = Sentence(diff, diff_count)
                            if new_s not in self.knowledge and new_s not in new_sentences:
                                new_sentences.append(new_s)

            if new_sentences:
                self.knowledge.extend(new_sentences)
                changed = True

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        """
        for cell in self.safes:
            if cell not in self.moves_made:
                return cell
        return None

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        """
        all_cells = {(i, j) for i in range(self.height) for j in range(self.width)}
        possible_moves = list(all_cells - self.moves_made - self.mines)
        if len(possible_moves) == 0:
            return None
        return random.choice(possible_moves)

