# -*- coding: utf-8 -*-
import random
import time
import rubik_engine as rb
from pyrevit import script

doc = __revit__.ActiveUIDocument.Document

# Ile ruchów losowych?
SCRAMBLE_MOVES = 20


def scramble_cube():
    # Odtwórz model kostki z parametrów DATA
    manager = rb.RubikManager(doc, size=rb.MATRIX_SIZE)

    if not manager.odtworz_z_revita():
        print("BLAD: Nie znaleziono kostki Rubika w projekcie.")
        print("Uruchom najpierw przycisk CONFIG, żeby ją stworzyć.")
        return

    axes = ['X', 'Y', 'Z']
    N = manager.N

    print("=== SCRAMBLE: {} losowych ruchów ===".format(SCRAMBLE_MOVES))

    for i in range(SCRAMBLE_MOVES):
        axis = random.choice(axes)
        layer = random.randint(0, N - 1)
        angle = rb.KAT_OBROTU if random.choice([True, False]) else -rb.KAT_OBROTU

        print("Ruch {:02d}: os {}  warstwa {}  kąt {}".format(i + 1, axis, layer, angle))
        manager.obroc_warstwe(axis, layer, angle)

    print("=== SCRAMBLE ZAKOŃCZONY ===")

    # Ładne zamknięcie konsoli po chwili
    out = script.get_output()
    time.sleep(1)
    out.close()


scramble_cube()
