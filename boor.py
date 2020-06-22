import random
import tkinter as Tk
from tkinter import messagebox
from PIL import ImageTk, Image

global settlements, converter, data, forbid, current, canvas, settlements_data, labelText, oval, root


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

def name_to_key(name):
    """
    Convert name of a settlement to a key of the dictionary.
    The key will be the final name in the game
    """
    # remove what in ()
    name = name.strip()
    if "(" in name and ")" in name:
        name = name[:name.find("(")]+name[name.find(")")+1:]
    # end letters
    for f,t in zip("מנצפכ", "םןץףך"):
        name = name.replace(t,f)
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


# Read data
main_file = "settlements.csv"
exceptions_file  = "exceptions.csv"
mapping_file  = "israel.csv"
settlements_data = create_settlements_data(main_file, exceptions_file)
settlements = list(settlements_data.keys())


converter = create_coordinates_converter(settlements_data, mapping_file)

forbid=[]
current = ''


# will return list of tuples - the next letter and next settlement
def choose_all(current, settlements, forbid = None):
    if not forbid:
        forbid=[]
    # first time - all are ok
    if not current:
        return [(s[-1], s) for s in settlements]

    # find starts with the letter
    settlements_options = list(filter(lambda x:x.endswith(current) and x!=current, settlements))
    settlements_options = list(filter(lambda x:x not in forbid, settlements_options))
    options = [(s[-1-len(current)], s) for s in settlements_options]

    # find if a full settlements can be removed
    full_settlement = list(filter(lambda x:current.endswith(x), settlements))
    for fs in full_settlement:
        forbid += [fs]
        new_current = current[:-len(fs)]
        options+=choose_all(new_current, settlements, forbid)
    return options

def draw_settlements(name):
    coordinates = converter(settlements_data[name]["itm"])
    coordinates = coordinates*zoom
    x,y = 10,10
    values = map(int, [coordinates[0]-x, coordinates[1]-y, coordinates[0]+x, coordinates[1]+y])
    canvas.coords(oval, *values)

def kp(event):
    global settlements, converter, data, forbid, current
    if event.keysym == "Escape":
        root.destroy()
    elif event.char == " ":
        forbid=[]
        current = ''
        labelText.set("-")
        canvas.coords(oval, -10,-10,-10,-10)

    elif event.char in "אבגדהוזחטיכלמנסעפצקרשת":
        current = event.char + current
        options = choose_all(current,settlements)
        if not options:
            options = choose_all(current[1:],settlements)
            option = options[random.randint(0,len(options)-1)]
            info = settlements_data[option[1]]
            m1 = "שם הישוב:{}".format(info["name"])
            m2 = "{}:הוקם בשנת".format(info["establishment"])
            m3 = "{}:תושבים".format(info["population"])
            message="\n".join([m1,m2,m3])
            messagebox.showerror(title="!אתה בור", message=message)
            # restart !
            current = ''
            options = choose_all(current,settlements)
        letter, chosen_settlement = options[random.randint(0,len(options)-1)]

        current = letter + current
        labelText.set(current[::-1])
        draw_settlements(chosen_settlement)


root = Tk.Tk()
image = Image.open("israel.jpg")
zoom = .1
pixels_x, pixels_y = tuple([int(zoom * x)  for x in image.size])
background_image = ImageTk.PhotoImage(image.resize((pixels_x, pixels_y)))
canvas = Tk.Canvas(root)
image = canvas.create_image(0, 0, anchor=Tk.NW, image=background_image)
labelText = Tk.StringVar()
labelText.set("-")
label = Tk.Label(root, textvariable=labelText)
oval = canvas.create_oval(-10,-10,-10,10, outline='red',width=3,fill='')


canvas.pack(side="top", fill="both", expand=True)
label.pack(side="bottom")
root.minsize(width=pixels_x, height=pixels_y+15)
root.resizable(0, 0) #Don't allow resizing in the x or y direction
#root.wm_geometry("794x370")
root.title('Map')
root.bind_all('<KeyPress>', kp)
root.mainloop()

quit()
for a in range(1000000):
    options = choose_all(current,settlements)
    if not options:
        print("end")
        quit()
    letter, chosen_settlement = options[random.randint(0,len(options)-1)]
    current = letter + current
    print(current)
    your = input("?")
    current = your + current
    print(current, chosen_settlement)


