import os
import random
import re
import sys

from nbformat import corpus

DAMPING = 0.85
SAMPLES = 10000


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python pagerank.py corpus")
    corpus = crawl(sys.argv[1])
    ranks = sample_pagerank(corpus, DAMPING, SAMPLES)
    print(f"PageRank Results from Sampling (n = {SAMPLES})")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")
    ranks = iterate_pagerank(corpus, DAMPING)
    print(f"PageRank Results from Iteration")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")


def crawl(directory):
    """
    Parse a directory of HTML pages and check for links to other pages.
    Return a dictionary where each key is a page, and values are
    a list of all other pages in the corpus that are linked to by the page.
    """
    pages = dict()

    # Extract all links from HTML files
    for filename in os.listdir(directory):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(directory, filename)) as f:
            contents = f.read()
            links = re.findall(r"<a\s+(?:[^>]*?)href=\"([^\"]*)\"", contents)
            pages[filename] = set(links) - {filename}

    # Only include links to other pages in the corpus
    for filename in pages:
        pages[filename] = set(
            link for link in pages[filename]
            if link in pages
        )

    return pages


def transition_model(corpus, page, damping_factor):
    """
    Return a probability distribution over which page to visit next,
    given a current page.

    With probability `damping_factor`, choose a link at random
    linked to by `page`. With probability `1 - damping_factor`, choose
    a link at random chosen from all pages in the corpus.
    """
    # example corpus = {"1.html": {"2.html", "3.html"}, "2.html": {"3.html"}, "3.html": {"2.html"}}
    # page = "1.html"
    # damping_factor = 0.85
    # result = {"1.html": 0.05, "2.html": 0.475, "3.html": 0.475}

    N = len(corpus)
    new_cor = {}
    if not corpus[page]:
        for p in corpus:
            new_cor[p] = (1 - damping_factor) / N
        return new_cor

    for p in corpus:
        new_cor[p] = (1 - damping_factor) / N

    for pa in corpus[page]:
        new_cor[pa] += damping_factor / len(corpus[page])

    return new_cor


def sample_pagerank(corpus, damping_factor, n):
    pagerank = {page: 0 for page in corpus}
    current_page = random.choice(list(corpus.keys()))

    for _ in range(n):
        pagerank[current_page] += 1
        probabilities = transition_model(corpus, current_page, damping_factor)
        current_page = random.choices(
            population=list(probabilities.keys()),
            weights=list(probabilities.values()),
            k=1
        )[0]

    # Нормализация значений
    for page in pagerank:
        pagerank[page] /= n

    return pagerank


def iterate_pagerank(corpus, damping_factor):
    """
    Return PageRank values for each page by iteratively updating
    PageRank values until convergence.
    """
    N = len(corpus)
    # Инициализируем начальный PageRank для всех страниц
    pagerank = {page: 1 / N for page in corpus}

    while True:
        new_pagerank = {}
        for page in corpus:
            # Первая часть формулы
            rank = (1 - damping_factor) / N

            # Вторая часть формулы: ссылки на текущую страницу
            for linking_page in corpus:
                # Если страница `linking_page` ссылается на текущую `page`
                if page in corpus[linking_page]:
                    rank += damping_factor * (pagerank[linking_page] / len(corpus[linking_page]))
                # Если `linking_page` не ссылается ни на одну страницу (dead end)
                elif not corpus[linking_page]:
                    rank += damping_factor * (pagerank[linking_page] / N)

            new_pagerank[page] = rank

        # Проверяем сходимость
        if all(abs(new_pagerank[page] - pagerank[page]) < 1e-6 for page in pagerank):
            break

        pagerank = new_pagerank

    return pagerank


if __name__ == "__main__":
    main()

