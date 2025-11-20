import subprocess
from tkinter import Tk, filedialog, ttk, messagebox
import os
from pathlib import Path
import shutil
import json
import tkinter as tk

# ==================== CONSTANTS ====================
# Currency & Stats
AMRITA_OFFSET = 0x7B8D0
GOLD_OFFSET = 0x7B8D8
PLAYER_LEVEL = 0x1C4904
CONSTITUTION = 0x1C490C
HEART = 0x1C4910
COURAGE = 0x1C4928
STAMINA = 0x1C4914
STRENGTH = 0x1C4918
SKILL = 0x1C491C
DEXTERITY = 0x1C4920
MAGIC = 0x1C4924

# Proficiency
NINJITSU = 0x1C4B58
ONMYO = 0x1C4B64
SWORD = 0x1C4A8C
DUAL_SWORD = 0x1C4A98
AXE = 0x1C4AB0
KUSARIGAMA = 0x1C4ABC
ODACHI = 0x1C4AC8
TONFA = 0x1C4AD4
HATCHET = 0x1C4AE0

# Inventory offsets
WEAPON_START = 0xED508
WEAPON_SIZE = 0x90
WEAPON_SLOTS = 700

ITEM_START = 0x105EC8
ITEM_SIZE = 0x88
ITEM_SLOTS = 900

SCROLL_START = 0x294080
SCROLL_SIZE = 0x88
SCROLL_SLOTS = 248

# ==================== GLOBALS ====================
data = None
MODE = None
decrypted_path = None
weapons = []
items = []
scrolls = []
selected_weapon = None
selected_weapon_index = None
selected_item = None
selected_item_index = None
selected_scroll = None
selected_scroll_index = None

base_dir = Path(__file__).parent

# ==================== JSON LOADING ====================
def load_json(file_name):
    file_path = base_dir / file_name
    with open(file_path, "r") as file:
        return json.load(file)

items_json = load_json("items.json")
effects_json = load_json("effects.json")
effect_dropdown_list = [
    f"{entry['id']} - {entry['Effect']}"
    for entry in effects_json
]

# ==================== HELPERS ====================
def find_value_at_offset(section_data, offset, byte_size):
    try:
        value_bytes = section_data[offset:offset+byte_size]
        if len(value_bytes) == byte_size:
            return int.from_bytes(value_bytes, 'little')
    except IndexError:
        pass
    return None

def write_le(value, length):
    if isinstance(value, int):
        return value.to_bytes(length, 'little')
    elif isinstance(value, (bytes, bytearray)):
        if len(value) != length:
            raise ValueError(f"Expected {length} bytes, got {len(value)}")
        return value
    else:
        raise TypeError(f"Cannot convert type {type(value)} to bytes")

def swap_endian_hex(val):
    """Convert item_id to hex string with endian swap"""
    return f"{((val & 0xFF) << 8) | (val >> 8):04X}"

# ==================== FILE OPERATIONS ====================
def open_file():
    global data, MODE, decrypted_path

    file_path = filedialog.askopenfilename(
        title="Select Save File",
        filetypes=[("Save Files", "*.BIN"), ("All Files", "*.*")]
    )
    if not file_path:
        return False
    
    file_name = os.path.basename(file_path)

    # PC Save
    if file_name == 'SAVEDATA.BIN':
        MODE = 'PC'
        exe_path = base_dir / "pc" / "pc.exe"
        
        proc = subprocess.run(
            [str(exe_path), file_path],
            cwd=exe_path.parent,
            input="\n",
            text=True,
            capture_output=True
        )
        
        decrypted_path = exe_path.parent / "decr_SAVEDATA.BIN"
        with open(decrypted_path, 'rb') as f:
            data = bytearray(f.read())
        
        # Disable integrity checks
        data[0x7B882+0x158] = 0
        data[0x7B884+0x158] = 0
        data[0x7B7E4+0x158] = 0
        data[0xECF4A+0x158] = 0
        
        return True

    # PS4 Save
    if file_name == 'APP.BIN':
        MODE = 'PS4'
        exe_path = base_dir / "ps4" / "ps4.exe"
        dst_path = exe_path.parent / "APP.BIN"

        shutil.copy2(file_path, dst_path)

        with open(dst_path, 'rb') as f:
            magic_bytes = f.read(4)

        if magic_bytes != b'\x00\x00\x00\x00':
            subprocess.run(
                [str(exe_path), str(dst_path)],
                cwd=exe_path.parent,
                input="\n",
                text=True,
                check=True
            )
        
        decrypted_path = exe_path.parent / "APP.BIN_out.bin"
        with open(decrypted_path, 'rb') as f:
            data = bytearray(f.read())
            # Add 0x148 zero bytes at the start
        padding = b'\x00' * 0x148
        data = bytearray(padding) + data
        data[0x7B882+0x158] = 0
        data[0x7B884+0x158] = 0
        data[0x7B7E4+0x158] = 0
        data[0xECF4A+0x158] = 0
        
        return True

    messagebox.showerror("Error", "Unknown file format. Please select SAVEDATA.BIN (PC) or APP.BIN (PS4)")
    return False

