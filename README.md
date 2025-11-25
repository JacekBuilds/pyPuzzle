```markdown
# pyPuzzle – rozszerzenie pyRevit z kostką Rubika

**pyPuzzle** to rozszerzenie do **pyRevit**, które buduje w modelu parametryczną kostkę Rubika i pozwala nią sterować bezpośrednio w Revit.  
Silnik napisany jest w Pythonie i korzysta z API Revita oraz pyRevit.:contentReference[oaicite:0]{index=0}  

## Co to robi?

- **Buduje kostkę Rubika N×N×N** z rodziny `Baza_01` jako obiekty Generic Model.  
  Rozmiar kostki (`MATRIX_SIZE`) oraz płynność animacji (`ANIMATION_STEPS`) można ustawić w pliku `assets/settings.txt`.:contentReference[oaicite:1]{index=1}  
- **Animuje obrót wybranej warstwy** – obrót jest dzielony na kilka klatek, a po zakończeniu stan kostki zapisywany jest w parametrze `DATA` na każdym klocku.:contentReference[oaicite:2]{index=2}  
- **Automatycznie tworzy typy rodziny**:
  - klocki wewnętrzne bez okładzin (czysty środek),
  - klocki zewnętrzne z odpowiednimi kolorami materiałów dla każdej ściany.:contentReference[oaicite:3]{index=3}  
- **Ładuje rodzinę bazową** z katalogu `assets/rfa/Baza_01.rfa` bez twardych ścieżek – ścieżka wyliczana jest relatywnie względem `lib`.:contentReference[oaicite:4]{index=4}  
- **Instaluje współdzielony parametr `DATA`** we wszystkich kategoriach Model + Annotation (obsługa zarówno starszego API, jak i Revit 2024+).:contentReference[oaicite:5]{index=5}  
- **Dodatkowy „szpieg”** – skrypt raportujący wszystkie rodziny, których nazwa zaczyna się na literę „B”, wraz z liczbą typów i instancji w projekcie. Raport wyświetlany jest w oknie pyRevit jako tabela.:contentReference[oaicite:6]{index=6}  

## Struktura rozszerzenia

- `pyPuzzle.tab/py_Puzzle.panel/...` – przyciski na wstążce (config + ruchy kostki).
- `lib/rubik_engine.py` – główny silnik kostki Rubika (model danych, animacja, rotacje).:contentReference[oaicite:7]{index=7}  
- `lib/wstaw_RFA.py` – bezpieczne wczytywanie rodziny `Baza_01.rfa`.:contentReference[oaicite:8]{index=8}  
- `lib/wstaw_parametr_DATA.py` – instalacja parametru współdzielonego `DATA`.:contentReference[oaicite:9]{index=9}  
- `lib/szpieg.py` – raport rodzin zaczynających się na „B”.:contentReference[oaicite:10]{index=10}  
- `assets/settings.txt` – konfiguracja kostki (rozmiar, liczba klatek animacji).:contentReference[oaicite:11]{index=11}  
- `assets/rfa/Baza_01.rfa` – rodzina bazowa pojedynczego klocka.:contentReference[oaicite:12]{index=12}  

## Wymagania

- Autodesk Revit (testowane na nowszych wersjach API).  
- Zainstalowany **pyRevit**.
- Folder rozszerzenia o nazwie `myTab.extension` / `pyPuzzle.extension` podpięty w pyRevit.

## Ogólny sposób użycia

1. Podłącz folder `.extension` w pyRevit.  
2. Użyj przycisku **CONFIG** (lub odpowiedniego przycisku instalacyjnego), aby:
   - wczytać rodzinę `Baza_01.rfa`,
   - zainstalować parametr `DATA`,
   - wygenerować kostkę Rubika w modelu.  
3. Zaznacz klocki wybranej warstwy i użyj przycisków obrotu (clockwise / counter-clockwise / random), aby animować ruch.:contentReference[oaicite:15]{index=15}  

Projekt jest w trakcie zabawy/eksperymentu – służy zarówno jako plugin do Revita, jak i poligon doświadczalny dla API oraz pyRevit w Pythonie.
```
