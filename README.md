# Science-support
### Harmonogram prací na projektu
#### Týden 1-2: Příprava a návrh
1. **Studium požadavků a specifikací**
   - Detailní studium požadavků a specifikací projektu.
2. **Vytvoření GitHub repozitáře**
   - Vytvoření nového repozitáře na GitHub pro projekt.
3. **Návrh databáze**
   - Navržení databázových modelů na základě specifikací.
   - Definice tabulek, atributů a vztahů mezi nimi.
4. **Návrh GraphQL schématu**
   - Navržení GraphQL schématu založeného na databázových modelech.
   - Definice query a mutation typů.
#### Týden 3-4: Implementace databáze a GraphQL
5. **Implementace databázových modelů**
   - Vytvoření samostatných souborů pro každý databázový model.
   - Implementace atributů `createdby`, `changedby`, `created`, `lastchange`.
6. **Implementace dataloadery**
   - Implementace AIODataLoader pro efektivní přístup k DB.
   - Inicializace dataloadery v kontextu.
7. **Implementace GraphQL schématu**
   - Vytvoření samostatných souborů pro GraphQL modely, queries a mutations.
   - Definice query a mutation resolver funkcí.
#### Týden 5-6: Validace vstupu a SQL statement generace
8. **Implementace funkce pro validaci vstupu**
   - Vytvoření funkce pro validaci vstupu pro parametr `where`.
   - Zabezpečení, že lze filtrovat na úrovni atributů entit.
9. **Implementace funkce pro konverzi where na SQL statement**
   - Vytvoření funkce pro konverzi parametru `where` na odpovídající SQL statement (SQLAlchemy).
   - Implementace filtrace řádků v tabulce.
#### Týden 7-8: Testování a optimalizace
10. **Implementace testů**
    - Vytvoření testovacího prostředí s pytest.
    - Implementace testů pro všechny části projektu.
11. **Optimalizace**
    - Provádění optimalizací a ladění projektu pro zlepšení výkonu.
#### Týden 9-10: Dokumentace a finální úpravy
12. **Dokumentace**
    - Vytvoření dokumentace pro projekt, včetně README s návodem na instalaci a použití.
13. **Finální úpravy a ladění**
    - Zajištění, že všechny části projektu jsou plně funkční a bez chyb.
#### Týden 11-12: Odevzdání a revize
14. **Odevzdání projektu**
    - Odevzdání hotového projektu včetně repozitáře na GitHub.
15. **Revize a testování**
    - Provádění revize projektu a testování na produkčním prostředí.
#### Týden 13: Dokončení a závěrečné úpravy
16. **Dokončení**
    - Závěrečné úpravy na základě revize a testování.
17. **Zveřejnění projektu**
    - Zveřejnění projektu na relevantním platformách nebo serverech.
   

# Popis entit (Entities)

## User (Uživatel)
   ID: Unikátní identifikátor uživatele
   Name: Jméno uživatele
   Valid: Atribut určující, zda je uživatel platný (True/False)
   CreatedBy: Kdo vytvořil záznam o uživateli
   ChangedBy: Kdo naposledy změnil záznam o uživateli
   Created: Datum a čas vytvoření záznamu
   LastChange: Datum a čas poslední změny záznamu

## OtherEntity (Další Entita)
   ID: Unikátní identifikátor entity
   Name: Jméno entity
   Valid: Atribut určující, zda je entita platná (True/False)
   CreatedBy: Kdo vytvořil záznam o entitě
   ChangedBy: Kdo naposledy změnil záznam o entitě
   Created: Datum a čas vytvoření záznamu
   LastChange: Datum a čas poslední změny záznamu
