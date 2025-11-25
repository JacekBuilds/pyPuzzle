# -*- coding: utf-8 -*-

# ##############################################################################
#   SKRYPT: RUBIK MASTER - FINAL "CLEAN CORE" EDITION (BIBLIOTEKA)
#   OPIS:   - Automatyczne wykrywanie trybu (w auto_run).
#           - Animacja.
#           - POPRAWKA: Wewnętrzne klocki nie mają kolorowych okładzin.
#           - UWAGA: Ten plik NIE odpala się sam — używaj go z innych skryptów.
# ##############################################################################

import clr
import math
import os
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Drawing')

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB.Structure import StructuralType

import System.Drawing as SD

# pyRevit
from pyrevit import script
import time

# Revit kontekst (dostępny tylko w pyRevit)
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

# ==============================================================================
# KONFIGURACJA
# ==============================================================================

MATRIX_SIZE = 3          # Zmień na 4, 5 itd.
ANIMATION_STEPS = 15     # Liczba klatek animacji

KAT_OBROTU = 90
SNAP_TOLERANCE = 5.0
NAZWA_RODZINY = "Baza_01"
PARAM_DATA = "DATA"
PREFIX_NAZWY_TYPU = "Rubik_Mat_"
M_TO_FT = 3.2808399

GLOBALNE_KOLORY_RGB = {
    "Czerwony":      (1, 255,   0,   0),
    "Pomarańczowy":  (2, 255, 128,   0),
    "Żółty":         (3, 255, 255,   0),
    "Biały":         (4, 255, 255, 255),
    "Niebieski":     (5,   0,   0, 255),
    "Zielony":       (6,   0, 128,   0),
}

# ========================================================================
# USTAWIENIA Z PLIKU settings.txt (opcjonalne)
# ========================================================================

# ...\MyTools.extension\lib\rubik_engine.py
LIB_DIR = os.path.dirname(__file__)
# ...\MyTools.extension
EXT_DIR = os.path.dirname(LIB_DIR)
# ...\MyTools.extension\assets\settings.txt
SETTINGS_PATH = os.path.join(EXT_DIR, 'assets', 'settings.txt')


def _load_settings_from_txt(path):
    """Czyta prosty plik key=value (ignoruje puste linie i komentarze #).
       Jeśli plik nie istnieje, tworzy go z wartościami domyślnymi.
    """
    settings = {}

    # jeśli nie ma pliku -> utwórz z domyślnymi wartościami
    if not os.path.exists(path):
        try:
            with open(path, 'w') as f:
                f.write("n={}\n".format(MATRIX_SIZE))
                f.write("animation_steps={}\n".format(ANIMATION_STEPS))
            print("Rubik settings: utworzono nowy settings.txt z domyślnymi wartościami.")
        except Exception as e:
            print("Rubik settings: nie udało się utworzyć pliku ustawień:", e)
        return settings  # zwracamy pusty, domyślne zostają

    # jeśli plik istnieje -> wczytaj
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    settings[key.strip()] = val.strip()
    except Exception as e:
        print("Rubik settings: błąd odczytu pliku:", e)

    return settings


# wczytanie ustawień i nadpisanie domyślnych wartości
_settings = _load_settings_from_txt(SETTINGS_PATH)
try:
    if 'n' in _settings:
        MATRIX_SIZE = int(_settings['n'])
    if 'animation_steps' in _settings:
        ANIMATION_STEPS = int(_settings['animation_steps'])
    print("Rubik settings: MATRIX_SIZE = {}, ANIMATION_STEPS = {}".format(
        MATRIX_SIZE, ANIMATION_STEPS
    ))
except Exception as e:
    print("Rubik settings: błąd parsowania wartości:", e)


# ==============================================================================
# MODEL DANYCH
# ==============================================================================

class MiniJson:
    @staticmethod
    def dump(data):
        return (str(data)
                .replace("'", '"')
                .replace("True", "true")
                .replace("False", "false"))

    @staticmethod
    def load(json_str):
        return eval(
            json_str
            .replace("true", "True")
            .replace("false", "False")
            .replace("null", "None")
        )


