import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import pygame
from PIL import Image, ImageTk
import requests
import time

#initialise pygame for sound
pygame.mixer.init()

#load and trim sound effeccts to 2 seconds
def load_sound(file_path, duration=2):
    sound = pygame.mixer.Sound(file_path)
    sound.set_volume(0.5)
    return sound

flip_sound = load_sound('flip.wav')
match_sound = load_sound('match.wav')
win_sound = load_sound('win.wav')

#flask  API URL
API_URL = 'http://127.0.0.1:5000/api'

#initialise the game window
root = tk.Tk()

root.title ('Two-Player Memory Game')
root.geometry("1600x800")
root.resizable(True,True)

#custome fonts and colors
FONT= ("Helvetica", 16)
TITLE_FONT=("Helvetica",24,"bold")
BUTTON_FONT=("Helvetica",14)
BG_COLOR="#2E3440"
TEXT_COLOR="#D8DEE9"
BUTTON_COLOR="#5E81AC"
HOVER_COLOR="#81A1C1"
CARD_BG_COLOR="#4C566A"

#Game variable
cards= []
flipped= []
matches = []
current_player = 1
scores = {1: 0,2: 0}
turns={1: 0, 2:0}
player_names = {1: "", 2:""}
start_time =0

#create a main frame for the game
main_frame = tk.Frame(root, bg=BG_COLOR)
main_frame.pack(fill=tk.BOTH, expand=True)

#add a title
title_label = tk.Label(main_frame, text="Memory Card Game", font=TITLE_FONT, bg=BG_COLOR, fg=TEXT_COLOR)
title_label.pack(pady=10)

#Create a canvas for the circle
canvas = tk.Canvas(main_frame, bg=BG_COLOR)
canvas.pack(fill= tk.BOTH, expand=True)

