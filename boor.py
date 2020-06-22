import random


def read_settlements(filename = "settlements.csv"):
    fid = open(filename,"r",encoding="utf8")
    fid.read(1)  # ignore BOM
    captions = fid.readline()
    used_captions = {"name":0, "religion":8, "population":9, "establishment":13, "location":16}
    JEWISH = '1'
    data = {}
    for line in fid:
        splitted = line.split(",")
        name = splitted[used_captions["name"]]
        if splitted[used_captions["religion"]] == JEWISH:
            data[name] = {}
            for column in ["name", "population", "establishment", "location"]:
                index = used_captions[column]
                data[name][column] = splitted[index]
    fid.close()
    return data

def split_exceptions(data, filename = "exceptions.csv"):
    fid = open("exceptions.csv","r",encoding="utf8")
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

def my_strip(name):
    # remove what in ()
    if "(" in name and ")" in name:
        name = name[:name.find("(")]+name[name.find(")")+1:]
    # end letters
    for f,t in zip("מנצפכ", "םןץףך"):
        name = name.replace(t,f)
    # special characters
    name = ''.join(ch for ch in name if ch.isalnum())
    return name

data = read_settlements()
split_exceptions(data)

settlements_data={}
for key, value in data.items():
    if not key:
        pass
    settlements_data[my_strip(key)] = value

settlements = list(map(lambda x:x[::-1],settlements_data.keys()))

print(settlements[0:10])

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


current = ''
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

