---
name: offline-ai-kit
description: Офлайн-AI на ноутбуці на випадок, коли зникне інтернет — локальна модель (Bionic або LM Studio) + офлайн-бібліотека Kiwix на 5–150 ГБ (Вікіпедія українською й англійською, медицина, ремонт, вода, їжа, радіо, город, підручники, карта Європи) + місток openzim-mcp, щоб модель сама шукала в бібліотеці. Агент сам міряє пам'ять і диск, підбирає модель, качає й звіряє файли, налаштовує автозапуск, підключає бібліотеку до моделі й перевіряє все в «пісочниці» без мережі. Застосовувати, коли просять «підготуй комп до життя без інтернету», «офлайн-Вікіпедія», «локальна модель без інтернету», «Kiwix», «ZIM», «Bionic», «LM Studio з Вікіпедією», «AI на випадок блекауту». Перевірено на MacBook Pro M4 Pro 24 ГБ, листопад 2026.
---

# Офлайн-AI: модель + бібліотека, які працюють без інтернету

ChatGPT, Claude і Gemini живуть у чужих дата-центрах і зникають разом з інтернетом.
Цей скіл ставить на ноутбук те, що лишається: **модель на твоєму залізі** і **бібліотеку на диску**,
і з'єднує їх, щоб модель сама знаходила статтю й відповідала з неї.

Перевірено 03–07.11.26 на MacBook Pro M4 Pro 24 ГБ: 10 питань у пісочниці без мережі,
жодного з'єднання назовні. Рахунки й код — відмінно, перша допомога, вода, ліки — добре,
але **дози й числа треба звіряти зі статтею**: 9B-модель написала «10 крапель хлорки на 20 л»
замість 40. Мануалів на конкретні машини в бібліотеці немає.

Що буде в кінці:
1. **Читати самому** — http://localhost:8080 у будь-якому браузері (стартує сам) і застосунок Kiwix.
2. **Питати модель** — Bionic або LM Studio з інструментом `wikipedia`: модель шукає, відкриває статтю, відповідає й каже джерело.
3. **Рахувати й писати код** — модель робить це сама, без бібліотеки.

Скільки часу: 1–3 години, здебільшого завантаження. Скільки місця: від 10 ГБ (мінімум) до ~170 ГБ (повний набір + дві моделі).
**Робити, поки інтернет є.** Без нього не встановиш нічого.

## Як працювати агенту

- Кожен крок — перевіряй результат командою, а не вір, що «мало спрацювати».
- Кожен скачаний файл — звіряй контрольну суму. Не збіглось — перекачай, не використовуй.
- Нічого не видаляй назавжди: старе — в Кошик (`mv … ~/.Trash/`).
- Наприкінці дай людині картку з розділу «Коли інтернету немає» — своїми словами, коротко.
- Шляхи нижче — для macOS. Windows і Linux — у розділі «Не Mac».

## Крок 0. Виміряй машину

```bash
sysctl -n hw.memsize | awk '{print $1/1073741824 " GB RAM"}'
sysctl -n machdep.cpu.brand_string
df -h ~ | awk 'NR==2{print "free:", $4}'
```

Тримай щонайменше 50 ГБ вільними після всього. Від пам'яті залежить модель (крок 2), від диска — бібліотека (крок 3).

## Крок 1. Програма для моделі

