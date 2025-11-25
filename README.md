# pyPuzzle – rozszerzenie pyRevit z kostką Rubika

**pyPuzzle** to rozszerzenie do **pyRevit**, które buduje w modelu parametryczną kostkę Rubika i pozwala nią sterować bezpośrednio w Revit.  
Silnik napisany jest w Pythonie i korzysta z API Revita oraz pyRevit.

## Co to robi?

- **Buduje kostkę Rubika N×N×N** z rodziny `Baza_01` jako obiekty Generic Model.  
  Rozmiar kostki (`MATRIX_SIZE`) oraz płynność animacji (`ANIMATION_STEPS`) można ustawić w pliku `assets/settings.txt`.
- **Animuje obrót wybranej warstwy** – obrót jest dzielony na kilka klatek, a po zakończeniu stan kostki zapisywany jest w parametrze `DATA` na każdym klocku.
- **Automatycznie tworzy typy rodziny**:
  - klocki wewnętrzne bez okładzin (czysty środek),
  - klocki zewnętrzne z odpowiednimi kolorami materiałów dla każdej ściany.
- **Ładuje rodzinę bazową** z katalogu `assets/rfa/Baza_01.rfa` bez twardych ścieżek – ścieżka wyliczana jest relatywnie względem `lib`.
- **Instaluje współdzielony parametr `DATA`** we wszystkich kategoriach Model + Annotation (obsługa również Revit 2024+).
- **Dodatkowy „szpieg”** – skrypt raportujący wszystkie rodziny, których nazwa zaczyna się na literę „B”, wraz z liczbą typów i instancji w projekcie.

## Struktura rozszerzenia

- `pyPuzzle.tab/py_Puzzle.panel/...` – przyciski na wstążce (config + ruchy kostki).
- `lib/rubik_engine.py` – główny silnik kostki Rubika (model danych, animacja, rotacje).
- `lib/wstaw_RFA.py` – bezpieczne wczytywanie rodziny `Baza_01.rfa`.
- `lib/wstaw_parametr_DATA.py` – instalacja parametru współdzielonego `DATA`.
- `lib/szpieg.py` – raport rodzin zaczynających się na „B”.
- `assets/settings.txt` – konfiguracja kostki (rozmiar, liczba klatek animacji).
- `assets/rfa/Baza_01.rfa` – rodzina bazowa pojedynczego klocka.

## Wymagania

- Autodesk Revit.
- Zainstalowany **pyRevit**.
- Folder rozszerzenia o nazwie `myTab.extension` / `pyPuzzle.extension` podpięty w pyRevit.

## Licencja

Kod rozszerzenia **pyPuzzle** jest udostępniany na licencji [MIT](./LICENSE).

Ta licencja dotyczy wyłącznie tego repozytorium (kod rozszerzenia oraz skrypty
Python). Sam pyRevit oraz Revit mają własne licencje i zasady użycia.

## Autorzy i AI

Pomysł, koncepcja działania dodatku oraz struktura rozszerzenia: **JacekBuilds**.  

Przy implementacji kodu korzystano z pomocy modeli AI (m.in. OpenAI ChatGPT / GPT
oraz Google Gemini) jako narzędzi asystujących przy pisaniu i refaktoryzacji
skryptów. Ostateczne decyzje projektowe i odpowiedzialność za kod należą do autora
repozytorium.
