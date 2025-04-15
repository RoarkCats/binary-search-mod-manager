from os import listdir as ls, rename

## Settings
MODS_DIR = './mods/'
JAR = '.jar'
DISABLED = '.disabled'
COMPACT_LEN = 16 # str len for mods compact display
COMPACT_PER_LINE = 5 # number of mods to show per line compact display

## Mod class
class Mod :
    def __init__(self, file) :
        self.id = file.replace(DISABLED,'')
        self.enabled = self.id == file # if enabled, file should be same as self.id
        self.excluded = False
        self.has_dependents = False
        self.dependents = set()
    
    def __repr__(self) :
        return self.id

    def __hash__(self) :
        return hash(self.id)
    
    def __eq__(self, other) :
        if isinstance(other, Mod) : 
            return self.id == other.id
        elif isinstance(other, str) :
            return self.id == other
        elif type(other) is bool :
            return self.enabled == other
        else :
            raise TypeError("Type mismatch! Expected a Mod, str, or bool.")
        
    def add_dependent(self, mod: 'Mod') :
        if self == mod : print("Cannot add self as dependent!"); return
        self.has_dependents = True
        self.dependents.add(mod)
        
    def remove_dependent(self, mod: 'Mod') :
        if mod in self.dependents : self.dependents.remove(mod)
        self.has_dependents = len(self.dependents) > 0
    
    def reset_dependents(self) :
        self.dependents.clear()
        self.has_dependents = False

    def toggle_exclusion(self) :
        if self.excluded : self.excluded = False
        else : self.excluded = True; self.enable()
    
    def enable(self) :
        if not self.enabled :
            try :
                rename(MODS_DIR+self.id+DISABLED, MODS_DIR+self.id)
                self.enabled = True
            except Exception as e :
                print(e)
    
    def disable(self) :
        if self.enabled and not self.excluded :
            try :
                live_dep = [d for d in self.dependents if d.enabled]
                if len(live_dep) > 0 : raise Exception(f"Cannot disable {self.id} while dependents live. {live_dep}")

                rename(MODS_DIR+self.id, MODS_DIR+self.id+DISABLED)
                self.enabled = False
            except Exception as e :
                print(e)
    
    def get_file(self) :
        return self.id if self.enabled else self.id+DISABLED

## Initialize mod lists
all_mods = []
try : all_mods = [Mod(m) for m in ls(MODS_DIR) if m.endswith(JAR) or m.endswith(JAR+DISABLED)]
except : input('FAILED TO FIND MODS FOLDER!'); exit()
history = [ (0,len(all_mods)) ]

## Display methods
def display(mods, compact=True) :
    for i,mod in enumerate(mods) :
        if not compact :
            print(f"{i} - {mod.get_file()}{dependents_str(mod)}")
        else :
            print(f"{str(i).rjust(3,'0')}: {compact_str(mod)}\t", end='')
            if ((i+1) % COMPACT_PER_LINE) == 0 : print()
    print('\n')

def compact_str(mod, len=COMPACT_LEN) :
    if isinstance(mod, Mod) : mod = mod.id
    mod = mod.replace(JAR,'').replace(DISABLED,'')
    mod = mod[:len].ljust(len)
    return mod

def dependents_str(mod: Mod) :
    return f"-->{str([compact_str(dep) for dep in mod.dependents])}" if mod.has_dependents else ''

## Search Operations
def reset() :
    [mod.enable() for mod in all_mods]
    history.clear()
    history.append((0,len(all_mods)))

def narrow_search(swap=False) :
    last_op = history[-1]
    count = last_op[1] - last_op[0]
    new_op = (last_op[0], last_op[1]-(count//2)) if not swap else (last_op[0]+(count//2), last_op[1])
    [mod.disable() for mod in all_mods[new_op[1]:]+all_mods[:new_op[0]] ] # disable outside operation
    history.append(new_op)

def swap_search() :
    # basically just going back and switching to other half of narrow_search
    undo_search()
    narrow_search(swap=True)

def undo_search() :
    if len(history) > 1 :
        history.pop()
        last_op = history[-1]
        [mod.enable() for mod in all_mods[last_op[0]:last_op[1]] ]
    else :
        print("Nothing to undo!\n")

## Mod Operations
def select_mods(last_displayed = None) :
    if last_displayed == None :
        display(all_mods)
        last_displayed = all_mods

    nums = input(" Select Mod(s) (ex 0,7,2-5): ")
    print()
    try :
        nums = nums.replace(' ','').split(',')
        nums = [[int(n) for n in num.split('-')] for num in nums] # [[a],[b],[c,d]]
        mods = [last_displayed[n[0]] for n in nums if len(n)==1] # add individual mod ids
        [mods.extend(last_displayed[n[0]:n[1]+1]) for n in nums if len(n)==2] # add series of mod ids
        return mods
    except Exception as e :
        print(e)
        return []
    
def edit_mods(last_displayed) :

    mods = select_mods(last_displayed)
    
    print(f"Editing: {", ".join([compact_str(mod,round(COMPACT_LEN*1.5))+dependents_str(mod) for mod in mods])}")
    print("Back (-1) - Disable/Enable (0/1) Toggle Exclusion (2) Add/Reset Dependents (3/4) Add/Remove Requirements (5/6)")

    choice = input("\n Operation: ")
    print()
    
    match choice :
        case '-1': return
        case '0':
            [mod.disable() for mod in mods]
        case '1':
            [mod.enable() for mod in mods]
        case '2':
            [mod.toggle_exclusion() for mod in mods]
        case '3':
            dependents = select_mods()
            [ [mod.add_dependent(dep) for dep in dependents] for mod in mods]
        case '4':
            [mod.reset_dependents() for mod in mods]
        case '5':
            reqs = select_mods()
            [ [req.add_dependent(mod) for mod in mods] for req in reqs]
        case '6':
            reqs = select_mods()
            [ [req.remove_dependent(mod) for mod in mods] for req in reqs]
        case _ : print("Invalid operation.\n")


## Menu
def menu(value = -1) :
    last_displayed = all_mods
    while True :
        
        choice = str(value)
        if value == -1 :
            print("Exit (-1) - List All/Enabled/Disabled (0/1/2) Narrow/Swap/Undo/Reset Search (3/4/5/6) Edit Mods (7)")
            choice = input("\n Operation: ")
            print()

        match choice :
            case '-1': exit()
            case '0':
                print('__ All Mods __')
                display(all_mods)
                last_displayed = all_mods
            case '1':
                print('__ Enabled Mods __')
                last_displayed = [mod for mod in all_mods if mod.enabled]
                display(last_displayed)
            case '2':
                print('__ Disabled Mods __')
                last_displayed = [mod for mod in all_mods if not mod.enabled]
                display(last_displayed)
            case '3': narrow_search()
            case '4': swap_search()
            case '5': undo_search()
            case '6': reset()
            case '7': edit_mods(last_displayed)
            case _ : print("Invalid operation.\n")
        
        if value != -1 : return


## Main
def main() :

    menu(0) # display all mods
    try : menu() # start menu
    except Exception as e : input(e)

if __name__ == '__main__' : main()