- **Mac на Apple Silicon:** [Bionic](https://lmstudio.ai) (новий застосунок LM Studio) або класичний LM Studio. Обидва безкоштовні.
  Якщо програми ще немає — попроси людину скачати її з https://lmstudio.ai і встановити самій; далі продовжуй.
  У Bionic: Settings → General → «Automatic updates» увімкнути.
- Перевір, що є консольна утиліта: `~/.lmstudio/bin/lms ls`.

## Крок 2. Модель під твою пам'ять

| Оперативна пам'ять | Модель (GGUF) | Файл | Навіщо |
|---|---|---|---|
| 8 ГБ | моделі не став | — | лише бібліотека (крок 3), читати самому |
| 16 ГБ | `mradermacher/Qwen3.8-9B-heretic-uncensored-GGUF` → `Q4_K_S` | 5,4 ГБ | швидка, але плутає цифри |
| 24 ГБ | `unsloth/Qwen3.8-27B-GGUF` → `Qwen3.8-27B-UD-IQ4_XS.gguf` + 9B вище як швидка запасна | 14,3 ГБ + 5,4 ГБ | найсильніша, що влазить у 24 ГБ (стеля Bionic для моделі — 14,76 ГіБ) |
| 32 ГБ і більше | `unsloth/Qwen3.8-27B-GGUF` → `Q4_K_M` | 16,5 ГБ | та сама модель, точніша |

Про 9B чесно: офіційної Qwen3.8 на 9B немає. Це стороння збірка-дистиляція зі знятими обмеженнями («uncensored»), саме її перевірено в тесті.
Хочеш без «uncensored» — `empero-ai/Qwen3.8-9B-Distill-GGUF` (автор її не тестував); скажи про цей вибір людині.

Качай у теку, яку бачить LM Studio, і звір контрольну суму:

```bash
brew install aria2
D=~/.lmstudio/models/unsloth/Qwen3.8-27B-GGUF; F=Qwen3.8-27B-UD-IQ4_XS.gguf
mkdir -p "$D" && cd "$D"
aria2c -x 8 -s 8 -c --file-allocation=none -o "$F" "https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/resolve/main/$F"
shasum -a 256 "$F"     # порівняй з lfs.oid цього файлу в https://huggingface.co/api/models/unsloth/Qwen3.8-27B-GGUF/tree/main
~/.lmstudio/bin/lms ls  # модель має з'явитись у списку
```

⚠️ `aria2c` без `-o` зберігає файл під хеш-іменем — тоді перейменуй руками.
Перед запуском 27B закрий важкі програми (браузер з десятками вкладок): інакше Mac піде в swap і модель писатиме в рази повільніше.

## Крок 3. Бібліотека Kiwix

Файли `.zim` — стислі копії сайтів. Тека: `~/zim-files`. Готовий список на 45 файлів (~150 ГБ) — [`files/kiwix-list.txt`](files/kiwix-list.txt):
по два рядки на файл (`.meta4` для завантаження і `.sha256` для перевірки). Порядок: спершу малі й важливі, наприкінці дві великі Вікіпедії.

| Набір | Що всередині | Місце |
|---|---|---|
| Мінімум | WikiMed (медицина), MedlinePlus, ліки NHS, військова медицина, вода, їжа, вузли, після катастрофи | ~5 ГБ |
| Стандарт | + iFixit, ремонт дому, Appropedia, енергетика, Wikivoyage, Вікісловник | ~16 ГБ |
| Великий | + уся українська Вікіпедія з картинками (28,2 ГБ) і вся англійська текстом (52,7 ГБ) | ~97 ГБ |
| Повний | + чеклісти Ready.gov (блекаут, мороз, ядерна загроза), ремонт Mac/iPhone, авто, електроніка й радіо, город, тварини, велосипед, столярка, підручники Wikibooks і Wikiversity, англійський словник, музика й звук, фітнес, карта Європи (26,7 ГБ) | ~150 ГБ |

Мінімум, стандарт і великий — це перші рядки списку: обріж `kiwix-list.txt` до потрібного файлу (`grep -B1`/`head`), повний — бери весь.

### Повний набір, як він стоїть у автора (перевірено 07.11.26)

45 файлів, **149,5 ГБ** бібліотеки. Разом із двома моделями (Qwen3.8 27B на 14,3 ГБ і 9B на 5,4 ГБ) — **≈170 ГБ** на диску. Плануй щонайменше 200 ГБ вільного місця, щоб лишився запас для системи й наступних оновлень.

| # | Тема | Що це | Файл | ГБ |
|---|---|---|---|---|
| 1 | Знання | Уся англійська Вікіпедія, без картинок | `wikipedia_en_all_nopic_2026-06.zim` | 52.69 |
| 2 | Знання | Уся українська Вікіпедія з картинками | `wikipedia_uk_all_maxi_2026-04.zim` | 28.16 |
| 3 | Карти | Карта Європи | `maps_en_europe_2026-08.zim` | 26.70 |
| 4 | Мова | Англійський Вікісловник | `wiktionary_en_all_nopic_2026-08.zim` | 9.16 |
| 5 | Навчання | Підручники Wikibooks, англ. | `wikibooks_en_all_maxi_2026-10.zim` | 4.74 |
| 6 | Ремонт | Електроніка: питання й відповіді | `electronics.stackexchange.com_en_all_2026-10.zim` | 4.26 |
| 7 | Ремонт | iFixit: ремонт техніки, Mac, iPhone, авто | `ifixit_en_all_2025-12.zim` | 3.57 |
| 8 | Навчання | Курси Wikiversity | `wikiversity_en_all_maxi_2026-11.zim` | 2.11 |
| 9 | Ремонт | Ремонт дому | `diy.stackexchange.com_en_all_2026-10.zim` | 2.09 |
| 10 | Виживання | Ready.gov: блекаут, мороз, ядерна загроза, евакуація | `ready.gov_en_all_2026-10.zim` | 2.06 |
| 11 | Медицина | MedlinePlus: хвороби, симптоми, ліки | `medlineplus.gov_en_all_2025-01.zim` | 1.94 |
| 12 | Медицина | WikiMed: медична Вікіпедія, англ. | `wikipedia_en_medicine_maxi_2026-10.zim` | 1.86 |
| 13 | Ремонт | Mac і iPhone: питання й відповіді | `apple.stackexchange.com_en_all_2026-10.zim` | 1.20 |
| 14 | Подорожі | Wikivoyage: путівники | `wikivoyage_en_all_maxi_2026-09.zim` | 1.07 |
| 15 | Їжа | Город і сад | `gardening.stackexchange.com_en_all_2026-10.zim` | 0.93 |
| 16 | Енергія | Energypedia: сонце, генератори, мережі | `energypedia_en_all_maxi_2026-06.zim` | 0.80 |
| 17 | Енергія | Low-tech Magazine: енергія без мережі | `solar.lowtechmagazine.com_mul_all_2025-01.zim` | 0.70 |
| 18 | Виживання | Після катастрофи: посібники | `zimgit-post-disaster_en_2024-05.zim` | 0.64 |
| 19 | Виживання | Appropedia: прості технології своїми руками | `appropedia_en_all_maxi_2026-02.zim` | 0.58 |
| 20 | Виживання | CD3WD: сільське господарство, вода, будівництво | `cd3wdproject.org_en_all_2025-11.zim` | 0.58 |
| 21 | Ремонт | Велосипед | `bicycles.stackexchange.com_en_all_2026-10.zim` | 0.50 |
| 22 | Мова | Англійська для тих, хто вчить | `ell.stackexchange.com_en_all_2026-10.zim` | 0.48 |
| 23 | Медицина | Медична Вікіпедія, укр. | `wikipedia_uk_medicine_maxi_2026-07.zim` | 0.42 |
| 24 | Музика | Музика і теорія | `music.stackexchange.com_en_all_2026-10.zim` | 0.35 |
| 25 | Ремонт | Авто: ремонт і обслуговування | `mechanics.stackexchange.com_en_all_2026-10.zim` | 0.34 |
| 26 | Їжа | Кулінарія і зберігання їжі | `cooking.stackexchange.com_en_all_2026-10.zim` | 0.24 |
| 27 | Медицина | CDC: здоров'я в подорожах, інфекції | `wwwnc.cdc.gov_en_all_2024-11.zim` | 0.18 |
| 28 | Виживання | Похід, вогонь, укриття | `outdoors.stackexchange.com_en_all_2026-10.zim` | 0.14 |
| 29 | Їжа | Gardenology: енциклопедія рослин | `gardenology.org_en_all_2026-09.zim` | 0.11 |
| 30 | Ремонт | Столярка | `woodworking.stackexchange.com_en_all_2026-10.zim` | 0.11 |
| 31 | Їжа | Приготування і консервування | `zimgit-food-preparation_en_2025-04.zim` | 0.10 |
| 32 | Тварини | Домашні тварини | `pets.stackexchange.com_en_all_2026-10.zim` | 0.09 |
| 33 | Здоров'я | Тренування, відновлення, біг | `fitness.stackexchange.com_en_all_2026-10.zim` | 0.08 |
| 34 | Мова | Український Вікісловник | `wiktionary_uk_all_nopic_2026-10.zim` | 0.08 |
| 35 | Зв'язок | Радіо й аматорський зв'язок | `ham.stackexchange.com_en_all_2026-10.zim` | 0.08 |
| 36 | Музика | Звук і запис | `sound.stackexchange.com_en_all_2026-10.zim` | 0.08 |
| 37 | Медицина | Медицина без лікаря: посібники | `zimgit-medicine_en_2024-08.zim` | 0.07 |
| 38 | Медицина | Військова медицина США | `irp.fas.org_en_military-medicine_2026-10.zim` | 0.06 |
| 39 | Медицина | Медицина: питання й відповіді | `medicalsciences.stackexchange.com_en_all_2026-10.zim` | 0.06 |
| 40 | Виживання | Вузли | `zimgit-knots_en_2024-08.zim` | 0.03 |
| 41 | Енергія | Автономне життя, економія ресурсів | `sustainability.stackexchange.com_en_all_2026-10.zim` | 0.03 |
| 42 | Навчання | Підручники Wikibooks, укр. | `wikibooks_uk_all_maxi_2026-10.zim` | 0.02 |
| 43 | Виживання | Вода: знайти, очистити, зберегти | `zimgit-water_en_2024-08.zim` | 0.02 |
| 44 | Їжа | USDA: консервування вдома | `usda-2015_en_2025-04.zim` | 0.02 |
| 45 | Медицина | NHS: довідник ліків | `nhs.uk_en_medicines_2026-09b.zim` | 0.02 |


Мова: усе англійською, крім Вікіпедії, медичної Вікіпедії, Вікісловника й Wikibooks українською. Модель відповідає українською навіть з англійських статей.

```bash
brew install aria2
mkdir -p ~/zim-incoming ~/zim-files
cp files/kiwix-list.txt ~/zim-incoming/list.txt     # або обрізаний список
cp files/refresh-library.sh ~/zim-files/ && chmod +x ~/zim-files/refresh-library.sh
files/fetch-kiwix.sh > ~/zim-incoming/fetch.log 2>&1   # качає, звіряє .sha256, переносить готове в ~/zim-files
tail -3 ~/zim-incoming/fetch.log                       # має бути «done: N moved, 0 not ready»
```

⚠️ **Не качай кнопкою в застосунку Kiwix:** у версії 3.18 вибір теки вимкнено, усе падає в «Завантаження», і модель цих файлів не побачить.
⚠️ Не качай одразу в `~/zim-files`: недокачаний файл зламає і сайт, і пошук моделі. Тому — `~/zim-incoming`, перевірка, перенос.
Обірвалось — запусти `fetch-kiwix.sh` ще раз: продовжить з місця зупинки.

## Крок 4. Сайт http://localhost:8080 з автозапуском

Читалка в браузері з пошуком по всіх файлах одразу. Програма — `kiwix-serve` з офіційного сайту:

```bash
cd /tmp && curl -LO https://download.kiwix.org/release/kiwix-tools/kiwix-tools_macos-x86_64-3.8.2.tar.gz
curl -L https://download.kiwix.org/release/kiwix-tools/kiwix-tools_macos-x86_64-3.8.2.tar.gz.md5   # звір: md5 kiwix-tools_macos-x86_64-3.8.2.tar.gz
mkdir -p ~/Applications/kiwix-tools && tar -xzf kiwix-tools_macos-x86_64-3.8.2.tar.gz --strip-components=1 -C ~/Applications/kiwix-tools
softwareupdate --install-rosetta --agree-to-license   # збірка для Intel; на Apple Silicon іде через Rosetta
~/zim-files/refresh-library.sh                        # пише ~/zim-files/library.xml
sed "s|__HOME__|$HOME|g" files/kiwix-serve.plist.template > ~/Library/LaunchAgents/local.kiwix-serve.plist
launchctl load ~/Library/LaunchAgents/local.kiwix-serve.plist
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/   # 200
```

Після кожного нового `.zim` — `~/zim-files/refresh-library.sh`; сайт підхопить сам.
Якщо агенту не дають поставити автозапуск — дай людині останні дві команди, хай запустить сама.

## Крок 5. Місток: модель → бібліотека

Модель сама `.zim` не читає. Місток — [openzim-mcp](https://github.com/cameronrye/openzim-mcp) (MIT), інструмент `zim_query`.

```bash
brew install uv
uv tool install openzim-mcp==3.4.0     # ставить ~/.local/bin/openzim-mcp
```

⚠️ Не `uvx openzim-mcp`: `uvx` щоразу лізе в інтернет по пакет і без мережі падає.
⚠️ Пошук по всіх файлах за замовчуванням має лише 20 секунд — на 45 файлах цього мало. Звідси змінна з таймаутом нижче.

## Крок 6. Підключити бібліотеку до моделі

**Bionic** (не читає `~/.lmstudio/mcp.json` — лише свої налаштування):
Settings → Integrations → MCP → «Manual MCP server setup» → «Add custom MCP»:
- Name: `wikipedia`
- Description — вставити дослівно (це інструкція для моделі, без неї мала модель вигадує):
  `Offline library (Kiwix ZIM files): Wikipedia, medicine, repair, survival, radio, gardening, textbooks. Use it for any question about facts, health, repair, cars, survival or how-to. How: 1) query='search all files for <2-4 English keywords>' (for Ukrainian topics also in Ukrainian). 2) query='get article <Path from the results>' with zim_file_path=<file from the results>; read the 1-3 best articles. 3) Answer only from what you read; if the library has nothing, say so. Name the article and file at the end.`
- Connection type: «On this computer»; Command: повний шлях `…/.local/bin/openzim-mcp` (`echo ~/.local/bin/openzim-mcp`)
- Show advanced options → Arguments: повний шлях до `~/zim-files`; Environment variables → `OPENZIM_MCP_SEARCH__SEARCH_ALL_TOTAL_TIMEOUT_SECONDS` = `120`; Request timeout — `150` секунд
- «Add MCP» → біля `wikipedia` має бути «Connected · 1 tool ready». На питання про дозвіл — «Always Allow»: інструмент лише читає файли.

Bionic зберігає це в `~/.lmstudio/apps/bionic/.internal/ng-mcp.json` (`connection.timeoutMs`). Якщо поле таймауту не приймає введення — закрий Bionic і допиши `"timeoutMs": 150000` у файл.

**Класичний LM Studio** — `~/.lmstudio/mcp.json` з повними шляхами (застосунок не бачить `PATH` з Термінала):

```json
{"mcpServers": {"wikipedia": {"command": "/Users/<ти>/.local/bin/openzim-mcp", "args": ["/Users/<ти>/zim-files"],
  "env": {"OPENZIM_MCP_SEARCH__SEARCH_ALL_TOTAL_TIMEOUT_SECONDS": "120"}}}}
```

Модель має вміти викликати інструменти: Qwen3.8 9B і 27B — вміють.

## Крок 7. Перевір без інтернету

Два тести, обидва обовʼязкові.

**а) Пісочниця (агент сам, без вимикання Wi-Fi):** модель, питання і місток запускаються в `sandbox-exec`, який забороняє будь-яке з'єднання, крім цього Mac.

```bash
brew install llama.cpp
osascript -e 'quit app "Bionic"'      # дві копії моделі в пам'яті — тісно
MODEL=~/.lmstudio/models/unsloth/Qwen3.8-27B-GGUF/Qwen3.8-27B-UD-IQ4_XS.gguf CTX=16384 \
  files/offline-test/run.sh ~/offline-test
cat ~/offline-test/network-check.txt   # google.com, 1.1.1.1 — blocked; 127.0.0.1:8080 — HTTP 200
```

Відповіді — `~/offline-test/<питання>.json` (поле `answer`), журнал з'єднань — `connections.log` (мають бути лише `127.0.0.1`).
Свої питання — допиши в `files/offline-test/questions.json`. Прочитай відповіді й перевір цифри (хлорка: 2 краплі 6 % хлорки без ароматизаторів на літр, почекати 30 хвилин; ібупрофен: до 1 200 мг на добу без рецепта).

**б) Людина (2 хвилини):** вимкнути Wi-Fi → Bionic → новий чат → «Як зупинити сильну кровотечу з руки? Знайди в бібліотеці». Відповідь має закінчуватись «Джерело: …».