def save_file():
    global data, decrypted_path

    if data is None or decrypted_path is None:
        messagebox.showwarning("Warning", "No data to save. Load a file first.")
        return

    # Write current changes back to data
    write_weapons_to_data()
    write_items_to_data()
    write_scrolls_to_data()

    if MODE == 'PC':
        with open(decrypted_path, 'wb') as file:
            file.write(data)
        
        exe_path = base_dir / "pc" / "pc.exe"
        subprocess.run(
            [str(exe_path), decrypted_path],
            cwd=exe_path.parent,
            input="\n",
            text=True,
            capture_output=True
        )

        last_path = base_dir / "pc" / "decr_decr_SAVEDATA.BIN"
        with open(last_path, 'rb') as last:
            final_data = last.read()

        output_path = filedialog.asksaveasfilename(
            defaultextension=".BIN",
            filetypes=[("Save Files", "*.BIN"), ("All Files", "*.*")]
        )
        if output_path:
            with open(output_path, 'wb') as file:
                file.write(final_data)
            messagebox.showinfo("Success", f"Saved to {output_path}")

    elif MODE == 'PS4':
        data=data[0x148:]
        with open(decrypted_path, 'wb') as file:
            
            file.write(data)

        exe_path = base_dir / "ps4" / "ps4.exe"
        subprocess.run(
            [str(exe_path), str(decrypted_path)],
            cwd=exe_path.parent,
            input="\n",
            text=True,
            check=True
        )

        dst_path = exe_path.parent / "APP.BIN_out.bin_out.bin"
        with open(dst_path, 'rb') as lol:
            final_data = lol.read()

        output_path = filedialog.asksaveasfilename(
            defaultextension=".BIN",
            filetypes=[("Save Files", "*.BIN"), ("All Files", "*.*")]
        )
        if output_path:
            with open(output_path, 'wb') as fu:
                fu.write(final_data)
            messagebox.showinfo("Success", f"Saved to {output_path}")

# ==================== ORIGINAL PARSING FUNCTIONS ====================

def inventory_par(offset):
    """Original weapon parsing function"""
    item_id_1=data[offset:offset+2]
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
    fam=data[offset:offset+4]
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

def inventory_par_items(offset):
    """Original items parsing function"""
    item_id_1=data[offset:offset+2]
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
    fam=data[offset:offset+4]
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

def inventory_par_scroll(offset):
    """Original scroll parsing function"""
    item_id_1=data[offset:offset+2]
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
        'offset': offset
    }

def player_weapons():
    global weapons
    weapons = []
    for slot in range(WEAPON_SLOTS):
        offset = WEAPON_START + (slot * WEAPON_SIZE)
        weapon = inventory_par(offset)
        weapon['slot'] = slot
        weapons.append(weapon)

def player_items():
    global items
    items = []
    for slot in range(ITEM_SLOTS):
        offset = ITEM_START + (slot * ITEM_SIZE)
        item = inventory_par_items(offset)
        item['slot'] = slot
        items.append(item)

def player_scroll():
    global scrolls
    scrolls = []
    for slot in range(SCROLL_SLOTS):
        offset = SCROLL_START + (slot * SCROLL_SIZE)
        if offset + SCROLL_SIZE > len(data):
            break
        
        # Check if slot has data (item_id_1 is not 0)
        item_id_check = int.from_bytes(data[offset:offset+2], 'little')
        if item_id_check == 0:
            continue  # Skip empty slots
            
        scroll = inventory_par_scroll(offset)
        scroll['slot'] = slot
        scrolls.append(scroll)

def write_weapons_to_data():
    """Write weapons back to data"""
    for weapon in weapons:
        slot = weapon['slot']
        
        offset = WEAPON_START + (slot * WEAPON_SIZE)
        
        data[offset:offset+2] = write_le(weapon['item_id_1'], 2)
        offset += 2
        data[offset:offset+2] = write_le(weapon['Refashion'], 2)
        offset += 2
        data[offset:offset+2] = write_le(weapon['quantity'], 2)
        offset += 2
        data[offset:offset+2] = write_le(weapon['weapon_level'], 2)
        offset += 2
        data[offset:offset+2] = write_le(weapon['weapon_level_start'], 2)
        offset += 2
        data[offset:offset+2] = write_le(weapon['Higher_Level_Modifier'], 2)
        offset += 2
        data[offset:offset+4] = write_le(weapon['fam'], 4)
        offset += 4
        data[offset:offset+1] = write_le(weapon['left_right_1'], 1)
        offset += 1
        data[offset:offset+1] = write_le(weapon['left_right_2'], 1)
        offset += 1
        data[offset:offset+1] = write_le(weapon['left_right_3'], 1)
        offset += 1
        data[offset:offset+1] = write_le(weapon['left_right_4'], 1)
        offset += 1
        data[offset:offset+1] = write_le(weapon['weapon_tier'], 1)
        offset += 1
        data[offset:offset+1] = write_le(weapon['left_right_5'], 1)
        offset += 1
        data[offset:offset+1] = write_le(weapon['left_right_6'], 1)
        offset += 1
        data[offset:offset+1] = write_le(weapon['left_right_7'], 1)
        offset += 1
        data[offset:offset+2] = write_le(weapon['yokai_weapon_gauge'], 2)
        offset += 2
        data[offset:offset+2] = write_le(weapon['rcmd_level'], 2)
        offset += 2
        data[offset:offset+2] = write_le(weapon['empty_1'], 2)
        offset += 2
        data[offset:offset+1] = write_le(weapon['remodel_type'], 1)
        offset += 1
        data[offset:offset+1] = write_le(weapon['attempt_remaining'], 1)
        offset += 1
        data[offset:offset+16] = write_le(weapon['extra_1'], 16)
        offset += 16
        
        # Effects
        for i in range(1, 8):
            data[offset:offset+4] = write_le(weapon[f'effect_id_{i}'], 4)
            offset += 4
            data[offset:offset+4] = write_le(weapon[f'effect_magnitude_{i}'], 4)
            offset += 4
            data[offset:offset+2] = write_le(weapon[f'effect_footer_part1_{i}'], 2)
            offset += 2
            data[offset:offset+2] = write_le(weapon[f'effect_footer_part2_{i}'], 2)
            offset += 2

