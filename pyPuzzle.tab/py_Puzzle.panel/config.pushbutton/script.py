# -*- coding: utf-8 -*-

import rubik_engine as rb          # silnik kostki (lib/rubik_engine.py)
import wstaw_RFA as loader         # pancerny importer RFA (lib/wstaw_RFA.py)
import wstaw_parametr_DATA as pdt  # dodawacz parametru DATA (lib/wstaw_parametr_DATA.py)

# 1. parametr DATA (shared parameter, zbindowany do wszystkich kategorii)
pdt.add_universal_parameter()

# 2. rodzina Baza_01.rfa z assets/rfa (używana przez RubikManager)
loader.run_capture_load()   # domyślnie Baza_01.rfa, typ "1"

# 3. zbuduj kostkę Rubika
doc = __revit__.ActiveUIDocument.Document
manager = rb.RubikManager(doc, size=rb.MATRIX_SIZE)

manager.zbuduj_nowa_kostke()