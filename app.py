# Pyxel Studio
import pyxel
import random
import copy

# Pour avoir accès aux niveaux
from storage import data

# Taille de la fenetre 128x128 pixels
pyxel.init(160, 120, title="Grid Crafter")
window_size = (160,120)
pyxel.mouse(True) # Affiche la souris

max_size = (9,7) # Taille max de la grille (x,y)
grid = [[0] * max_size[0] for _ in range(max_size[1])] # Initialisation de la grille (Matrice)
grid = [[1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1]]

cell_size = (16,16)

# Taille totale de la grille
grid_width = max_size[0] * cell_size[0]
grid_height = max_size[1] * cell_size[1]

# Position de fin du rebord ou taille du rebord
start_x = (window_size[0] - grid_width) // 2
start_y = (window_size[1] - grid_height) // 2

# Chargement des images
pyxel.load("res.pyxres")

'''
-- Codes des différents blocs --
- 0 : empty block
- 1 : wall block
- 2 : blue cable block (on)
- 3 : blue cable block (off)
- 4 : tnt (explosif)
- 5 : green block
- 6 : yellow block
- 7 : generator
- 8 : receiver (on)
- 9 : receiver (off)
- 10 : hard tnt (explosif, breaks walls)
- 11 : keep tnt (explosif, gives you destroyed blocks)
- 12 : infinite tnt (explode when activate, but stay and reexplode only until the next activation)
- 13 : unidirectionnel cable bloc (horizontal, on)
- 14 : unidirectionnel cable bloc (horizontal, off)
- 15 : unidirectionnel cable bloc (vertical, on)
- 16 : unidirectionnel cable bloc (vertical, off)
- 17 : pusher (right)
- 18 : pusher (left)
- 19 : pusher (up)
- 20 : pusher (down)
'''
# Positions des texture des blocs dans l'image 0
blocks_textures = {0:(0,0),1:(16,0),2:(0,16),3:(16,16),4:(32,0),5:(0,64),6:(16,64),7:(32,32),8:(48,48),9:(48,32),10:(48,0),11:(32,16),12:(48,16),13:(0,32),14:(16,32),15:(0,48),16:(16,48),17:(32,64),18:(48,64),19:(32,80),20:(48,80)}
# Positions des texture des icones dans l'image 1
icons_textures = {0:(0,0),1:(8,0),2:(0,8),3:(8,8),4:(16,0),5:(0,32),6:(8,32),7:(16,16),8:(24,24),9:(24,16),10:(24,0),11:(16,8),12:(24,8),13:(0,16),14:(8,16),15:(0,24),16:(8,24),17:(16,32),18:(24,32),19:(16,40),20:(24,40)}

## Tags des différents blocs ##
energie_source = (2,7,13,15)
normal_cables = (2,3)
horizontal_cables = (13,14)
vertical_cables = (15,16)
cables_blocks = normal_cables + horizontal_cables + vertical_cables
replaceable_block = 0
receiver_blocks = (8,9)
destroyable_blocks = cables_blocks + (5,6)
tnts = (4,10,11,12)
pushers = (17,18,19,20)
pushable = cables_blocks + tnts + (5,6)
notpushable = (1,7) + receiver_blocks

# Réserve de blocs (id:count)
block_storage = {}
# Bloc sélectionné
selected_block = None
# Temps de décalage de la sélection en frame, pour ajuster le clignotement si le joueur change de bloc sélectionné
selected_block_delayed_time = 0
# Blocs affichés
blocks_displayed = []

as_init = False
as_win = False
in_level_menu = True
in_help_menu = True

# Niveau en cours et niveau initial
level = 0

# Animation de fumée : [[x,y,temps de décallage]]
smoke_times = []

# Historique des actions : [[x,y,id avant,id apres]]
move_history = []

# Historique des positions des pushers déjà actionné à ce tour (update_blocks(),push_block())
grid_push_history = [[False] * max_size[False] for _ in range(max_size[1])]

