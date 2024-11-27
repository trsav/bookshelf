from python_tsp.heuristics import solve_tsp_simulated_annealing
from python_tsp.exact import solve_tsp_dynamic_programming
import pickle 
import numpy as np 
import matplotlib.pyplot as plt
from tsne import plot_embeddings_with_balanced_arrows


with open(f'embedding/tsne_embeddings.pkl','rb') as f:
    embeddings_df = pickle.load(f)

# x and y column as array
embeddings = np.array(embeddings_df[['x','y']])
title = embeddings_df['label']

distance_matrix = np.zeros((len(embeddings), len(embeddings)))
for i in range(len(embeddings)):
    for j in range(i,len(embeddings)):
        distance_matrix[i][j] = np.linalg.norm(embeddings[i] - embeddings[j])
        distance_matrix[j][i] = distance_matrix[i][j]

permutation, distance = solve_tsp_simulated_annealing(distance_matrix)

fig, ax = plot_embeddings_with_balanced_arrows(
    embeddings_df['x'],
    embeddings_df['y'],
    embeddings_df['label']
)

# plot tsp solution 
for i in range(len(permutation)):
    first = i 
    second = i + 1
    if second == len(permutation):
        second = 0

    plt.plot(
        [embeddings_df['x'][permutation[first]], embeddings_df['x'][permutation[second]]],
        [embeddings_df['y'][permutation[first]], embeddings_df['y'][permutation[second]]],
        'tab:red',
        ls='dashed',
        alpha=0.75
    )

plt.savefig('embedding/tsp.png',dpi=600)
