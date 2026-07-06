import pandas as pd
import random
import os
import torch
import tkinter as tk
from PIL import ImageTk, Image
import pyperclip
import webbrowser

MIN_CONFIDENCE = 0.8
IMAGES_DIR = 'images'
DISPLAY_SIZE = 500
PRICE_LENIENCE = 10_000


def load_property() -> pd.DataFrame:
    df = pd.read_csv('properties.csv')
    listing_id = random.choice(df['listing_id'].unique())
    df = df.loc[(df['listing_id'] == listing_id) & (df['confidence'] >= MIN_CONFIDENCE)]
    return df


class PropertyGame:
    def __init__(self, root: tk.Tk, dfs: list[pd.DataFrame]):
        self.root = root
        self.dfs = dfs
        self.true_price = int(dfs[0]['price'].values[0])
        self.size = int(dfs[0]['size'].values[0])
        self.rooms = dfs[0]['rooms'].values[0]
        self.location = dfs[0]['location'].values[0]
        self.energy_label = dfs[0]['energy_label'].values[0]
        self.listing_id = dfs[0]['listing_id'].values[0]

        self.df = self.n = self.current = None
        self.current_df = -1

        self._build_layout()
        self.show_current()

    def _build_layout(self):
        self.root.geometry("1100x850")
        self.root.title("Pictures")

        self.img_label = tk.Label(self.root)
        self.img_label.grid(row=0, column=0, padx=10, pady=10)

        self.progress_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.progress_var, font=("Arial", 10)).grid(row=1, column=0)

        ctrl_frame = tk.Frame(self.root)
        ctrl_frame.grid(row=0, column=1, sticky="n", padx=20, pady=20)
        self._build_info(ctrl_frame)
        self._build_controls(ctrl_frame)

    def _build_info(self, parent):
        frame = tk.Frame(parent)
        frame.pack(pady=10)
        rows = [
            ("Property size",   f"{self.size} m²"),
            ("Energy label",    self.energy_label),
            ("Number of rooms", str(self.rooms)),
            ("Location", str(self.location)),
        ]
        for i, (label, value) in enumerate(rows):
            tk.Label(frame, text=label, font=("Arial", 12), anchor="w").grid(row=i, column=0, sticky="w", padx=5, pady=3)
            tk.Label(frame, text=value, font=("Arial", 12), anchor="w").grid(row=i, column=1, sticky="w", padx=5, pady=3)

    def _build_controls(self, parent):
        self.result_var = tk.StringVar()
        tk.Label(parent, textvariable=self.result_var, font=("Arial", 12)).pack(pady=5)

        self.btn_frame = tk.Frame(parent)
        tk.Button(self.btn_frame, text="Next (n / →)", width=15, command=self.advance).pack()
        tk.Button(self.btn_frame, text="Back (b / ←)", width=15, command=self.back).pack()
        self.root.bind("n", lambda e: self.advance())
        self.root.bind("<Right>", lambda e: self.advance())
        self.root.bind("b", lambda e: self.back())
        self.root.bind("<Left>", lambda e: self.back())

        tk.Label(parent, text="Enter your guess", font=("Arial", 12)).pack(pady=(10, 0))
        self.guess_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.guess_var, font=("Arial", 12), width=20).pack(pady=5)

        self.submit_btn = tk.Button(parent, text="Submit (Enter)", width=15, command=self.submit_guess)
        self.submit_btn.pack()
        self.root.bind("<Return>", lambda e: self.submit_guess())

        self.end_frame = tk.Frame(parent)
        self.end_frame.pack()

    def next_df(self):
        self.current_df += 1
        if self.current_df < len(self.dfs):
            self.df = self.dfs[self.current_df].reset_index(drop=True)
            self.n = len(self.df)
            self.current = 0
            self.btn_frame.pack(pady=10)
        else:
            self.btn_frame.pack_forget()
            self.img_label.grid_remove()
            self.submit_btn.pack_forget()
            self.progress_var.set("")
            self.result_var.set(f"The price was €{self.true_price:,}")
            url = f'https://www.funda.nl/detail/{self.listing_id}'
            tk.Button(self.end_frame, text="Open listing (o)", width=15, command=lambda: webbrowser.open(url)).pack()
            self.root.bind("o", lambda e: webbrowser.open(url))

    def show_current(self):
        if self.df is not None:
            row = self.df.iloc[self.current]
            folder = os.path.join(IMAGES_DIR, str(row['listing_id']))
            image = Image.open(os.path.join(folder, f"{row['hash']}.jpg"))
            photo = ImageTk.PhotoImage(image.resize((DISPLAY_SIZE, DISPLAY_SIZE), Image.Resampling.LANCZOS))
            self.img_label.config(image=photo)
            self.img_label.image = photo
            self.progress_var.set(f"{self.current + 1} / {self.n}")

    def advance(self):
        self.current = (self.current + 1) % self.n
        self.show_current()

    def back(self):
        self.current = (self.current - 1) % self.n
        self.show_current()

    def submit_guess(self):
        try:
            guess = int(self.guess_var.get().replace('.', '').replace(',', ''))
            if abs(guess - self.true_price) < PRICE_LENIENCE:
                hint = "Which is correct 🎉"
            else:
                hint = f'True value is {"higher" if guess < self.true_price else "lower"}'
            self.result_var.set(f"Your guess: €{guess:,}. {hint}")
            self.next_df()
            self.show_current()
        except ValueError:
            self.result_var.set("Enter a valid number")


if __name__ == '__main__':
    df = load_property()
    dfs = [
        df.loc[df['class_prediction'].str.contains('other_map')],
        df.loc[df['class_prediction'].str.contains('exterior')],
        df.loc[df['class_prediction'].str.contains('interior')],
    ]
    root = tk.Tk()
    PropertyGame(root, dfs)
    root.mainloop()