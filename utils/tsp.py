from python_tsp.heuristics import solve_tsp_simulated_annealing
from python_tsp.exact import solve_tsp_dynamic_programming
import matplotlib.pyplot as plt
import sqlite3
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import pickle
import numpy as np
import sqlite3
import pandas as pd
from adjustText import adjust_text
import ast
import time

def no_return_dm(X):
    distance_matrix = np.zeros((len(X), len(X)))
    for i in range(len(X)):
        for j in range(i,len(X)):
            distance_matrix[i][j] = np.linalg.norm(X[i] - X[j])
            distance_matrix[j][i] = distance_matrix[i][j]

    distance_matrix[:, 0] = 0 # no return 
    return distance_matrix

def get_titles_and_embeddings(bookshelf_loc='bookshelf.db'):
    conn = sqlite3.connect(bookshelf_loc)
    c = conn.cursor()
    c.execute('SELECT * FROM books')
    books = c.fetchall()
    conn.close()
    # get headers
    conn = sqlite3.connect('bookshelf.db')
    c = conn.cursor()
    c.execute('PRAGMA table_info(books)')
    headers = c.fetchall()
    conn.close()

    # only get title and embedding
    headers = [header[1] for header in headers]
    book_list = []
    for book in books:
        book = dict(zip(headers, book))
        book_list.append(book)

    embeddings = []
    titles = []
    for book in book_list:
        embeddings.append(ast.literal_eval(book['embedding']))
        titles.append(book['title'])
    return embeddings, titles


def visual_tsp(bookshelf_loc='bookshelf.db'):
    
    embeddings, titles = get_titles_and_embeddings(bookshelf_loc)

    # dimensionality reduction 
    tsne = TSNE(n_components=2, perplexity=15, random_state=10, n_iter=10000)
    X = tsne.fit_transform(np.array(embeddings))

    x,y = X[:,0], X[:,1]
    fig, ax = plt.subplots(figsize=(11,8))
    scatter = ax.scatter(x,y, c='k', s=10,lw=0,alpha=0.5)

    texts = []
    for x, y, title in zip(x, y, titles):
        x_center = np.mean(x)
        y_center = np.mean(y)

        texts.append(plt.text(x , y , title,
                            fontsize=6,
                            horizontalalignment='center'))

    # Adjust text positions with more balanced forces
    adjust_text(texts,
                x=x,
                y=y,
                arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5,
                                connectionstyle='arc3'),
                force_text=0.3,
                pull_threshold=0.1,
                expand_points=(1.2, 1.2),
                force_explode=(1.4, 1.4))

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.tight_layout()
    
    distance_matrix = no_return_dm(X)
    permutation, distance = solve_tsp_simulated_annealing(distance_matrix, max_processing_time=60)

    # plot tsp solution 
    for i in range(len(permutation)-1):
        first = i 
        second = i + 1

        plt.plot(
            [X[:,0][permutation[first]], X[:,0][permutation[second]]],
            [X[:,1][permutation[first]], X[:,1][permutation[second]]],
            'tab:red',
            ls='dashed',
            alpha=0.75,
        )
        
    date = time.strftime('%Y-%m-%d %H:%M:%S')
    path = f'{date}_tsp.png'
    plt.savefig(path,dpi=600)

    tour = [titles[i] for i in permutation]
    tour = [f'{i+1}. {book}' for i,book in enumerate(tour)]

    return tour,path

def fullspace_tsp(bookshelf_loc='bookshelf.db'):
    embeddings, titles = get_titles_and_embeddings(bookshelf_loc)
    distance_matrix = no_return_dm(np.array(embeddings))
    permutation, distance = solve_tsp_simulated_annealing(distance_matrix, max_processing_time=60)
    tour = [titles[i] for i in permutation]
    date = time.strftime('%Y-%m-%d %H:%M:%S')
    path = f'{date}_tour.txt'
    with open(path,'w') as f:
        for i in range(len(tour)):
            f.write(f'{i+1}. {tour[i]}\n')

    return tour, path
