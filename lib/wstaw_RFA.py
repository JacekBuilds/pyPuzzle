# -*- coding: utf-8 -*-

# Działający kod 2025-11-19 (wersja biblioteka)
# Bez twardej ścieżki, plik RFA jest w:
#   <TwojaExtension>\assets\rfa\Baza_01.rfa

import clr
import os

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

# Revit doc
doc = __revit__.ActiveUIDocument.Document

# ---------------------------------------------------------------------------
# ŚCIEŻKI: bazujemy na lokalizacji TEGO pliku (lib\wstaw_RFA.py)
# ---------------------------------------------------------------------------
LIB_DIR = os.path.dirname(__file__)              # ...\MyTools.extension\lib
EXT_DIR = os.path.dirname(LIB_DIR)               # ...\MyTools.extension
RFA_DIR = os.path.join(EXT_DIR, 'assets', 'rfa') # ...\MyTools.extension\assets\rfa

# domyślnie ładujemy Baza_01.rfa, typ "1"
SCIEZKA = os.path.join(RFA_DIR, 'Baza_01.rfa')
CEL_TYP = "1"


# --- KLASA OPCJI (Zeby Revit nie pytal o nadpisywanie) ---
class FamilyOption(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        overwriteParameterValues.Value = True
        return True


def get_safe_symbol_name(symbol):
    """Bezpieczne pobieranie nazwy typu bez uzycia .Name"""
    try:
        p = symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
        if p:
            return p.AsString()
    except:
        pass
    return "Unknown"


def run_capture_load(rfa_path=None, target_type=None):
    """
    Bezpieczne wczytanie rodziny z pliku.
    - rfa_path: pełna ścieżka do pliku .rfa (domyślnie Baza_01.rfa z assets/rfa)
    - target_type: nazwa typu do wyszukania (domyślnie CEL_TYP = "1")
    """
    path = rfa_path or SCIEZKA
    typ_name = target_type or CEL_TYP

    print("--- START (Metoda Capture) ---")
    print("Plik RFA:", path)

    if not os.path.exists(path):
        print("BLAD: Plik nie istnieje na dysku!")
        return

    t = Transaction(doc, "Wczytaj rodzine (Capture)")
    t.Start()

    try:
        # 1. Przygotowanie zmiennej na 'złapaną' rodzinę
        loaded_fam_ref = clr.Reference[Family]()

        # 2. Wczytanie z pobraniem obiektu
        result = doc.LoadFamily(path, FamilyOption(), loaded_fam_ref)

        target_family = None

        if result and loaded_fam_ref.Value:
            print("Wczytano nowa rodzine z pliku.")
            target_family = loaded_fam_ref.Value
        else:
            print("Rodzina juz byla w projekcie. Szukam jej...")
            # Szukamy po nazwie PLIKU (bez .rfa)
            target_name = os.path.basename(path).replace(".rfa", "")

            collector = FilteredElementCollector(doc).OfClass(Family)
            for f in collector:
                p_name = f.get_Parameter(BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM)
                check_name = p_name.AsString() if p_name else "N/A"
                if check_name == target_name:
                    target_family = f
                    break

            if not target_family:
                print("UWAGA: Nazwa wewnetrzna rodziny jest inna niz nazwa pliku!")
                print("Wypisuje dostepne rodziny w projekcie, sprawdz ktora to Twoja:")
                for f in collector:
                    try:
                        print(" - " + f.Name)
                    except:
                        pass
                t.RollBack()
                return

        print("Mamy rodzine! Jej wewnetrzna nazwa to: " + target_family.Name)

        # 3. Szukanie typu (bez wstawiania rodziny do modelu)
        symbol_ids = target_family.GetFamilySymbolIds()
        final_symbol = None

        for sid in symbol_ids:
            sym = doc.GetElement(sid)
            s_name = get_safe_symbol_name(sym)
            if s_name == typ_name:
                final_symbol = sym
                break

        if not final_symbol and symbol_ids.Count > 0:
            print("Nie ma typu '" + typ_name + "'. Biore pierwszy dostepny.")
            final_symbol = doc.GetElement(symbol_ids[0])

        if final_symbol:
            print("OK: typ '{}' jest dostępny.".format(get_safe_symbol_name(final_symbol)))
        else:
            print("BLAD: Rodzina nie ma typow.")

    except Exception as e:
        import traceback
        print("BLAD GLOWNY:\n" + str(e))
        print(traceback.format_exc())
        t.RollBack()
    else:
        t.Commit()


# UWAGA:
# Nie wywołujemy tutaj run_capture_load() automatycznie.
# Biblioteka jest pasywna – przycisk ma ją zawołać sam:
#   import wstaw_RFA as loader
#   loader.run_capture_load()