class AbstractCubie:
    def __init__(self, revit_id, current_idx, initial_idx, orientation_mtx):
        self.revit_id = revit_id
        self.pos = list(current_idx)
        self.init = list(initial_idx)
        self.rot = orientation_mtx

    def to_dict(self):
        return {
            "rid": self.revit_id,
            "pos": self.pos,
            "init": self.init,
            "rot": self.rot
        }


class AbstractModel:
    def __init__(self):
        self.cubies = []
        self.lock_state = {
            "is_locked": False,
            "active_axis": None,
            "layer_offsets": {}
        }

    def add_cubie(self, cubie):
        self.cubies.append(cubie)

    def get_cubies_in_layer(self, axis, layer_idx):
        axis_map = {'X': 0, 'Y': 1, 'Z': 2}
        return [c for c in self.cubies if c.pos[axis_map[axis]] == layer_idx]


# ==============================================================================
# MANAGER
# ==============================================================================

class RubikManager:
    def __init__(self, doc, size=3):
        self.doc = doc
        self.N = size
        self.model = AbstractModel()
        self.center_point = XYZ(0, 0, 0)  # Będzie nadpisane przez autokalibrację

    def aktualizuj_srodek_ciezkosci(self):
        """Dynamiczne wykrywanie srodka kostki (dla pivot point)."""
        if not self.model.cubies:
            return
        min_x, min_y, min_z = 999999, 999999, 999999
        max_x, max_y, max_z = -999999, -999999, -999999
        c = 0
        for cb in self.model.cubies:
            el = self.doc.GetElement(ElementId(cb.revit_id))
            if el and el.Location:
                pt = el.Location.Point
                if pt.X < min_x: min_x = pt.X
                if pt.X > max_x: max_x = pt.X
                if pt.Y < min_y: min_y = pt.Y
                if pt.Y > max_y: max_y = pt.Y
                if pt.Z < min_z: min_z = pt.Z
                if pt.Z > max_z: max_z = pt.Z
                c += 1
        if c > 0:
            self.center_point = XYZ(
                (min_x + max_x) / 2,
                (min_y + max_y) / 2,
                (min_z + max_z) / 2
            )

    # --- TWORZENIE ---
    def zbuduj_nowa_kostke(self):
        print(">>> TWORZENIE KOSTKI {}x{} (Czysty Srodek) <<<".format(self.N, self.N))

        fam_check = FilteredElementCollector(self.doc).OfClass(Family)
        if not any(f.Name == NAZWA_RODZINY for f in fam_check):
            print("BLAD: Brak rodziny '{}'.".format(NAZWA_RODZINY))
            return

        col = (FilteredElementCollector(self.doc)
               .OfClass(FamilyInstance)
               .OfCategory(BuiltInCategory.OST_GenericModel))
        ids = List[ElementId]()
        for inst in col:
            if inst.Symbol.Family.Name == NAZWA_RODZINY:
                ids.Add(inst.Id)
        if ids.Count > 0:
            t = Transaction(self.doc, "Clean")
            t.Start()
            self.doc.Delete(ids)
            t.Commit()

        t = Transaction(self.doc, "Build")
        t.Start()

        try:
            mat_ids = self._ensure_materials()
            sym = self._get_any_family_symbol_safe()
            if not sym:
                t.RollBack()
                return

            cnt = 0
            for x in range(self.N):
                for y in range(self.N):
                    for z in range(self.N):
                        # Tutaj uzywamy nowej logiki typow
                        typ = self._get_or_create_type(sym, x, y, z, mat_ids)

                        loc = XYZ(x * M_TO_FT, y * M_TO_FT, z * M_TO_FT)
                        inst = self.doc.Create.NewFamilyInstance(
                            loc,
                            typ,
                            StructuralType.NonStructural
                        )

                        try:
                            rid = inst.Id.Value
                        except:
                            rid = inst.Id.IntegerValue

                        cubie = AbstractCubie(
                            rid,
                            [x, y, z],
                            [x, y, z],
                            [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
                        )
                        self.model.add_cubie(cubie)

                        p = inst.LookupParameter(PARAM_DATA)
                        if p:
                            p.Set(MiniJson.dump(cubie.to_dict()))
                        cnt += 1
            t.Commit()
            print("SUKCES! Zbudowano {} elementow.".format(cnt))
            self.aktualizuj_srodek_ciezkosci()

        except Exception as e:
            print("BLAD BUDOWANIA: " + str(e))
            t.RollBack()

    # --- STEROWANIE ---
    def obroc_warstwe(self, axis, layer_idx, angle):
        lock = self.model.lock_state
        if lock["is_locked"] and lock["active_axis"] != axis:
            print("BLOKADA! Os zajeta.")
            return

        tg = TransactionGroup(self.doc, "Animacja")
        tg.Start()

        steps = ANIMATION_STEPS
        step_angle = float(angle) / steps

        for _ in range(steps):
            self._fizyczny_obrot(axis, layer_idx, step_angle)
            uidoc.RefreshActiveView()

        if not lock["is_locked"]:
            lock["is_locked"] = True
            lock["active_axis"] = axis

        off = lock["layer_offsets"].get(layer_idx, 0.0) + angle
        lock["layer_offsets"][layer_idx] = off

        target = round(off / 90.0) * 90.0
        delta = target - off

        if abs(delta) <= SNAP_TOLERANCE:
            if abs(delta) > 0.0001:
                self._fizyczny_obrot(axis, layer_idx, delta)

            steps_logic = int(round(target / 90.0))
            if steps_logic != 0:
                self._logiczny_obrot(axis, layer_idx, steps_logic)
                lock["layer_offsets"][layer_idx] = 0.0
                self._zapisz_stan(axis, layer_idx)

        if all(abs(v) < 0.001 for v in lock["layer_offsets"].values()):
            lock["is_locked"] = False
            lock["active_axis"] = None
            lock["layer_offsets"] = {}
            print("RUCH OK")

        tg.Assimilate()

    # --- HELPERS ---
    def odtworz_z_revita(self):
        self.model = AbstractModel()
        col = (FilteredElementCollector(self.doc)
               .OfClass(FamilyInstance)
               .OfCategory(BuiltInCategory.OST_GenericModel))
        c = 0
        for inst in col:
            if inst.Symbol.Family.Name == NAZWA_RODZINY:
                p = inst.LookupParameter(PARAM_DATA)
                if p and p.AsString():
                    try:
                        d = MiniJson.load(p.AsString())
                        self.model.add_cubie(
                            AbstractCubie(d['rid'], d['pos'], d['init'], d['rot'])
                        )
                        c += 1
                    except:
                        pass
        if c > 0:
            self.aktualizuj_srodek_ciezkosci()
        return c > 0

    def _fizyczny_obrot(self, axis, layer_idx, angle):
        cubies = self.model.get_cubies_in_layer(axis, layer_idx)
        if not cubies:
            return
        ids = List[ElementId]([ElementId(c.revit_id) for c in cubies])
        p1 = self.center_point
        vec = (XYZ(1, 0, 0) if axis == 'X'
               else (XYZ(0, 1, 0) if axis == 'Y' else XYZ(0, 0, 1)))
        line = Line.CreateBound(p1, p1 + vec)
        rad = (math.pi * angle) / 180.0 * -1
        t = Transaction(self.doc, "Klatka")
        t.Start()
        ElementTransformUtils.RotateElements(self.doc, ids, line, rad)
        t.Commit()

    def _logiczny_obrot(self, axis, layer_idx, steps):
        cubies = self.model.get_cubies_in_layer(axis, layer_idx)
        N = self.N - 1
        for _ in range(abs(steps)):
            d = 1 if steps > 0 else -1
            for c in cubies:
                x, y, z = c.pos
                if axis == 'Z':
                    c.pos = [y, N - x, z] if d == 1 else [N - y, x, z]
                elif axis == 'X':
                    c.pos = [x, z, N - y] if d == 1 else [x, N - z, y]
                elif axis == 'Y':
                    c.pos = [N - z, y, x] if d == 1 else [z, y, N - x]

    def _zapisz_stan(self, axis, layer_idx):
        t = Transaction(self.doc, "Zapis")
        t.Start()
        for c in self.model.get_cubies_in_layer(axis, layer_idx):
            el = self.doc.GetElement(ElementId(c.revit_id))
            if el:
                el.LookupParameter(PARAM_DATA).Set(MiniJson.dump(c.to_dict()))
        t.Commit()

    def _ensure_materials(self):
        mats = {}
        for name, data in GLOBALNE_KOLORY_RGB.items():
            mid, r, g, b = data
            found = False
            for m in FilteredElementCollector(self.doc).OfClass(Material):
                if m.Name == name:
                    mats[mid] = m.Id
                    found = True
                    break
            if not found:
                nm_id = Material.Create(self.doc, name)
                self.doc.GetElement(nm_id).Color = SD.Color.FromArgb(255, r, g, b)
                mats[mid] = nm_id
        return mats

    def _get_any_family_symbol_safe(self):
        col = FilteredElementCollector(self.doc).OfClass(FamilySymbol)
        for s in col:
            p_fam = s.get_Parameter(BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM)
            if p_fam and p_fam.AsString() == NAZWA_RODZINY:
                if not s.IsActive:
                    s.Activate()
                return s
        return None

    def _get_name(self, el):
        p = el.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
        return p.AsString() if p else ""

    # --- POPRAWIONA FUNKCJA GENEROWANIA TYPOW (CZYSTE WNETRZE) ---
    def _get_or_create_type(self, base_sym, x, y, z, mat_ids):
        # Sprawdzamy, czy klocek jest wewnetrzny (nie dotyka scianek)
        is_internal = (0 < x < self.N - 1) and (0 < y < self.N - 1) and (0 < z < self.N - 1)

        if is_internal:
            # --- LOGIKA DLA SRODKA (BEZ OKLADZIN) ---
            core_name = "Rubik_Core_Internal"
            col = FilteredElementCollector(self.doc).OfClass(FamilySymbol)
            for s in col:
                if self._get_name(s) == core_name:
                    return s

            # Tworzymy typ dla wnetrza
            new_core = base_sym.Duplicate(core_name)
            vps = ["Vis_Face_1", "Vis_Face_2", "Vis_Face_3",
                   "Vis_Face_4", "Vis_Face_5", "Vis_Face_6"]
            # Wylaczamy widocznosc wszystkich scianek
            for v in vps:
                p = new_core.LookupParameter(v)
                if p:
                    p.Set(0)
            return new_core
            # ----------------------------------------

        # --- LOGIKA DLA ZEWNETRZNYCH (KOLOROWE) ---
        name = "{}{}X{}Y{}Z{}".format(PREFIX_NAZWY_TYPU, self.N, x, y, z)
        col = FilteredElementCollector(self.doc).OfClass(FamilySymbol)
        for s in col:
            if self._get_name(s) == name:
                return s
        new_sym = base_sym.Duplicate(name)

        vis = [False] * 6
        cols = [None] * 6
        N = self.N
        if y == N - 1:
            vis[0] = True
            cols[0] = mat_ids[3]
        if y == 0:
            vis[1] = True
            cols[1] = mat_ids[4]
        if x == 0:
            vis[2] = True
            cols[2] = mat_ids[2]
        if x == N - 1:
            vis[3] = True
            cols[3] = mat_ids[1]
        if z == N - 1:
            vis[4] = True
            cols[4] = mat_ids[5]
        if z == 0:
            vis[5] = True
            cols[5] = mat_ids[6]

        vps = ["Vis_Face_1", "Vis_Face_2", "Vis_Face_3",
               "Vis_Face_4", "Vis_Face_5", "Vis_Face_6"]
        mps = ["Material_Face_1", "Material_Face_2", "Material_Face_3",
               "Material_Face_4", "Material_Face_5", "Material_Face_6"]
        for i in range(6):
            new_sym.LookupParameter(vps[i]).Set(1 if vis[i] else 0)
            if vis[i] and cols[i]:
                new_sym.LookupParameter(mps[i]).Set(cols[i])
        return new_sym


# ==============================================================================
# AUTO-RUN (DALEJ DOSTĘPNY, ALE NIE JEST JUŻ WYWOŁYWANY AUTOMATYCZNIE)
# ==============================================================================

def auto_run(doc, manager):
    """Stary tryb: brak kostki -> tworzy, jest kostka -> obraca zaznaczoną warstwę."""
    col = (FilteredElementCollector(doc)
           .OfClass(FamilyInstance)
           .OfCategory(BuiltInCategory.OST_GenericModel))
    cube_exists = False
    for inst in col:
        if inst.Symbol.Family.Name == NAZWA_RODZINY:
            p = inst.LookupParameter(PARAM_DATA)
            if p and p.AsString():
                cube_exists = True
                break

    if not cube_exists:
        print("INFO: Brak kostki. TWORZENIE...")
        manager.zbuduj_nowa_kostke()
    else:
        print("INFO: Kostka wykryta. STEROWANIE...")
        if manager.odtworz_z_revita():
            sel_ids = uidoc.Selection.GetElementIds()
            if sel_ids.Count < 2:
                print("BLAD: Zaznacz min. 2 klocki.")
                return

            sel_ints = []
            for eid in sel_ids:
                try:
                    sel_ints.append(eid.Value)
                except:
                    sel_ints.append(eid.IntegerValue)

            found = [c for c in manager.model.cubies if c.revit_id in sel_ints]
            if not found:
                print("BLAD: Nie znaleziono danych.")
                return

            first = found[0]
            cx = all(c.pos[0] == first.pos[0] for c in found)
            cy = all(c.pos[1] == first.pos[1] for c in found)
            cz = all(c.pos[2] == first.pos[2] for c in found)
            matches = sum([cx, cy, cz])

            if matches == 1:
                axis = None
                layer = -1
                if cx:
                    axis = 'X'
                    layer = first.pos[0]
                elif cy:
                    axis = 'Y'
                    layer = first.pos[1]
                elif cz:
                    axis = 'Z'
                    layer = first.pos[2]
                print("Ruch: Os {} Warstwa {}".format(axis, layer))

                print("\n--- SUKCES! Okno zamknie sie samoczynnie za 1 sekundę... ---")
                manager.obroc_warstwe(axis, layer, KAT_OBROTU)

                # Pobieramy obiekt okna konsoli
                output = script.get_output()
                # Czekamy 1 sekundę
                time.sleep(1)
                # Programowo zamykamy okno
                output.close()

            elif matches > 1:
                print("BLAD: Niejednoznacznosc. Zaznacz klocki po przekatnej.")
            else:
                print("BLAD: Klocki nie leza na jednej plaszczyznie.")

def detect_layer_from_selection(manager):
    """Zwraca (axis, layer) na podstawie zaznaczonych klocków, albo (None, None) przy błędzie."""
    sel_ids = uidoc.Selection.GetElementIds()
    if sel_ids.Count < 2:
        print("BLAD: Zaznacz min. 2 klocki.")
        return None, None

    sel_ints = []
    for eid in sel_ids:
        try:
            sel_ints.append(eid.Value)
        except:
            sel_ints.append(eid.IntegerValue)

    found = [c for c in manager.model.cubies if c.revit_id in sel_ints]
    if not found:
        print("BLAD: Nie znaleziono danych dla zaznaczonych elementow.")
        return None, None

    first = found[0]
    cx = all(c.pos[0] == first.pos[0] for c in found)
    cy = all(c.pos[1] == first.pos[1] for c in found)
    cz = all(c.pos[2] == first.pos[2] for c in found)
    matches = sum([cx, cy, cz])

    if matches == 1:
        if cx:
            axis = 'X'; layer = first.pos[0]
        elif cy:
            axis = 'Y'; layer = first.pos[1]
        elif cz:
            axis = 'Z'; layer = first.pos[2]
        print("Ruch: Os {} Warstwa {}".format(axis, layer))
        return axis, layer

    elif matches > 1:
        print("BLAD: Niejednoznacznosc. Zaznacz klocki po przekatnej.")
    else:
        print("BLAD: Klocki nie leza na jednej plaszczyznie.")

    return None, None


def rotate_from_selection(angle):
    """Odtwarza kostkę z Revita i obraca wybraną warstwę o zadany kąt."""
    manager = RubikManager(doc, size=MATRIX_SIZE)

    if not manager.odtworz_z_revita():
        print("BLAD: Nie znaleziono danych kostki (uruchom najpierw przycisk CONFIG).")
        return

    axis, layer = detect_layer_from_selection(manager)
    if axis is None:
        return

    print("Ruch: Os {} Warstwa {} Kat {}".format(axis, layer, angle))
    manager.obroc_warstwe(axis, layer, angle)

    # Zamknij okno konsoli po sekundzie
    out = script.get_output()
    time.sleep(1)
    out.close()

