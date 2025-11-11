import subprocess
from tkinter import Tk, filedialog
import os
from pathlib import Path
import shutil
import json

#Constents
amrita_offset=0x7B8D0
gold_offset=0x7B8D8
player_level=0x1C4904 # and 0x1C4908
constitution=0x1C490C
heart=0x1C4910
courage=0x1C4928
stamina=0x1C4914
strenght=0x1C4918
skill=0x1C491C
dexterity=0x1C4920
magic=0x1C4924




#

data=None
MODE=None
decrypted_path=None


base_dir = Path(__file__).parent

def load_and_copy_json(file_name):
    file_path = base_dir / file_name
    with open(file_path, "r") as file:
        return json.load(file)

items_json = load_and_copy_json("items.json")

#Hekpers
def find_value_at_offset(section_data, offset, byte_size):
    try:
        value_bytes = section_data[offset:offset+byte_size]
        if len(value_bytes) == byte_size:
            return int.from_bytes(value_bytes, 'little')
    except IndexError:
        pass
    return None

######

def open_file():
    global data, MODE, decrypted_path


    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    file_name = os.path.basename(file_path)

    #PC
    if file_name=='SAVEDATA.BIN':
        MODE='PC'
        #subprocess
        Tk().withdraw()
        exe_path = base_dir / "pc" / "pc.exe"
        if file_path:
            proc = subprocess.run(
            [str(exe_path), file_path],
            cwd=exe_path.parent,
            input="\n",
            text=True,
            capture_output=True
        )
            print(proc.stdout)
            print(proc.stderr)
        decrypted_path = exe_path.parent / "decr_SAVEDATA.BIN"
        with open(decrypted_path, 'rb') as f:
            data = bytearray(f.read())
        
        #Disable integrity checks
        data[0x7B882+0x158]=0
        data[0x7B884+0x158]=0
        data[0x7B7E4+0x158]=0
        data[0xECF4A+0x158]=0

    


    if file_name == 'APP.BIN':
        MODE='PS4'
        exe_path = base_dir / "ps4" / "ps4.exe"
        dst_path = exe_path.parent / "APP.BIN"

        # copy file to EXE folder (overwrite if exists)
        shutil.copy2(file_path, dst_path)

        # check if encrypted (first 4 bytes not all zeros)
        with open(dst_path, 'rb') as f:
            data = f.read(4)
        magic_bytes = data[:4]

        if magic_bytes != b'\x00\x00\x00\x00':
            print("Detected encrypted PS4 save. Running decryption tool...")
            subprocess.run(
                [str(exe_path), str(dst_path)],
                cwd=exe_path.parent,
                input="\n",  # auto press Enter
                text=True,
                check=True
            )
            print("Decryption finished.")
        else:
            print("File already decrypted — skipping decryption.")
        
        decrypted_path = exe_path.parent / "APP.BIN_out.bin"
        with open(decrypted_path, 'rb') as f:
            data = bytearray(f.read())
            print(data[:4])

    return data

def save_file():
    global data, decrypted_path


    if MODE=='PC':
        
        if decrypted_path is None or data is None:
            print("Nothing to save")
            return
        with open(decrypted_path, 'wb') as file:
            file.write(data)
        print(f"Saved {len(data)} bytes to {decrypted_path}")
        Tk().withdraw()
        exe_path = base_dir / "pc" / "pc.exe"
        if decrypted_path:
            proc = subprocess.run(
            [str(exe_path), decrypted_path],
            cwd=exe_path.parent,
            input="\n",
            text=True,
            capture_output=True
        )
            print(proc.stdout)
            print(proc.stderr)

        last_path = base_dir / "pc" / "decr_decr_SAVEDATA.BIN"
        with open(last_path, 'rb') as last:
            data=last.read()

        output_path=filedialog.asksaveasfilename()
        with open(output_path, 'wb') as file:
            file.write(data)
    
    if MODE=='PS4':
        if decrypted_path is None or data is None:
            print("Nothing to save")
            return
        with open(decrypted_path, 'wb') as file:
            file.write(data)
        print(f"Saved {len(data)} bytes to {decrypted_path}")

        Tk().withdraw()

        exe_path = base_dir / "ps4" / "ps4.exe"
        subprocess.run(
                [str(exe_path), str(decrypted_path)],
                cwd=exe_path.parent,
                input="\n",  # auto press Enter
                text=True,
                check=True
            )
        print("Decryption finished.")

        dst_path = exe_path.parent / "APP.BIN_out.bin_out.bin"
        with open(dst_path, 'rb') as lol:
            data=lol.read()

        output_path=filedialog.asksaveasfilename()

        with open(output_path, 'wb') as fu:
            fu.write(data)

        print('wrote ps4 save')


            
