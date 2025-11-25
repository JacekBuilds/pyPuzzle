# -*- coding: utf-8 -*-
# pyRevit – raport rodzin zaczynających się na "B" w tabeli pyRevit

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Family,
    FamilySymbol,
)
from pyrevit import script

doc = __revit__.ActiveUIDocument.Document
output = script.get_output()
output.resize(900, 600)   # opcjonalnie powiększ okno

# nagłówek
output.print_md("## RAPORT RODZIN (nazwa zaczyna się na 'B')")

# --- pobierz rodziny ---
families = FilteredElementCollector(doc).OfClass(Family).ToElements()
families_b = [f for f in families if f.Name and f.Name.upper().startswith("B")]

symbols_all = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
instances_all = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()

rows = []          # dane do tabeli
total_types = 0
total_instances = 0

for fam in families_b:
    symbols = [s for s in symbols_all if s.Family.Id == fam.Id]
    num_types = len(symbols)

    sym_ids = [s.Id for s in symbols]
    num_inst = 0
    for inst in instances_all:
        try:
            if inst.GetTypeId() in sym_ids:
                num_inst += 1
        except:
            pass

    total_types += num_types
    total_instances += num_inst

    rows.append([fam.Name, num_types, num_inst])

# tabela – pyRevit sam ją ładnie narysuje
if rows:
    output.print_table(
        table_data=rows,
        columns=["Rodzina", "Typów", "Instancji"]
    )
else:
    output.print_md("_Brak rodzin zaczynających się na 'B'._")

# podsumowanie
output.print_md("---")
output.print_md("**Podsumowanie**")
output.print_md("- Rodzin zaczynających się na 'B': **{}**".format(len(rows)))
output.print_md("- Łączna liczba typów: **{}**".format(total_types))
output.print_md("- Łączna liczba instancji: **{}**".format(total_instances))
