from enum import Enum, auto
import pygame
import sys
import os
import random

class PieceType(Enum):
    PAWN   = auto()
    KNIGHT = auto()
    BISHOP = auto()
    ROOK   = auto()
    QUEEN  = auto()
    KING   = auto()

class Game:
    def __init__(self):
        width = 640 
        height = 640 
        self.screen = pygame.display.set_mode((width, height+60))
        self.board = Board(width, height, self.screen)
        self.current_turn = 'white'
        self.input_text = ""
        self.font = pygame.font.SysFont(None, 32)
        self.font_small = pygame.font.SysFont(None, 24)
        self.error_message = None
        
        # Game mode buttons
        self.buttons = []
        self.create_buttons()
        self.game_mode = None  # None, 'normal', 'fischer', or 'two_rooks'
        
        # Piece selection and valid moves
        self.selected_piece = None
        self.valid_moves = []
        
        # PGN file handling
        self.use_pgn_file = True  # Set this to True to use PGN file
        # Use absolute path to avoid issues with relative paths
        self.pgn_file_path = os.path.join(os.path.dirname(__file__), "game.pgn")  # Set your PGN file path here
        self.pgn_moves = []
        self.current_move_index = 0
        
        if self.use_pgn_file:
            self.load_pgn_file()

    def create_buttons(self):
        button_width = 150
        button_height = 40
        spacing = 20
        total_width = (button_width * 3) + (spacing * 2)
        start_x = (self.board.width - total_width) // 2
        
        # Create three buttons
        self.buttons = [
            pygame.Rect(start_x, self.board.height + 10, button_width, button_height),
            pygame.Rect(start_x + button_width + spacing, self.board.height + 10, button_width, button_height),
            pygame.Rect(start_x + (button_width + spacing) * 2, self.board.height + 10, button_width, button_height)
        ]
        
        # Button text
        self.button_texts = ["Aufgabe 1", "Aufgabe 2", "Aufgabe 3"]
        self.button_font = pygame.font.SysFont(None, 28)

    def draw_buttons(self):
        for i, button in enumerate(self.buttons):
            # Draw button background
            pygame.draw.rect(self.screen, (200, 200, 200), button)
            pygame.draw.rect(self.screen, (100, 100, 100), button, 2)
            
            # Draw button text
            text = self.button_font.render(self.button_texts[i], True, (0, 0, 0))
            text_rect = text.get_rect(center=button.center)
            self.screen.blit(text, text_rect)

    def handle_button_click(self, pos):
        for i, button in enumerate(self.buttons):
            if button.collidepoint(pos):
                if i == 0:  # Aufgabe 1 - Normal Chess
                    self.game_mode = 'normal'
                    self.board.setup_pieces()  # Reset to normal starting position
                elif i == 1:  # Aufgabe 2 - Fischer Random
                    self.game_mode = 'fischer'
                    print("Fischer Random")
                    self.board.setup_fischer_random()
                elif i == 2:  # Aufgabe 3 - Two Rooks vs Two Pawns
                    self.game_mode = 'two_rooks'
                    print("Two Rooks vs Two Pawns")
                    self.board.setup_two_rooks()
                return True
        return False

    def get_grid_position(self, screen_pos):
        # Convert screen coordinates to grid coordinates
        x, y = screen_pos
        if y >= self.board.height:  # Clicked below the board
            return None
        col = x // self.board.square_size
        row = y // self.board.square_size
        return (row, col)

    def handle_piece_click(self, pos):
        grid_pos = self.get_grid_position(pos)
        if grid_pos is None:
            return

        row, col = grid_pos
        clicked_piece = self.board.grid[row][col]

        # If no piece is selected and clicked on a piece of current player's color
        if self.selected_piece is None and clicked_piece and clicked_piece.color == self.current_turn:
            self.selected_piece = (row, col)
            # Get valid moves for the selected piece
            self.valid_moves = clicked_piece.get_valid_moves(self.board)
            return
        if self.selected_piece is not None:
            if row == self.selected_piece[0] and col == self.selected_piece[1]:
                self.selected_piece = None
                self.valid_moves = []   
                return
            elif clicked_piece is not None:
                self.selected_piece = (row, col)
                # Get valid moves for the selected piece
                self.valid_moves = clicked_piece.get_valid_moves(self.board)
                return

    def load_pgn_file(self):
        try:
            with open(self.pgn_file_path, 'r') as file:
                content = file.read()
                # Split the content into moves
                moves = content.split()
                # Remove move numbers (e.g., "1.", "2.", etc.)
                self.pgn_moves = [move for move in moves if not move.endswith('.')]
                if self.pgn_moves:
                    self.input_text = self.pgn_moves[0]
        except FileNotFoundError:
            self.error_message = f"PGN file not found: {self.pgn_file_path}"
        except Exception as e:
            self.error_message = f"Error loading PGN file: {str(e)}"

    def load_next_move(self):
        if self.current_move_index < len(self.pgn_moves) - 1:
            self.current_move_index += 1
            self.input_text = self.pgn_moves[self.current_move_index]
            return True
        return False

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.game_mode is None:
                        if self.handle_button_click(event.pos):
                            continue
                    else:
                        self.handle_piece_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if self.game_mode is None:
                    continue
                if event.key == pygame.K_RETURN:
                    if self.play_move(self.input_text):
                        self.error_message = None
                        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
                        self.board.print_board()
                        
                        if self.use_pgn_file:
                            if not self.load_next_move():
                                self.error_message = "End of PGN file reached"
                        else:
                            self.input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                    self.error_message = None
                else:
                    if not self.use_pgn_file and len(self.input_text) < 4:
                        self.input_text += event.unicode
                        self.error_message = None
        if self.game_mode is None:
            self.screen.fill((255, 255, 255))
            self.draw_buttons()
            pygame.display.flip()
            return
        self.board.print_board()
        self.draw_valid_moves()
        self.draw_input_field()
        pygame.display.flip()

    def draw_input_field(self):
        input_rect = pygame.Rect(0, self.board.height+20, self.board.width, 40)
        pygame.draw.rect(self.screen, (255, 255, 255), input_rect)
        
        # Draw current player indicator
        player_color = (0, 0, 0)
        player_text = f"{self.current_turn.capitalize()}'s turn"
        player_surface = self.font_small.render(player_text, True, player_color)
        self.screen.blit(player_surface, (self.board.width - 100, self.board.height + 30))
        
        # Draw input field label
        label_surface = self.font.render("Input Move:", True, (0, 0, 0))
        self.screen.blit(label_surface, (10, self.board.height + 30))
        
        input_field_rect = pygame.Rect(200, self.board.height + 25, 100, 30)
        pygame.draw.rect(self.screen, (240, 240, 240), input_field_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), input_field_rect, 1)
        
        input_surface = self.font.render(self.input_text, True, (0, 0, 0))
        self.screen.blit(input_surface, (205, self.board.height + 30))

        # Draw error message if exists
        if self.error_message:
            error_rect = pygame.Rect(320, self.board.height + 25, 300, 30)
            pygame.draw.rect(self.screen, (255, 200, 200), error_rect)
            pygame.draw.rect(self.screen, (255, 0, 0), error_rect, 1)
            error_surface = self.font.render(self.error_message, True, (255, 0, 0))
            self.screen.blit(error_surface, (325, self.board.height + 30))

    def draw_valid_moves(self):
        if self.selected_piece is not None:
            for move in self.valid_moves:
                # Draw a circle to indicate valid move
                center_x = move.to_col * self.board.square_size + self.board.square_size // 2
                center_y = move.to_row * self.board.square_size + self.board.square_size // 2
                pygame.draw.circle(self.screen, (0, 255, 0, 128), (center_x, center_y), self.board.square_size // 4, 2)

    def play_move(self, text_move):
        #Convert row and column to 0-7 range
        file_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    
        try:
            # Handle castling
            #We extract were we are castling and give the logic to the board
            if text_move == "O-O":  # Kingside castling
                rank = 7 if self.current_turn == 'white' else 0
                king_from = (rank, 4)
                king_to = (rank, 6)
                rook_from = (rank, 7)
                rook_to = (rank, 5)
                
                success = self.board.castle(king_from, king_to, rook_from, rook_to, self.current_turn)
                if not success:
                    self.error_message = "Invalid castling move"
                return success
            
            elif text_move == "O-O-O":  # Queenside castling
                rank = 7 if self.current_turn == 'white' else 0
                king_from = (rank, 4)
                king_to = (rank, 2)
                rook_from = (rank, 0)
                rook_to = (rank, 3)
                
                success = self.board.castle(king_from, king_to, rook_from, rook_to, self.current_turn)
                if not success:
                    self.error_message = "Invalid castling move"
                return success
            
            #We save if there is a check or checkmate and at the end we check if there is a check or checkmate on our side
            is_check = '+' in text_move
            is_checkmate = '#' in text_move
            # Remove check/checkmate symbols
            text_move = text_move.replace('+', '').replace('#', '')

            # Handle pawn promotion
            #We do the move and then we check for promotion
            promotion_type = None
            if '=' in text_move:
                move_part, promotion_part = text_move.split('=')
                #We remove the = and the promotion part
                text_move = move_part
                piece_map = {
                    'Q': PieceType.QUEEN,
                    'R': PieceType.ROOK,
                    'B': PieceType.BISHOP,
                    'N': PieceType.KNIGHT
                }
                promotion_type = piece_map[promotion_part]
            
            # Handle captures
            is_capture = 'x' in text_move
            #We remove the x
            text_move = text_move.replace('x', '')

            # Handle basic pawn moves and captures these are just the first two letters of the move
            if len(text_move) == 2 and text_move[0].lower() in file_map:  # e.g., "e4"
                # We get the file from the map. The rank is the secind char but bc. we start at the top left we need to subtract it from 8
                file = file_map[text_move[0].lower()]
                rank = 8 - int(text_move[1])
                from_rank = None
                #We move the pawn and then we check if there is a promotion
                success = self.board.move_piece(PieceType.PAWN, (from_rank, file), (rank, file), self.current_turn)
                if not success:
                    self.error_message = "Invalid pawn move"
                if success and promotion_type:
                    success = self.board.promote_pawn(promotion_type, (rank, file))
                    if not success:
                        self.error_message = "Invalid pawn promotion"
                return success

            # Handle pawn captures (e.g., "exd5") the x is already removed. When the first char is in the file_map we know it is a pawn capture
            elif len(text_move) == 3 and text_move[0] in file_map and is_capture:
                src_file = None
                src_rank = None
                if text_move[0].isalpha():
                    src_file = file_map[text_move[0]]
                    src_rank = None
                else:
                    src_file = None
                    src_rank = 8 - int(text_move[0])
                dest_file = file_map[text_move[1]]
                dest_rank = 8 - int(text_move[2])
                success = self.board.move_piece_capture(PieceType.PAWN, (src_rank, src_file), (dest_rank, dest_file), self.current_turn)
                if not success:
                    self.error_message = "Invalid pawn capture"
                return success

            # Handle piece moves other than pawn with possible disambiguation
            else:
                piece_map = {
                    'K': PieceType.KING,
                    'Q': PieceType.QUEEN,
                    'R': PieceType.ROOK,
                    'B': PieceType.BISHOP,
                    'N': PieceType.KNIGHT
                }
                
                #Check if the first char is a piece. when not this is invalid
                if text_move[0] in piece_map:
                    piece_type = piece_map[text_move[0]]
                    dest_file = file_map[text_move[-2]]
                    dest_rank = 8 - int(text_move[-1])
                    
                    # Handle disambiguation (e.g., "Nbd7" or "R1e2")
                    src_file = None
                    src_rank = None
                    #If there is a second char we know it is a disambiguation
                    if len(text_move) == 4:
                        if text_move[1].isalpha():
                            src_file = file_map[text_move[1].lower()]
                        else:
                            src_rank = 8 - int(text_move[1])
                    #src_rank and src_file will be None if there is no disambiguation. the logic will be handled in the move_piece function
                    if is_capture:
                        success = self.board.move_piece_capture(piece_type, (src_rank, src_file), (dest_rank, dest_file), self.current_turn)
                        if not success:
                            self.error_message = f"Invalid {piece_type.name.lower()} capture"
                    else:
                        success = self.board.move_piece(piece_type, (src_rank, src_file), (dest_rank, dest_file), self.current_turn)
                        if not success:
                            self.error_message = f"Invalid {piece_type.name.lower()} move"
                    return success
                else:
                    self.error_message = "Invalid piece notation"
                    return False
            #If the move is not handled by the above, it is invalid
            self.error_message = "Invalid move format"
            return False
        
        except (KeyError, ValueError, IndexError):
            self.error_message = "Invalid move syntax"
            return False

class Board:
    def __init__(self, width, height, screen):
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.square_size = width // 8
        self.screen = screen
        self.width = width
        self.height = height
        self.whiteInCheck = False
        self.blackInCheck = False
        
        # Cache for piece images
        self.piece_images = {}
        self.load_piece_images()

    def load_piece_images(self):
        # Load and scale all piece images once
        piece_types = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
        colors = ['white', 'black']
        
        for color in colors:
            for piece_type in piece_types:
                pre_string = f"{color}_{piece_type}"
                image_path = os.path.join(os.path.dirname(__file__), f"Figuren/{pre_string}.png")
                image = pygame.image.load(image_path)
                scaled_image = pygame.transform.scale(image, (self.square_size, self.square_size))
                self.piece_images[pre_string] = scaled_image

    def setup_pieces(self):
        #We setup the pieces in the starting position
        white_pieces = [
            Piece('white', (7, 0), PieceType.ROOK),
            Piece('white', (7, 1), PieceType.KNIGHT),
            Piece('white', (7, 2), PieceType.BISHOP),
            Piece('white', (7, 3), PieceType.QUEEN),
            Piece('white', (7, 4), PieceType.KING),
            Piece('white', (7, 5), PieceType.BISHOP),
            Piece('white', (7, 6), PieceType.KNIGHT),
            Piece('white', (7, 7), PieceType.ROOK),
            Piece('white', (6, 0), PieceType.PAWN),
            Piece('white', (6, 1), PieceType.PAWN), 
            Piece('white', (6, 2), PieceType.PAWN),
            Piece('white', (6, 3), PieceType.PAWN),
            Piece('white', (6, 4), PieceType.PAWN),
            Piece('white', (6, 5), PieceType.PAWN),
            Piece('white', (6, 6), PieceType.PAWN),
            Piece('white', (6, 7), PieceType.PAWN)
        ]
        black_pieces = [
            Piece('black', (0, 0), PieceType.ROOK),
            Piece('black', (0, 1), PieceType.KNIGHT),
            Piece('black', (0, 2), PieceType.BISHOP),
            Piece('black', (0, 3), PieceType.QUEEN),
            Piece('black', (0, 4), PieceType.KING),
            Piece('black', (0, 5), PieceType.BISHOP),
            Piece('black', (0, 6), PieceType.KNIGHT),
            Piece('black', (0, 7), PieceType.ROOK),
            Piece('black', (1, 0), PieceType.PAWN),
            Piece('black', (1, 1), PieceType.PAWN),
            Piece('black', (1, 2), PieceType.PAWN),
            Piece('black', (1, 3), PieceType.PAWN),
            Piece('black', (1, 4), PieceType.PAWN),
            Piece('black', (1, 5), PieceType.PAWN),
            Piece('black', (1, 6), PieceType.PAWN),
            Piece('black', (1, 7), PieceType.PAWN)
        ]
        #We add the pieces to the grid
        for piece in white_pieces:
            self.grid[piece.position[0]][piece.position[1]] = piece
        for piece in black_pieces:
            self.grid[piece.position[0]][piece.position[1]] = piece
 
    # starting position rules: 
    # pawns are in their usual position
    # bishops must be on opposite-colored squares
    # king must be between the two rooks

    def setup_fischer_random(self):
        print("Fischer Random")      
        # set up pawns 
        black_pieces = [
            Piece('black', (1, 0), PieceType.PAWN),
            Piece('black', (1, 1), PieceType.PAWN),
            Piece('black', (1, 2), PieceType.PAWN),
            Piece('black', (1, 3), PieceType.PAWN),
            Piece('black', (1, 4), PieceType.PAWN),
            Piece('black', (1, 5), PieceType.PAWN),
            Piece('black', (1, 6), PieceType.PAWN),
            Piece('black', (1, 7), PieceType.PAWN)
        ]
        white_pieces = [
            Piece('white', (6, 0), PieceType.PAWN),
            Piece('white', (6, 1), PieceType.PAWN), 
            Piece('white', (6, 2), PieceType.PAWN),
            Piece('white', (6, 3), PieceType.PAWN),
            Piece('white', (6, 4), PieceType.PAWN),
            Piece('white', (6, 5), PieceType.PAWN),
            Piece('white', (6, 6), PieceType.PAWN),
            Piece('white', (6, 7), PieceType.PAWN)
        ]

        # set up white bank-rank pieces 

        numbers = list(range(8))  # [0, 1, 2, ..., 8]

        # set up bishops 
        bish_pos = random.randint(0, 7)
       
        if bish_pos%2 == 0: # if bishop is on pink
            bish_pos2 = random.choice([1, 3, 5, 7,])
        else:
            bish_pos2 = random.choice([0, 2, 4, 6])
        
        white_pieces.append(Piece('white',(7, bish_pos), PieceType.BISHOP))
        white_pieces.append(Piece('white',(7, bish_pos2), PieceType.BISHOP))

        numbers.remove(bish_pos)
        numbers.remove(bish_pos2)

        # set rooks 
        rook_pos = random.choice(numbers)
        index = numbers.index(rook_pos)
        numbers.remove(rook_pos)
        valid_choices = []
        for i, num in enumerate(numbers):
             if abs(i - index) > 1:  # not same index, not neighbor
                 valid_choices.append(num)

        rook_pos2 = random.choice(valid_choices)

        white_pieces.append(Piece('white', (7, rook_pos), PieceType.ROOK))
        white_pieces.append(Piece('white', (7, rook_pos2), PieceType.ROOK))
        numbers.remove(rook_pos2)
    
        # set king
        # Determine the lower and upper bounds
        lower = min(rook_pos, rook_pos2)
        upper = max(rook_pos, rook_pos2)
        valid_choices2= [num for num in numbers if lower < num < upper]
        king_pos = random.choice(valid_choices2)

        white_pieces.append(Piece('white', (7, king_pos), PieceType.KING))
        numbers.remove(king_pos)

        # set Queen
        queen_pos = random.choice(numbers)

        white_pieces.append(Piece('white', (7, queen_pos), PieceType.QUEEN))
        numbers.remove(queen_pos)

        # set knight
        knight_pos = random.choice(numbers)
        numbers.remove(knight_pos)
        knight_pos2 = random.choice(numbers)

        white_pieces.append(Piece('white', (7, knight_pos), PieceType.KNIGHT))
        white_pieces.append(Piece('white', (7, knight_pos2), PieceType.KNIGHT))
        
        numbers.remove(knight_pos2)







        # set up black back-rank pieces

        numbers_black = list(range(8))  # [0, 1, 2, ..., 8]

        # set up bishops
        bish_pos_black = random.randint(0, 7)

        if bish_pos_black % 2 == 0:  # if bishop is on white
            bish_pos2_black = random.choice([1, 3, 5, 7])
        else:
            bish_pos2_black = random.choice([0, 2, 4, 6])

        black_pieces.append(Piece('black', (0, bish_pos_black), PieceType.BISHOP))
        black_pieces.append(Piece('black', (0, bish_pos2_black), PieceType.BISHOP))

        numbers_black.remove(bish_pos_black)
        numbers_black.remove(bish_pos2_black)

        # set rooks
        rook_pos_black = random.choice(numbers_black)
        index_black = numbers_black.index(rook_pos_black)
        numbers_black.remove(rook_pos_black)
        valid_choices_black = []
        for i, num in enumerate(numbers_black):
            if abs(i - index_black) > 1:  # not same index, not neighbor
                valid_choices_black.append(num)

        rook_pos2_black = random.choice(valid_choices_black)

        black_pieces.append(Piece('black', (0, rook_pos_black), PieceType.ROOK))
        black_pieces.append(Piece('black', (0, rook_pos2_black), PieceType.ROOK))

        numbers_black.remove(rook_pos2_black)

        # set king
        lower_black = min(rook_pos_black, rook_pos2_black)
        upper_black = max(rook_pos_black, rook_pos2_black)
        valid_choices2_black = [num for num in numbers_black if lower_black < num < upper_black]

        king_pos_black = random.choice(valid_choices2_black)

        black_pieces.append(Piece('black', (0, king_pos_black), PieceType.KING))
        numbers_black.remove(king_pos_black)

        # set Queen
        queen_pos_black = random.choice(numbers_black)

        black_pieces.append(Piece('black', (0, queen_pos_black), PieceType.QUEEN))
        numbers_black.remove(queen_pos_black)

        # set knights
        knight_pos_black = random.choice(numbers_black)
        numbers_black.remove(knight_pos_black)

        knight_pos2_black = random.choice(numbers_black)
        numbers_black.remove(knight_pos2_black)

        black_pieces.append(Piece('black', (0, knight_pos_black), PieceType.KNIGHT))
        black_pieces.append(Piece('black', (0, knight_pos2_black), PieceType.KNIGHT))


        for piece in white_pieces:
            self.grid[piece.position[0]][piece.position[1]] = piece
        for piece in black_pieces:
            self.grid[piece.position[0]][piece.position[1]] = piece




    def setup_two_rooks(self):
        pass
    def move_piece(self, piece_type: PieceType, from_pos: tuple[int | None, int | None], to_pos: tuple[int, int], current_turn: str) -> bool:
        # Find all pieces that match the type and position constraints
        candidate_pieces = []
        
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if (piece and 
                    piece.type == piece_type and 
                    piece.color == current_turn and  # Make sure it's the current player's piece
                    (from_pos[0] is None or from_pos[0] == row) and  # Match rank if specified
                    (from_pos[1] is None or from_pos[1] == col)):    # Match file if specified
                    
                    # Check if this piece can actually move to the target
                    valid_moves = piece.get_valid_moves(self)
                    for move in valid_moves:
                        if move.to_row == to_pos[0] and move.to_col == to_pos[1] and move.is_capture == False:
                            candidate_pieces.append((piece, move))
        
        # If there's exactly one candidate, make the move
        if len(candidate_pieces) == 1:
            piece, move = candidate_pieces[0]
            
            # Make the move
            self.grid[move.to_row][move.to_col] = piece
            self.grid[move.from_row][move.from_col] = None
            piece.position = (move.to_row, move.to_col)
            piece.has_moved = True
            return True
        
        return False

    def move_piece_capture(self, piece_type: PieceType, from_pos: tuple[int | None, int | None], to_pos: tuple[int, int], current_turn: str) -> bool:
        if piece_type == PieceType.PAWN:
            print(from_pos, to_pos)
        print("PAWN-----")
        candidate_pieces = []
        
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if (piece and 
                    piece.type == piece_type and 
                    piece.color == current_turn and  # Make sure it's the current player's piece
                    (from_pos[0] is None or from_pos[0] == row) and  # Match rank if specified
                    (from_pos[1] is None or from_pos[1] == col)):    # Match file if specified
                    
                    # Check if this piece can actually move to the target
                    valid_moves = piece.get_valid_moves(self)
                    for move in valid_moves:
                        if piece_type == PieceType.PAWN:
                            print(move.to_row, move.to_col)
                        #We check if the move is a capture
                        if move.to_row == to_pos[0] and move.to_col == to_pos[1] and move.is_capture == True:
                            candidate_pieces.append((piece, move))
        
        # If there's exactly one candidate, make the move
        if len(candidate_pieces) == 1:
            piece, move = candidate_pieces[0]
            
            # Make the move
            self.grid[move.to_row][move.to_col] = piece
            self.grid[move.from_row][move.from_col] = None
            piece.position = (move.to_row, move.to_col)
            piece.has_moved = True
            return True
        
        return False

    def castle(self, king_from: tuple[int, int], king_to: tuple[int, int], rook_from: tuple[int, int], rook_to: tuple[int, int], current_turn: str) -> bool:
         # Check if king and rook are in the correct positions
        king = self.grid[king_from[0]][king_from[1]]
        rook = self.grid[rook_from[0]][rook_from[1]]
        #We check if the king and rook are in the correct positions
        if not king or king.type != PieceType.KING or not rook or rook.type != PieceType.ROOK:
            return False
        
        # Check the path is clear between king and rook
        if king_to[1] > king_from[1]:  # Kingside castle
            path_range = range(king_from[1] + 1, rook_from[1])
        else:  # Queenside castle
            path_range = range(rook_from[1] + 1, king_from[1])
        
        for col in path_range:
            if self.grid[king_from[0]][col] is not None:
                return False
        
        # Check that the king is not currently in check
        if current_turn == 'white' and self.whiteInCheck:
            return False
        elif current_turn == 'black' and self.blackInCheck:
            return False
        
        #Check if king and rook have not moved yet
        if king.has_moved or rook.has_moved:
            return False

        # Check that the squares the king passes through aren't under attack
        if king_to[1] > king_from[1]:  # Kingside
            for col in [king_from[1] + 1, king_from[1] + 2]:
                if self.is_square_under_attack(king.color, king_from[0], col):
                    return False
        else:  # Queenside
            for col in [king_from[1] - 1, king_from[1] - 2]:
                if self.is_square_under_attack(king.color, king_from[0], col):
                    return False
        
        # Perform the castle
        self.grid[king_to[0]][king_to[1]] = king
        self.grid[king_from[0]][king_from[1]] = None
        king.position = king_to
        king.has_moved = True
        
        self.grid[rook_to[0]][rook_to[1]] = rook
        self.grid[rook_from[0]][rook_from[1]] = None
        rook.position = rook_to
        rook.has_moved = True
        
        return True

    def promote_pawn(self, piece_type: PieceType, pos: tuple[int, int]) -> bool:
        piece = self.grid[pos[0]][pos[1]]
        # Check that there's a pawn at the specified position
        if not piece or piece.type != PieceType.PAWN:
            return False
        
        # Check that the pawn is at the last rank
        if (piece.color == 'white' and pos[0] != 7) or (piece.color == 'black' and pos[0] != 0):
            return False
        
        # Promote the pawn
        piece.type = piece_type
        return True

    #Checks if the king is in check of the given color
    def is_check(self, color: str) -> bool:
        king = None
        opponent_color = 'black' if color == 'white' else 'white'
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.color == opponent_color:
                    valid_moves = piece.get_valid_moves(self)
                    for move in valid_moves:
                        if move.to_row == king.position[0] and move.to_col == king.position[1]:
                            return True
        return False
                    
    #Checks if the king is in checkmate of the given color
    def is_checkmate(self, color: str) -> bool:
        king_pos = None
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.type == PieceType.KING and piece.color == color:
                    king_pos = (row, col)
                    break
        
        #When there is no king of the given color we return False this should not happen
        if not king_pos:
            return False
        
        if not self.is_check(color):
            return False

        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.color == color and piece.type == PieceType.KING:
                    valid_moves = piece.get_valid_moves(self)
                    #Get all the moves of our king and check if any of them get him out of check
                    for move in valid_moves:
                        #Try to do the move and check if it is a check
                        original_piece = self.grid[move.to_row][move.to_col]
                        self.grid[move.to_row][move.to_col] = piece
                        self.grid[move.from_row][move.from_col] = None
                        old_position = piece.position
                        piece.position = (move.to_row, move.to_col)
                        
                        # Check if king is still in check
                        still_in_check = self.is_check(color)
                        
                        # Undo the move
                        self.grid[move.from_row][move.from_col] = piece
                        self.grid[move.to_row][move.to_col] = original_piece
                        piece.position = old_position
                        
                        if not still_in_check:
                            return False  # Found a move that gets out of check

        return True

    #Checks if a square is under attack by any piece of the opposite color. we need this to see if we can castle
    def is_square_under_attack(self, color: str, row: int, col: int) -> bool:
        opponent_color = 'black' if color == 'white' else 'white'
        
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece and piece.color == opponent_color:
                    # Check if this piece can attack the square
                    valid_moves = piece.get_valid_moves(self)
                    for move in valid_moves:
                        if move.to_row == row and move.to_col == col:
                            return True
        
        return False

    #print the game with pygame
    def print_board(self):
        WHITE = (240, 217, 181)
        PINK = (255, 166, 201)
        self.screen.fill(WHITE)
        
        # Draw board squares
        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 0:
                    color = (WHITE)
                else:
                    color = (PINK)
                pygame.draw.rect(self.screen, color, (col * self.square_size, row * self.square_size, self.square_size, self.square_size))
        
        # Draw pieces using cached images
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece:
                    piece_types = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
                    pre_string = "white_" if piece.color == "white" else "black_"
                    pre_string = pre_string + piece_types[piece.type.value - 1]
                    # Use cached image
                    self.screen.blit(self.piece_images[pre_string], (col * self.square_size, row * self.square_size))
                        
        # Draw coordinates
        font = pygame.font.SysFont(None, 24)
        
        # Draw column labels (a-h)
        for col in range(8):
            label = chr(ord('a') + col)
            text = font.render(label, True, (0, 0, 0))
            text_rect = text.get_rect(center=(col * self.square_size + self.square_size // 2, self.height + 5))
            self.screen.blit(text, text_rect)
        
        # Draw row labels (1-8)
        for row in range(8):
            label = str(8 - row)  # 8-1 from top to bottom
            text = font.render(label, True, (0, 0, 0))
            text_rect = text.get_rect(center=(5, row * self.square_size + self.square_size // 2))
            self.screen.blit(text, text_rect)

#This class is used to store the move when we get the valid moves
class Move:
    def __init__(self, from_col, from_row, to_col, to_row, is_capture):
        self.from_col = from_col
        self.from_row = from_row
        self.to_col = to_col
        self.to_row = to_row
        self.is_capture = is_capture

class Piece:
    def __init__(self, color, position, type):
        self.color = color
        self.position = position
        self.type = type
        self.has_moved = False
    def get_valid_moves(self, board) -> list[Move]:
        valid_moves = []  # List of tuples (row, col, is_capture)
        row, col = self.position
        opponent_color = 'black' if self.color == 'white' else 'white'
        if self.type == PieceType.PAWN:
            direction = -1 if self.color == 'white' else 1
            start_row = 6 if self.color == 'white' else 1

            # One square forward without captures for that: 1. Square has to be valid 2. Square has to be empty
            if 0 <= row + direction < 8 and board.grid[row + direction][col] is None:
                valid_moves.append(Move(col, row, col, row + direction, False))
                # Two squares forward from starting position
                if row == start_row and board.grid[row + 2*direction][col] is None:
                    valid_moves.append(Move(col, row, col, row + 2*direction, False))
            
            # Captures (diagonally) for that: 1. Square has to be valid 2. Square has to have an opponent piece
            for capture_col in [col-1, col+1]:
                if 0 <= capture_col < 8 and 0 <= row + direction < 8:
                    target = board.grid[row + direction][capture_col]
                    if target and target.color == opponent_color:
                        valid_moves.append(Move(col, row, capture_col, row + direction, True))
            #TODO: En passant
        elif self.type == PieceType.KNIGHT:
             # Knights move in L-shape
            moves = [
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1)
            ]
            for move_row, move_col in moves:
                new_row, new_col = row + move_row, col + move_col
                #We check if the move is valid: 1. Square has to be on the board 2. Square has to be empty or have an opponent piece
                if (0 <= new_row < 8 and 0 <= new_col < 8):
                    if board.grid[new_row][new_col] is None:
                        valid_moves.append(Move(col, row, new_col, new_row, False))
                    elif board.grid[new_row][new_col].color != self.color:
                        valid_moves.append(Move(col, row, new_col, new_row, True))
        elif self.type == PieceType.BISHOP:
            # Check all diagonal directions
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dir_row, dir_col in directions:
                # Start from current position and look along entire diagonal
                new_row, new_col = row, col
                while True:
                    new_row += dir_row
                    new_col += dir_col
                    # Stop if we go off the board
                    if new_row < 0 or new_row >= 8 or new_col < 0 or new_col >= 8:
                        break
                    # Empty square is valid move
                    if board.grid[new_row][new_col] is None:
                        valid_moves.append(Move(col, row, new_col, new_row, False))
                    # Square has a piece
                    else:
                        # Can capture opponent piece but then must stop
                        if board.grid[new_row][new_col].color != self.color:
                            valid_moves.append(Move(col, row, new_col, new_row, True))
                        break
        elif self.type == PieceType.ROOK:
            # Same logic as bishop but only for the horizontal and vertical directions
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dir_row, dir_col in directions:
                new_row, new_col = row, col
                while True:
                    new_row += dir_row
                    new_col += dir_col
                    if new_row < 0 or new_row >= 8 or new_col < 0 or new_col >= 8:
                        break
                    if board.grid[new_row][new_col] is None:
                        valid_moves.append(Move(col, row, new_col, new_row, False))
                    else:
                        if board.grid[new_row][new_col].color != self.color:
                            valid_moves.append(Move(col, row, new_col, new_row, True))
                        break
        elif self.type == PieceType.QUEEN:
            directions = [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1),  (1, 0),  (1, 1)
            ]
            for dir_row, dir_col in directions:
                new_row, new_col = row, col
                while True:
                    new_row += dir_row
                    new_col += dir_col
                    if new_row < 0 or new_row >= 8 or new_col < 0 or new_col >= 8:
                        break
                    if board.grid[new_row][new_col] is None:
                        valid_moves.append(Move(col, row, new_col, new_row, False))
                    else:
                        if board.grid[new_row][new_col].color != self.color:
                            valid_moves.append(Move(col, row, new_col, new_row, True))
                        break
        elif self.type == PieceType.KING:
            #King moves one square in any direction
            moves = [(-1, -1), (-1, 0), (-1, 1),
                     (0, -1),           (0, 1),
                     (1, -1),  (1, 0),  (1, 1)]
            for move_row, move_col in moves:
                new_row, new_col = row + move_row, col + move_col
                #We check if the move is valid: 1. Square has to be on the board 2. Square has to be empty or have an opponent piece
                if  0 <= new_row < 8 and 0 <= new_col < 8:
                    if board.grid[new_row][new_col] is None:
                        valid_moves.append(Move(col, row, new_col, new_row, False))
                    elif board.grid[new_row][new_col].color != self.color:
                        valid_moves.append(Move(col, row, new_col, new_row, True))
        return valid_moves
    

if __name__ == "__main__":
    pygame.init()
    game = Game()

    while True:
        game.update()
       