def undo():
    '''
    Cette procédure annule la dernière action de l'utilisateur et ses conséquence sur la grille. Elle lui redonne également les blocs utilisés. Et le bloc précédement sélectionné.
    '''
    
    global move_history
    global grid
    global block_storage
    global selected_block

    if len(move_history) == 0:  # Vérifie si l'historique est vide
        print("Aucune action à annuler.")  # Message d'information
        return  # Rien à annuler
    
    last_move = move_history.pop()  # On récupère et on enlève le dernier mouvement

    grid = last_move[0]  # Recharger l'état de la grille avant l'action
    block_storage = last_move[1]  # Recharger les blocs de la réserve avant l'action
    auto_change_selected_block()
    selected_block = last_move[2]  # Recharger le bloc sélectionné avant l'action
    
    update_blocks()  # Mettre à jour la grille en fonction de l'énergie
    
def reset():
    '''
    Cette procédure reset totalement le niveau en remplaçant la grille et les blocs à disposition grâce à la procédure start_level().
    '''
    
    start_level(level)
    auto_change_selected_block() # Actualiser la sélection
    
def auto_change_selected_block():
    '''
    Cette procédure change la variable selected_block avec le premier élément d'un dictonnaire parcouru par itération, pour définir à nouveau le block à placer par défaut, si le dictionnaire block_storage est vide, selected_block prend la valeur None.
        La procédure ajoute également les 6 premiers éléments de du dictionnaire dans le tableau blocks_displayed
    '''
    global selected_block
    global blocks_displayed
    
    if len(block_storage) == 0:
        selected_block = None
        return # Pour arrêter la procédure
    
    if not (selected_block in block_storage):
        for elt in block_storage:
            selected_block = elt
            break
    
    # Pour mettres les premiers éléments dans blocks_displayed
    blocks_displayed = []
    counter = 0
    for elt in block_storage:
        blocks_displayed.append(elt)
        counter += 1
        if counter == 6:
            break

def start_level(level_id):
    '''
    Cette procédure va charger le niveau en utilisant le tableau data contenant les niveau, et en mettant grid et block_storage à leur valeur dans le dictionnaire n°level_id du tableau data
    :param level_id: (int) id du niveau (à partir de 0)
    '''
    
    # Préconditions
    assert type(level_id) is int, "level_id doit être un nombre entier"
    assert 0 <= level_id < len(data), "cet id ne correspond à aucun niveau, veillez à être entre 0 et len(data) exclus"
    
    print(f"Chargement du niveau {level_id}")
    
    global grid
    global block_storage
    global as_win
    global move_history
    global level
    
    grid = copy.deepcopy(data[level_id]["grid"])
    block_storage = copy.deepcopy(data[level_id]["block_storage"])
    level = level_id
    as_win = False # On vient de lancer le niveau, on a pas encore gagné
    move_history = [] # Reset l'historique des mouvements
    
    update_blocks()
    
    print(f"Grille chargée: {grid}")
    print(f"Stockage des blocs: {block_storage}")

def check_cell(x,y):
    '''
    Cette fonction va regarder la cellules aux coordonées x, y dans la liste grid (sous la forme grid[y][x]). Et renvoyer son contenu (donc grid[y][x]) ou bien None si l'indice ne correspond pas à une cellule de notre grille.
    :param x: (int), coordonée x
    :param y: (int), coordonée y
    :return: (int), block_id, id du bloc, grid[y][x]
    or :return: None, coordonées hors liste
    '''
    if 0 <= x < max_size[0] and 0 <= y < max_size[1]:
        return grid[y][x]
    else:
        return None