def load_data():
    

    #Amrita
    amrita_value= find_value_at_offset(data, amrita_offset, 8)
    #Gold
    gold_value=find_value_at_offset(data, gold_offset, 8)

    player_level_value=find_value_at_offset(data, player_level, 2)
    constitution_value=find_value_at_offset(data, constitution, 2)
    heart_value=find_value_at_offset(data, heart, 2)
    courage_value=find_value_at_offset(data,courage,2)
    stamina_value=find_value_at_offset(data,stamina,2)
    strenght_value=find_value_at_offset(data,strenght,2)
    skill_value=find_value_at_offset(data,skill,2)
    dexterity_value=find_value_at_offset(data,dexterity,2)
    magic_value=find_value_at_offset(data, magic,2)
    print(magic_value)



import struct

def inventory_par(offset):
    
    #first item:0xED508, len =0x90.
    item_id_1=data[offset:offset+2] # 2 bytes
    offset+= 2
    item_id_2=data[offset:offset+2]
    offset+= 2
    quantity=data[offset:offset+2]
    offset+= 2
    weapon_level=data[offset:offset+2]
    offset+= 2
    weapon_level_start=data[offset:offset+2]
    offset+= 2
    Higher_Level_Modifier=data[offset:offset+2]
    offset+= 2
    fam=data[offset:offset+4] # 4bytes
    offset+=4
    left_right_1=data[offset:offset+1]
    offset+=1
    left_right_2=data[offset:offset+1]
    offset+=1
    left_right_3=data[offset:offset+1]
    offset+=1
    left_right_4=data[offset:offset+1]
    offset+=1
    weapon_tier=data[offset:offset+1]
    offset+=1
    left_right_5=data[offset:offset+1]
    offset+=1
    left_right_6=data[offset:offset+1]
    offset+=1
    left_right_7=data[offset:offset+1]
    offset+=1
    yokai_weapon_gauge=data[offset:offset+2]
    offset+= 2
    rcmd_level=data[offset:offset+2]
    offset+= 2
    empty_1=data[offset:offset+2]
    offset+= 2
    remodel_type=data[offset:offset+1]
    offset+=1
    attempt_remaining=data[offset:offset+1]
    offset+=1
    extra_1=data[offset:offset+16]
    offset+=16
    effect_id_1=data[offset:offset+4]
    offset+=4
    effect_magnitude_1=data[offset:offset+4]
    offset+=4
    effect_footer_part1_1=data[offset:offset+2]
    offset+=2
    effect_footer_part2_1=data[offset:offset+2]
    offset+=2
    
    effect_id_2=data[offset:offset+4]
    offset+=4
    effect_magnitude_2=data[offset:offset+4]
    offset+=4
    effect_footer_part1_2=data[offset:offset+2]
    offset+=2
    effect_footer_part2_2=data[offset:offset+2]
    offset+=2

    effect_id_3=data[offset:offset+4]
    offset+=4
    effect_magnitude_3=data[offset:offset+4]
    offset+=4
    effect_footer_part1_3=data[offset:offset+2]
    offset+=2
    effect_footer_part2_3=data[offset:offset+2]
    offset+=2

    effect_id_4=data[offset:offset+4]
    offset+=4
    effect_magnitude_4=data[offset:offset+4]
    offset+=4
    effect_footer_part1_4=data[offset:offset+2]
    offset+=2
    effect_footer_part2_4=data[offset:offset+2]
    offset+=2

    effect_id_5=data[offset:offset+4]
    offset+=4
    effect_magnitude_5=data[offset:offset+4]
    offset+=4
    effect_footer_part1_5=data[offset:offset+2]
    offset+=2
    effect_footer_part2_5=data[offset:offset+2]
    offset+=2

    effect_id_6=data[offset:offset+4]
    offset+=4
    effect_magnitude_6=data[offset:offset+4]
    offset+=4
    effect_footer_part1_6=data[offset:offset+2]
    offset+=2
    effect_footer_part2_6=data[offset:offset+2]
    offset+=2

    effect_id_7=data[offset:offset+4]
    offset+=4
    effect_magnitude_7=data[offset:offset+4]
    offset+=4
    effect_footer_part1_7=data[offset:offset+2]
    offset+=2
    effect_footer_part2_7=data[offset:offset+2]
    offset+=2

    empty_2=data[offset:offset+4]
    offset+=4

    is_equiped=data[offset:offset+1]
    offset+=1

    empty_3=data[offset:offset+7]
    offset+=7

    return {
        'item_id_1': int.from_bytes(item_id_1, 'little'),
        'Refashion': int.from_bytes(item_id_2, 'little'),
        'quantity': int.from_bytes(quantity, 'little'),
        'weapon_level': int.from_bytes(weapon_level, 'little'),
        'weapon_level_start': int.from_bytes(weapon_level_start, 'little'),
        'Higher_Level_Modifier': int.from_bytes(Higher_Level_Modifier, 'little'),
        'fam': int.from_bytes(fam, 'little'),
        'left_right_1': int.from_bytes(left_right_1, 'little'),
        'left_right_2': int.from_bytes(left_right_2, 'little'),
        'left_right_3': int.from_bytes(left_right_3, 'little'),
        'left_right_4': int.from_bytes(left_right_4, 'little'),
        'weapon_tier': int.from_bytes(weapon_tier, 'little'),
        'left_right_5': int.from_bytes(left_right_5, 'little'),
        'left_right_6': int.from_bytes(left_right_6, 'little'),
        'left_right_7': int.from_bytes(left_right_7, 'little'),
        'yokai_weapon_gauge': int.from_bytes(yokai_weapon_gauge, 'little'),
        'rcmd_level': int.from_bytes(rcmd_level, 'little'),
        'empty_1': int.from_bytes(empty_1, 'little'),
        'remodel_type': int.from_bytes(remodel_type, 'little'),
        'attempt_remaining': int.from_bytes(attempt_remaining, 'little'),
        'extra_1': int.from_bytes(extra_1, 'little'),
        'effect_id_1': int.from_bytes(effect_id_1, 'little'),
        'effect_magnitude_1': int.from_bytes(effect_magnitude_1, 'little'),
        'effect_footer_part1_1': int.from_bytes(effect_footer_part1_1, 'little'),
        'effect_footer_part2_1': int.from_bytes(effect_footer_part2_1, 'little'),
        'effect_id_2': int.from_bytes(effect_id_2, 'little'),
        'effect_magnitude_2': int.from_bytes(effect_magnitude_2, 'little'),
        'effect_footer_part1_2': int.from_bytes(effect_footer_part1_2, 'little'),
        'effect_footer_part2_2': int.from_bytes(effect_footer_part2_2, 'little'),
        'effect_id_3': int.from_bytes(effect_id_3, 'little'),
        'effect_magnitude_3': int.from_bytes(effect_magnitude_3, 'little'),
        'effect_footer_part1_3': int.from_bytes(effect_footer_part1_3, 'little'),
        'effect_footer_part2_3': int.from_bytes(effect_footer_part2_3, 'little'),
        'effect_id_4': int.from_bytes(effect_id_4, 'little'),
        'effect_magnitude_4': int.from_bytes(effect_magnitude_4, 'little'),
        'effect_footer_part1_4': int.from_bytes(effect_footer_part1_4, 'little'),
        'effect_footer_part2_4': int.from_bytes(effect_footer_part2_4, 'little'),
        'effect_id_5': int.from_bytes(effect_id_5, 'little'),
        'effect_magnitude_5': int.from_bytes(effect_magnitude_5, 'little'),
        'effect_footer_part1_5': int.from_bytes(effect_footer_part1_5, 'little'),
        'effect_footer_part2_5': int.from_bytes(effect_footer_part2_5, 'little'),
        'effect_id_6': int.from_bytes(effect_id_6, 'little'),
        'effect_magnitude_6': int.from_bytes(effect_magnitude_6, 'little'),
        'effect_footer_part1_6': int.from_bytes(effect_footer_part1_6, 'little'),
        'effect_footer_part2_6': int.from_bytes(effect_footer_part2_6, 'little'),
        'effect_id_7': int.from_bytes(effect_id_7, 'little'),
        'effect_magnitude_7': int.from_bytes(effect_magnitude_7, 'little'),
        'effect_footer_part1_7': int.from_bytes(effect_footer_part1_7, 'little'),
        'effect_footer_part2_7': int.from_bytes(effect_footer_part2_7, 'little'),
        'empty_2': int.from_bytes(empty_2, 'little'),
        'is_equiped': int.from_bytes(is_equiped, 'little'),
        'empty_3': int.from_bytes(empty_3, 'little'),
        'offset': offset
    }

