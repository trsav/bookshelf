Optimal Bookshelf Organiser

<p align="center">
<img width="400" alt="bookshelf" src="https://github.com/user-attachments/assets/e034879b-be90-4f6a-b158-ec492f3ab8fd">
</p>

A terminal-based book management system with an intuitive interface. Track reading progress, manage your collection, and discover optimal reading paths through semantic relationships between books.
Features

Add books via Google Books API search
Add specific edition, or edit information
Track reading status (Unread, In Progress, Finished)
Interactive scrolling view or view overall bookshelf
Generate semantic embeddings of your library
Create optimal reading paths using TSP algorithms
Visualize book relationships in 2D space

Installation
First, install uv (reccomended over pip):
bashCopycurl -LsSf https://astral.sh/uv/install.sh | sh
Then install the project:
bashCopy# Clone repository
git clone https://github.com/trsav/bookshelf.git
cd bookshelf
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
# Add to your .bashrc or .zshrc for easier access
echo 'alias books="cd /path/to/bookshelf && source .venv/bin/activate && python cli.py"' >> ~/.bashrc
source ~/.bashrc
Now you can just type books scroll or books add from anywhere.
Usage
bashCopybooks add    # Add new books
books view   # View library
books scroll # Interactive scroll view
books edit   # Edit books in library
books embed  # Create embeddings for optimal organization
books tsp    # Generate optimal reading path
books tsp -v # Visualize reading path in 2D
Scroll View Controls

↑/↓ or j/k: Navigate through books
1: Mark as Unread
2: Mark as In Progress
3: Mark as Finished
Q: Quit

Optimal Organization
The embed command creates semantic embeddings for your books using descriptions and metadata. These embeddings capture relationships between books based on their content and themes.
The tsp command uses these embeddings to create an optimal reading path through your library:

Default mode finds a path in the full semantic space
Visual mode (-v) projects books into 2D space and generates a visualization
Both modes save the recommended reading order

Run embed after adding new books to ensure your optimal paths include your entire library.