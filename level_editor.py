import tkinter as tk
from tkinter import messagebox

# Paramètres de la grille
grid_size = (9, 7)  # (colonnes, lignes) -> x, y
cell_size = 40  # Taille d'une cellule en pixels

# Couleurs associées aux blocs
colors = {
    0: "white",     # Case vide
    1: "black",     # Mur
    2: "blue",      # Conducteur on
    3: "light blue",# Conducteur off
    4: "red",       # Explosif
    5: "green",     # Multiplicateur
    6: "yellow",    # Réparateur
    7: "purple"     # Portail
}

# Grille initialisée en [y][x] au lieu de [x][y]
grid = [[0] * grid_size[0] for _ in range(grid_size[1])]
current_block = 1  # Bloc sélectionné par défaut

def change_block_type(block):
    global current_block
    current_block = block

def on_cell_click(event):
    """Change la couleur et le type du bloc dans la grille."""
    x, y = event.x // cell_size, event.y // cell_size
    if 0 <= x < grid_size[0] and 0 <= y < grid_size[1]:
        grid[y][x] = current_block  # Accès sous forme [y][x]
        canvas.itemconfig(cells[y][x], fill=colors[current_block])

def export_grid():
    """Affiche la grille sous forme de liste Python et la copie dans le presse-papier."""
    grid_str = str(grid)
    root.clipboard_clear()
    root.clipboard_append(grid_str)
    root.update()
    messagebox.showinfo("Export", "Grille copiée dans le presse-papier !")

# Création de la fenêtre
root = tk.Tk()
root.title("Éditeur de niveaux")

# Création du canevas
canvas = tk.Canvas(root, width=grid_size[0] * cell_size, height=grid_size[1] * cell_size, bg="white")
canvas.pack()
canvas.bind("<Button-1>", on_cell_click)

# Création des cellules en [y][x]
cells = []
for y in range(grid_size[1]):  # Parcours des lignes
    row = []
    for x in range(grid_size[0]):  # Parcours des colonnes
        rect = canvas.create_rectangle(
            x * cell_size, y * cell_size, (x + 1) * cell_size, (y + 1) * cell_size,
            fill="white", outline="gray"
        )
        row.append(rect)
    cells.append(row)  # Ajoute la ligne complète

# Création de la palette de couleurs
frame = tk.Frame(root)
frame.pack()
for code, color in colors.items():
    btn = tk.Button(frame, bg=color, width=5, height=2, command=lambda c=code: change_block_type(c))
    btn.pack(side=tk.LEFT)

# Bouton d'export
export_btn = tk.Button(root, text="Exporter la grille", command=export_grid)
export_btn.pack()

root.mainloop()