def energie_next_to_cell(x,y):
    '''
    Cette fonction regarde si l'un des blocs autours du bloc de coordonées x, y est alimenté par de l'énergie, si oui la fonction renvoie True sinon False
    :param x: (int) coordonée x dans la liste grid du bloc
    :param y: (int) coordonée y dans la liste grid du bloc
    :return: (bool)
    '''
    
    # Définition des directions possibles
    around_blocks = [[(-1, 0), (1, 0), (0, -1), (0, 1)],[(-1, 0), (1, 0)],[(0, -1), (0, 1)]]

    # Matrice pour marquer les blocs déjà vérifiés
    as_been_verif = [[False for _ in range(max_size[0])] for _ in range(max_size[1])]

    # On utilise une pile pour faire un parcours en profondeur
    stack = [(x, y)]
    
    # On vérifie qu'il y a des blocs cables dans la pile
    while len(stack) > 0:
        # On supprime le dernier cable de la pile et on récupère ses coordonnées
        now_x, now_y = stack.pop()

        # On vérifie si la position est hors limites
        if not (0 <= now_x < max_size[0] and 0 <= now_y < max_size[1]):
            continue # On passe au bloc suivant dans la pile

        stack_cell_id = check_cell(now_x, now_y)  # On sauvegarde le type du bloc actuel de la pile dans stack_cell_id
        
        
        if stack_cell_id == 15 or stack_cell_id == 16:
            verif_type = 2
        elif stack_cell_id == 13 or stack_cell_id == 14:
            verif_type = 1
        else:
            verif_type = 0
        
        # On regarde pour toutes les positions en fonction du type de vérification
        for pos in around_blocks[verif_type]:
            # Et on attribut des coordonnées temporaire à chaque bloc sélectionner
            new_x, new_y = now_x + pos[0], now_y + pos[1]

            # On vérifie si la position est hors limites
            if not (0 <= new_x < max_size[0] and 0 <= new_y < max_size[1]):
                continue # On passe à la position suivante de la boucle

            # On Vérifie si le bloc a déjà été visité
            if not as_been_verif[new_y][new_x]:
                as_been_verif[new_y][new_x] = True  # Si non, on le note comme visité dans la matrice as_been_verif

                cell_id = check_cell(new_x, new_y)  # On sauvegarde le type de ce bloc dans cell_id
                
                # Si c'est un générateur, on retourne True immédiatement, car cela veut dire que le cable est lié à un générateur
                if cell_id == 7:
                    return True

                # Si c'est un câble, on continue la recherche, on rajoute la position du cable trouvé dans la pile pour pouvoir le vérifier à son tour
                if cell_id in cables_blocks:
                        if (cell_id == 13 and new_y == now_y) or (cell_id == 15 and new_x == now_x) or (cell_id not in (13, 15)):
                            stack.append((new_x, new_y))
                
                # Après l'éxécution de la boucle for tout les voisins cables on été ajouté à la pile, s'il n'ont jamais été visité par notre recherche. On va donc parcourir tout les cables à la recherche d'un générateur.
                
    return False  # Aucun générateur n'a été trouvé, la pile est vide

def update_blocks():
    global grid_push_history
    grid_push_history = [[False] * max_size[False] for _ in range(max_size[1])] # On reset la grille d'historique d'utilisation des pushers pour un tour de vérification
    
    pushersToPush = []
    
    for y in range(max_size[1]):
        for x in range(max_size[0]):
            ## Changement de textures et effets avec l'énergie ##
            asEnergie = energie_next_to_cell(x, y) # Pour éviter de rappeller la fonction à chaque foit on sauveagrde le résultat dans une variable
            
            # Normal Cables #
            if grid[y][x] in normal_cables:
                grid[y][x] = 2 if asEnergie else 3
            # Unidirectional Cables #
            if grid[y][x] in horizontal_cables:
                grid[y][x] = 13 if asEnergie else 14
            if grid[y][x] in vertical_cables:
                grid[y][x] = 15 if asEnergie else 16
            # TNT #
            if grid[y][x] in tnts:
                if asEnergie:
                    explode_tnt(x,y)
            # Receiver #
            if grid[y][x] in receiver_blocks:
                if asEnergie:
                    grid[y][x] = 8
                    win()
                else:
                    grid[y][x] = 9
            # Pushers #
            if grid[y][x] in pushers and asEnergie:
                pushersToPush.append([x,y])
                
    for pusher in pushersToPush:
        push_block(pusher[0],pusher[1])

