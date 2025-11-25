# -*- coding: utf-8 -*-
import clr
import os
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document

# --- KONFIGURACJA ---
PARAM_NAME = "DATA"

# 1. DETEKCJA GRUPY (Gdzie parametr ma wylądować w panelu właściwości?)
target_group = None
try:
    target_group = GroupTypeId.Data  # Revit 2024+
    print("API: Wykryto GroupTypeId (Nowy Revit)")
except:
    target_group = BuiltInParameterGroup.PG_DATA  # Stary Revit
    print("API: Wykryto BuiltInParameterGroup (Stary Revit)")


def add_universal_parameter():
    """Dodaje parametr współdzielony 'DATA' do wszystkich kategorii Model+Annotation."""
    t = Transaction(doc, "Instalacja parametru DATA")
    t.Start()

    try:
        # 2. PLIK PARAMETRÓW WSPÓŁDZIELONYCH (tymczasowy)
        temp_file = os.path.join(os.environ["TEMP"], "Rubik_Final_Params.txt")
        if not os.path.exists(temp_file):
            with open(temp_file, 'w') as f:
                pass

        app.SharedParametersFilename = temp_file
        sp_file = app.OpenSharedParameterFile()

        if not sp_file:
            with open(temp_file, 'w') as f:
                f.write(
                    "# Shared Params.\n"
                    "*META\tVERSION\tMINVERSION\n"
                    "META\t2\t1\n"
                    "*GROUP\tID\tNAME\n"
                    "*PARAM\tGUID\tNAME\tDATATYPE\tDATACATEGORY\tGROUP\tVISIBLE\tDESCRIPTION\tUSERMODIFIABLE\n"
                )
            sp_file = app.OpenSharedParameterFile()

        # 3. TWORZENIE DEFINICJI (Obsługa API stare/nowe)
        group = sp_file.Groups.get_Item("Rubik_Global")
        if not group:
            group = sp_file.Groups.Create("Rubik_Global")

        definition = group.Definitions.get_Item(PARAM_NAME)
        if not definition:
            try:
                # Revit 2024+ (SpecTypeId)
                options = ExternalDefinitionCreationOptions(PARAM_NAME, SpecTypeId.String.Text)
            except:
                # Starsze Revity (ParameterType)
                options = ExternalDefinitionCreationOptions(PARAM_NAME, ParameterType.Text)

            definition = group.Definitions.Create(options)

        # 4. ZBIERANIE KATEGORII
        categories = app.Create.NewCategorySet()
        all_cats = doc.Settings.Categories

        count = 0
        for cat in all_cats:
            if cat.AllowsBoundParameters and (
                cat.CategoryType == CategoryType.Model
                or cat.CategoryType == CategoryType.Annotation
            ):
                categories.Insert(cat)
                count += 1

        print("Znaleziono {} pasujących kategorii.".format(count))

        # 5. WIĄZANIE
        binding = app.Create.NewInstanceBinding(categories)
        map_bindings = doc.ParameterBindings

        if map_bindings.Contains(definition):
            map_bindings.ReInsert(definition, binding, target_group)
            print("SUKCES: Zaktualizowano parametr '{}' dla wszystkich kategorii.".format(PARAM_NAME))
        else:
            map_bindings.Insert(definition, binding, target_group)
            print("SUKCES: Utworzono parametr '{}' dla wszystkich kategorii.".format(PARAM_NAME))

        t.Commit()

    except Exception as e:
        t.RollBack()
        print("BLAD KRYTYCZNY: " + str(e))
        import traceback
        traceback.print_exc()


# UWAGA: tutaj NIC nie wywołujemy automatycznie.
# Przyciski mają używać:  add_universal_parameter()
