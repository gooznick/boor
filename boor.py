import random
fid=open("settlements.txt","r",encoding="utf8")
lines=fid.readlines()
fid.close()
settlements = list(map(lambda x: x.strip()[::-1], lines))
for r in '"':
    settlements = [s for s in settlements if r not in s]
for r in '()" -'+"'":
    settlements = list(map(lambda x: x.replace(r,''), settlements))
for f,t in zip("מנצפכ", "םןץףך"):
    settlements = list(map(lambda x: x.replace(t,f), settlements))

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
    #your = input("?")
    #current = your + current
    #print(current, chosen_settlement)

