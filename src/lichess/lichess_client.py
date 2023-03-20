from playwright.sync_api import sync_playwright
import subprocess
import time

class Lichess_Client:
    def __init__(self, variant:int = 0, fen_position:str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR", time_control:int = 0, side_duration:float = 5.0, side_increment:int = 0, strength:int = 4, colour:int = 1, debug:bool = True) -> None:
        self.variant = variant
        self.fen_position = fen_position
        self.time_control = time_control
        self.side_duration = side_duration
        self.side_increment = side_increment
        self.strength = strength
        self.colour = colour
        self.debug = debug

        self.start()

    def start(self):
        p = sync_playwright().start()
        self.browser = p.chromium.launch(headless=not self.debug)
        self.context = self.browser.new_context()
        self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.page = self.context.new_page()
        self.page.goto("https://lichess.org/")

        comp_button = self.page.get_by_text(text="Play with the computer", exact=True)
        comp_button.click()

        setup_content = self.page.locator("div[class='setup-content'] > div").all()

        # choose variant
        variant_select = setup_content[0].locator("select")
        variants = [opt.inner_text() for opt in variant_select.locator("option").all()]

        variant_select.select_option(value=variants[self.variant])
        print("Variant :", variants[self.variant])

        # if from position
        if self.variant == 9:
            fen_input = self.page.get_by_placeholder(text="Paste the FEN text here")
            fen_input.type(text=self.fen_position)

        # choose time control
        time_select = setup_content[1].locator("select")
        time_controls = [opt.inner_text() for opt in time_select.locator("option").all()]

        time_select.select_option(value=time_controls[self.time_control])
        print("Time Control :", time_controls[self.time_control])

        # if real-time
        if self.time_control == 0:        
            side_dur, inc_dur = setup_content[1].locator("div > input").all()
            # duration per side
            side_controls = ["¼", "½", "¾"] + list(range(1,20)) + list(range(20,40,5)) + list(range(45,181,15))
            side_dur.click()
            self.page.keyboard.press("Home")
            
            if self.side_duration < 1 and not (self.side_duration % 0.25):
                self.side_duration = ["¼", "½", "¾"][self.side_duration / 0.25 - 1]
            else:
                self.side_duration = str(int(self.side_duration))
            
            print("Duration per Side :", self.side_duration)

            while setup_content[1].locator("div[class='time-choice range']").inner_text().split(": ")[-1] != self.side_duration:
                self.page.keyboard.press("ArrowRight")

            # increment per turn
            inc_controls = list(range(0,21)) + list(range(25,46,5)) + list(range(60,181,30))
            inc_dur.click()
            self.page.keyboard.press("Home")

            self.side_increment = str(self.side_increment)

            print("Increment per Side :", self.side_increment)

            while setup_content[1].locator("div[class='increment-choice range']").inner_text().split(": ")[-1] != self.side_increment:
                print(setup_content[1].locator("div[class='increment-choice range']").inner_text().split(": ")[-1], self.side_increment)
                self.page.keyboard.press("ArrowRight")

        # strength of bot
        strength_select = setup_content[2].locator("div").first.locator("group > div").all()

        print("Strength :", self.strength)

        strength_select[self.strength-1].click()

        # colour of side
        colour_select = setup_content[3].locator("button").all()
        colour_controls = [opt.get_attribute("title") for opt in colour_select]

        print("Colour :", colour_controls[self.colour])

        colour_select[self.colour].click()
        self.page.wait_for_load_state("load")
        self.orient()
        
        self.context.tracing.stop(path="src/lichess/trace.zip")
        self.context.close()
        self.browser.close()

    def orient(self):
        pieces_coords = self.get_coords()
        self.coords_pos_map = {}
        self.colour = int("white" in pieces_coords[0][0])
        step = pieces_coords[1][1][0] - pieces_coords[0][1][0]
        
        if not self.colour:
            for x in range(8):
                for y in range(8):
                    coords = (x*step, y*step)
                    pos = chr(ord("a")+x) + str(abs(y-8))
                    self.coords_pos_map[coords] = pos
        else:
            for x in range(8):
                for y in range(8):
                    coords = (x*step, y*step)
                    pos = chr(ord("h")-x) + str(y+1)
                    self.coords_pos_map[coords] = pos

    def get_coords(self):
        pieces = self.page.locator("cg-container > cg-board > piece").all()
        board = pieces[0].locator("..")
        pieces_coords = []

        while True:
            try:
                pieces_coords = [(p.get_attribute("class", timeout=1000), p.get_attribute("style", timeout=1000).replace("px", "")) for p in pieces]
                pieces_coords = [(p[0], p[1][p[1].find("(")+1:p[1].find(")")].split(", ")) for p in pieces_coords]
                pieces_coords = sorted([(p[0], tuple(map(int, p[1]))) for p in pieces_coords], key=lambda p: (p[1][1],p[1][0]))
                if len(pieces_coords) != 32 or pieces_coords[0][1] != (0, 0):
                    raise ValueError
                else:
                    break
            except:
                pieces = board.locator("piece").all()
        
        return pieces_coords

    # def get_fen(self):
    #     pieces_coords = self.get_position()

    #     piece_symbols = {
    #         'white pawn': 'P',
    #         'white knight': 'N',
    #         'white bishop': 'B',
    #         'white rook': 'R',
    #         'white queen': 'Q',
    #         'white king': 'K',
    #         'black pawn': 'p',
    #         'black knight': 'n',
    #         'black bishop': 'b',
    #         'black rook': 'r',
    #         'black queen': 'q',
    #         'black king': 'k'
    #     }

    #     board = [['.' for _ in range(8)] for _ in range(8)]

        

lichess = Lichess_Client(debug=True, colour=2)
subprocess.run(["playwright", "show-trace", r"C:\Users\chong\Desktop\Coding\Chess Bot\src\lichess\trace.zip"], shell=True)