def write_items_to_data():
    """Write items back to data"""
    for item in items:
        slot = item['slot']
        offset = ITEM_START + (slot * ITEM_SIZE)
        
        data[offset:offset+2] = write_le(item['item_id_1'], 2)
        offset += 2
        data[offset:offset+2] = write_le(item['Refashion'], 2)
        offset += 2
        data[offset:offset+2] = write_le(item['quantity'], 2)

def write_scrolls_to_data():
    """Write scrolls back to data"""
    for scroll in scrolls:
        slot = scroll['slot']
        offset = SCROLL_START + (slot * SCROLL_SIZE)
        
        # Don't write beyond the original file size
        if offset + SCROLL_SIZE > len(data):
            print(f"Skipping scroll slot {slot} write: exceeds data size")
            continue
        
        # Write directly to data (like write_weapons_to_data does)
        data[offset:offset+2] = write_le(scroll['item_id_1'], 2); offset += 2
        data[offset:offset+2] = write_le(scroll['item_id_2'], 2); offset += 2
        data[offset:offset+2] = write_le(scroll['item_id_3'], 2); offset += 2
        data[offset:offset+2] = write_le(scroll['item_level_1'], 2); offset += 2
        data[offset:offset+2] = write_le(scroll['item_level_2'], 2); offset += 2
        data[offset:offset+2] = write_le(scroll['higher_level_mod'], 2); offset += 2
        data[offset:offset+4] = write_le(scroll['unk_1'], 4); offset += 4
        data[offset:offset+2] = write_le(scroll['extra_1'], 2); offset += 2
        data[offset:offset+1] = write_le(scroll['is_it_locked'], 1); offset += 1
        data[offset:offset+1] = write_le(scroll['extra_2'], 1); offset += 1
        data[offset:offset+1] = write_le(scroll['tier'], 1); offset += 1
        data[offset:offset+1] = write_le(scroll['unk_2'], 1); offset += 1
        data[offset:offset+9] = write_le(scroll['unk_3'], 9); offset += 9
        data[offset:offset+1] = write_le(scroll['attempts_remaining'], 1); offset += 1
        data[offset:offset+16] = write_le(scroll['unk_4'], 16); offset += 16

        # Effects
        for i in range(1, 8):
            data[offset:offset+4] = write_le(scroll[f'effect_id_{i}'], 4); offset += 4
            data[offset:offset+4] = write_le(scroll[f'effect_magnitude_{i}'], 4); offset += 4
            data[offset:offset+2] = write_le(scroll[f'effect_footer_part1_{i}'], 2); offset += 2
            data[offset:offset+2] = write_le(scroll[f'effect_footer_part2_{i}'], 2); offset += 2
        
        data[offset:offset+4] = write_le(scroll['extra_3'], 4)



class SearchableCombobox(ttk.Frame):
    def __init__(self, master=None, values=None, width=40, **kwargs):
        super().__init__(master, **kwargs)
        
        self.full_values = values if values else []
        self.filtered_values = self.full_values.copy()
        
        # Entry field
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(side="left", fill="x", expand=True)
        
        # Dropdown button
        self.btn = ttk.Button(self, text="▼", width=2, command=self.toggle_dropdown)
        self.btn.pack(side="right")
        
        # Listbox for dropdown (hidden by default)
        self.listbox_frame = tk.Toplevel(self)
        self.listbox_frame.withdraw()
        self.listbox_frame.overrideredirect(True)
        
        self.listbox = tk.Listbox(self.listbox_frame, height=10, width=width)
        self.listbox.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # Bindings
        self.var.trace_add("write", self._on_type)
        self.entry.bind("<Down>", self._on_arrow_down)
        self.entry.bind("<Up>", self._on_arrow_up)
        self.entry.bind("<Return>", self._on_return)
        self.entry.bind("<Escape>", self._on_escape)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Return>", self._on_return)
        self.listbox.bind("<Escape>", self._on_escape)
        self.listbox.bind("<Double-Button-1>", self._on_select)
        
        self.dropdown_visible = False
        
    def _on_type(self, *args):
        """Filter values as user types"""
        typed = self.var.get().lower()
        
        if typed == "":
            self.filtered_values = self.full_values.copy()
        else:
            self.filtered_values = [v for v in self.full_values if typed in v.lower()]
        
        self._update_listbox()
        
        # Show dropdown automatically when typing
        if not self.dropdown_visible and self.filtered_values:
            self.show_dropdown()
    
    def _update_listbox(self):
        """Update listbox with filtered values"""
        self.listbox.delete(0, tk.END)
        for value in self.filtered_values:
            self.listbox.insert(tk.END, value)
    
    def show_dropdown(self):
        """Show the dropdown listbox"""
        if not self.filtered_values:
            return
            
        self.dropdown_visible = True
        
        # Position the dropdown below the entry
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        width = self.entry.winfo_width() + self.btn.winfo_width()
        
        self.listbox_frame.geometry(f"{width}x200+{x}+{y}")
        self.listbox_frame.deiconify()
        self.listbox_frame.lift()
        
    def hide_dropdown(self):
        """Hide the dropdown listbox"""
        self.dropdown_visible = False
        self.listbox_frame.withdraw()
    
    def toggle_dropdown(self):
        """Toggle dropdown visibility"""
        if self.dropdown_visible:
            self.hide_dropdown()
        else:
            self.filtered_values = self.full_values.copy()
            self._update_listbox()
            self.show_dropdown()
            self.entry.focus_set()
    
    def _on_arrow_down(self, event):
        """Move selection down in listbox"""
        if not self.dropdown_visible:
            self.show_dropdown()
        else:
            current = self.listbox.curselection()
            if not current:
                self.listbox.selection_set(0)
            elif current[0] < self.listbox.size() - 1:
                self.listbox.selection_clear(current)
                self.listbox.selection_set(current[0] + 1)
                self.listbox.see(current[0] + 1)
        return "break"
    
    def _on_arrow_up(self, event):
        """Move selection up in listbox"""
        if self.dropdown_visible:
            current = self.listbox.curselection()
            if current and current[0] > 0:
                self.listbox.selection_clear(current)
                self.listbox.selection_set(current[0] - 1)
                self.listbox.see(current[0] - 1)
        return "break"
    
    def _on_return(self, event):
        """Select current item and close dropdown"""
        if self.dropdown_visible:
            current = self.listbox.curselection()
            if current:
                self.var.set(self.listbox.get(current[0]))
            self.hide_dropdown()
        return "break"
    
    def _on_escape(self, event):
        """Close dropdown without selecting"""
        self.hide_dropdown()
        return "break"
    
    def _on_select(self, event):
        """Handle selection from listbox"""
        current = self.listbox.curselection()
        if current:
            self.var.set(self.listbox.get(current[0]))
            self.hide_dropdown()
    
    def _on_focus_out(self, event):
        """Hide dropdown when focus is lost"""
        # Delay to allow click on listbox
        self.after(200, lambda: self.hide_dropdown() if not self.listbox.focus_get() else None)
    
    def get(self):
        """Get current value"""
        return self.var.get()
    
    def set(self, value):
        """Set current value"""
        self.var.set(value)
    
    def configure(self, **kwargs):
        """Configure the entry widget"""
        if 'values' in kwargs:
            self.full_values = list(kwargs['values'])
            self.filtered_values = self.full_values.copy()
            del kwargs['values']
        if kwargs:
            self.entry.configure(**kwargs)
    
    def __setitem__(self, key, value):
        """Allow dict-style configuration"""
        if key == 'values':
            self.full_values = list(value)
            self.filtered_values = self.full_values.copy()
    
    def __getitem__(self, key):
        """Allow dict-style access"""
        if key == 'values':
            return self.full_values
        return None
