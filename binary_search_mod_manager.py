##> Binary Search Mod Manager <##
#        Version: 1.3.2         #
#        By: RoarkCats          #
##> ------------------------- <##

from os import listdir as ls, rename, makedirs
from ast import literal_eval
import re

## Settings
MODS_DIR = './mods/'
JAR = '.jar'
DISABLED = '.disabled'
COMPACT_LEN = 16 # str len for mods compact display
COMPACT_PER_LINE = 5 # number of mods to show per line compact display
STATE_FILE_DIR = './' # dir for state files
STATE_FILE_EXT = '.bsmm' # file extension for state import/exports

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
        if not self.enabled and mod.enabled : self.enable()
        
    def remove_dependent(self, mod: 'Mod') :
        if mod in self.dependents : self.dependents.remove(mod)
        self.has_dependents = len(self.dependents) > 0
    
    def reset_dependents(self) :
        self.dependents.clear()
        self.has_dependents = False

    def toggle_exclusion(self) :
        self.excluded = not self.excluded
    
    def enable(self, print_err=True) -> list[bool] :
        if not self.enabled and not self.excluded :
            try :
                rename(MODS_DIR+self.id+DISABLED, MODS_DIR+self.id)
                self.enabled = True
            except Exception as e :
                if print_err: print(e)
        return self.enabled
    
    def disable(self, print_err=False) -> list[bool] :
        if self.enabled and not self.excluded :
            try :
                live_dep = [d for d in self.dependents if d.enabled]
                if len(live_dep) > 0 : raise Exception(f"Cannot disable {self.id} while dependents live. {live_dep}")

                rename(MODS_DIR+self.id, MODS_DIR+self.id+DISABLED)
                self.enabled = False
            except Exception as e :
                if print_err: print(e)
        return not self.enabled
    
    def get_file(self) -> str :
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
            print(f"{str(i).rjust(3,'0')}: {compact_str(mod)}", end='')
            if ((i+1) % COMPACT_PER_LINE) == 0 : print()
            else : print("\t",end='')
    print('\n')

def compact_str(mod, len=COMPACT_LEN) -> str :
    if isinstance(mod, Mod) : mod = mod.id
    mod = mod.replace(JAR,'').replace(DISABLED,'')
    mod = mod[:len].ljust(len)
    return mod

def dependents_str(mod: Mod) -> str :
    return f"-->{str([compact_str(dep) for dep in mod.dependents])}" if mod.has_dependents else ''

U = '\033[4m' # underline
R = '\033[0m' # reset
def format_txt_char(txt: str, code: str=U, repl: str='^') -> str :
    # formats the char after `repl` with `code`
    text = txt.split(repl)
    return ''.join(text[:1]+[code+t[:1]+R+t[1:] for t in text[1:]])

## Search Operations
def reset() :
    success = [mod.enable() for mod in all_mods]
    history.clear()
    history.append((0,len(all_mods)))
    print(f"Reset binary search ({sum(success)}/{len(success)} enabled)\n")

