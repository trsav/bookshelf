# ```BOOKSHELF```

<p align="center">
<img width="400" alt="bookshelf" src="https://github.com/user-attachments/assets/e034879b-be90-4f6a-b158-ec492f3ab8fd">
</p>

A terminal-based book management system with an intuitive interface. Track reading progress, add books, and manage a book collection from the command line.

## Features

- Add books via Google Books API search.
- Add specific edition, or edit information.
- Track reading status (Unread, In Progress, Finished).
- Interactive scrolling view or view overall bookshelf.

## Installation

First, install `uv` (reccomended over pip):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the project:
```bash
# Clone repository
git clone https://github.com/trsav/bookshelf.git
cd bookshelf

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Add to your .bashrc or .zshrc for easier access
echo 'alias books="cd /path/to/bookshelf && source .venv/bin/activate && python cli.py"' >> ~/.bashrc
source ~/.bashrc
```
Now you can just type `books scroll` or `books add` from anywhere. Use `books edit` to edit existing books.

## Usage

```bash
books add    # Add new books
books view   # View library
books scroll # Interactive scroll view
```

### Scroll View Controls
- ↑/↓ or j/k: Navigate through books
- 1: Mark as Unread
- 2: Mark as In Progress
- 3: Mark as Finished
- Q: Quit

