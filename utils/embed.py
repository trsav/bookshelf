from openai import OpenAI
import sqlite3
from dotenv import load_dotenv

def create_embeddings(bookshelf_loc='bookshelf.db'):
    load_dotenv()
    conn = sqlite3.connect(bookshelf_loc)
    c = conn.cursor()
    
    # get headers first
    c.execute('PRAGMA table_info(books)')
    headers = [header[1] for header in c.fetchall()]
    
    c.execute('SELECT * FROM books')
    books = c.fetchall()
    
    book_list = []
    for book in books:
        book = dict(zip(headers, book))
        book.pop('date_added')
        book.pop('embedding')
        book_list.append(str(book))
    
    client = OpenAI()
    res = client.embeddings.create(
        model="text-embedding-3-large",
        input=book_list,
        encoding_format="float"
    )
    
    embeddings = [r.embedding for r in res.data]
        
    if 'embedding' not in headers:
        c.execute('ALTER TABLE books ADD COLUMN embedding TEXT')
    
    for i, embedding in enumerate(embeddings):
        c.execute('UPDATE books SET embedding = ? WHERE rowid = ?', 
                 (str(embedding), books[i][0]))
    
    conn.commit()
    conn.close()
