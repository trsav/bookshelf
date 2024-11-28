from python_tsp.heuristics import solve_tsp_simulated_annealing
from python_tsp.exact import solve_tsp_dynamic_programming
import pickle 
import numpy as np 
import matplotlib.pyplot as plt
from tsne import plot_embeddings_with_balanced_arrows


with open(f'embedding/pickled_embeddings.pkl','rb') as f:
    res = pickle.load(f)

embeddings = []
for r in res.data:
    embeddings.append(r.embedding)

matrix = np.array(embeddings)

with open(f'embedding/tsne_embeddings.pkl','rb') as f:
    embeddings_df = pickle.load(f)

# x and y column as array
embeddings = np.array(embeddings_df[['x','y']])
title = embeddings_df['label']


# x and y column as array
embeddings = np.array(embeddings_df[['x','y']])
title = embeddings_df['label']

distance_matrix = np.zeros((len(matrix), len(matrix)))
for i in range(len(matrix)):
    for j in range(i,len(matrix)):
        distance_matrix[i][j] = np.linalg.norm(matrix[i] - matrix[j])
        distance_matrix[j][i] = distance_matrix[i][j]


distance_matrix[:, 0] = 0

permutation, distance = solve_tsp_simulated_annealing(distance_matrix, max_processing_time=60)

# ordered list of titles of tour
tour = [title[i] for i in permutation]
with open('embedding/tour.txt','w') as f:
    for t in tour:
        f.write(f'{t}\n')
    