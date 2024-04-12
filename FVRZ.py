import requests
from bs4 import BeautifulSoup
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

url = "https://matchcenter.fvrz.ch/default.aspx?lng=1"

try:
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    specific_class_content = soup.find_all('div', class_='nisListeRD list-group')
    i = 0
    for content in specific_class_content:
        raw_data = content.text

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")


games = soup.find_all("div", class_="list-group-item")

data = {
    "Datum": [],
    "Zeit": [],
    "Heimmannschaft": [],
    "Auswärtsmannschaft": [],
    "Punktestand A": [],
    "Punktestand B": [],
    "Ort": [],
    "Bemerkungen": [],
    "Details zur Meisterschaft": [],
    "Spielnummer": [],
}

def safe_text(element):
    if element:
        if element.text.strip() != ' ' and element.text.strip() != '':
            return element.text.strip()
    return '-'

for game in games:
    game : BeautifulSoup
    time = safe_text(game.find("div", class_="time"))
    teamA = safe_text(game.find("div", class_="teamA"))
    teamB = safe_text(game.find("div", class_="teamB"))
    scoreA = safe_text(game.find("div", class_="torA"))
    scoreB = safe_text(game.find("div", class_="torB"))
    checkDate = True if str(game)[0:38] == '<div class="list-group-item sppTitel">' else False
    if checkDate:
        date = str(game)[41:52]
    div_info = game.find('div', {'class': 'col-xs-12 col-md-11 col-md-offset-1'})
    spp_status_text = game.find('span', {'class': 'sppStatusText'}).get_text() if game.find('span', {'class': 'sppStatusText'}) else '-'
    if div_info and not checkDate:
        text_parts = div_info.get_text(separator="|").split('|')
        if len(text_parts) == 3:
            location_and_allocation = text_parts[0].strip() if len(text_parts) > 0 else '-'
            championship_details = text_parts[1].strip() if len(text_parts) > 1 else '-'
            game_number = text_parts[2].strip() if len(text_parts) > 2 else '-'
        else:
            location_and_allocation = text_parts[0].strip() if len(text_parts) > 0 else '-'
            championship_details = text_parts[2].strip() if len(text_parts) > 2 else '-'
            game_number = text_parts[3].strip() if len(text_parts) > 3 else '-'
    else:
        location_and_allocation = "-"
        championship_details = "-"
        game_number = "-"

    if not checkDate:
        data["Datum"].append(date)
        data["Zeit"].append(time)
        data["Heimmannschaft"].append(teamA)
        data["Auswärtsmannschaft"].append(teamB)
        data["Punktestand A"].append(scoreA if scoreA.isdigit() else '-')
        data["Punktestand B"].append(scoreB if scoreB.isdigit() else '-')
        data["Ort"].append(location_and_allocation)
        data["Bemerkungen"].append(spp_status_text)
        data["Details zur Meisterschaft"].append(championship_details)
        if game_number != "-":
            data["Spielnummer"].append(game_number.split(' ')[1])
        else:
            data["Spielnummer"].append(game_number)


df = pd.DataFrame(data)

def load_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        geometry = app.geometry()
        global df
        df = pd.read_csv(file_path)
        display_data(df)
        app.geometry(geometry)

def save_csv():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        df.to_csv(file_path, index=False)
        messagebox.showinfo("Data Export", "CSV file has been saved")

def combined_search():
    filters = [(col, var.get()) for col, var in search_vars.items() if var.get()]
    filtered_df = df.copy()
    for col, query in filters:
        if query:
            filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(query, na=False)]
    display_data(filtered_df)

def display_data(data):
    clear_data()
    tree["column"] = list(data.columns)
    tree["show"] = "headings"
    for column in tree["column"]:
        tree.heading(column, text=column)

    df_rows = data.to_numpy().tolist()
    for row in df_rows:
        tree.insert("", "end", values=row)

def clear_data():
    tree.delete(*tree.get_children())

app = tk.Tk()
app.title("FVRZ Manager")
app.geometry("1000x600")

frame = tk.Frame(app)
frame.pack(fill=tk.BOTH, expand=True)

tree = ttk.Treeview(frame)
tree.pack(side="top", fill=tk.BOTH, expand=True)

v_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
v_scroll.pack(side='right', fill='y')
tree.configure(yscrollcommand=v_scroll.set)

h_scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
h_scroll.pack(side='bottom', fill='x')
tree.configure(xscrollcommand=h_scroll.set)

frame_controls = tk.Frame(app)
frame_controls.pack(pady=20, fill=tk.X)

search_vars = {}

def create_search_bars(columns):
    for widget in frame_controls.winfo_children():
        widget.destroy()

    btn_load = ttk.Button(frame_controls, text="CSV hochladen", command=lambda: [load_csv(), create_search_bars(df.columns)])
    btn_load.pack(side=tk.RIGHT, padx=10)

    btn_save = ttk.Button(frame_controls, text="CSV speichern", command=save_csv)
    btn_save.pack(side=tk.RIGHT, padx=10)

    btn_search_all = ttk.Button(frame_controls, text="Suchen", command=combined_search)
    btn_search_all.pack(side=tk.RIGHT, padx=10)

    i = 0
    for col in columns:
        if i < 2:
            frame_search = tk.Frame(frame_controls)
            frame_search.pack(side=tk.LEFT, fill=tk.X, expand=False)
            lbl = tk.Label(frame_search, text=f"{col}:")
            lbl.pack(side=tk.LEFT, padx=5)
            search_var = tk.StringVar()
            search_vars[col] = search_var
            search_entry = ttk.Entry(frame_search, textvariable=search_var)
            search_entry.pack(side=tk.LEFT, padx=5)
            i+=1
        else:
            break


btn_load = ttk.Button(frame_controls, text="CSV hochladen", command=lambda: [load_csv(), create_search_bars(df.columns)])
btn_load.pack(side=tk.RIGHT, padx=10)

btn_save = ttk.Button(frame_controls, text="CSV speichern", command=save_csv)
btn_save.pack(side=tk.RIGHT, padx=10)

display_data(df)
create_search_bars(df.columns)

app.mainloop()