weapons = []

def player_weapons():
    global weapons
    start_offset = 0xED508
    
    
    for slot in range(700):
        offset = start_offset + (slot * 0x90)
        weapon = inventory_par(offset)
        weapons.append(weapon)
    return weapons


def inventory():
    for weapon in weapons:
        val = weapon['item_id_1']
        # swap endian
        weapon_id_hex = f"{((val & 0xFF) << 8) | (val >> 8):04X}"

        if weapon_id_hex in items_json:
            item_info = items_json[weapon_id_hex]
            print(f"Weapon ID: {weapon_id_hex}, Name: {item_info['name']}, Type: {item_info['type']}")




##ITems section

items=[]

def inventory_par_items(offset):
    
    #first item:0xED508, len =0x90.
    item_id_1=data[offset:offset+2] # 2 bytes
    offset+= 2
    item_id_2=data[offset:offset+2]
    offset+= 2
    quantity=data[offset:offset+2]
    offset+= 2
    weapon_level=data[offset:offset+2]
    offset+= 2
    weapon_level_start=data[offset:offset+2]
    offset+= 2
    Higher_Level_Modifier=data[offset:offset+2]
    offset+= 2
    fam=data[offset:offset+4] # 4bytes
    offset+=4
    left_right_1=data[offset:offset+1]
    offset+=1
    left_right_2=data[offset:offset+1]
    offset+=1
    left_right_3=data[offset:offset+1]
    offset+=1
    left_right_4=data[offset:offset+1]
    offset+=1
    weapon_tier=data[offset:offset+1]
    offset+=1
    left_right_5=data[offset:offset+1]
    offset+=1
    left_right_6=data[offset:offset+1]
    offset+=1
    left_right_7=data[offset:offset+1]
    offset+=1
    yokai_weapon_gauge=data[offset:offset+2]
    offset+= 2
    rcmd_level=data[offset:offset+2]
    offset+= 2
    empty_1=data[offset:offset+2]
    offset+= 2
    remodel_type=data[offset:offset+1]
    offset+=1
    attempt_remaining=data[offset:offset+1]
    offset+=1
    extra_1=data[offset:offset+16]
    offset+=16
    effect_id_1=data[offset:offset+4]
    offset+=4
    effect_magnitude_1=data[offset:offset+4]
    offset+=4
    effect_footer_part1_1=data[offset:offset+2]
    offset+=2
    effect_footer_part2_1=data[offset:offset+2]
    offset+=2
    
    effect_id_2=data[offset:offset+4]
    offset+=4
    effect_magnitude_2=data[offset:offset+4]
    offset+=4
    effect_footer_part1_2=data[offset:offset+2]
    offset+=2
    effect_footer_part2_2=data[offset:offset+2]
    offset+=2

    effect_id_3=data[offset:offset+4]
    offset+=4
    effect_magnitude_3=data[offset:offset+4]
    offset+=4
    effect_footer_part1_3=data[offset:offset+2]
    offset+=2
    effect_footer_part2_3=data[offset:offset+2]
    offset+=2

    effect_id_4=data[offset:offset+4]
    offset+=4
    effect_magnitude_4=data[offset:offset+4]
    offset+=4
    effect_footer_part1_4=data[offset:offset+2]
    offset+=2
    effect_footer_part2_4=data[offset:offset+2]
    offset+=2

    effect_id_5=data[offset:offset+4]
    offset+=4
    effect_magnitude_5=data[offset:offset+4]
    offset+=4
    effect_footer_part1_5=data[offset:offset+2]
    offset+=2
    effect_footer_part2_5=data[offset:offset+2]
    offset+=2

    effect_id_6=data[offset:offset+4]
    offset+=4
    effect_magnitude_6=data[offset:offset+4]
    offset+=4
    effect_footer_part1_6=data[offset:offset+2]
    offset+=2
    effect_footer_part2_6=data[offset:offset+2]
    offset+=2

    effect_id_7=data[offset:offset+4]
    offset+=4
    effect_magnitude_7=data[offset:offset+4]
    offset+=4
    effect_footer_part1_7=data[offset:offset+2]
    offset+=2
    effect_footer_part2_7=data[offset:offset+2]
    offset+=2

    empty_2=data[offset:offset+4]
    offset+=4

    return {
        'item_id_1': int.from_bytes(item_id_1, 'little'),
        'Refashion': int.from_bytes(item_id_2, 'little'),
        'quantity': int.from_bytes(quantity, 'little'),
        'offset': offset
    }


