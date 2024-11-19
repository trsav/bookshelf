import click
import requests
import sqlite3
import os
from typing import List, Dict

class BookManager:
    def __init__(self, db_path="bookshelf.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()


    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT,
                isbn TEXT,
                read_status TEXT DEFAULT 'unread',
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def search_google_books(self, query: str) -> List[Dict]:
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return [{
                    'title': item.get('volumeInfo', {}).get('title', 'Unknown').upper(),
                    'author': (item.get('volumeInfo', {}).get('authors', ['Unknown'])[0]).upper(),
                    'isbn': next((id['identifier'] for id in item.get('volumeInfo', {}).get('industryIdentifiers', [])
                                if id.get('type') in ['ISBN_13', 'ISBN_10']), ''),
                    'year': item.get('volumeInfo', {}).get('publishedDate', '')[:4]
                } for item in data.get('items', [])]
            return []
        except Exception as e:
            click.secho(f"Error searching Google Books: {e}", fg='red')
            return []

    def add_book(self, book):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO books (title, author, isbn, read_status)
            VALUES (?, ?, ?, 'unread')
        ''', (book['title'], book['author'], book['isbn']))
        self.conn.commit()
        return cursor.lastrowid

    def get_books(self, sort_by_status: bool = False) -> List:
        cursor = self.conn.cursor()
        order_clause = 'CASE read_status WHEN "finished" THEN 1 WHEN "in_progress" THEN 2 ELSE 3 END, ' if sort_by_status else ''
        cursor.execute(f'SELECT id, title, author, isbn, read_status FROM books ORDER BY {order_clause}title')
        return cursor.fetchall()

    def update_read_status(self, book_id: int, status: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE books SET read_status = ? WHERE id = ?', (status, book_id))
        self.conn.commit()



def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version='1.0.0')
def cli():
    " BOOKSHELF"
    pass

@cli.command()
def scroll():
    """Scroll through books with full context and status updates"""
    manager = BookManager()
    books = manager.get_books()
    current_idx = 0
    def get_terminal_size():
        try:
            return os.get_terminal_size()
        except OSError:
            return os.terminal_size((80, 24))  # Fallback values

    def get_status_color(status):
        return {
            'unread': 'red',
            'in_progress': 'yellow',
            'finished': 'green'
        }.get(status, 'white')

    def get_adjacent_indices(current):
        total = len(books)
        prev_idx = (current - 1) % total
        next_idx = (current + 1) % total
        return prev_idx, next_idx

    def display_book_info(book, style='normal'):
        """Display book info with given style (normal or dim)"""
        color = 'white' if style == 'normal' else 'bright_black'
        indent = ""
        term_width = get_terminal_size().columns
        avail_width = term_width - len(indent)
        title = book[1][:avail_width-3] + "..." if len(book[1]) > avail_width else book[1]
        author = book[2][:avail_width-3] + "..." if len(book[2]) > avail_width else book[2]

        click.secho(f"{indent}{title}", fg=color, bold=(style == 'normal'))
        click.secho(f"{indent} - {author}", fg=color)
        click.secho(f"{indent}Status: {book[4]}", fg=get_status_color(book[4]) if style == 'normal' else color)
        click.secho(f"{indent}ISBN: {book[3]}", fg=color)

    def display_books():
        clear_screen()
        term_width = get_terminal_size().columns
        prev_idx, next_idx = get_adjacent_indices(current_idx)
        
        display_book_info(books[prev_idx], 'dim')
        click.echo()
        
        click.secho(f"Book {current_idx + 1} of {len(books)}", fg='blue')
        click.echo("─" * term_width)
        display_book_info(books[current_idx], 'normal')
        click.echo("\n" + "─" * term_width)
        
        click.echo()
        display_book_info(books[next_idx], 'dim')
        
        click.echo("\nControls:")
        controls = "↑/↓ or j/k: Navigate • 1: Unread • 2: In Progress • 3: Finished • Q: Quit"
        if len(controls) > term_width:
            controls = "↑/↓: Nav • 1:Unread • 2:Progress • 3:Done • Q:Quit"
        click.secho(controls, fg='bright_black')

    while True:
        display_books()
        c = click.getchar()

        if c == '\x1b[A' or c == 'k':  # Up arrow or k
            current_idx = max(0, current_idx - 1)
        elif c == '\x1b[B' or c == 'j':  # Down arrow or j
            current_idx = min(len(books) - 1, current_idx + 1)
        elif c in ['1', '2', '3']:
            status_map = {'1': 'unread', '2': 'in_progress', '3': 'finished'}
            manager.update_read_status(books[current_idx][0], status_map[c])
            books = manager.get_books()  # Refresh book list
        elif c.lower() == 'q':
            break

@cli.command()
@click.option('--sort-status', '-s', is_flag=True, help='Sort by read status')
def view(sort_status):
    """View and manage your library"""
    manager = BookManager()
    status_colors = {
        'unread': 'red',
        'in_progress': 'yellow',
        'finished': 'green',
    }
    
    while True:
        clear_screen()
        click.secho("THE BOOKSHELF", fg='green', bold=True)
        click.echo("─" * 50)
        
        books = manager.get_books(sort_by_status=sort_status)
        if not books:
            click.secho("Library is empty! Add some books first.", fg='yellow')
            break

        for idx, (book_id, title, author, isbn, status) in enumerate(books, 1):
            click.secho(f"{idx}. ", nl=False)
            click.secho(f"{title}", fg='bright_white', bold=True)
            click.secho(f" by {author}", fg='white')
            click.secho(f"   Status: ", nl=False)
            click.secho(f"{status.replace('_', ' ').title()}", fg=status_colors[status])

        click.echo("\n" + "─" * 50)
        click.secho("\nActions:", fg='blue', bold=True)
        click.echo("1. Mark as Finished ")
        click.echo("2. Mark as In Progress ")
        click.echo("3. Mark as Unread ")
        click.echo("4. Toggle Status Sort ")
        click.echo("5. Exit ")

        action = click.prompt(
            "\nChoose action",
            type=click.IntRange(1, 5),
            default=5
        )

        if action == 5:
            break
        elif action == 4:
            sort_status = not sort_status
            continue
            
        if action in (1, 2, 3):
            book_num = click.prompt(
                "Enter book number",
                type=click.IntRange(1, len(books)),
                default=1
            )
            status = {1: "finished", 2: "in_progress", 3: "unread"}[action]
            manager.update_read_status(books[book_num - 1][0], status)
            click.secho("Status updated!", fg='green')
            click.pause(info='Press any key to continue...')

@cli.command()
@click.option('--quick', '-q', is_flag=True, help='Quick add mode - first result is automatically selected')
def add(quick):
    """Add new books to your library"""
    manager = BookManager()
    
    while True:
        clear_screen()
        click.secho("📖 Add Books to Library", fg='green', bold=True)
        click.echo("─" * 50)
        
        query = click.prompt("Enter book title/author (or 'q' to quit)")
        if query.lower() == 'q':
            break

        with click.progressbar(length=1, label='Searching Google Books') as bar:
            results = manager.search_google_books(query)
            bar.update(1)

        if not results:
            click.secho("❌ No matches found", fg='red')
            if not click.confirm("Search again?"):
                break
            continue

        if quick and results:
            book = results[0]
            manager.add_book(book)
            click.secho(f"✅ Added: {book['title']} by {book['author']}", fg='green')
            if not click.confirm("Add another book?"):
                break
            continue

        click.secho("\nSearch Results:", fg='blue', bold=True)
        for idx, book in enumerate(results, 1):
            click.echo(f"{idx}. {book['title']} by {book['author']} ({book['year']})")
            click.secho(f"ISBN: {book['isbn']}", fg='bright_black')

        choice = click.prompt(
            "\nSelect book number (0 to search again)",
            type=click.IntRange(0, len(results)),
            default=0
        )
        
        if choice == 0:
            continue
            
        book = results[choice - 1]
        manager.add_book(book)
        click.secho(f"✅ Successfully added: {book['title']}", fg='green')
        
        if not click.confirm("Add another book?"):
            break

if __name__ == "__main__":
    cli()
