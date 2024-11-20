import click
import requests
import sqlite3
import os
from typing import List, Dict
from datetime import datetime

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
                publisher TEXT,
                publication_year TEXT,
                edition TEXT,
                format TEXT,
                language TEXT,
                page_count INTEGER,
                read_status TEXT DEFAULT 'unread',
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def edit_book_field(self, book_id: int, field: str, value: str):
        """Edit a specific field of a book"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f'UPDATE books SET {field} = ? WHERE id = ?', (value, book_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            click.secho(f"Error updating field: {e}", fg='red')
            return False

    def get_edition_details(self, isbn: str) -> List[Dict]:
        """Search for all editions of a book using ISBN"""
        editions = []
        
        # Search by ISBN
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&maxResults=40"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if 'items' in data:
                    editions.extend(self._parse_editions(data['items']))

            # If we found a book, search for other editions using title and author
            if editions:
                first_book = editions[0]
                title = first_book['title']
                author = first_book['author']
                
                # Search by title and author
                url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}+inauthor:{author}&maxResults=40"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if 'items' in data:
                        editions.extend(self._parse_editions(data['items']))

            # Remove duplicates based on ISBN
            seen_isbns = set()
            unique_editions = []
            for edition in editions:
                if edition['isbn'] and edition['isbn'] not in seen_isbns:
                    seen_isbns.add(edition['isbn'])
                    unique_editions.append(edition)

            return unique_editions

        except Exception as e:
            click.secho(f"Error searching for editions: {e}", fg='red')
            return []

    def _parse_editions(self, items: List[Dict]) -> List[Dict]:
        """Parse edition information from Google Books API response"""
        editions = []
        for item in items:
            volume_info = item.get('volumeInfo', {})
            
            # Get ISBN (prefer ISBN-13, fallback to ISBN-10)
            isbn = ''
            for identifier in volume_info.get('industryIdentifiers', []):
                if identifier.get('type') == 'ISBN_13':
                    isbn = identifier.get('identifier')
                    break
                elif identifier.get('type') == 'ISBN_10':
                    isbn = identifier.get('identifier')

            # Skip if no ISBN (likely not a real edition)
            if not isbn:
                continue

            # Extract format from physical attributes
            format_ = 'Unknown'
            if 'printType' in volume_info:
                if volume_info['printType'] == 'BOOK':
                    if volume_info.get('isEbook', False):
                        format_ = 'eBook'
                    else:
                        format_ = self._guess_format(volume_info)

            edition = {
                'title': volume_info.get('title', 'Unknown').upper(),
                'author': (volume_info.get('authors', ['Unknown'])[0]).upper(),
                'isbn': isbn,
                'publisher': volume_info.get('publisher', 'Unknown'),
                'publication_year': volume_info.get('publishedDate', '')[:4],
                'language': volume_info.get('language', 'unknown'),
                'page_count': volume_info.get('pageCount', 0),
                'format': format_,
                'description': volume_info.get('description', ''),
                'preview_link': volume_info.get('previewLink', ''),
                'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', '')
            }
            
            editions.append(edition)
        
        return editions

    def _guess_format(self, volume_info: Dict) -> str:
        """Guess book format based on available information"""
        if 'dimensions' in volume_info:
            dims = volume_info['dimensions']
            # Common mass market paperback dimensions
            if any('17.5' in str(dim) or '6.8' in str(dim) for dim in dims.values()):
                return 'Mass Market Paperback'
            # Common trade paperback dimensions
            elif any('23' in str(dim) or '9' in str(dim) for dim in dims.values()):
                return 'Trade Paperback'
            # Common hardcover dimensions
            elif any('24' in str(dim) or '9.5' in str(dim) for dim in dims.values()):
                return 'Hardcover'
        return 'Paperback'  # Default assumption

    def search_google_books(self, query: str) -> List[Dict]:
        """Initial search for books"""
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=15"
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
            INSERT INTO books (
                title, author, isbn, publisher, publication_year,
                edition, format, language, page_count, read_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unread')
        ''', (
            book['title'],
            book['author'],
            book['isbn'],
            book.get('publisher', ''),
            book.get('publication_year', ''),
            book.get('edition', ''),
            book.get('format', ''),
            book.get('language', 'en'),
            book.get('page_count', 0)
        ))
        self.conn.commit()
        return cursor.lastrowid

    def delete_book(self, book_id):
        cursor = self.conn.cursor()

        # First get the book details
        cursor.execute('SELECT title, author FROM books WHERE id = ?', (book_id,))
        book_info = cursor.fetchone()

        if book_info:
            title, author = book_info
            # Delete the book
            cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
            self.conn.commit()
            click.secho(f"\nDeleted: {title} by {author}", fg='yellow')
            return True
        else:
            click.secho("\nBook not found!", fg='red')
            return False


    def get_books(self, sort_by_status: bool = False) -> List:
        cursor = self.conn.cursor()
        order_clause = 'CASE read_status WHEN "finished" THEN 1 WHEN "in_progress" THEN 2 ELSE 3 END, ' if sort_by_status else ''
        cursor.execute(f'''
            SELECT id, title, author, isbn, publisher, publication_year,
                   edition, format, language, page_count, read_status
            FROM books
            ORDER BY {order_clause}title
        ''')
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
            return os.terminal_size((80, 24))

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

        # Unpack all book details
        id_, title, author, isbn, publisher, year, edition, format_, language, pages, status = book

        # Format title and author with ellipsis if too long
        title = title[:avail_width-3] + "..." if len(title) > avail_width else title
        author = author[:avail_width-3] + "..." if len(author) > avail_width else author

        # Display main info
        click.secho(f"{indent}{title}", fg=color, bold=(style == 'normal'))
        click.secho(f"{indent} - {author}", fg=color)

        # Display edition info
        edition_info = []
        if edition:
            edition_info.append(edition)
        if format_:
            edition_info.append(format_)
        if year:
            edition_info.append(year)
        if publisher:
            edition_info.append(publisher)

        if edition_info:
            edition_str = " • ".join(filter(None, edition_info))
            click.secho(f"{indent}{edition_str}", fg=color)

        # Display additional details
        if pages:
            click.secho(f"{indent}Pages: {pages}", fg=color)
        if language:
            click.secho(f"{indent}Language: {language.upper()}", fg=color)

        # Display status and ISBN
        click.secho(f"{indent}Status: {status}", fg=get_status_color(status) if style == 'normal' else color)
        click.secho(f"{indent}ISBN: {isbn}", fg=color)

    def display_books():
        clear_screen()
        term_width = get_terminal_size().columns
        prev_idx, next_idx = get_adjacent_indices(current_idx)

        display_book_info(books[prev_idx], 'dim')
        click.secho(f"Book {current_idx + 1} of {len(books)}", fg='blue')
        click.echo("─" * term_width)
        display_book_info(books[current_idx], 'normal')
        click.echo("─" * term_width)
        display_book_info(books[next_idx], 'dim')

        click.echo("Controls:")
        controls = "↑/↓ or j/k: Navigate • 1: Unread • 2: In Progress • 3: Finished • D: Delete Book • Q: Quit"
        if len(controls) > term_width:
            controls = "↑/↓: Nav • 1:Unread • 2:Progress • 3:Done • Q:Quit • D:Delete"
        click.secho(controls, fg='bright_black')

    while True:
        display_books()
        c = click.getchar()

        if c == '\x1b[A' or c == 'k':  # Up arrow or k
            current_idx = (current_idx - 1) % len(books)
        elif c == '\x1b[B' or c == 'j':  # Down arrow or j
            current_idx = (current_idx + 1) % len(books)
        elif c in ['1', '2', '3']:
            status_map = {'1': 'unread', '2': 'in_progress', '3': 'finished'}
            manager.update_read_status(books[current_idx][0], status_map[c])
            books = manager.get_books()  # Refresh book list
        elif c.lower() == 'q':
            break
        elif c.lower() == 'd':
            if manager.delete_book(books[current_idx][0]):
                books = manager.get_books()  # Refresh book list
                if not books:  # If last book was deleted
                    break
                current_idx = min(current_idx, len(books) - 1)

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

        for idx, (book_id, title, author, isbn, publisher, year, edition, format_, language, pages, status) in enumerate(books, 1):
            click.secho(f"{idx}. ", nl=False)
            click.secho(f"{title}", fg='bright_white', bold=True)
            click.secho(f" by {author}", fg='white')

            # Edition information
            edition_info = []
            if edition:
                edition_info.append(edition)
            if format_:
                edition_info.append(format_)
            if year:
                edition_info.append(year)
            if publisher:
                edition_info.append(publisher)

            if edition_info:
                click.secho(f"   {' • '.join(edition_info)}", fg='bright_black')

            # Additional details
            details = []
            if pages:
                details.append(f"{pages} pages")
            if language:
                details.append(f"Lang: {language.upper()}")
            if details:
                click.secho(f"   {' • '.join(details)}", fg='bright_black')

            # Status and ISBN
            click.secho(f"   Status: ", nl=False)
            click.secho(f"{status.replace('_', ' ').title()}", fg=status_colors[status])
            click.secho(f"   ISBN: {isbn}", fg='bright_black')
            click.echo()

        click.echo("─" * 50)
        click.secho("\nActions:", fg='blue', bold=True)
        click.echo("1. Mark as Finished")
        click.echo("2. Mark as In Progress")
        click.echo("3. Mark as Unread")
        click.echo("4. Toggle Status Sort")
        click.echo("5. Delete Book")
        click.echo("6. Exit")

        action = click.prompt(
            "\nChoose action",
            type=click.IntRange(1, 6),
            default=6
        )

        if action == 6:
            break

        if action == 5:
            book_num = click.prompt(
                "Enter book number",
                type=click.IntRange(1, len(books)),
                default=1
            )
            manager.delete_book(books[book_num-1][0])

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
def add():
    """Add new books to your library with automatic edition detection"""
    manager = BookManager()
    
    while True:
        clear_screen()
        click.secho("📖 Add Books to Library", fg='green', bold=True)
        click.echo("─" * 50)
        
        query = click.prompt("Enter book title/author (or 'q' to quit)")
        if query.lower() == 'q':
            break

        # Initial search
        with click.progressbar(length=1, label='Searching Google Books') as bar:
            results = manager.search_google_books(query)
            bar.update(1)

        if not results:
            click.secho("❌ No matches found", fg='red')
            if not click.confirm("Search again?"):
                break
            continue

        # Show initial results
        click.secho("\nSearch Results:", fg='blue', bold=True)
        for idx, book in enumerate(results, 1):
            click.echo(f"{idx}. {book['title']} by {book['author']} ({book['year']})")

        choice = click.prompt(
            "\nSelect book to view all editions (0 to search again)",
            type=click.IntRange(0, len(results)),
            default=0
        )
        
        if choice == 0:
            continue

        # Get all editions for the selected book
        selected_book = results[choice - 1]
        with click.progressbar(length=1, label='Finding all editions') as bar:
            editions = manager.get_edition_details(selected_book['isbn'])
            bar.update(1)

        while True:
            clear_screen()
            click.secho(f"📚 Available Editions of '{selected_book['title']}'", fg='green', bold=True)
            click.echo("─" * 50)

            for idx, edition in enumerate(editions, 1):
                click.secho(f"\n{idx}. ", nl=False)
                click.secho(f"{edition['title']}", fg='bright_white', bold=True)
                click.secho(f"Author: {edition['author']}", fg='white')
                click.secho(f"Publisher: {edition['publisher']} ({edition['publication_year']})", fg='bright_black')
                click.secho(f"Format: {edition['format']} • Pages: {edition['page_count']} • Lang: {edition['language'].upper()}", fg='bright_black')
                click.secho(f"ISBN: {edition['isbn']}", fg='bright_black')

            edition_choice = click.prompt(
                "\nSelect edition to add (0 to go back)",
                type=click.IntRange(0, len(editions)),
                default=0
            )

            if edition_choice == 0:
                break

            selected_edition = editions[edition_choice - 1]
            
            # Show detailed view of selected edition
            clear_screen()
            click.secho("Edition Details:", fg='blue', bold=True)
            click.echo("─" * 50)
            for key, value in selected_edition.items():
                if key not in ['description', 'preview_link', 'thumbnail'] and value:
                    click.secho(f"{key.replace('_', ' ').title()}: ", nl=False)
                    click.echo(value)

            if selected_edition['description']:
                click.echo("\nDescription:")
                click.echo(selected_edition['description'][:200] + "...")

            if click.confirm("\nAdd this edition to your library?"):
                manager.add_book(selected_edition)
                click.secho(f"✅ Successfully added: {selected_edition['title']}", fg='green')
                break

        if not click.confirm("Search for another book?"):
            break


@cli.command()
def edit():
    """Edit book details"""
    manager = BookManager()
    
    while True:
        clear_screen()
        click.secho("📝 Edit Book Details", fg='green', bold=True)
        click.echo("─" * 50)
        
        # Get all books
        books = manager.get_books()
        if not books:
            click.secho("Library is empty!", fg='yellow')
            break

        # Display books
        for idx, book in enumerate(books, 1):
            click.secho(f"{idx}. ", nl=False)
            click.secho(f"{book[1]}", fg='bright_white', bold=True)  # title
            click.secho(f" by {book[2]}", fg='white')  # author

        # Select book
        book_num = click.prompt(
            "\nSelect book to edit (0 to exit)",
            type=click.IntRange(0, len(books)),
            default=0
        )
        
        if book_num == 0:
            break
            
        selected_book = books[book_num-1]
        
        # Show editable fields
        clear_screen()
        click.secho(f"Editing: {selected_book[1]}", fg='blue', bold=True)
        click.echo("─" * 50)
        
        fields = [
            ('title', 'Title'),
            ('author', 'Author'),
            ('isbn', 'ISBN'),
            ('publisher', 'Publisher'),
            ('publication_year', 'Publication Year'),
            ('edition', 'Edition'),
            ('format', 'Format'),
            ('language', 'Language'),
            ('page_count', 'Page Count'),
            ('read_status', 'Read Status')
        ]
        
        # Display current values
        for idx, (field_name, field_label) in enumerate(fields, 1):
            current_value = selected_book[fields.index((field_name, field_label))+1] or 'Not set'
            click.echo(f"{idx}. {field_label}: {current_value}")

        # Select field to edit
        field_num = click.prompt(
            "\nSelect field to edit (0 to go back)",
            type=click.IntRange(0, len(fields)),
            default=0
        )
        
        if field_num == 0:
            continue
            
        selected_field = fields[field_num-1]
        
        # Handle special cases for certain fields
        if selected_field[0] == 'read_status':
            new_value = click.prompt(
                "Enter new value",
                type=click.Choice(['unread', 'in_progress', 'finished'], case_sensitive=False),
                default=selected_book[fields.index(selected_field)+1] or 'unread'
            )
        elif selected_field[0] == 'format':
            new_value = click.prompt(
                "Enter new value",
                type=click.Choice(['Hardcover', 'Paperback', 'Mass Market', 'eBook', 'Other'], case_sensitive=False),
                default=selected_book[fields.index(selected_field)+1] or 'Paperback'
            )
        elif selected_field[0] == 'page_count':
            new_value = click.prompt(
                "Enter new value",
                type=int,
                default=selected_book[fields.index(selected_field)+1] or 0
            )
        else:
            new_value = click.prompt(
                "Enter new value",
                default=selected_book[fields.index(selected_field)+1] or ''
            )
        
        # Update the field
        if manager.edit_book_field(selected_book[0], selected_field[0], new_value):
            click.secho(f"\n✅ Successfully updated {selected_field[1]}", fg='green')
        else:
            click.secho(f"\n❌ Failed to update {selected_field[1]}", fg='red')
        
        if not click.confirm("\nEdit another field?"):
            break

if __name__ == "__main__":
    cli()