def player_items():
    global items
    start_offset = 0x105EC8
    
    
    for slot in range(900):
        offset = start_offset + (slot * 0x88)
        item= inventory_par_items(offset)
        items.append(item)
    return items


def inventory_items():
    for item in items:
        val = item['item_id_1']
        quantity = item['quantity']
        # swap endian
        item_id_hex = f"{((val & 0xFF) << 8) | (val >> 8):04X}"

        if item_id_hex in items_json:
            item_info = items_json[item_id_hex]
            print(f"item ID: {item_id_hex}, Name: {item_info['name']}, Type: {item_info['type']}, quantity: {quantity}")

# # Scrolls

def inventory_par_scroll(offset):
    
    #first item:0xED508, len =0x90.
    item_id_1=data[offset:offset+2] # 2 bytes
    offset+= 2
    item_id_2=data[offset:offset+2]
    offset+= 2
    item_id_3=data[offset:offset+2]
    offset+= 2
    item_level_1=data[offset:offset+2]
    offset+= 2
    item_level_2=data[offset:offset+2]
    offset+= 2
    higher_level_mod=data[offset:offset+2]
    offset+= 2
    unk_1=data[offset:offset+4]
    offset+= 4
    extra_1=data[offset:offset+2]
    offset+= 2
    is_it_locked=data[offset:offset+1]
    offset+= 1
    extra_2=data[offset:offset+1]
    offset+= 1
    tier=data[offset:offset+1]
    offset+= 1
    unk_2=data[offset:offset+1]
    offset+= 1
    unk_3=data[offset:offset+9]
    offset+= 9
    attempts_remaining=data[offset:offset+1]
    offset+= 1
    unk_4=data[offset:offset+16]
    offset+= 16

    effect_id_1=data[offset:offset+4]
    offset+=4
    effect_magnitude_1=data[offset:offset+4]
    offset+=4
    effect_footer_part1_1=data[offset:offset+2]
    offset+=2
    effect_footer_part2_1=data[offset:offset+2]
    offset+=2
    
    effect_id_2=data[offset:offset+4]
    offset+=4
    effect_magnitude_2=data[offset:offset+4]
    offset+=4
    effect_footer_part1_2=data[offset:offset+2]
    offset+=2
    effect_footer_part2_2=data[offset:offset+2]
    offset+=2

    effect_id_3=data[offset:offset+4]
    offset+=4
    effect_magnitude_3=data[offset:offset+4]
    offset+=4
    effect_footer_part1_3=data[offset:offset+2]
    offset+=2
    effect_footer_part2_3=data[offset:offset+2]
    offset+=2

    effect_id_4=data[offset:offset+4]
    offset+=4
    effect_magnitude_4=data[offset:offset+4]
    offset+=4
    effect_footer_part1_4=data[offset:offset+2]
    offset+=2
    effect_footer_part2_4=data[offset:offset+2]
    offset+=2

    effect_id_5=data[offset:offset+4]
    offset+=4
    effect_magnitude_5=data[offset:offset+4]
    offset+=4
    effect_footer_part1_5=data[offset:offset+2]
    offset+=2
    effect_footer_part2_5=data[offset:offset+2]
    offset+=2

    effect_id_6=data[offset:offset+4]
    offset+=4
    effect_magnitude_6=data[offset:offset+4]
    offset+=4
    effect_footer_part1_6=data[offset:offset+2]
    offset+=2
    effect_footer_part2_6=data[offset:offset+2]
    offset+=2

    effect_id_7=data[offset:offset+4]
    offset+=4
    effect_magnitude_7=data[offset:offset+4]
    offset+=4
    effect_footer_part1_7=data[offset:offset+2]
    offset+=2
    effect_footer_part2_7=data[offset:offset+2]
    offset+=2
    extra_3=data[offset:offset+4]
    offset+=4
    is_it_equiped=data[offset:offset+1]
    offset+=1
    extra_4=data[offset:offset+7]
    offset+=7

    return {
        'item_id_1': int.from_bytes(item_id_1, 'little'),
        'item_id_2': int.from_bytes(item_id_2, 'little'),
        'item_id_3': int.from_bytes(item_id_3, 'little'),
        'item_level_1': int.from_bytes(item_level_1, 'little'),
        'item_level_2': int.from_bytes(item_level_2, 'little'),
        'higher_level_mod': int.from_bytes(higher_level_mod, 'little'),
        'unk_1': int.from_bytes(unk_1, 'little'),
        'extra_1': int.from_bytes(extra_1, 'little'),
        'is_it_locked': int.from_bytes(is_it_locked, 'little'),
        'extra_2': int.from_bytes(extra_2, 'little'),
        'tier': int.from_bytes(tier, 'little'),
        'unk_2': int.from_bytes(unk_2, 'little'),
        'unk_3': int.from_bytes(unk_3, 'little'),
        'attempts_remaining': int.from_bytes(attempts_remaining, 'little'),
        'unk_4': int.from_bytes(unk_4, 'little') ,
        'effect_id_1': int.from_bytes(effect_id_1, 'little'),
        'effect_magnitude_1': int.from_bytes(effect_magnitude_1, 'little'),
        'effect_footer_part1_1': int.from_bytes(effect_footer_part1_1, 'little'),
        'effect_footer_part2_1': int.from_bytes(effect_footer_part2_1, 'little'),
        'effect_id_2': int.from_bytes(effect_id_2, 'little'),
        'effect_magnitude_2': int.from_bytes(effect_magnitude_2, 'little'),
        'effect_footer_part1_2': int.from_bytes(effect_footer_part1_2, 'little'),
        'effect_footer_part2_2': int.from_bytes(effect_footer_part2_2, 'little'),
        'effect_id_3': int.from_bytes(effect_id_3, 'little'),
        'effect_magnitude_3': int.from_bytes(effect_magnitude_3, 'little'),
        'effect_footer_part1_3': int.from_bytes(effect_footer_part1_3, 'little'),
        'effect_footer_part2_3': int.from_bytes(effect_footer_part2_3, 'little'),
        'effect_id_4': int.from_bytes(effect_id_4, 'little'),
        'effect_magnitude_4': int.from_bytes(effect_magnitude_4, 'little'),
        'effect_footer_part1_4': int.from_bytes(effect_footer_part1_4, 'little'),
        'effect_footer_part2_4': int.from_bytes(effect_footer_part2_4, 'little'),
        'effect_id_5': int.from_bytes(effect_id_5, 'little'),
        'effect_magnitude_5': int.from_bytes(effect_magnitude_5, 'little'),
        'effect_footer_part1_5': int.from_bytes(effect_footer_part1_5, 'little'),
        'effect_footer_part2_5': int.from_bytes(effect_footer_part2_5, 'little'),
        'effect_id_6': int.from_bytes(effect_id_6, 'little'),
        'effect_magnitude_6': int.from_bytes(effect_magnitude_6, 'little'),
        'effect_footer_part1_6': int.from_bytes(effect_footer_part1_6, 'little'),
        'effect_footer_part2_6': int.from_bytes(effect_footer_part2_6, 'little'),
        'effect_id_7': int.from_bytes(effect_id_7, 'little'),
        'effect_magnitude_7': int.from_bytes(effect_magnitude_7, 'little'),
        'effect_footer_part1_7': int.from_bytes(effect_footer_part1_7, 'little'),
        'effect_footer_part2_7': int.from_bytes(effect_footer_part2_7, 'little'),
        'extra_3': int.from_bytes(extra_3, 'little'),
        'is_it_equiped': int.from_bytes(is_it_equiped, 'little'),
        'extra_4': int.from_bytes(extra_4, 'little'),
        'offset': offset
    }

scrolls=[]
def player_scroll():
    global items
    start_offset = 0x294080
    
    
    for slot in range(248):
        offset = start_offset + (slot * 0x88)
        scroll= inventory_par_scroll(offset)
        scrolls.append(scroll)
    return scrolls


def inventory_scroll():
    for item in scrolls:
        val = item['item_id_1']
        tier= item['tier']
        # swap endian
        item_id_hex = f"{((val & 0xFF) << 8) | (val >> 8):04X}"

        if item_id_hex in items_json:
            item_info = items_json[item_id_hex]
            print(f"item ID: {item_id_hex}, Name: {item_info['name']}, Type: {item_info['type']},tier: {tier}")



open_file()
load_data()
player_weapons()
inventory()
player_items()
inventory_items()
player_scroll()
inventory_scroll()
#save_file()