# ==================== GUI ====================
class Nioh2Editor:
    def __init__(self, root):
        self.root = root
        self.root.title("Nioh 2 Save Editor")
        self.root.geometry("1200x700")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Menu
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Save File", command=self.load_file)
        file_menu.add_command(label="Save File", command=save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        
        # Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_weapons_tab()
        self.create_weapon_editor_tab()
        self.create_items_tab()
        self.create_item_editor_tab()
        self.create_scrolls_tab()
        self.create_scroll_editor_tab()
        self.create_stats_tab()
        
        self.file_loaded = False
    
    def load_file(self):
        if open_file():
            player_weapons()
            player_items()
            player_scroll()
            self.populate_weapons()
            self.populate_items()
            self.populate_scrolls()
            self.update_stats_display()
            self.file_loaded = True
            messagebox.showinfo("Success", f"Loaded {MODE} save file\n{len([w for w in weapons if w['item_id_1'] != 0])} weapons\n{len([i for i in items if i['item_id_1'] != 0])} items\n{len([s for s in scrolls if s['item_id_1'] != 0])} scrolls")
    
    
    # ==================== WEAPONS TAB ====================
    def create_weapons_tab(self):
        self.tab_weapons = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_weapons, text="Weapons")
        
        # Filter
        filter_frame = ttk.Frame(self.tab_weapons)
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side="left", padx=5)
        self.weapon_filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.weapon_filter_var, width=30)
        filter_entry.pack(side="left", padx=5)
        filter_entry.bind('<KeyRelease>', lambda e: self.populate_weapons())
        
        ttk.Button(filter_frame, text="Clear", command=lambda: [self.weapon_filter_var.set(''), self.populate_weapons()]).pack(side="left", padx=5)
        
        # Tree
        columns = ("slot", "weapon_id", "name", "type", "level", "tier", "fam")
        self.weapon_tree = ttk.Treeview(self.tab_weapons, columns=columns, show="headings", height=25)
        
        vsb = ttk.Scrollbar(self.tab_weapons, orient="vertical", command=self.weapon_tree.yview)
        self.weapon_tree.configure(yscrollcommand=vsb.set)
        
        self.weapon_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        for col in columns:
            self.weapon_tree.heading(col, text=col.capitalize())
        
        self.weapon_tree.column("slot", width=50)
        self.weapon_tree.column("weapon_id", width=80)
        self.weapon_tree.column("name", width=250)
        self.weapon_tree.column("type", width=120)
        self.weapon_tree.column("level", width=60)
        self.weapon_tree.column("tier", width=50)
        self.weapon_tree.column("fam", width=80)
        
        # Buttons
        btn_frame = ttk.Frame(self.tab_weapons)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Modify Selected", command=self.modify_weapon).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Weapon", command=self.delete_weapon).pack(side="left", padx=5)
    
    def populate_weapons(self):
        self.weapon_tree.delete(*self.weapon_tree.get_children())
        filter_text = self.weapon_filter_var.get().lower()
        
        for weapon in weapons:
            if weapon['item_id_1'] == 0:
                continue
            
            wid = weapon['item_id_1']
            weapon_id_hex = swap_endian_hex(wid)
            
            if weapon_id_hex in items_json:
                name = items_json[weapon_id_hex]["name"]
                type_ = items_json[weapon_id_hex]["type"]
            else:
                name, type_ = "Unknown", "?"
            
            if filter_text and filter_text not in name.lower() and filter_text not in type_.lower():
                continue
            
            self.weapon_tree.insert("", "end", iid=weapon['slot'], values=(
                weapon['slot'],
                weapon_id_hex,
                name,
                type_,
                weapon['weapon_level'],
                weapon['weapon_tier'],
                weapon['fam']
            ))
    
    def modify_weapon(self):
        global selected_weapon, selected_weapon_index
        sel = self.weapon_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a weapon first.")
            return
        
        idx = int(sel[0])
        selected_weapon_index = idx
        selected_weapon = weapons[idx]
        
        self.load_weapon_editor()
        self.notebook.select(self.tab_weapon_editor)
    
    def delete_weapon(self):
        sel = self.weapon_tree.selection()
        if not sel:
            return
        
        idx = int(sel[0])
        if messagebox.askyesno("Confirm", "Delete this weapon?"):
            weapons[idx]['item_id_1'] = 0
            self.populate_weapons()
    
    # ==================== WEAPON EDITOR TAB ====================
    def create_weapon_editor_tab(self):
        self.tab_weapon_editor = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_weapon_editor, text="Weapon Editor")
        
        canvas = tk.Canvas(self.tab_weapon_editor)
        scrollbar = ttk.Scrollbar(self.tab_weapon_editor, orient="vertical", command=canvas.yview)
        editor_frame = ttk.Frame(canvas)
        
        editor_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Properties
        self.weapon_entries = {}
        props_frame = ttk.LabelFrame(editor_frame, text="Weapon Properties", padding=10)
        props_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        props = [
    ("item_id_1", "Item ID"),
    ("Refashion", "Refashion"),
    ("quantity", "Quantity"),
    ("weapon_level", "Level"),
    ("weapon_level_start", "Level Start"),
    ("Higher_Level_Modifier", "Higher Level Modifier"),
    ("fam", "Familiarity"),
    ("left_right_1", "Left/Right 1"),
    ("left_right_2", "Left/Right 2"),
    ("left_right_3", "Left/Right 3"),
    ("left_right_4", "Left/Right 4"),
    ("weapon_tier", "Tier"),
    ("left_right_5", "Left/Right 5"),
    ("left_right_6", "Left/Right 6"),
    ("left_right_7", "Left/Right 7"),
    ("yokai_weapon_gauge", "Yokai Weapon Gauge"),
    ("rcmd_level", "Recommended Level"),
    ("empty_1", "Empty 1"),
    ("remodel_type", "Remodel Type"),
    ("attempt_remaining", "Attempts Remaining"),
    ("extra_1", "Extra 1"),
    ("effect_footer_part1_1", "Effect Footer Part1 1"),
    ("effect_footer_part2_1", "Effect Footer Part2 1"),

    ("effect_footer_part1_2", "Effect Footer Part1 2"),
    ("effect_footer_part2_2", "Effect Footer Part2 2"),

    ("effect_footer_part1_3", "Effect Footer Part1 3"),
    ("effect_footer_part2_3", "Effect Footer Part2 3"),

    ("effect_footer_part1_4", "Effect Footer Part1 4"),
    ("effect_footer_part2_4", "Effect Footer Part2 4"),

    ("effect_footer_part1_5", "Effect Footer Part1 5"),
    ("effect_footer_part2_5", "Effect Footer Part2 5"),

    ("effect_footer_part1_6", "Effect Footer Part1 6"),
    ("effect_footer_part2_6", "Effect Footer Part2 6"),

    ("effect_footer_part1_7", "Effect Footer Part1 7"),
    ("effect_footer_part2_7", "Effect Footer Part2 7"),
    ("empty_2", "Empty 2"),
    ("is_equiped", "Is Equipped"),
    ("empty_3", "Empty 3"),
    ("offset", "Offset")
]
        
        for i, (key, label) in enumerate(props):
            ttk.Label(props_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            e = ttk.Entry(props_frame, width=20)
            e.grid(row=i, column=1, sticky="w", padx=5, pady=3)
            self.weapon_entries[key] = e
        
        # Effects
        effects_frame = ttk.LabelFrame(editor_frame, text="Effects", padding=10)
        effects_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.weapon_effect_combos = []
        self.weapon_effect_mags = []
        
        for i in range(7):
            ttk.Label(effects_frame, text=f"Effect {i+1}:").grid(row=i, column=0, sticky="w", padx=5, pady=3)
            combo = SearchableCombobox(
                effects_frame,
                width=40,
                values=effect_dropdown_list
            )
            combo.grid(row=i, column=1, sticky="w", padx=5, pady=3)
            self.weapon_effect_combos.append(combo)
            
            ttk.Label(effects_frame, text="Mag:").grid(row=i, column=2, sticky="w", padx=5, pady=3)
            mag = ttk.Entry(effects_frame, width=10)
            mag.grid(row=i, column=3, sticky="w", padx=5, pady=3)
            self.weapon_effect_mags.append(mag)
        
        # Buttons
        btn_frame = ttk.Frame(editor_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Apply Changes", command=self.apply_weapon_changes).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Back", command=lambda: self.notebook.select(self.tab_weapons)).pack(side="left", padx=5)
    
    def load_weapon_editor(self):
        w = selected_weapon
        for key, entry in self.weapon_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, w[key])
        
        for i in range(7):
            hex_id = f"{w[f'effect_id_{i+1}']:08X}"[-4:]
            for item in effect_dropdown_list:
                if item.startswith(hex_id):
                    self.weapon_effect_combos[i].set(item)
                    break
            
            self.weapon_effect_mags[i].delete(0, tk.END)
            self.weapon_effect_mags[i].insert(0, w[f'effect_magnitude_{i+1}'])
    
    def apply_weapon_changes(self):
        w = weapons[selected_weapon_index]
        for key, entry in self.weapon_entries.items():
            try:
                w[key] = int(entry.get())
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for {key}")
                return
        
        for i in range(7):
            chosen = self.weapon_effect_combos[i].get()
            if chosen:
                hex_id = chosen.split(" ")[0]
                w[f'effect_id_{i+1}'] = int(hex_id, 16)
            
            mag_val = self.weapon_effect_mags[i].get()
            if mag_val:
                w[f'effect_magnitude_{i+1}'] = int(mag_val)
        
        self.populate_weapons()
        messagebox.showinfo("Success", "Weapon updated!")
    
    # ==================== ITEMS TAB ====================
    def create_items_tab(self):
        self.tab_items = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_items, text="Items")
        
        # Filter
        filter_frame = ttk.Frame(self.tab_items)
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side="left", padx=5)
        self.item_filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.item_filter_var, width=30)
        filter_entry.pack(side="left", padx=5)
        filter_entry.bind('<KeyRelease>', lambda e: self.populate_items())
        
        ttk.Button(filter_frame, text="Clear", command=lambda: [self.item_filter_var.set(''), self.populate_items()]).pack(side="left", padx=5)
        
        # Tree
        columns = ("slot", "item_id", "name", "type", "quantity")
        self.item_tree = ttk.Treeview(self.tab_items, columns=columns, show="headings", height=25)
        
        vsb = ttk.Scrollbar(self.tab_items, orient="vertical", command=self.item_tree.yview)
        self.item_tree.configure(yscrollcommand=vsb.set)
        
        self.item_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        for col in columns:
            self.item_tree.heading(col, text=col.capitalize())
        
        self.item_tree.column("slot", width=50)
        self.item_tree.column("item_id", width=80)
        self.item_tree.column("name", width=300)
        self.item_tree.column("type", width=150)
        self.item_tree.column("quantity", width=80)
        
        # Buttons
        btn_frame = ttk.Frame(self.tab_items)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Modify Selected", command=self.modify_item).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Item", command=self.delete_item).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Max Out All Items", command=self.max_out_all_items).pack(side="left", padx=5)
    
    def populate_items(self):
        self.item_tree.delete(*self.item_tree.get_children())
        filter_text = self.item_filter_var.get().lower()
        
        for item in items:
            if item['item_id_1'] == 0:
                continue
            
            iid = item['item_id_1']
            item_id_hex = swap_endian_hex(iid)
            
            if item_id_hex in items_json:
                name = items_json[item_id_hex]["name"]
                type_ = items_json[item_id_hex]["type"]
            else:
                name, type_ = "Unknown", "?"
            
            if filter_text and filter_text not in name.lower() and filter_text not in type_.lower():
                continue
            
            self.item_tree.insert("", "end", iid=item['slot'], values=(
                item['slot'],
                item_id_hex,
                name,
                type_,
                item['quantity']
            ))
    
    def modify_item(self):
        global selected_item, selected_item_index
        sel = self.item_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select an item first.")
            return
        
        idx = int(sel[0])
        selected_item_index = idx
        selected_item = items[idx]
        
        self.load_item_editor()
        self.notebook.select(self.tab_item_editor)
    
    def delete_item(self):
        sel = self.item_tree.selection()
        if not sel:
            return
        
        idx = int(sel[0])
        if messagebox.askyesno("Confirm", "Delete this item?"):
            items[idx]['item_id_1'] = 0
            items[idx]['quantity'] = 0
            self.populate_items()
    
    def max_out_all_items(self):
        if messagebox.askyesno("Confirm", "Set all items quantity to 9999?"):
            count = 0
            for item in items:
                if item['item_id_1'] != 0:  # Only max out existing items
                    item['quantity'] = 9999
                    count += 1
            self.populate_items()
            messagebox.showinfo("Success", f"Maxed out {count} items to 9999!")
    
    # ==================== ITEM EDITOR TAB ====================
    def create_item_editor_tab(self):
        self.tab_item_editor = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_item_editor, text="Item Editor")
        
        editor_frame = ttk.Frame(self.tab_item_editor)
        editor_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Properties
        self.item_entries = {}
        props_frame = ttk.LabelFrame(editor_frame, text="Item Properties", padding=10)
        props_frame.pack(fill="x", padx=5, pady=5)
        
        props = [
            ("item_id_1", "Item ID"),
            ("Refashion", "Refashion"),
            ("quantity", "Quantity")
        ]
        
        for i, (key, label) in enumerate(props):
            ttk.Label(props_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            e = ttk.Entry(props_frame, width=30)
            e.grid(row=i, column=1, sticky="w", padx=5, pady=5)
            self.item_entries[key] = e
        
        # Buttons
        btn_frame = ttk.Frame(editor_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Apply Changes", command=self.apply_item_changes).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Back", command=lambda: self.notebook.select(self.tab_items)).pack(side="left", padx=5)
    
    def load_item_editor(self):
        item = selected_item
        for key, entry in self.item_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, item[key])
    
    def apply_item_changes(self):
        item = items[selected_item_index]
        for key, entry in self.item_entries.items():
            try:
                item[key] = int(entry.get())
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for {key}")
                return
        
        self.populate_items()
        messagebox.showinfo("Success", "Item updated!")
    
    # ==================== SCROLLS TAB ====================
    def create_scrolls_tab(self):
        self.tab_scrolls = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_scrolls, text="Scrolls")
        
        # Filter
        filter_frame = ttk.Frame(self.tab_scrolls)
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side="left", padx=5)
        self.scroll_filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.scroll_filter_var, width=30)
        filter_entry.pack(side="left", padx=5)
        filter_entry.bind('<KeyRelease>', lambda e: self.populate_scrolls())
        
        ttk.Button(filter_frame, text="Clear", command=lambda: [self.scroll_filter_var.set(''), self.populate_scrolls()]).pack(side="left", padx=5)
        
        # Tree
        columns = ("slot", "scroll_id", "name", "type", "tier", "level")
        self.scroll_tree = ttk.Treeview(self.tab_scrolls, columns=columns, show="headings", height=25)
        
        vsb = ttk.Scrollbar(self.tab_scrolls, orient="vertical", command=self.scroll_tree.yview)
        self.scroll_tree.configure(yscrollcommand=vsb.set)
        
        self.scroll_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        for col in columns:
            self.scroll_tree.heading(col, text=col.capitalize())
        
        self.scroll_tree.column("slot", width=50)
        self.scroll_tree.column("scroll_id", width=80)
        self.scroll_tree.column("name", width=250)
        self.scroll_tree.column("type", width=150)
        self.scroll_tree.column("tier", width=50)
        self.scroll_tree.column("level", width=60)
        
        # Buttons
        btn_frame = ttk.Frame(self.tab_scrolls)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Modify Selected", command=self.modify_scroll).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Scroll", command=self.delete_scroll).pack(side="left", padx=5)
    
    def populate_scrolls(self):
        self.scroll_tree.delete(*self.scroll_tree.get_children())
        filter_text = self.scroll_filter_var.get().lower()
        
        for scroll in scrolls:
            if scroll['item_id_1'] == 0:
                continue
            
            sid = scroll['item_id_1']
            scroll_id_hex = swap_endian_hex(sid)
            
            if scroll_id_hex in items_json:
                name = items_json[scroll_id_hex]["name"]
                type_ = items_json[scroll_id_hex]["type"]
            else:
                name, type_ = "Unknown", "?"
            
            if filter_text and filter_text not in name.lower() and filter_text not in type_.lower():
                continue
            
            self.scroll_tree.insert("", "end", iid=scroll['slot'], values=(
                scroll['slot'],
                scroll_id_hex,
                name,
                type_,
                scroll['tier'],
                scroll['item_level_1']
            ))
    
    def modify_scroll(self):
        global selected_scroll, selected_scroll_index
        sel = self.scroll_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a scroll first.")
            return
        
        idx = int(sel[0])
        selected_scroll_index = idx
        selected_scroll = scrolls[idx]
        
        self.load_scroll_editor()
        self.notebook.select(self.tab_scroll_editor)
    
    def delete_scroll(self):
        sel = self.scroll_tree.selection()
        if not sel:
            return
        
        idx = int(sel[0])
        if messagebox.askyesno("Confirm", "Delete this scroll?"):
            scrolls[idx]['item_id_1'] = 0
            self.populate_scrolls()
    
    # ==================== SCROLL EDITOR TAB ====================
    def create_scroll_editor_tab(self):
        self.tab_scroll_editor = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_scroll_editor, text="Scroll Editor")
        
        canvas = tk.Canvas(self.tab_scroll_editor)
        scrollbar = ttk.Scrollbar(self.tab_scroll_editor, orient="vertical", command=canvas.yview)
        editor_frame = ttk.Frame(canvas)
        
        editor_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Properties
        self.scroll_entries = {}
        props_frame = ttk.LabelFrame(editor_frame, text="Scroll Properties", padding=10)
        props_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        props = [
    ("item_id_1", "Item ID"),
    ("item_id_2", "Item ID 2"),
    ("item_id_3", "Item ID 3"),
    ("item_level_1", "Level 1"),
    ("item_level_2", "Level 2"),
    ("higher_level_mod", "Higher Level Modifier"),
    ("unk_1", "Unknown 1"),
    ("extra_1", "Extra 1"),
    ("is_it_locked", "Is Locked"),
    ("extra_2", "Extra 2"),
    ("tier", "Tier"),
    ("unk_2", "Unknown 2"),
    ("unk_3", "Unknown 3"),
    ("attempts_remaining", "Attempts Remaining"),
    ("unk_4", "Unknown 4"),
    ("effect_footer_part1_1", "Effect Footer Part1 1"),
    ("effect_footer_part2_1", "Effect Footer Part2 1"),
    ("effect_footer_part1_2", "Effect Footer Part1 2"),
    ("effect_footer_part2_2", "Effect Footer Part2 2"),
    ("effect_footer_part1_3", "Effect Footer Part1 3"),
    ("effect_footer_part2_3", "Effect Footer Part2 3"),
    ("effect_footer_part1_4", "Effect Footer Part1 4"),
    ("effect_footer_part2_4", "Effect Footer Part2 4"),
    ("effect_footer_part1_5", "Effect Footer Part1 5"),
    ("effect_footer_part2_5", "Effect Footer Part2 5"),
    ("effect_footer_part1_6", "Effect Footer Part1 6"),
    ("effect_footer_part2_6", "Effect Footer Part2 6"),
    ("effect_footer_part1_7", "Effect Footer Part1 7"),
    ("effect_footer_part2_7", "Effect Footer Part2 7"),
    ("extra_3", "Extra 3"),
    ("offset", "Offset")
]
        
        for i, (key, label) in enumerate(props):
            ttk.Label(props_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            e = ttk.Entry(props_frame, width=20)
            e.grid(row=i, column=1, sticky="w", padx=5, pady=3)
            self.scroll_entries[key] = e
        
        # Effects
        effects_frame = ttk.LabelFrame(editor_frame, text="Effects", padding=10)
        effects_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.scroll_effect_combos = []
        self.scroll_effect_mags = []
        
        for i in range(7):
            ttk.Label(effects_frame, text=f"Effect {i+1}:").grid(row=i, column=0, sticky="w", padx=5, pady=3)
            combo = SearchableCombobox(
            effects_frame,
            width=40,
            values=effect_dropdown_list
        )
            combo.grid(row=i, column=1, sticky="w", padx=5, pady=3)
            self.scroll_effect_combos.append(combo)
            
            ttk.Label(effects_frame, text="Mag:").grid(row=i, column=2, sticky="w", padx=5, pady=3)
            mag = ttk.Entry(effects_frame, width=10)
            mag.grid(row=i, column=3, sticky="w", padx=5, pady=3)
            self.scroll_effect_mags.append(mag)
        
        # Buttons
        btn_frame = ttk.Frame(editor_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Apply Changes", command=self.apply_scroll_changes).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Back", command=lambda: self.notebook.select(self.tab_scrolls)).pack(side="left", padx=5)
    
    def load_scroll_editor(self):
        s = selected_scroll
        for key, entry in self.scroll_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, s[key])
        
        for i in range(7):
            hex_id = f"{s[f'effect_id_{i+1}']:08X}"[-4:]
            for item in effect_dropdown_list:
                if item.startswith(hex_id):
                    self.scroll_effect_combos[i].set(item)
                    break
            
            self.scroll_effect_mags[i].delete(0, tk.END)
            self.scroll_effect_mags[i].insert(0, s[f'effect_magnitude_{i+1}'])
    
    def apply_scroll_changes(self):
        s = scrolls[selected_scroll_index]
        for key, entry in self.scroll_entries.items():
            try:
                s[key] = int(entry.get())
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for {key}")
                return
        
        for i in range(7):
            chosen = self.scroll_effect_combos[i].get()
            if chosen:
                hex_id = chosen.split(" ")[0]
                s[f'effect_id_{i+1}'] = int(hex_id, 16)
            
            mag_val = self.scroll_effect_mags[i].get()
            if mag_val:
                s[f'effect_magnitude_{i+1}'] = int(mag_val)
        
        self.populate_scrolls()
        messagebox.showinfo("Success", "Scroll updated!")
    
    # ==================== STATS TAB ====================
    def create_stats_tab(self):
        self.tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stats, text="Character Stats")

        stats_frame = ttk.LabelFrame(self.tab_stats, text="Character Stats", padding=10)
        stats_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.stat_entries = {}

        stats = [
            ("Amrita", AMRITA_OFFSET, 8),
            ("Gold", GOLD_OFFSET, 8),
            ("Level", PLAYER_LEVEL, 2),
            ("Constitution", CONSTITUTION, 2),
            ("Heart", HEART, 2),
            ("Courage", COURAGE, 2),
            ("Stamina", STAMINA, 2),
            ("Strength", STRENGTH, 2),
            ("Skill", SKILL, 2),
            ("Dexterity", DEXTERITY, 2),
            ("Magic", MAGIC, 2),
            ("Ninjutsu", NINJITSU, 4),
            ("Onmyo", ONMYO, 4),
            ("Sword", SWORD, 4),
            ("Dual Sword", DUAL_SWORD, 4),
            ("Axe", AXE, 4),
            ("Kusarigama", KUSARIGAMA, 4),
            ("Odachi", ODACHI, 4),
            ("Tonfa", TONFA, 4),
            ("Hatchet", HATCHET, 4),
        ]

        # Split into 2 columns
        half = (len(stats) + 1) // 2
        left_col = stats[:half]
        right_col = stats[half:]

        # LEFT column
        for i, (name, offset, size) in enumerate(left_col):
            ttk.Label(stats_frame, text=name).grid(row=i, column=0, sticky="w", padx=10, pady=5)
            e = ttk.Entry(stats_frame, width=20)
            e.grid(row=i, column=1, sticky="w", padx=10, pady=5)
            self.stat_entries[name] = (e, offset, size)

        # RIGHT column
        for i, (name, offset, size) in enumerate(right_col):
            ttk.Label(stats_frame, text=name).grid(row=i, column=2, sticky="w", padx=20, pady=5)
            e = ttk.Entry(stats_frame, width=20)
            e.grid(row=i, column=3, sticky="w", padx=10, pady=5)
            self.stat_entries[name] = (e, offset, size)

        # Buttons at the bottom
        button_frame = ttk.Frame(self.tab_stats)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Load Stats", command=self.update_stats_display).pack(side="left", padx=20)
        ttk.Button(button_frame, text="Save Stats", command=self.save_stats).pack(side="left", padx=20)

    
    def update_stats_display(self):
        if data is None:
            return
        
        for name, (entry, offset, size) in self.stat_entries.items():
            value = find_value_at_offset(data, offset, size)
            entry.delete(0, tk.END)
            entry.insert(0, value if value is not None else 0)
    
    def save_stats(self):
        if data is None:
            messagebox.showwarning("Warning", "No save file loaded")
            return
        
        for name, (entry, offset, size) in self.stat_entries.items():
            try:
                value = int(entry.get())
                data[offset:offset+size] = write_le(value, size)
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for {name}")
                return
        
        messagebox.showinfo("Success", "Stats updated in memory!")

# ==================== MAIN ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = Nioh2Editor(root)
    root.mainloop()