def narrow_search(swap=False, new_op=None) :
    if new_op == None :
        last_op = history[-1]
        count = last_op[1] - last_op[0]
        new_op = (last_op[0], last_op[1]-(count//2)) if not swap else (last_op[0]+(count//2), last_op[1])
        history.append(new_op)
    mods = all_mods[new_op[1]:]+all_mods[:new_op[0]]
    success = [mod.disable() for mod in mods] # disable outside operation
    if False in success : # try again for failed disables (ex dependency got disabled after)
        success = [successful or mods[i].disable() for i,successful in enumerate(success)]
    print(f"Narrowed binary search ({sum(success)}/{len(success)} disabled)\n")

def swap_search() :
    # basically just going back and switching to other half of narrow_search
    undo_search(swap=True)
    print("Swapped last binary search to alternate half")
    narrow_search(swap=True)

def undo_search(swap=False) :
    if len(history) > 1 :
        history.pop()
        last_op = history[-1]
        success = [mod.enable() for mod in all_mods[last_op[0]:last_op[1]] ]
        if not swap : print(f"Undid last binary search ({sum(success)}/{len(success)} enabled)\n")
    else :
        if not swap : print("Nothing to undo!\n")

## Mod Operations
def search_mod_name(txt: str) -> list[Mod] :
    mods = [mod for mod in all_mods if txt.lower() in mod.id.lower()] # partial string match
    if len(mods) == 0 : print(f"No mods found matching: '{txt}'!")
    if len(mods) <= 1 : return mods # return mod if 1 found

    print("Multiple mods found!")
    display(mods)
    return select_mods(mods)

def select_mods(last_displayed = None) -> list[Mod] :
    if last_displayed == None :
        display(all_mods)
        last_displayed = all_mods

    nums = input(" Select Mod(s) (ex 7,2-5,jei): ")
    mods = []
    print()
    try :
        nums = nums.replace(' ','').split(',')
        text = [n for n in nums if re.search('[A-Za-z_]',n)]
        nums = [n for n in nums if n not in text] # filter text inputs out of nums and into text
        [mods.extend(search_mod_name(txt)) for txt in text] # get mods from text
        nums = [[int(n) for n in num.split('-')] for num in nums] # [[a],[b],[c,d]]
        mods += [last_displayed[n[0]] for n in nums if len(n)==1] # add individual mod ids
        [mods.extend(last_displayed[n[0]:n[1]+1]) for n in nums if len(n)==2] # add series of mod ids
        return mods
    except Exception as e :
        print(e)
        return []
    
def edit_mods(last_displayed) :

    mods = select_mods(last_displayed)
    
    while (True) :

        print(f"Editing: {", ".join([compact_str(mod,round(COMPACT_LEN*1.5))+dependents_str(mod) for mod in mods])}")
        print(format_txt_char("^Back (-1) - ^Disable/^Enable (0/1) ^Toggle Exclusion (2) ^Add/^Reset De^pendents (3/4) ^Add/^Remove Re^quirements (5/6)"))

        choice = input("\n Operation: ")
        print()
    
        match choice.strip().lower() :
            case '-1'|'b': return
            case '0'|'d':
                disabled = sum([mod.disable(print_err=True) for mod in mods])
                print(f"Disabled {disabled}/{len(mods)} selected mods\n")
            case '1'|'e':
                enabled = sum([mod.enable() for mod in mods])
                print(f"Enabled {enabled}/{len(mods)} selected mods\n")
            case '2'|'t':
                [mod.toggle_exclusion() for mod in mods]
                print("Toggled exclusion on selected mods\n")
            case '3'|'ap'|'p':
                dependents = select_mods()
                out = [ [mod.add_dependent(dep) for dep in dependents] for mod in mods]
                print(f"Added selected {len(out[0])} mods as dependents\n")
            case '4'|'rp':
                [mod.reset_dependents() for mod in mods]
                print("Reset dependents on selected mods\n")
            case '5'|'aq'|'q':
                reqs = select_mods()
                out = [ [req.add_dependent(mod) for mod in mods] for req in reqs]
                print(f"Added selected {len(out[0])} mods as requirements\n")
            case '6'|'rq':
                reqs = select_mods()
                out = [ [req.remove_dependent(mod) for mod in mods] for req in reqs]
                print(f"Removed selected {len(out[0])} mods as requirements\n")
            case _ : 
                print("Invalid operation.\n")
                continue
        break

## State Operations
def mk_dir_state() :
    try : makedirs(STATE_FILE_DIR)
    except : pass

def export_state() :
    mk_dir_state()
    name = input(" State Name: ")
    if name == '' : return

    try :
        with open(f"{STATE_FILE_DIR}{name}{STATE_FILE_EXT}", "w") as f :
            f.write("# This file is imported by binary_search_mod_manager.py as a saved state (do not edit this file!)\n")
            f.write(f"{{ 'history': {history}, ")
            f.write(f"'exclusions': {[mod.id for mod in all_mods if mod.excluded]}, ")
            f.write(f"'dependents': {[(mod.id, [str(d) for d in mod.dependents]) for mod in all_mods if mod.has_dependents]} }}")
        print(f"\nState exported to {name}{STATE_FILE_EXT}\n")
    except Exception as e :
        print(e)

def import_state() :
    mk_dir_state()
    print(f" Found States: {[f.replace(STATE_FILE_EXT,'') for f in ls(STATE_FILE_DIR) if f.endswith(STATE_FILE_EXT)]}")
    name = input(" State Name: ")
    if name == '' : return

    try :
        with open(f"{STATE_FILE_DIR}{name}{STATE_FILE_EXT}", "r") as f :
            data = f.readlines()[1]
            data = literal_eval(data)

            [mod.toggle_exclusion() for mod_id in data['exclusions'] for mod in search_mod_name(mod_id) if not mod.excluded]
            [search_mod_name(mod_id)[0].add_dependent(search_mod_name(dep)[0]) for mod_id, dependents in data['dependents'] for dep in dependents]
            global history
            history = history[:1]+data['history'][1:] # preserve largest scope of history
            if len(history) > 1 : narrow_search(new_op = history[-1]) # rerun last operation (narrowest)

        print(f"State imported from {name}{STATE_FILE_EXT}\n")
    except Exception as e :
        print(e)

## Menu
def menu(value = -1) :
    last_displayed = all_mods
    while True :
        
        choice = str(value)
        if value == -1 :
            print(format_txt_char("E^xit (-1) - ^List ^All/^Enabled/^Disabled (0/1/2) ^Narrow/^Swap/^Undo/^Reset Search (3/4/5/6) Edit ^Mods (7) ^Export/^Import (8/9)"))
            choice = input("\n Operation: ")
            print()

        match choice.strip().lower() :
            case '-1'|'x': exit()
            case '0'|'la'|'l':
                print('__ All Mods __')
                display(all_mods)
                last_displayed = all_mods
            case '1'|'le':
                print('__ Enabled Mods __')
                last_displayed = [mod for mod in all_mods if mod.enabled]
                display(last_displayed)
            case '2'|'ld':
                print('__ Disabled Mods __')
                last_displayed = [mod for mod in all_mods if not mod.enabled]
                display(last_displayed)
            case '3'|'n': narrow_search()
            case '4'|'s': swap_search()
            case '5'|'u': undo_search()
            case '6'|'r': reset()
            case '7'|'m': edit_mods(last_displayed)
            case '8'|'e': export_state()
            case '9'|'i': import_state()
            case _ : print("Invalid operation.\n")
        
        if value != -1 : return


## Main
def main() :

    menu(0) # display all mods
    try : menu() # start menu
    except Exception as e : input(e)

if __name__ == '__main__' : main()