## Коли інтернету немає — картка для людини

1. **Факт, інструкція, медицина** → спершу http://localhost:8080 (або Kiwix): пошук, стаття. Це першоджерело.
2. **Питання своїми словами** → Bionic, новий чат, додай «знайди в бібліотеці». Чекай: мала модель (9B) — 1–4 хвилини, велика (27B) — 10–17 хвилин. Відповідь без «Джерело: …» — проси «відкрий статтю».
3. **Дози, пропорції, час, тиск — завжди звіряй у статті**, яку назвала модель. Модель помиляється в цифрах.
4. **Рахунки** (енергія з павербанка, пропорції, рівняння) — модель робить сама і добре.
5. **Ремонт конкретної машини чи техніки** — мануалів у бібліотеці немає. Збережи PDF своїх інструкцій заздалегідь.
6. Ноутбук від павербанка/EcoFlow живе години, телефон — дні. Kiwix є і на телефоні: поклади туди медичний мінімум (~5 ГБ).

## Чого в Kiwix немає

- Окремих книжок про худобу й ферму — лише загальні статті. Найповніше — Survivor Library (`survivorlibrary.com_en_all`, ~220 ГБ старих практичних книжок, переважно для читання людиною); ставити лише, якщо є стільки місця.
- Мануалів на конкретні машини й техніку — зберігайте свої PDF заздалегідь.

