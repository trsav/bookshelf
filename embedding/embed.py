from openai import OpenAI
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# read from bookshelf.db, each row is a separate dictionary
bookshelf_loc = 'embedding/bookshelf.db'
conn = sqlite3.connect(bookshelf_loc)
c = conn.cursor()
c.execute('SELECT * FROM books')
books = c.fetchall()
conn.close()
# get headers
conn = sqlite3.connect(bookshelf_loc)
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
    book_list.append(str(book))
print(book_list)

from openai import OpenAI
client = OpenAI()

res = client.embeddings.create(
  model = "text-embedding-3-large",
  input=book_list,
  encoding_format="float"
)

import pickle

with open('embedding/pickled_embeddings.pkl','wb') as f:
    pickle.dump(res,f)