def push_block(x,y):
    '''
    A dplacer autre part : Le but est bougé un bloc lorsqu'il est activé
    '''
    
    # On récupère l'id du pusher
    block_id = check_cell(x,y)
    
    if block_id == 17: # Si le bloc a l'id 17 (correspondant au pusher vers la droite)
        direction = (1,0) # La direction est défini pour que quand je l'ajoute à mes coordonnées, je sois une case plus à droite
    elif block_id == 18:
        direction = (-1,0) # Direction définie sur gauche
    elif block_id == 19:
        direction = (0,-1) # Direction définie sur haut
    else:
        direction = (0,1) # Direction définie sur bas
    
    new_x, new_y = x, y # On définit les nouvelles coordonées
    block_counter = 0 # Nombre de blocs à déplacer avec le pusher
    
    while True:
        # On définit les nouvelles coordonées
        new_x, new_y = new_x + direction[0], new_y + direction[1]
        # On vérifie le bloc est hors limite
        if not (0 <= new_x < max_size[0] and 0 <= new_y < max_size[1]):
            return # On arrête la fonction
        
        # On récupère l'id du nouveau bloc dans la direction
        new_block_id = check_cell(new_x,new_y)
        if new_block_id in notpushable: # Si on ne peut pas le pousser
            return # On arrête la fonction
        
        if new_block_id == 0: # Si le bloc est du vide
            break # On arrête la boucle, on peut commencer à poucer
        
        # Si le bloc à passer les tests, on devra probablement le pousser
        block_counter += 1
        # La boucle continue
    
    new_x, new_y = x, y # On définit les nouvelles coordonées
    
    temp_block = [block_id] # Liste de blocs temporaire à remplacer
    grid[new_y][new_x] = 0
    
    for i in range(block_counter + 1):
        # On définit les nouvelles coordonées
        new_x, new_y = new_x + direction[0], new_y + direction[1]
            
        new_block_id = check_cell(new_x,new_y)
        if i < block_counter:  # On sauvegarde le bloc uniquement si ce n'est pas le dernier tour. Le bloc qui va être remplacer et que l'on va replacer à l'écution suivante de la boucle
            temp_block.append(new_block_id)
        
        grid[new_y][new_x] = temp_block.pop(0) # On change le bloc par le bloc le plus ancien de la liste que l'on retire de celle-ci
            
        print(f"Processing: ({new_x}, {new_y}), Block ID: {new_block_id}, Temp Block: {temp_block}")
        
    update_blocks() # Actualise la grille en fonction de l'énergie
    
def place_block(x,y,block_id):
    '''
    Cette procédure change le bloc aux coordonnées x, y dans la liste grid (sous la forme grid[y][x]) en le remplaçant par le bloc d'id block_id, ou directement par son alternative en fonction de si la case est alimentée en énergie.
    :param x: (int), coordonée x, comprise entre 0 et max_size[0] - 1
    :param y: (int), coordonée y, comprise entre 0 et max_size[1] - 1
    :param block_id: (int) id du bloc à placer
    '''
    
    # Préconditions
    assert type(x) is int, "x doit être un nombre entier"
    assert type(y) is int, "y doit être un nombre entier"
    assert 0 <= x < max_size[0], "x doit être compris entre 0 et max_size[0] - 1"
    assert 0 <= y < max_size[1], "y doit être compris entre 0 et max_size[1] - 1"
    
    # Ajouter le placement à l'historique
    move_history.append([copy.deepcopy(grid),copy.deepcopy(block_storage),selected_block])
    
    # Jouer le son de placement de bloc
    pyxel.play(0,0)
    
    if block_id in normal_cables and energie_next_to_cell(x,y):
        grid[y][x] = 2
    elif block_id in normal_cables:
        grid[y][x] = 3
    else:
        grid[y][x] = block_id
        
    # Enlever 1 bloc dans la réserve : block_storage, et changer de bloc sélectionner
    block_storage[block_id] -= 1
    if block_storage[block_id] == 0:
        del block_storage[block_id]
        auto_change_selected_block()
    
    update_blocks() # Actualise la grille en fonction de l'énergie

