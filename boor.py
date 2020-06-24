import random
import tkinter as Tk
from tkinter import messagebox
import os
import json
import codecs

global gui_globals, game_globals


def choose_all(current, settlements, former = None):
    """
    The main function.

    Will return all possibilities, a list of tuples :
        next letter, next settlement, former settlements
    """
    if not former:
        former=[]
    # first time - all are ok
    if not current:
        return [(s[-1], s, []) for s in settlements]

    # find starts with the letter
    settlements_options = list(filter(lambda x:x.endswith(current) and x!=current, settlements))
    settlements_options = list(filter(lambda x:x not in former, settlements_options))
    options = [(s[-1-len(current)], s, former) for s in settlements_options]

    # find if a full settlements can be removed
    full_settlement = list(filter(lambda x:current.endswith(x), settlements))
    for fs in full_settlement:
        former += [fs]
        new_current = current[:-len(fs)]
        options+=choose_all(new_current, settlements, former)
    return options

def find_all_former(options):
    """
    Find all settlements that were already in the game, from the options.

    (will find only settlements that are sure)
    """
    if not options :
        return set()
    former = set(options[0][2])  # begin with first
    for option in options :
        former = former.intersection(set(option[2]))  # all former
    return former


def draw_settlements(name):
    x,y = settlements_data[name]["x"], settlements_data[name]["y"]
    dx,dy = 10,10
    values = map(int, [x-dx, y-dy, x+dx, y+dy])
    gui_globals["canvas"].coords(gui_globals["oval"], *values)


def remove_sofit(name):
    """
    Change the final letters מנצפכ to regular
    """
    # end letters
    for f,t in zip("מנצפכ", "םןץףך"):
        name = name.replace(t,f)
    return name


def kp(event):
    settlements_data, settlements = game_globals["settlements_data"], game_globals["settlements"]
    char = remove_sofit(event.char)
    if event.keysym == "Escape":
        gui_globals["root"].destroy()
    elif char == " ":
        game_globals["forbid"]=[]
        game_globals["current"] = ''
        gui_globals["label"].set("-")
        gui_globals["canvas"].coords(gui_globals["label"], -10,-10,-10,-10)

    elif char in "אבגדהוזחטיכלמנסעפצקרשת":
        game_globals["current"] = char + game_globals["current"]
        options = choose_all(game_globals["current"], settlements, game_globals["forbid"])
        if not options:
            options = choose_all(game_globals["current"][1:],settlements, game_globals["forbid"])
            option = options[random.randint(0,len(options)-1)]
            info = settlements_data[option[1]]
            draw_settlements(option[1])
            m1 = "שם הישוב:{}".format(info["name"])
            m2 = "{}:הוקם בשנת".format(info["establishment"])
            m3 = "{}:תושבים".format(info["population"])
            message="\n".join([m1,m2,m3])

            all_former = find_all_former(options)
            if all_former:
                names = [settlements_data[n]["name"] for n in all_former]
                message += "\n"
                message += ":מחוץ למשחק"
                message += "\n"
                message += ",".join(names)
                game_globals["forbid"] = list(all_former)

            messagebox.showerror(title="!אתה בור", message=message)
            # restart !
            game_globals["current"] = ''
            options = choose_all(game_globals["current"],settlements, game_globals["forbid"])
        letter, chosen_settlement, former = options[random.randint(0,len(options)-1)]

        game_globals["current"] = letter + game_globals["current"]
        to_show = game_globals["current"][::-1]
        if len(to_show)>50:
            to_show=to_show[50:]
        gui_globals["label"].set(to_show)
        draw_settlements(chosen_settlement)
        gui_globals["canvas"].itemconfig(gui_globals["points"], text=str(len(game_globals["current"])*5))


# Read data
here_dir = os.path.dirname(__file__)
image_file = os.path.join(here_dir,"israel.png")

data_file = os.path.join(here_dir,"data.json")
with codecs.open(data_file, 'r', 'utf-8-sig') as fid:
    settlements_data = json.load(fid)
settlements = list(settlements_data.keys())

# init globals
gui_globals = {}
game_globals = {}
game_globals["settlements"] = settlements
game_globals["current"] = ''
game_globals["forbid"] = []
game_globals["settlements_data"] = settlements_data

gui_globals["root"] = Tk.Tk()
root = gui_globals["root"]

background_image = Tk.PhotoImage(file=image_file)
canvas = Tk.Canvas(gui_globals["root"])
gui_globals["canvas"] = canvas
image = canvas.create_image(0, 0, anchor=Tk.NW, image=background_image)
gui_globals["points"] = canvas.create_text(30,20,fill="orange",font="Times 20 italic bold", text="-")
gui_globals["label"] = Tk.StringVar()
gui_globals["label"].set("-")
label = Tk.Label(root, textvariable=gui_globals["label"])
gui_globals["oval"] = canvas.create_oval(-10,-10,-10,10, outline='red',width=3,fill='')
canvas.pack(side="top", fill="both", expand=True)
label.pack(side="bottom")
root.minsize(width=background_image.width(), height=background_image.height()+15)
root.resizable(0, 0) #Don't allow resizing in the x or y direction
root.title('Map')
root.bind_all('<KeyPress>', kp)
root.mainloop()


# usused
def no_gui():
    for a in range(1000000):
        options = choose_all(current,settlements)
        if not options:
            print("end")
            quit()
        letter, chosen_settlement, former = options[random.randint(0,len(options)-1)]
        current = letter + current
        print(current)
        your = input("?")
        current = your + current
        print(current, chosen_settlement)
