from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import pickle
import numpy as np
import sqlite3
import pandas as pd
from adjustText import adjust_text

with open('embedding/pickled_embeddings.pkl', 'rb') as f:
    res = pickle.load(f)

# read 

embeddings = []
for r in res.data:
    embeddings.append(r.embedding)

matrix = np.array(embeddings)

conn = sqlite3.connect('embedding/bookshelf.db')
c = conn.cursor()
c.execute('SELECT * FROM books')
books = c.fetchall()
conn.close()
# get headers
conn = sqlite3.connect('embedding/bookshelf.db')
c = conn.cursor()
c.execute('PRAGMA table_info(books)')
headers = c.fetchall()
conn.close()
headers = [header[1] for header in headers]
book_list = []
for book in books:
    book = dict(zip(headers, book))
    # delete the 'date_added' field
    book.pop('date_added')
    book_list.append(book)
print(book_list)

tsne = TSNE(n_components=2, perplexity=10, random_state=42, init="random", learning_rate='auto')
X = tsne.fit_transform(matrix)

def plot_embeddings_with_balanced_arrows(x_coords, y_coords, labels, figsize=(11,10)):
    """
    Create an embedding plot with balanced arrow directions
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Create scatter plot
    scatter = ax.scatter(x_coords, y_coords, c='k', s=10,lw=0,alpha=0.5)

    # Create texts with balanced positioning
    texts = []
    for x, y, label in zip(x_coords, y_coords, labels):
        # Determine preferred direction based on position relative to center
        # This helps create a more balanced spread of labels
        x_center = np.mean(x_coords)
        y_center = np.mean(y_coords)

        texts.append(plt.text(x , y , label,
                            fontsize=6,
                            horizontalalignment='center'))

    # Adjust text positions with more balanced forces
    adjust_text(texts,
               x=x_coords,
               y=y_coords,
               arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5,
                             connectionstyle='arc3'),
                force_text=0.3,
                pull_threshold=0.1,
                expand_points=(1.2, 1.2),
                force_explode=(1.4, 1.4))

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    # no ticks or axis at all 
    ax.set_xticks([])
    ax.set_yticks([])

    plt.tight_layout()
    return fig, ax

embeddings_df = pd.DataFrame({
    'x': X[:,0],
    'y': X[:,1],
    'label': [book['title'] for book in book_list]
})

fig, ax = plot_embeddings_with_balanced_arrows(
    embeddings_df['x'],
    embeddings_df['y'],
    embeddings_df['label']
)
plt.savefig('embedding/tsne.png',dpi=700)