def explode_tnt(x,y):
    '''
    Cette procédure fait exploser une tnt de coordonées x, y.
    C'est à dire que tout les blocs destructibles à côté d'elle sont détruit et que les tnt à côté d'elle vont à leur tour exploser
    :param x: (int), coordonée x, comprise entre 0 et max_size[0] - 1
    :param y: (int), coordonée y, comprise entre 0 et max_size[1] - 1
    '''
    
    # Préconditions
    assert type(x) is int, "x doit être un nombre entier"
    assert type(y) is int, "y doit être un nombre entier"
    assert 0 <= x < max_size[0], "x doit être compris entre 0 et max_size[0] - 1"
    assert 0 <= y < max_size[1], "y doit être compris entre 0 et max_size[1] - 1"
    
    global block_storage
    
    # Tnt types : normal 4, hard 10, keep 11
    tnt_type = grid[y][x] # On sauvegarde le type de la tnt
    
    grid[y][x] = 0 # On remplace la tnt par un bloc vide
    smoke_times.append([x,y,pyxel.frame_count + 20])
    
    # Jouer le son d'explosion
    pyxel.play(0,1)
    
    # Liste de position des 4 blocs autour
    around_blocks = [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]
    
    for pos in around_blocks:
        # Pour détruire les blocs destructibles
        if check_cell(pos[0],pos[1]) in destroyable_blocks:
            # Donner le bloc détruit au joueur si tnt keep
            if tnt_type == 11:
                block_id = grid[pos[1]][pos[0]]
                if block_id in block_storage: # Si on a déjà un compteur du bloc d'id bloc_id dans block_storage
                    block_storage[block_id] += 1
                else:
                    block_storage[block_id] = 1
                auto_change_selected_block() # Pour actualisé réserve sur l'écran
            
            grid[pos[1]][pos[0]] = 0 # Remplacer le bloc par une case vide
        # Pour détruire les murs si la tnt est hard
        if check_cell(pos[0],pos[1]) == 1 and tnt_type == 10:
            grid[pos[1]][pos[0]] = 0
        # Pour faire exploser les autres tnt
        if check_cell(pos[0],pos[1]) in tnts:
            explode_tnt(pos[0],pos[1])
    
    update_blocks() # Actualise la grille en fonction de l'énergie

def win():
    global as_win
    as_win = True

def init():
    global as_init
    global as_win
    
    # A éxécuter une seule fois au tout début
    start_level(level)
    auto_change_selected_block()
        
    as_init = True

def game_update():
    '''
    Cette procédure gère tous les aspects du jeu à chaque frame, lorqu'il est en cours.
    On y retrouve par exemple : la gestion des clics sur la grille pour poser les blocs, la gestion des clics dans la réserve pour sélectionner des blocs, l'actualisation des cellules de la grille en fonction de l'énergie, et la possibilité de reset et annuler
    '''
    
    global selected_block
    global selected_block_delayed_time
    global in_level_menu
    global block_displayed

    ## Placement de blocs  et Changement de bloc sélectioné ##
    if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and selected_block != None:
        x = pyxel.mouse_x
        y = pyxel.mouse_y
        
        # Vérifier qu'on clique sur la grille
        if start_x < x < window_size[0] - start_x and start_y < y < window_size[1] - start_y:
            
            aim_x = (x - start_x) // cell_size[0]
            aim_y = (y - start_y) // cell_size[1]
            
            if (grid[aim_y][aim_x] == replaceable_block):
                place_block(aim_x,aim_y,selected_block)
                
        # Changement de bloc sélectionné       
        element_distance = window_size[0] // 7
        for i in range(1,7):
            if element_distance * i - 1 < x < element_distance * i + 8 and 5 < y < 14:
                selected_block = blocks_displayed[i-1]
                selected_block_delayed_time = pyxel.frame_count % 60 # On met le décalage de l'animation de sélection au moment où on clique
        
    # Annuler le dernier mouvement si touche z appuyée
    if pyxel.btnp(pyxel.KEY_Z):
        undo()
   
    # Reset du niveau si touche r appuyée
    if pyxel.btnp(pyxel.KEY_R):
        reset()
        
    # va au menu des niveaux si touche m appuyée
    if pyxel.btnp(pyxel.KEY_M):
        in_level_menu = True
    
    if pyxel.btnp(pyxel.KEY_SPACE):
        # Actualise la grille, permet de faire un nouveau tour
        update_blocks()
        
    # Changer de bloc sélectionné
    if pyxel.btnp(pyxel.KEY_RIGHT):  # Appuyez sur les fleches de direction pour changer de bloc
        if selected_block != None:
            current_index = blocks_displayed.index(selected_block) # On sauvegarde l'indice dans block_displayed de notre bloc sélectionné
            next_index = (current_index + 1) % len(blocks_displayed)  # On incrémente l'indexe actuel de 1 pour passer au suivant. Et on garde le reste de la division par le nombre d'éléments dans blocks_displayed. Donc si current_index + 1 est égal ou dépasse la longueur de blocks_displayed, celle ci sera soutraite au résultat, créant une boucle. 
            selected_block = blocks_displayed[next_index]
            selected_block_delayed_time = pyxel.frame_count % 60 # On met le décalage de l'animation de sélection au moment où on clique
    if pyxel.btnp(pyxel.KEY_LEFT):  # Pour la droite donc dans l'autre sens
        if selected_block != None:
            current_index = blocks_displayed.index(selected_block) # Récupération de l'indice de la sélection
            next_index = (current_index - 1) % len(blocks_displayed)  # On décrémente l'indexe actuel de 1 pour passer au précédant. Le nombre peut ici être négatif. Le symbole % représente donc l'opérateur modulo en python qui grâce à mes tests m'a montré que par exemple -1%4 = 3. Donc si notre indice est négatif (donc -1) et que je fait un modulo avec la longueur de la liste, on en revient au dernier indice de la liste (len(liste)-1), créant une boucle. 
            selected_block = blocks_displayed[next_index]
            selected_block_delayed_time = pyxel.frame_count % 60 # On met le décalage de l'animation de sélection au moment où on clique
    
