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


class Clock:
    def __init__(self, minutes, increment=0):
        self.minutes = minutes
        self.increment = increment
        self.white_time = minutes * 60  # Convert to seconds
        self.black_time = minutes * 60
        self.is_running = False
        self.current_player = 'white'

    def start_clock(self):
        self.is_running = True

    def stop_clock(self):
        self.is_running = False
    
    def update_clock(self, delta_time):
        delta_time = delta_time / 1000
        if self.is_running:
            if self.current_player == 'white':
                self.white_time -= delta_time
            else:
                self.black_time -= delta_time

    def switch_player(self):
        if self.current_player == 'white':
            self.white_time += self.increment
            self.current_player = 'black'
        else:
            self.black_time += self.increment
            self.current_player = 'white'        
        

    def get_time_string(self, time_in_seconds):
        time_in_seconds = int(time_in_seconds)
        minutes = time_in_seconds // 60
        seconds = time_in_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_white_time_string(self):
        return self.get_time_string(self.white_time)

    def get_black_time_string(self):
        return self.get_time_string(self.black_time)

class Game:
    def __init__(self):
        #Width and height of the board
        width = 640 
        height = 640 
        #Width (board + buttons(clock+resign etc) and height (board + buttons)
        self.screen = pygame.display.set_mode((width+200, height+60))
        self.board = Board(width, height, self.screen)
        self.current_turn = 'white'
        self.input_text = ""
        self.font = pygame.font.SysFont(None, 32)
        self.font_small = pygame.font.SysFont(None, 24)
        self.error_message = None
        
        # Game mode buttons
        self.buttons = []
        self.create_startSelectButtons()
        self.game_mode = None  # None, 'normal', 'fischer', or 'two_rooks' or 'done'
        self.game_result = None # None, 'white_win', 'black_win', 'draw'
        
        # Clock settings
        self.use_clock = False
        self.clock = None
        self.clock_options = [
            ("3+2", Clock(3, 2)),
            ("5+0", Clock(5, 0)),
            ("10+0", Clock(10, 0)),
            ("15+10", Clock(15, 10))
        ]
        self.clock_buttons = []
        self.sideBarButtons = []
        self.create_sideBarButtons()
        
        # Piece selection and valid moves
        self.selected_piece = None
        self.valid_moves = []
        
        # PGN file handling
        self.use_pgn_file = False  # Set this to True to use PGN file
        # Use absolute path to avoid issues with relative paths
        self.pgn_file_path = os.path.join(os.path.dirname(__file__), "game.pgn")  # Set your PGN file path here
        self.pgn_moves = []
        self.current_move_index = 0
        self.whiteWantsDraw = False
        self.blackWantsDraw = False

        self.gameMoves = []
        self.save_game_button = pygame.Rect(840/2 - 120/2, 840/2 + 90, 120, 40)
        
        if self.use_pgn_file:
            self.load_pgn_file()

    #Create the buttons for the start screen on which you can select the game mode
    def create_startSelectButtons(self):
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

    #Create the buttons for the clock options
    def create_sideBarButtons(self):
        button_width = 100
        button_height = 30
        spacing = 20
        start_x = 160
        
        # Create clock option buttons
        for i in range(4):
            self.clock_buttons.append(
                pygame.Rect(
                    start_x + (button_width + spacing) * i,
                    95,
                    button_width,
                    button_height
                )
            )
        self.sideBarButtons.append(pygame.Rect(self.board.width + 35, 330, 130, 30))
        self.sideBarButtons.append(pygame.Rect(self.board.width + 35, 380, 130,30))
        self.sideBarButtons.append(pygame.Rect(self.board.width + 35, 530, 130, 30))
        self.sideBarButtons.append(pygame.Rect(self.board.width + 35, 580, 130, 30))


    #Draw the sidebar on the right with the following information:
    #- Clock
    #- Resign button
    #- Draw button
    #- Draw offer button
    #- Draw offer accept button
    #- Draw offer decline button
    def draw_sidebar(self):
        #Draw the clock first
        if self.use_clock and self.game_mode in ['normal', 'fischer'] and self.clock is not None:
            # Define clock dimensions and position
            clock_width = 180
            clock_height = 200
            clock_x = self.board.width + 10
            clock_y = 10
            
            # Draw clock background
            clock_bg = pygame.Rect(clock_x, clock_y, clock_width, clock_height)
            pygame.draw.rect(self.screen, (240, 240, 240), clock_bg)
            pygame.draw.rect(self.screen, (200, 200, 200), clock_bg, 2)
            
            # Draw title
            title = self.font_small.render("Chess Clock", True, (50, 50, 50))
            title_rect = title.get_rect(center=(clock_x + clock_width//2, clock_y + 20))
            self.screen.blit(title, title_rect)
            
            # Draw white player's time
            white_bg = pygame.Rect(clock_x + 10, clock_y + 40, clock_width - 20, 70)
            pygame.draw.rect(self.screen, (255, 255, 255), white_bg)
            pygame.draw.rect(self.screen, (200, 200, 200), white_bg, 2)
            
            white_label = self.font_small.render("White", True, (50, 50, 50))
            white_label_rect = white_label.get_rect(center=(clock_x + clock_width//2, clock_y + 55))
            self.screen.blit(white_label, white_label_rect)
            
            white_time = self.font.render(self.clock.get_white_time_string(), True, (0, 0, 0))
            white_time_rect = white_time.get_rect(center=(clock_x + clock_width//2, clock_y + 85))
            self.screen.blit(white_time, white_time_rect)
            
            # Draw black player's time
            black_bg = pygame.Rect(clock_x + 10, clock_y + 120, clock_width - 20, 70)
            pygame.draw.rect(self.screen, (255, 255, 255), black_bg)
            pygame.draw.rect(self.screen, (200, 200, 200), black_bg, 2)
            
            black_label = self.font_small.render("Black", True, (50, 50, 50))
            black_label_rect = black_label.get_rect(center=(clock_x + clock_width//2, clock_y + 135))
            self.screen.blit(black_label, black_label_rect)
            
            black_time = self.font.render(self.clock.get_black_time_string(), True, (0, 0, 0))
            black_time_rect = black_time.get_rect(center=(clock_x + clock_width//2, clock_y + 165))
            self.screen.blit(black_time, black_time_rect)
            
            # Highlight current player's time
            if self.current_turn == 'white':
                pygame.draw.rect(self.screen, (100, 255, 100), white_bg, 3)
            else:
                pygame.draw.rect(self.screen, (100, 255, 100), black_bg, 3)

        #Draw the buttons for the sidebar
        blackTitle = self.font.render("Black", True, (0, 0, 0))
        whiteTitle = self.font.render("White", True, (0, 0, 0))
        whiteTitleRect = whiteTitle.get_rect(center=(self.board.width + 100, 300))
        blackTitleRect = blackTitle.get_rect(center=(self.board.width + 100, 500))
        self.screen.blit(blackTitle, blackTitleRect)
        self.screen.blit(whiteTitle, whiteTitleRect)

        whiteText = "Request Draw" if not self.blackWantsDraw else "Accept Draw"
        whiteTextRect = self.font_small.render(whiteText, True, (0, 0, 0))
        whiteDrawButton = self.sideBarButtons[0]
        pygame.draw.rect(self.screen, (220, 220, 220), whiteDrawButton)
        pygame.draw.rect(self.screen, (100, 100, 100), whiteDrawButton, 2)
        whiteTextPos = whiteTextRect.get_rect(center=whiteDrawButton.center)
        self.screen.blit(whiteTextRect, whiteTextPos)
        whiteTextRect = self.font_small.render("Resign", True, (0, 0, 0))
        whiteResignButton = self.sideBarButtons[1]
        pygame.draw.rect(self.screen, (220, 220, 220), whiteResignButton)
        pygame.draw.rect(self.screen, (100, 100, 100), whiteResignButton, 2)
        whiteTextPos = whiteTextRect.get_rect(center=whiteResignButton.center)
        self.screen.blit(whiteTextRect, whiteTextPos)

        blackText = "Request Draw" if not self.whiteWantsDraw else "Accept Draw"
        blackTextRect = self.font_small.render(blackText, True, (0, 0, 0))
        blackDrawButton = self.sideBarButtons[2]
        pygame.draw.rect(self.screen, (220, 220, 220), blackDrawButton)
        pygame.draw.rect(self.screen, (100, 100, 100), blackDrawButton, 2)
        blackTextPos = blackTextRect.get_rect(center=blackDrawButton.center)
        self.screen.blit(blackTextRect, blackTextPos)
        blackTextRect = self.font_small.render("Resign", True, (0, 0, 0))
        blackResignButton = self.sideBarButtons[3]
        pygame.draw.rect(self.screen, (220, 220, 220), blackResignButton)
        pygame.draw.rect(self.screen, (100, 100, 100), blackResignButton, 2)
        blackTextPos = blackTextRect.get_rect(center=blackResignButton.center)
        self.screen.blit(blackTextRect, blackTextPos)
         
    
    #Draw the buttons for the start screen for selecting the game mode
    def draw_startSelectButtons(self):
        for i, button in enumerate(self.buttons):
            # Draw button background
            pygame.draw.rect(self.screen, (200, 200, 200), button)
            pygame.draw.rect(self.screen, (100, 100, 100), button, 2)
            
            # Draw button text
            text = self.button_font.render(self.button_texts[i], True, (0, 0, 0))
            text_rect = text.get_rect(center=button.center)
            self.screen.blit(text, text_rect)

    #Draw the settings for the clock and the pgn file on the start screen
    def draw_settings_beg(self):
        # Draw clock checkbox
        checkbox_rect = pygame.Rect(10, 50, 20, 20)
        pygame.draw.rect(self.screen, (200, 200, 200), checkbox_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), checkbox_rect, 2)
        
        #When clock is enabled we draw the checkbox checked
        if self.use_clock:
            pygame.draw.rect(self.screen, (0, 0, 0), checkbox_rect)
            
        # Draw "Use Clock" text
        text = self.font_small.render("Use Clock", True, (0, 0, 0))
        self.screen.blit(text, (35, 53))
        
        # Draw clock options if clock is enabled
        if self.use_clock:
            text = self.font_small.render("Clock Options:", True, (0, 0, 0))
            self.screen.blit(text, (10, 100))
            for i, (text, _) in enumerate(self.clock_options):
                button = self.clock_buttons[i]
                pygame.draw.rect(self.screen, (200, 200, 200), button)
                pygame.draw.rect(self.screen, (100, 100, 100), button, 2)
                if self.clock == self.clock_options[i][1]:
                    pygame.draw.rect(self.screen, (100, 100, 100), button, 5)
                
                text_surface = self.font_small.render(text, True, (0, 0, 0))
                text_rect = text_surface.get_rect(center=button.center)
                self.screen.blit(text_surface, text_rect)

        # PGN File Option
        checkbox_enablepgn = pygame.Rect(10, 300, 20, 20)
        # Draw checkbox background
        pygame.draw.rect(self.screen, (200, 200, 200), checkbox_enablepgn)
        pygame.draw.rect(self.screen, (100, 100, 100), checkbox_enablepgn, 2)
        
        # Fill checkbox if enabled
        if self.use_pgn_file:
            # Draw checkmark inside
            pygame.draw.rect(self.screen, (0, 0, 0), checkbox_enablepgn.inflate(-8, -8))
        
        text = self.font_small.render("Use PGN File", True, (0, 0, 0))
        self.screen.blit(text, (40, checkbox_enablepgn.centery - text.get_height() // 2))
        
        # Show PGN file path if enabled
        if self.use_pgn_file:
            # Create a rounded rectangle for the file path display
            path_rect = pygame.Rect(35, 330, 400, 25)
            pygame.draw.rect(self.screen, (230, 230, 230), path_rect, border_radius=5)
            pygame.draw.rect(self.screen, (150, 150, 150), path_rect, 1, border_radius=5)
            
            # Display only the last folder and filename
            pgn_path = self.pgn_file_path
            parts = pgn_path.replace('\\', '/').split('/')
            if len(parts) > 1:
                pgn_path = parts[-2] + '/' + parts[-1]
            else:
                pgn_path = parts[-1]
            
            pgn_text = "PGN File: " + pgn_path
            text = self.font_small.render(pgn_text, True, (50, 50, 50))
            self.screen.blit(text, (path_rect.x + 10, path_rect.centery - text.get_height() // 2))

    def handle_sidebar_click(self, pos):
        if self.sideBarButtons[0].collidepoint(pos):
            if self.blackWantsDraw:
                self.check_game_result(force_draw=True)
            else:
                self.whiteWantsDraw = not self.whiteWantsDraw
        elif self.sideBarButtons[2].collidepoint(pos):
            if self.whiteWantsDraw:
                self.check_game_result(force_draw=True)
            else:
                self.blackWantsDraw = not self.blackWantsDraw
        elif self.sideBarButtons[1].collidepoint(pos):
            self.check_game_result(force_black_win=True)
        elif self.sideBarButtons[3].collidepoint(pos):
            self.check_game_result(force_white_win=True)

    #Handle the click on the game mode buttons
    def handle_button_click(self, pos):
        for i, button in enumerate(self.buttons):
            if button.collidepoint(pos):
                if i == 0:  # Aufgabe 1 - Normal Chess
                    self.game_mode = 'normal'
                    self.board.game_mode = 'normal'
                    self.board.setup_pieces()  # Reset to normal starting position
                    if self.use_clock and self.clock is not None:
                        self.clock.start_clock()
                        self.last_update = pygame.time.get_ticks()
                elif i == 1:  # Aufgabe 2 - Fischer Random
                    self.game_mode = 'fischer'
                    self.board.game_mode = 'fischer'
                    print("Fischer Random")
                    self.board.setup_fischer_random()
                    if self.use_clock and self.clock is not None:
                        self.clock.start_clock()
                        self.last_update = pygame.time.get_ticks()
                elif i == 2:  # Aufgabe 3 - Two Rooks vs Two Pawns
                    self.game_mode = 'two_rooks'
                    self.board.game_mode = 'two_rooks'
                    print("Two Rooks vs Two Pawns")
                    self.board.setup_two_rooks()
                    if self.use_clock and self.clock is not None:
                        self.clock.start_clock()
                        self.last_update = pygame.time.get_ticks()
                return True
        return False

    #Handle the click on the settings for the clock and the pgn file on the start screen
    def handle_settings_click(self, pos):
        # Check if clock checkbox was clicked
        checkbox_rect = pygame.Rect(10, 50, 20, 20)
        if checkbox_rect.collidepoint(pos):
            self.use_clock = not self.use_clock
            if not self.use_clock:
                self.clock = None
            return True
        
        # Check if clock options were clicked
        if self.use_clock:
            for i, button in enumerate(self.clock_buttons):
                if button.collidepoint(pos):
                    self.clock = self.clock_options[i][1]
                    return True

                    
        # Check if PGN file checkbox was clicked
        checkbox_enablepgn = pygame.Rect(10, 300, 20, 20)
        if checkbox_enablepgn.collidepoint(pos):
            self.use_pgn_file = not self.use_pgn_file
            return True
        
        return False

    #Get the grid index when clicking on the board so you can select pieces
    def get_grid_position(self, screen_pos):
        #Check if the click is on the sidebar
        if screen_pos[0] >= self.board.width or screen_pos[1] >= self.board.height:
            return None
        # Convert screen coordinates to grid coordinates
        x, y = screen_pos
        if y >= self.board.height:  # Clicked below the board
            return None
        col = x // self.board.square_size
        row = y // self.board.square_size
        return (row, col)

    #Handle the click on a piece so you can see valid moves from this piece
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

    def handle_save_game_click(self, pos):
        if self.save_game_button.collidepoint(pos):
            self.save_game()

    #Load the pgn file form the file system and load all valid moves
    def load_pgn_file(self):
        try:
            with open(self.pgn_file_path, 'r') as file:
                content = file.read()
                # Split the content into moves
                moves = content.split()
                # Remove move numbers (e.g., "1.", "2.", etc.)
                self.pgn_moves = [move for move in moves if not move.endswith('.') and not move.startswith('$')]
                if self.pgn_moves:
                    self.input_text = self.pgn_moves[0]
        except FileNotFoundError:
            self.error_message = f"PGN file not found: {self.pgn_file_path}"
        except Exception as e:
            self.error_message = f"Error loading PGN file: {str(e)}"

    #Load the next move from the pgn file which was loaded before
    def load_next_move(self):
        if self.current_move_index < len(self.pgn_moves) - 1:
            self.current_move_index += 1
            self.input_text = self.pgn_moves[self.current_move_index]
            return True
        return False

    def save_game(self):
        counter = 0
        with open('game_moves.txt', 'w') as file:
            for move in self.gameMoves:
                if counter % 2 == 0:
                    file.write(str(counter // 2 + 1) + '. ' + move + ' ')
                else:
                    file.write(move + ' ')
                counter += 1

    #Draw the input field for the move entered by the user
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

    #Draw the valid moves when clicked on a piece
    def draw_valid_moves(self):
        if self.selected_piece is not None:
            for move in self.valid_moves:
                # Draw a circle to indicate valid move
                center_x = move.to_col * self.board.square_size + self.board.square_size // 2
                center_y = move.to_row * self.board.square_size + self.board.square_size // 2
                pygame.draw.circle(self.screen, (0, 255, 0, 128), (center_x, center_y), self.board.square_size // 4, 2)

    #Draw the game result
    def draw_game_result(self):
        self.screen.fill((255, 255, 255))
        
        # Render "Game Over" text
        game_over_text = self.font.render("Game Over", True, (0, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(840/2, 840/2 - 30))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Render game result text
        result_text = self.font.render(self.game_result, True, (0, 0, 0))
        result_rect = result_text.get_rect(center=(840/2, 840/2 + 30))
        self.screen.blit(result_text, result_rect)

        # Render the save game button below the game result
        pygame.draw.rect(self.screen, (220, 220, 220), self.save_game_button)
        pygame.draw.rect(self.screen, (0, 0, 0), self.save_game_button, 2)
        save_game_text = self.font.render("Save Game", True, (0, 0, 0))
        save_text_rect = save_game_text.get_rect(center=self.save_game_button.center)
        self.screen.blit(save_game_text, save_text_rect)

    #MAIN LOOP OF THE GAME in this loop we handle all events and update the game
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
                        if self.handle_settings_click(event.pos):
                            continue
                    else:
                        self.handle_piece_click(event.pos)
                        self.handle_sidebar_click(event.pos)
                        self.handle_save_game_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if self.game_mode is None:
                    continue
                if event.key == pygame.K_RETURN:
                    if self.play_move(self.input_text):
                        self.gameMoves.append(self.input_text)
                        self.error_message = None
                        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
                        self.board.print_board()
                        self.check_game_result()
                        if self.use_clock and self.clock is not None:
                            self.clock.switch_player()
                        
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
            self.draw_startSelectButtons()
            self.draw_settings_beg()
            pygame.display.flip()
            return
        if self.game_mode == 'done':
            self.screen.fill((255, 255, 255))
            self.draw_game_result()
            pygame.display.flip()
            return
        self.board.print_board()
        self.draw_sidebar()
        if self.use_clock and self.clock is not None:
            self.clock.update_clock(pygame.time.get_ticks() - self.last_update)
            self.last_update = pygame.time.get_ticks()
        self.draw_valid_moves()
        self.draw_input_field()
        pygame.display.flip()

    #Check the game result, this is called when a move is played or when a button is clicked
    def check_game_result(self, force_draw=False, force_white_win=False, force_black_win=False):
        if force_draw:
            self.game_mode = 'done'
            self.game_result = 'draw'
            return True
        if force_white_win:
            self.game_mode = 'done'
            self.game_result = 'white_win'
            return True
        if force_black_win:
            self.game_mode = 'done'
            self.game_result = 'black_win'
            return True
        if self.use_clock and self.clock is not None:
            if self.clock.white_time <= 0:
                self.game_mode = 'done'
                self.game_result = 'black_win'
                return True
            if self.clock.black_time <= 0:
                self.game_mode = 'done'
                self.game_result = 'white_win'
                return True
        if self.board.is_checkmate('white'):
            self.game_mode = 'done'
            self.game_result = 'black_win'
            return True
        if self.board.is_checkmate('black'):
            self.game_mode = 'done'
            self.game_result = 'white_win'
            return True
        return False

    #Parse move entered by the user in standard chess notation and play it with the board functions,
    #Give error messages if the move is invalid
    def play_move(self, text_move):
        #Convert row and column to 0-7 range
        file_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        success = False  # We'll set this True if we successfully do a move.
        try:
            # 1) Handle castling
            if text_move == "O-O":  # Kingside castling
                rank = 7 if self.current_turn == 'white' else 0
                color = self.current_turn
                king_to = (rank, 6)  # g1/g8
                rook_to = (rank, 5)  # f1/f8

                # Find the king
                king_pos = None
                for col in range(8):
                    piece = self.board.grid[rank][col]
                    if piece and piece.type == PieceType.KING and piece.color == color:
                        king_pos = (rank, col)
                        break

                # Find the rook to the right of the king
                rook_pos = None
                if king_pos:
                    for col in range(king_pos[1] + 1, 8):
                        piece = self.board.grid[rank][col]
                        if piece and piece.type == PieceType.ROOK and piece.color == color:
                            rook_pos = (rank, col)
                            break

                # Attempt castling if we found king and rook
                if king_pos and rook_pos:
                    success = self.board.castle(
                        king_from=king_pos,
                        king_to=king_to,
                        rook_from=rook_pos,
                        rook_to=rook_to,
                        current_turn=self.current_turn
                    )

                if not success:
                    self.error_message = "Invalid castling move"
                    return  False# or you could raise an exception, or handle differently
                return success

            elif text_move == "O-O-O":  # Queenside castling
                rank = 7 if self.current_turn == 'white' else 0
                color = self.current_turn
                king_to = (rank, 2)  # c1/c8
                rook_to = (rank, 3)  # d1/d8

                # Find the king
                king_pos = None
                for col in range(8):
                    piece = self.board.grid[rank][col]
                    if piece and piece.type == PieceType.KING and piece.color == color:
                        king_pos = (rank, col)
                        break

                # Find the rook to the left of the king
                rook_pos = None
                if king_pos:
                    for col in range(king_pos[1] - 1, -1, -1):
                        piece = self.board.grid[rank][col]
                        if piece and piece.type == PieceType.ROOK and piece.color == color:
                            rook_pos = (rank, col)
                            break

                # Attempt castling if we found king and rook
                if king_pos and rook_pos:
                    success = self.board.castle(
                        king_from=king_pos,
                        king_to=king_to,
                        rook_from=rook_pos,
                        rook_to=rook_to,
                        current_turn=self.current_turn
                    )

                if not success:
                    self.error_message = "Invalid castling move"
                    return False
                return True

            # 2) If it's not a castling move, handle normal moves here.
            else:
                # parse something like "e2e4", call your regular move function, etc.
                # If that move succeeds, set success = True
                pass

            # 3) If we reach here, we either castled successfully or did a normal move.
            #    You can do additional steps, like toggling self.current_turn from white <-> black.
            if success:
                self.current_turn = 'black' if self.current_turn == 'white' else 'white'
            else:
                # Possibly handle normal moves or print some error message for invalid normal move
                pass


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
        self.grid: list[list[Piece | None]] = [[None for _ in range(8)] for _ in range(8)]
        self.square_size = width // 8
        self.screen = screen
        self.width = width
        self.height = height
        self.whiteInCheck = False
        self.blackInCheck = False
        self.game_mode = None
        
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

        # set up white & black bank-rank pieces 

        numbers = list(range(8))  # [0, 1, 2, ..., 8]

        # set up bishops 
        bish_pos = random.randint(0, 7)
       
        if bish_pos%2 == 0: # if bishop is on pink
            bish_pos2 = random.choice([1, 3, 5, 7,])
        else:
            bish_pos2 = random.choice([0, 2, 4, 6])
        
        white_pieces.append(Piece('white',(7, bish_pos), PieceType.BISHOP))
        white_pieces.append(Piece('white',(7, bish_pos2), PieceType.BISHOP))
        black_pieces.append(Piece('black',(0, bish_pos), PieceType.BISHOP))
        black_pieces.append(Piece('black',(0, bish_pos2), PieceType.BISHOP))

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
        black_pieces.append(Piece('black', (0, rook_pos), PieceType.ROOK))
        black_pieces.append(Piece('black', (0, rook_pos2), PieceType.ROOK))
        numbers.remove(rook_pos2)
    
        # set king
        # Determine the lower and upper bounds
        lower = min(rook_pos, rook_pos2)
        upper = max(rook_pos, rook_pos2)
        valid_choices2= [num for num in numbers if lower < num < upper]
        king_pos = random.choice(valid_choices2)

        white_pieces.append(Piece('white', (7, king_pos), PieceType.KING))
        black_pieces.append(Piece('black', (0, king_pos), PieceType.KING))
        numbers.remove(king_pos)

        # set Queen
        queen_pos = random.choice(numbers)

        white_pieces.append(Piece('white', (7, queen_pos), PieceType.QUEEN))
        black_pieces.append(Piece('black', (0, queen_pos), PieceType.QUEEN))
        numbers.remove(queen_pos)

        # set knight
        knight_pos = random.choice(numbers)
        numbers.remove(knight_pos)
        knight_pos2 = random.choice(numbers)

        white_pieces.append(Piece('white', (7, knight_pos), PieceType.KNIGHT))
        white_pieces.append(Piece('white', (7, knight_pos2), PieceType.KNIGHT))
        black_pieces.append(Piece('black', (0, knight_pos), PieceType.KNIGHT))
        black_pieces.append(Piece('black', (0, knight_pos2), PieceType.KNIGHT))
        
        numbers.remove(knight_pos2)


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
            #if we moved a piece and we are in check, we undo the move
            if self.is_check(piece.color):
                self.grid[move.to_row][move.to_col] = None
                self.grid[move.from_row][move.from_col] = piece
                piece.position = (move.from_row, move.from_col)
                return False
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
            piece_before = self.grid[move.to_row][move.to_col]
            # Make the move
            self.grid[move.to_row][move.to_col] = piece
            self.grid[move.from_row][move.from_col] = None
            #if we moved a piece and we are in check, we undo the move
            if self.is_check(piece.color):
                self.grid[move.to_row][move.to_col] = piece_before
                self.grid[move.from_row][move.from_col] = piece
                piece.position = (move.from_row, move.from_col)
                return False
            piece.position = (move.to_row, move.to_col)
            piece.has_moved = True
            return True
        
        return False

    def castle(self, king_from: tuple[int, int], king_to: tuple[int, int],
            rook_from: tuple[int, int], rook_to: tuple[int, int],
            current_turn: str) -> bool:
        # Retrieve the king and rook from the board.
        king = self.grid[king_from[0]][king_from[1]]
        rook = self.grid[rook_from[0]][rook_from[1]]

        # 1) Verify that the pieces are correct.
        if not king or king.type != PieceType.KING:
            return False
        if not rook or rook.type != PieceType.ROOK:
            return False

        # 2) Check if they have moved before.
        if king.has_moved or rook.has_moved:
            return False

        # 3) They must be on the same row (no vertical castling).
        if king_from[0] != rook_from[0]:
            return False
        row = king_from[0]

        # 4) Ensure all squares between the king and rook are empty (except king/rook).
        #    We only check the *strictly* in-between squares.
        col_start = min(king_from[1], rook_from[1]) + 1
        col_end = max(king_from[1], rook_from[1])
        for col in range(col_start, col_end):
            if self.grid[row][col] is not None:
                return False

        # 5) Ensure the king is not currently in check.
        if (current_turn == 'white' and self.whiteInCheck) or \
        (current_turn == 'black' and self.blackInCheck):
            return False

        # 6) Check that none of the squares the king passes through (including destination)
        #    are under attack.
        step = 1 if king_to[1] > king_from[1] else -1
        for col in range(king_from[1] + step, king_to[1] + step, step):
            if self.is_square_under_attack(king.color, row, col):
                return False

        # 7) Ensure the final squares (king_to, rook_to) are empty
        #    (Castling cannot capture any piece, whether friendly or enemy.)
        if self.grid[king_to[0]][king_to[1]] is not None:
            return False
        if self.grid[rook_to[0]][rook_to[1]] is not None:
            return False

        # --- If we reach here, castling is valid. Perform the move. ---
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

    def get_king_position(self, color: str) -> tuple[int, int] | None:
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.type == PieceType.KING and piece.color == color:
                    return (row, col)
        return None

    #Checks if the king is in check of the given color
    def is_check(self, color: str) -> bool:
        king = self.get_king_position(color)
        if not king:
            return False
        opponent_color = 'black' if color == 'white' else 'white'
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.color == opponent_color:
                    valid_moves = piece.get_valid_moves(self)
                    for move in valid_moves:
                        if move.to_row == king[0] and move.to_col == king[1]:
                            return True
        return False
                    
    #Checks if the king is in checkmate of the given color
    def is_checkmate(self, color: str) -> bool:
        king_pos = self.get_king_position(color)
        if not king_pos:
            return False
        
        if not self.is_check(color):
            return False

        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece and piece.color == color:
                    valid_moves = piece.get_valid_moves(self)
                    for move in valid_moves:
                        #Try to do the move and check if it is a check
                        original_piece = self.grid[move.to_row][move.to_col]
                        self.grid[move.to_row][move.to_col] = piece
                        self.grid[move.from_row][move.from_col] = None
                        old_position = piece.position
                        piece.position = (move.to_row, move.to_col)
                        if not self.is_check(color):
                            self.grid[move.from_row][move.from_col] = piece
                            self.grid[move.to_row][move.to_col] = original_piece
                            piece.position = old_position
                            return False
                        #Undo the move
                        self.grid[move.from_row][move.from_col] = piece
                        self.grid[move.to_row][move.to_col] = original_piece
                        piece.position = old_position
                        
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
       