## Підтримка

- Раз на місяць — перевірити, чи вийшла сильніша модель під твою пам'ять (Artificial Analysis Intelligence Index), поставити, прогнати крок 7а, стару — в Кошик.
- Раз на квартал — новіші `.zim` на download.kiwix.org; міняти, якщо новіший щонайменше на 3 місяці.
- Друга копія `~/zim-files` на зовнішній диск: `rsync -a ~/zim-files/ /Volumes/<диск>/zim-files/`.

## Не Mac

- **Windows / Linux:** LM Studio (є для обох), Kiwix Desktop або `kiwix-serve` (`kiwix-tools_win-x86_64-*.zip`, `kiwix-tools_linux-*` на download.kiwix.org), `uv tool install openzim-mcp==3.4.0`, підключення через `mcp.json` LM Studio.
- Пісочниці `sandbox-exec` там немає: тест — відключити мережу на рівні ОС і спитати модель.
- Автозапуск: Windows — «Планувальник завдань» на вхід, Linux — `systemd --user` сервіс.

## На що ми вже наступили

| Що | Як правильно |
|---|---|
| Кнопка завантаження в Kiwix кладе все в «Завантаження» | aria2 за списком у `~/zim-incoming`, перевірка, перенос |
| `uvx openzim-mcp` без мережі падає | `uv tool install`, повний шлях до `~/.local/bin/openzim-mcp` |
| Bionic не бачить `~/.lmstudio/mcp.json` | Settings → Integrations → MCP → Add custom MCP |
| Bionic обриває виклик через 60 с | Request timeout 150 с + змінна 120 с |
| Мала модель читає лише уривки пошуку й вигадує | інструкція «знайди → відкрий статтю → відповідай з прочитаного» в описі інструмента |
| Український пошук бачить лише точну форму слова | шукати англійською або 2–3 формами слова |
| `aria2c` зберіг модель під хеш-іменем | `-o <ім'я файлу>` |
| 27B повзе | закрити браузер і важкі програми: модель має вміститись у пам'ять без swap |