def update():
    # Déclancher la fonction init si elle n'a pas encore été éxecuter
    if not as_init:
        init()
    
    global level
    global in_level_menu
    global in_help_menu
    global as_win
    
    if as_win: # Si on a gagné
        if pyxel.btnp(pyxel.KEY_SPACE) and level < len(data) - 1:
            level += 1
            start_level(level)
            auto_change_selected_block()
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x = pyxel.mouse_x
            y = pyxel.mouse_y
            
            if 28 < x < 70 and 78 < y < 86: # Si on clique sur le bouton Level Menu
                in_level_menu = True
                as_win = False
            elif 83 < x < 125 and 78 < y < 86 and level < len(data) - 1: # Si on clique sur le bouton Next level
                level += 1
                start_level(level)
                auto_change_selected_block()
    elif in_level_menu and not in_help_menu: # Si on est dans le menu des niveaux, mais pas dans le menu aide
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x = pyxel.mouse_x
            y = pyxel.mouse_y
            
            rank = 0 # Corespond au rang actuel, ou va être placé le niveau
            step = 0 # Correspond à la place actuelle, ou va être placé le niveau
            for i in range(len(data)):
                if step == 6:
                    step = 0
                    rank += 1
            #pyxel.rect(20 + step * 20, 35 + rank * 20, 15, 15, 5)
                if (19 + step * 20 < x < 35 + step * 20) and (34 + rank * 20 < y < 50 + rank * 20): # Si on clique sur le bouton Level Menu
                    in_level_menu = False
                    start_level(rank * 6 + step)
                    auto_change_selected_block()
                step += 1
    elif in_help_menu:
        # Si on clique sur la croix rouge
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x = pyxel.mouse_x
            y = pyxel.mouse_y
            
            if (132<x<143) and (24<y<35):
                in_help_menu = False
    else: # Si on a pas gagné et que l'on est pas dans le menu de sélection des niveaux et/ou dans le menu aide, les actions du jeu sont possibles
        game_update()

