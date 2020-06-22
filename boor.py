import random
import tkinter as Tk
from tkinter import messagebox
from PIL import ImageTk, Image
import os

global gui_globals, game_globals

def read_settlements(filename):
    """
    This method reads the settlements file.
    It's an csv file, exported by excel, imported from https://data.gov.il/dataset/settlement-file :
    https://www.cbs.gov.il/he/publications/doclib/2019/ishuvim/bycode2018.xlsx

    The file begins with a BOM of utf8.

    The method return an dictionary, the key is the name of the settlement, and the values are the parsed columns :
        population
        establishment (year)
        location (touple, itm)
    """

    fid = open(filename,"r",encoding="utf8")
    fid.read(1)  # ignore BOM
    captions = fid.readline()
    used_captions = {"name":0, "religion":8, "population":9, "establishment":13, "location":16}
    JEWISH = '1'
    MEORAV = '4'
    data = {}
    for line in fid:
        splitted = line.split(",")
        name = splitted[used_captions["name"]]
        if splitted[used_captions["religion"]] in [JEWISH, MEORAV]:
            data[name] = {}
            for column in ["name", "population", "establishment", "location"]:
                index = used_captions[column]
                data[name][column] = splitted[index]
            itm = data[name]["location"]
            data[name]["itm"] = (float(itm[:5]), float(itm[5:]))
    fid.close()
    return data

def split_exceptions(data, filename):
    """
    This method uses an exceptions file to split some settlement to more than one :
     ("תל אביב-יפו") will become both "תל אביב" and "יפו"
    The manually made file is an csv, with the format :
        name(as in the main file), name-option1, name-option2, ...
    The original name will be deleted.
    """

    fid = open(filename,"r",encoding="utf8")
    fid.read(1)  # ignore BOM
    for line in fid:
        splitted = line.split(",")
        name = splitted[0]
        for alternative in splitted[1:]:
            alternative=alternative.strip()
            if alternative:
                data[alternative] = data[name]
        del data[name]
    fid.close()

def remove_sofit(name):
    """
    Change the final letters מנצפכ to regular
    """
    # end letters
    for f,t in zip("מנצפכ", "םןץףך"):
        name = name.replace(t,f)
    return name

def name_to_key(name):
    """
    Convert name of a settlement to a key of the dictionary.
    The key will be the final name in the game
    """
    # remove what in ()
    name = name.strip()
    if "(" in name and ")" in name:
        name = name[:name.find("(")]+name[name.find(")")+1:]
    name = remove_sofit(name)
    # special characters
    name = ''.join(ch for ch in name if ch.isalnum())
    return name[::-1]

def create_coordinates_converter(settlements_data, map_file):
    """
    Create coordinate converted from itm to the image coordinates, using 3 pre-found settlements.
    """

    fid = open(map_file,"r",encoding="utf8")
    fid.read(1)  # ignore BOM
    mappings = {}
    for line in fid:
        splitted = line.split(",")
        mappings[name_to_key(splitted[0])] = (int(splitted[1]),int(splitted[2]))

    import numpy as np
    def solve_affine( p1, p2, p3, s1, s2, s3 ):
        x = np.transpose(np.matrix([p1,p2,p3]))
        y = np.transpose(np.matrix([s1,s2,s3]))
        # add ones on the bottom of x and y
        x = np.vstack((x,[1,1,1]))
        y = np.vstack((y,[1,1,1]))
        # solve for A2
        A2 = y * x.I
        # return function that takes input x and transforms it
        # don't need to return the 4th row as it is
        return lambda x: (A2*np.vstack((np.matrix(x).reshape(2,1),1)))[0:2,:]
    map_settlemets = list(mappings.keys())
    transformFn = solve_affine( settlements_data[map_settlemets[0]]["itm"], settlements_data[map_settlemets[1]]["itm"], settlements_data[map_settlemets[2]]["itm"],
                                mappings[map_settlemets[0]], mappings[map_settlemets[1]], mappings[map_settlemets[2]])

    return transformFn

def create_settlements_data(main_file, exceptions_file):
    """
    Create settlement data from settlements and exceptions csv files

    Output :
    a dictionary - keys are the final names of the game, value is a dictionary with the data about each settlement
    """
    data = read_settlements(main_file)
    split_exceptions(data,exceptions_file)

    settlements_data={}
    for key, value in data.items():
        if not key:
            pass
        settlements_data[name_to_key(key)] = value
    return settlements_data


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
    coordinates = gui_globals["converter"](settlements_data[name]["itm"])
    coordinates = coordinates*gui_globals["zoom"]
    x,y = 10,10
    values = map(int, [coordinates[0]-x, coordinates[1]-y, coordinates[0]+x, coordinates[1]+y])
    gui_globals["canvas"].coords(gui_globals["oval"], *values)

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

main_file = os.path.join(here_dir,"settlements.csv")
exceptions_file  = os.path.join(here_dir,"exceptions.csv")
mapping_file  = os.path.join(here_dir,"israel.csv")
image_file = os.path.join(here_dir,"israel.jpg")

settlements_data = create_settlements_data(main_file, exceptions_file)
settlements = list(settlements_data.keys())
converter = create_coordinates_converter(settlements_data, mapping_file)

# init globals
gui_globals = {}
game_globals = {}
game_globals["settlements"] = settlements
game_globals["current"] = ''
game_globals["forbid"] = []
game_globals["settlements_data"] = settlements_data

gui_globals["converter"] = converter
gui_globals["root"] = Tk.Tk()
root = gui_globals["root"]
image = Image.open(image_file)
gui_globals["zoom"] = .15
pixels_x, pixels_y = tuple([int(gui_globals["zoom"] * x)  for x in image.size])
background_image = ImageTk.PhotoImage(image.resize((pixels_x, pixels_y)))
canvas = Tk.Canvas(gui_globals["root"])
gui_globals["canvas"] = canvas
image = canvas.create_image(0, 0, anchor=Tk.NW, image=background_image)
gui_globals["points"] = canvas.create_text(250*gui_globals["zoom"],150*gui_globals["zoom"],fill="orange",font="Times 20 italic bold", text="-")
gui_globals["label"] = Tk.StringVar()
gui_globals["label"].set("-")
label = Tk.Label(root, textvariable=gui_globals["label"])
gui_globals["oval"] = canvas.create_oval(-10,-10,-10,10, outline='red',width=3,fill='')
canvas.pack(side="top", fill="both", expand=True)
label.pack(side="bottom")
root.minsize(width=pixels_x, height=pixels_y+15)
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