#resize images dyanamicaly based on window size
def resize_images(image_path, width,height):
    
    image=Image.open(image_path)
    image=image.resize((width,height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)

#load card images (replace with your image paths)
card_images = [
    resize_images('card1.jpeg', 100, 100),
    resize_images('card3.jpeg', 100, 100),
    resize_images('card4.jpeg', 100, 100),
    resize_images('card5.jpeg', 100, 100),
    resize_images('card6.jpeg', 100, 100),
    resize_images('card7.jpeg', 100, 100),
    resize_images('card8.jpeg', 100, 100),
    resize_images('card9.jpeg', 100, 100 ),
]


# Duplicate card images to create pairs
card_images *= 6
random.shuffle(card_images)

#create card back image
card_back = resize_images("back_card.jpeg",100,100)

# create cards
def create_cards():
    global cards
    cards=[]
    canvas_width= canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    card_width = 100
    card_height = 100
    spacing= 10
    
    rows = 4
    cols = 12

    #calculate card postions dymanically
    #calculate card postions dymanically
    start_x= (canvas_width - (cols * (card_width+spacing)) ) //2
    start_y = (canvas_height - (rows * (card_height+spacing))) //2

    for i in range(rows):
        for j in range(cols):
            x = start_x + j * (card_width + spacing)
            y = start_y + i * (card_height + spacing)
            card = canvas.create_image(x, y,  anchor="nw", image=card_back)
            cards.append({
                "id": card,
                "image": card_images[i* cols+j],
                "flipped": False,
                "matched": False
            })
            canvas.tag_bind(card, "<Button-1>", lambda e,idx=i* cols+j: flip_card(idx))
    #flip a card
    def flip_card(index):
        if len(flipped) < 2 and not cards[index]["flipped"] and not cards[index]["matched"]:
            cards[index]["flipped"] = True
            canvas.itemconfig(cards[index]["id"], image=cards[index]["image"])
            flipped.append(index)
            flip_sound.play()
            if len(flipped) == 2:
                turns[current_player]+=1
                root.after(1000, check_match)
    #check if flipped cards match
    def check_match():
        global current_player, start_time
        index1,index2 = flipped
        if cards[index1]["image"] == cards[index2]["image"]:
            
            cards[index1]["matched"] = True
            cards[index2]["matched"] = True
            scores[current_player] +=1
            match_sound.play()
            messagebox.showinfo(" Match Found", f"{player_names[current_player]} found a match!")
            if all(card["matched"] for card in cards):
                messagebox.showinfo("Game Over","All matche found!")
                end_game()
        else:
            cards[index1]["flipped"] = False
            cards[index2]["flipped"] = False
            canvas.itemconfig(cards[index1]["id"],image=card_back)
            canvas.itemconfig(cards[index2]["id"],image=card_back)
        
            current_player = 3 - current_player
        flipped.clear()
        update_score()

        # Update score display
def update_score():
    canvas.delete("score")
    canvas_width = canvas.winfo_width()
    canvas.create_text(
        2, 20,
        text=f"{player_names[1]}: {scores[1]} | {player_names[2]}: {scores[2]} | "
             f"Time: {int(time.time()-start_time)}s | Current Turn: {player_names[current_player]}",
        font=FONT, fill=TEXT_COLOR, tag="score"
    )

# End the game
def end_game():
    global start_time
    winner = 1 if scores[1] > scores[2] else 2 if scores[2] > scores[1] else 0  # 0 for draw
    win_sound.play()  # Play win sound
    game_time = int(time.time() - start_time)

    if winner == 0:
        winner_details = "It's a draw!\n"
    else:
        winner_details = f"Winner: {player_names[winner]}\n"
        winner_details += f"Score: {scores[1]} vs {scores[2]}\nTurns: {turns[1]} vs {turns[2]}\nTime: {game_time}s"

    messagebox.showinfo("Game Over", winner_details)
    save_scores(game_time)
    show_leaderboard()
    restart_game()  # Automatically restart the game


# Save scores to the database
def save_scores(game_time):
    for player_id, score in scores.items():
        requests.post(f"{API_URL}/save_score", json={"player_id": player_id, "score": score, "time": game_time})

# Show leaderboard
def show_leaderboard():
    try:
        response = requests.get(f"{API_URL}/leaderboard")
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        leaderboard = response.json()

        leaderboard_window = tk.Toplevel(root)
        leaderboard_window.title("Leaderboard")
        leaderboard_window.geometry("300x200")
        leaderboard_window.configure(bg=BG_COLOR)

        tk.Label(leaderboard_window, text="Leaderboard", font=TITLE_FONT, bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=10)

        if leaderboard:
            for entry in leaderboard:
                tk.Label(leaderboard_window, text=f"{entry[0]}: {entry[1]} points in {entry[2]} seconds",
                         font=FONT, bg=BG_COLOR, fg=TEXT_COLOR).pack()
        else:
            tk.Label(leaderboard_window, text="No data available", font=FONT, bg=BG_COLOR, fg=TEXT_COLOR).pack()

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch leaderboard: {e}")

# Restart the game
def restart_game():
    global cards, flipped, matched, current_player, scores, turns, start_time
    cards = []
    flipped = []
    matched = []
    current_player = 1
    scores = {1: 0, 2: 0}
    turns = {1: 0, 2: 0}
    start_time = time.time()
    
    canvas.delete("all")
    create_cards()
    update_score()

# Get player names
def get_player_names():
    player_names[1] = simpledialog.askstring("Player 1", "Enter Player 1's name:", parent=root)
    player_names[2] = simpledialog.askstring("Player 2", "Enter Player 2's name:", parent=root)
    
    if player_names[1] and player_names[2]:
        response1 = requests.post(f"{API_URL}/register", json={"name": player_names[1]})
        response2 = requests.post(f"{API_URL}/register", json={"name": player_names[2]})
        
        player_ids = {1: response1.json()["player_id"], 2: response2.json()["player_id"]}
        
        start_game()

# Start the game
def start_game():
    global start_time
    create_cards()
    start_time = time.time()
    update_score()

# Add styled buttons
def create_button(text, command):
    button = tk.Button(main_frame, text=text, font=BUTTON_FONT, bg=BUTTON_COLOR, 
                       fg=TEXT_COLOR, activebackground=HOVER_COLOR, command=command)
    button.pack(pady=10)

# Get player names
get_player_names()

# Add restart button
create_button("Restart", restart_game)

# Add quit button
create_button("Quit", root.quit)

# Run the game
root.mainloop()