def draw():
    pyxel.cls(1)  # Efface l'écran en bleu foncé
    
    ## On affiche la grille ##
    # Inverser les indices ici aussi
    for y in range(max_size[1]):
        for x in range(max_size[0]):
            texture_x, texture_y = blocks_textures[grid[y][x]]  # Coordonnées de texture
            
            pos_x = start_x + x * cell_size[0]
            pos_y = start_y + y * cell_size[1]
        
            pyxel.blt(pos_x, pos_y, 0, texture_x, texture_y, cell_size[0], cell_size[1])
    
    ## On affiche les petits icones pour montrer les blocs dans la réserve ##
    different_blocks_count = 0
    element_distance = window_size[0] // 7
    
    for elt in block_storage: # elt correspond à la clef du dictionnaire
        if different_blocks_count == 6:
            break # On ne veux que 6 blocs max de notre réserve affichés à l'écran
        
        texture_x, texture_y = icons_textures[elt]  # Coordonnées de texture
        pyxel.blt(element_distance * ( different_blocks_count + 1 ), 6, 1, texture_x, texture_y, 8, 8)
        pyxel.text(element_distance * ( different_blocks_count + 1 ) + 10, 7, "x" + str(block_storage[elt]),7)
        
        # Si le bloc est sélectionner, lui ajouter un contour pendant 1s toutes les 1s
        if selected_block == elt and (pyxel.frame_count + selected_block_delayed_time) % 60 > 30:
            pyxel.blt(element_distance * ( different_blocks_count + 1 ) - 4, 2, 1, 32, 0, 16, 16, 1)
        
        different_blocks_count += 1
    
    if as_win: # Afficher l'écran de fin de niveau
        pyxel.rect(20, 25, window_size[0] - 40, 65, 5) # Fond
        pyxel.text(58, 30, "Well Done !",7)
        pyxel.text(65, 40, "You won",7)
        pyxel.text(25, 60, "Press the space bar to go to",7)
        pyxel.text(50, 70, "the next level...",7)
        pyxel.rect(29, 79, 41, 7, 12) # Fond du bouton level menu
        pyxel.rect(84, 79, 41, 7, 12) # Fond du bouton next level
        pyxel.text(30, 80, "Level Menu",7)
        pyxel.text(85, 80, "Next Level",7)
        
        
    for time in smoke_times[:]: # On parcourt une copie de la liste pour éviter les problèmes dû à la supression d'éléments
        if pyxel.frame_count < time[2]:
            pyxel.blt(start_x + time[0] * cell_size[0], start_y + time[1] * cell_size[1], 1, 48, 0, 16, 16, 1)
        else:
            smoke_times.remove(time)
    
    # Afficher l'identifiant du niveau dans le coin haut-droit
    pyxel.text(window_size[0] - 5, 4, str(level), 7)
    
    if in_level_menu: # Afficher le menu des niveaux
        pyxel.cls(1)  # Efface l'écran en bleu foncé
        #pyxel.rect(20, 25, window_size[0] - 40, 65, 5) # Fond
        pyxel.text(58, 10, "GridPower",7)
        pyxel.text(20, 25, "Select a level...",7)
        
        rank = 0 # Corespond au rang actuel, ou va être placé le niveau
        step = 0 # Correspond à la place actuelle, ou va être placé le niveau
        for i in range(len(data)):
            if step == 6:
                step = 0
                rank += 1
            
            pyxel.rect(20 + step * 20, 35 + rank * 20, 15, 15, 5) # Fond du bouton level menu
            if i < 10:
                pyxel.text(24 + step * 20, 40 + rank * 20, "0" + str(i), 7) # Id du niveau au milieu de la case avec un 0 en plus
            else:
                pyxel.text(24 + step * 20, 40 + rank * 20, str(i), 7) # Id du niveau au milieu de la case
            
            step += 1

    if in_help_menu: # Si on affiche le menu d'aide
        pyxel.blt(15, 25, 2, 0, 0, 128, 80, 1) # On affiche la texture de base du menu
        # Puis on affiche les textes
        pyxel.text(30, 32, "To undo an action", 7) # Texte pour touche Z
        pyxel.text(30, 48, "To reset the entire level", 7) # Texte pour touche R
        pyxel.text(30, 64, "To return in the level menu", 7) # Texte pour touche M
        pyxel.text(32, 80, "To do nothing,", 7) # Texte pour space bar
        pyxel.text(32, 88, "pass one turn (for pushers)", 7) # Texte pour space bar

pyxel.run(update, draw)