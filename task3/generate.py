import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Обновляет `self.domains`, чтобы каждая переменная была согласована с узлом.
        (Удаляет любые значения, которые не соответствуют унарным ограничениям переменной;
         в данном случае, длине слова.)
        """
        for var in self.crossword.variables:
            words_to_remove = set()
            for word in self.domains[var]:
                if len(word) != var.length:
                    words_to_remove.add(word)
            self.domains[var] -= words_to_remove

    def revise(self, x, y):
        """
        Делает переменную `x` согласованной с переменной `y`.
        Удаляет значения из `self.domains[x]`, для которых нет соответствующих
        значений в `self.domains[y]`.
        Возвращает True, если произошло изменение домена `x`, иначе False.
        """
        revised = False
        overlap = self.crossword.overlaps.get((x, y))

        if overlap is None:
            return False

        i, j = overlap

        words_to_remove = set()
        for word_x in self.domains[x]:
            # Проверяем, существует ли слово в домене y, которое соответствует
            if not any(word_x[i] == word_y[j] for word_y in self.domains[y]):
                words_to_remove.add(word_x)
                revised = True

        if revised:
            self.domains[x] -= words_to_remove

        return revised

    def ac3(self, arcs=None):
        """
        Обеспечивает согласованность дуг для всех переменных.
        Если `arcs` не задано, инициализирует очередь всеми дугами.
        Возвращает True, если согласованность обеспечена и домены не пусты;
        иначе False.
        """
        if arcs is None:
            # Инициализация очереди всеми дугами
            queue = []
            for x in self.crossword.variables:
                for y in self.crossword.neighbors(x):
                    queue.append((x, y))
        else:
            queue = list(arcs)

        while queue:
            (x, y) = queue.pop(0)  # Используем pop(0) для очереди
            if self.revise(x, y):
                if not self.domains[x]:
                    return False
                for z in self.crossword.neighbors(x):
                    if z != y:
                        queue.append((z, x))
        return True

    def assignment_complete(self, assignment):
        """
        Возвращает True, если `assignment` завершено (каждой переменной присвоено слово);
        иначе False.
        """
        return len(assignment) == len(self.crossword.variables)

    def consistent(self, assignment):
        """
        Возвращает True, если `assignment` согласовано (слова уникальны, соответствуют длине переменных и пересечениям);
        иначе False.
        """
        words = set()
        for var, word in assignment.items():
            # Проверка уникальности слов
            if word in words:
                print(f"Слово '{word}' используется более одного раза.")
                return False
            words.add(word)

            # Проверка длины слова
            if len(word) != var.length:
                print(
                    f"Слово '{word}' не соответствует длине переменной {var}. Ожидалась длина {var.length}, а получена {len(word)}.")
                return False

            # Проверка пересечений
            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    overlap = self.crossword.overlaps.get((var, neighbor))
                    if overlap:
                        i, j = overlap
                        if word[i] != assignment[neighbor][j]:
                            print(
                                f"Несоответствие в пересечении между переменными {var} и {neighbor}: '{word[i]}' != '{assignment[neighbor][j]}'")
                            return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Возвращает список значений домена `var`, отсортированных по числу исключений для соседних переменных.
        """
        def count_conflicts(word):
            count = 0
            for neighbor in self.crossword.neighbors(var):
                if neighbor not in assignment:
                    overlap = self.crossword.overlaps.get((var, neighbor))
                    if overlap:
                        i, j = overlap
                        for neighbor_word in self.domains[neighbor]:
                            if word[i] != neighbor_word[j]:
                                count += 1
            return count

        return sorted(self.domains[var], key=count_conflicts)

    def select_unassigned_variable(self, assignment):
        """
        Выбирает не назначенную переменную с наименьшим количеством оставшихся значений (MRV).
        В случае равенства выбирает переменную с наибольшей степенью (Degree heuristic).
        """
        unassigned = [v for v in self.crossword.variables if v not in assignment]

        # Сортировка по MRV, затем по степени
        def sort_criteria(var):
            return (len(self.domains[var]), -len(self.crossword.neighbors(var)))

        return min(unassigned, key=sort_criteria)

    def backtrack(self, assignment):
        """
        Выполняет поиск с возвратом для нахождения полного согласованного присваивания.
        """
        if self.assignment_complete(assignment):
            return assignment

        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            new_assignment = assignment.copy()
            new_assignment[var] = value
            if self.consistent(new_assignment):
                # Сохраняем текущие домены для возможного отката
                saved_domains = {v: self.domains[v].copy() for v in self.domains}
                # Назначаем значение
                assignment[var] = value
                # Обеспечиваем согласованность дуг после назначения
                if self.ac3():
                    result = self.backtrack(assignment)
                    if result:
                        return result
                # Восстанавливаем домены при неудаче
                self.domains = saved_domains
                # Убираем назначение
                del assignment[var]
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)




if __name__ == "__main__":
    main()
