"""peace.py – DrawGenerator that renders "peace" in ~200 languages on a 1920×1080 canvas.

Word list spans majority languages, indigenous North/South American, Asian,
Australian/Oceanic, African, and European minority languages, with native scripts
where a Unicode font covers them.

Font priority (first available wins per script group):
  Latin/extended  → NotoSans, DejaVuSans, FreeSans, Liberation Sans, Arial
  CJK             → NotoSansCJK, WenQuanYi, AR PL UMing
  Arabic/Hebrew   → NotoSansArabic, NotoSansHebrew, FreeMono
  Devanagari      → NotoSansDevanagari, Lohit Devanagari
  Thai            → NotoSansThai, Garuda
  Korean          → NotoSansCJKkr, UnDotum
  Tifinagh/Ge'ez  → NotoSansTifinagh, NotoSansEthiopic
  Fallback        → any found Latin font
"""

from __future__ import annotations

import os
import random
import math
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

from .drawGenerator import DrawGenerator

# ──────────────────────────────────────────────────────────────────────────────
# DATA: (word, language_label, script_hint)
# script_hint keys: latin, cjk, arabic, hebrew, devanagari, thai, korean,
#                   georgian, armenian, ethiopic, tifinagh, sinhala, tibetan,
#                   myanmar, khmer, tamil, telugu, kannada, malayalam, bengali,
#                   gujarati, gurmukhi, cherokee, canadian_syllabics, cyrillic
# ──────────────────────────────────────────────────────────────────────────────
PEACE_WORDS: list[tuple[str, str, str]] = [
    # ── Major world languages ──
    ("Peace",           "English",          "latin"),
    ("Paz",             "Spanish",          "latin"),
    ("Paix",            "French",           "latin"),
    ("Frieden",         "German",           "latin"),
    ("Pace",            "Italian",          "latin"),
    ("Paz",             "Portuguese",       "latin"),
    ("Мир",             "Russian",          "cyrillic"),
    ("和平",             "Mandarin",         "cjk"),
    ("平和",             "Japanese",         "cjk"),
    ("평화",             "Korean",           "korean"),
    ("शांति",           "Hindi",            "devanagari"),
    ("سلام",            "Arabic",           "arabic"),
    ("שָׁלוֹם",          "Hebrew",           "hebrew"),
    ("Barış",           "Turkish",          "latin"),
    ("สันติภาพ",         "Thai",             "thai"),
    ("Hòa bình",        "Vietnamese",       "latin"),
    ("শান্তি",           "Bengali",          "bengali"),
    ("ਸ਼ਾਂਤੀ",           "Punjabi",          "gurmukhi"),
    ("శాంతి",           "Telugu",           "telugu"),
    ("சமாதானம்",         "Tamil",            "tamil"),
    ("ಶಾಂತಿ",           "Kannada",          "kannada"),
    ("സമാധാനം",          "Malayalam",        "malayalam"),
    ("Pokój",           "Polish",           "latin"),
    ("Mír",             "Czech",            "latin"),
    ("Мир",             "Serbian",          "cyrillic"),
    ("Mir",             "Croatian",         "latin"),
    ("Béke",            "Hungarian",        "latin"),
    ("Vrede",           "Dutch",            "latin"),
    ("Fred",            "Swedish",          "latin"),
    ("Fred",            "Norwegian",        "latin"),
    ("Fred",            "Danish",           "latin"),
    ("Rahu",            "Finnish",          "latin"),
    ("Rahu",            "Estonian",         "latin"),
    ("Мир",             "Ukrainian",        "cyrillic"),
    ("Мір",             "Belarusian",       "cyrillic"),
    ("Mier",            "Slovak",           "latin"),
    ("Mir",             "Slovenian",        "latin"),
    ("Мир",             "Bulgarian",        "cyrillic"),
    ("Paqe",            "Albanian",         "latin"),
    ("Paqja",           "Albanian (Gheg)",  "latin"),
    ("Ειρήνη",          "Greek",            "greek"),
    ("Paçe",            "Romanian",         "latin"),
    ("Pace",            "Latin",            "latin"),
    ("Llonydd",         "Welsh",            "latin"),
    ("Síocháin",        "Irish",            "latin"),
    ("Sìth",            "Scottish Gaelic",  "latin"),
    ("Peoc'h",          "Breton",           "latin"),
    ("Bakea",           "Basque",           "latin"),
    ("Pau",             "Catalan",          "latin"),
    ("Bake",            "Basque",           "latin"),
    ("Мир",             "Macedonian",       "cyrillic"),
    ("Pax",             "Galician",         "latin"),
    ("Barış",           "Azerbaijani",      "latin"),
    ("Тынчтык",         "Kyrgyz",           "cyrillic"),
    ("Tinchlik",        "Uzbek",            "latin"),
    ("Мир",             "Kazakh",           "cyrillic"),
    ("Parahatçylyk",    "Turkmen",          "latin"),
    ("ሰላም",             "Amharic",          "ethiopic"),
    ("Мир",             "Tajik",            "cyrillic"),
    ("صلح",             "Persian/Farsi",    "arabic"),
    ("سکون",            "Urdu",             "arabic"),
    ("آشتی",            "Dari",             "arabic"),
    ("ژیان",            "Kurdish (Kurmanji)","arabic"),
    ("Aşitî",           "Kurdish (Sorani)", "latin"),
    ("Rongo",           "Maori",            "latin"),
    ("Maluhia",         "Hawaiian",         "latin"),
    ("Aloha",           "Hawaiian (love/peace)", "latin"),
    ("Kapayapaan",      "Filipino/Tagalog", "latin"),
    ("Kalinaw",         "Cebuano",          "latin"),
    ("Damai",           "Malay",            "latin"),
    ("Damai",           "Indonesian",       "latin"),
    ("ສັນຕິພາບ",         "Lao",              "lao"),
    ("សន្តិភាព",         "Khmer",            "khmer"),
    ("ငြိမ်းချမ်းရေး",   "Burmese",          "myanmar"),
    ("བདེ་གཞིས།",        "Tibetan",          "tibetan"),
    ("གཞིས་བདེ།",        "Dzongkha",         "tibetan"),
    ("ශාන්තිය",          "Sinhala",          "sinhala"),
    ("ᐊᓯᖏᑦ",            "Inuktitut",        "canadian_syllabics"),
    ("Wolakota",        "Lakota",           "latin"),
    ("Hozho",           "Navajo (Diné)",    "latin"),
    ("Wetaskiwin",      "Cree",             "latin"),
    ("Kizhaay",         "Ojibwe",           "latin"),
    ("Kanenhí:io",      "Mohawk",           "latin"),
    ("Skén:nen",        "Oneida",           "latin"),
    ("Skennen",         "Seneca",           "latin"),
    ("ᏙᏯ",             "Cherokee",         "cherokee"),
    ("Tohono",          "O'odham",          "latin"),
    ("Kʼéʼ",           "Navajo clan peace","latin"),
    ("Hopi Nahongvita", "Hopi",             "latin"),
    ("Alafia",          "Yoruba",           "latin"),
    ("Ukweli",          "Swahili",          "latin"),
    ("Amani",           "Swahili",          "latin"),
    ("Khotso",          "Sotho",            "latin"),
    ("Ukuthula",        "Zulu",             "latin"),
    ("Uxolo",           "Xhosa",            "latin"),
    ("Kagiso",          "Tswana",           "latin"),
    ("Bérété",          "Bambara",          "latin"),
    ("Jàmm",            "Wolof",            "latin"),
    ("An laafia",       "Hausa",            "latin"),
    ("Onye udo",        "Igbo",             "latin"),
    ("Asomdwee",        "Twi/Akan",         "latin"),
    ("Afia",            "Fante",            "latin"),
    ("Layeen",          "Somali",           "latin"),
    ("Nagaya",          "Tigrinya",         "ethiopic"),
    ("Fihavanana",      "Malagasy",         "latin"),
    ("Fiadanana",       "Malagasy (also)",  "latin"),
    ("ⴰⵎⵓⵏ",            "Tamazight/Berber", "tifinagh"),
    ("Aglif",           "Tachelhit",        "latin"),
    ("Tazenka",         "Tachelhit (alt)",  "latin"),
    ("Wukro",           "Tigre",            "ethiopic"),
    ("Salama",          "Lingala",          "latin"),
    ("Kimya",           "Swahili (also)",   "latin"),
    ("Raha",            "Swahili (also 2)", "latin"),
    ("Enkoben",         "Somali (also)",    "latin"),
    ("Bann",            "Bambara (calm)",   "latin"),
    # ── Indigenous Americas ──
    ("Pakta",           "Quechua",          "latin"),
    ("Iyo'",            "Guaraní",          "latin"),
    ("Ixy'",            "Kiche' Maya",      "latin"),
    ("Lekil kuxlejal",  "Tzotzil Maya",     "latin"),
    ("Q'anil",          "Mam Maya",         "latin"),
    ("Nahnkamaw",       "Nahuatl",          "latin"),
    ("Nemiliztli",      "Nahuatl (peace)",  "latin"),
    ("Neltiliztli",     "Nahuatl (truth)",  "latin"),
    ("Simi",            "Aymara",           "latin"),
    ("Yanapa",          "Aymara (help)",    "latin"),
    ("Ayni",            "Quechua (reciprocity)", "latin"),
    ("Teko marana'ey",  "Guaraní (also)",   "latin"),
    ("Wixáritari",      "Huichol/Wixáritari","latin"),
    ("Lemaruri",        "Rarámuri/Tarahumara","latin"),
    ("Paxaral",         "Yucatec Maya",     "latin"),
    ("Hózhó",           "Diné (Navajo)",    "latin"),
    ("Nizhóní",         "Diné (beauty)",    "latin"),
    ("Miyo-wîcêhtowin", "Plains Cree",      "latin"),
    ("Wîcêhtowin",      "Woods Cree",       "latin"),
    ("Kâ-pimâcihoyan",  "Cree (living well)","latin"),
    ("Mino-Bimaadiziwin","Anishinaabe",      "latin"),
    ("Minobimaatisiiwin","Ojibwe (good life)","latin"),
    ("Gadagwi",         "Oneida (also)",    "latin"),
    ("Nekwisa",         "Lenape",           "latin"),
    ("Nematak",         "Lenape (also)",    "latin"),
    ("Kici-asotamâtowin","Cree (promise)",   "latin"),
    ("Ayiwak",          "Cree (enough)",    "latin"),
    ("Taino areyto",    "Taíno",            "latin"),
    ("Biabani",         "Mapuche",          "latin"),
    ("Küme mongen",     "Mapuche (good life)","latin"),
    ("Nehuen",          "Mapuche (strength)","latin"),
    ("Sumak Kawsay",    "Kichwa",           "latin"),
    ("Suma Qamaña",     "Aymara (full life)","latin"),
    ("Kametsa asaiki",  "Asháninka",        "latin"),
    ("Jori",            "Shipibo-Conibo",   "latin"),
    ("Mura",            "Tikuna",           "latin"),
    ("Yupora",          "Yanomami",         "latin"),
    ("Aweti",           "Xingu",            "latin"),
    ("Tekoa porã",      "Guaraní Kaiowá",   "latin"),
    ("Ka'i",            "Munduruku",        "latin"),
    # ── Pacific / Oceania ──
    ("Maluhia",         "Hawaiian",         "latin"),
    ("Filemu",          "Samoan",           "latin"),
    ("Melino",          "Tongan",           "latin"),
    ("Nofo mālie",      "Niuean",           "latin"),
    ("Mālohi",          "Fijian",           "latin"),
    ("Bula",            "Fijian (life/peace)","latin"),
    ("Fakaalofa",       "Niuean",           "latin"),
    ("Ofa",             "Tongan (love)",    "latin"),
    ("Alofa",           "Samoan (love)",    "latin"),
    ("Aroha",           "Maori (love/peace)","latin"),
    ("Fakalofa lahi atu","Niuean greeting", "latin"),
    ("Haumaru",         "Cook Island Maori","latin"),
    ("Noa",             "Tahitian",         "latin"),
    ("Ia ora na",       "Tahitian greeting","latin"),
    ("Meitaki",         "Cook Island",      "latin"),
    ("Talofa",          "Samoan greeting",  "latin"),
    ("Kia ora",         "Maori greeting",   "latin"),
    ("Tēnā koe",        "Maori (peace)",    "latin"),
    ("Mauri",           "Maori (life force)","latin"),
    ("Mauri ora",       "Maori (well-being)","latin"),
    # ── Australian Aboriginal ──
    ("Yaama",           "Gamilaraay",       "latin"),
    ("Murra",           "Wiradjuri",        "latin"),
    ("Palya",           "Pitjantjatjara",   "latin"),
    ("Yuwa",            "Arrernte",         "latin"),
    ("Mabo",            "Meriam",           "latin"),
    ("Dili",            "Yolŋu",            "latin"),
    ("Yo",              "Bininj Kunwok",    "latin"),
    ("Liyan",           "Nyoongar",         "latin"),
    ("Warray",          "Lardil",           "latin"),
    ("Dungala",         "Bangerang",        "latin"),
    # ── Central / East Asia additional ──
    ("Энх тайван",      "Mongolian",        "cyrillic"),
    ("Мир",             "Chechen",          "cyrillic"),
    ("Мир",             "Ingush",           "cyrillic"),
    ("ამანი",           "Georgian",         "georgian"),
    ("Խաղաղություն",    "Armenian",         "armenian"),
    ("Sulh",            "Uyghur",           "arabic"),
    ("བདེ་བ།",           "Tibetan (calm)",   "tibetan"),
    ("和",               "Classical Chinese","cjk"),
    ("平",               "Chinese (peace)",  "cjk"),
    ("安",               "Japanese (peace)", "cjk"),
    ("靜",               "Chinese (quiet)",  "cjk"),
    ("寧",               "Chinese (tranquil)","cjk"),
    ("泰",               "Chinese (serene)", "cjk"),
    ("恬",               "Chinese (still)",  "cjk"),
    ("穩",               "Chinese (stable)", "cjk"),
    # ── South / SE Asia additional ──
    ("ສງົ",             "Lao",              "lao"),
    ("Shánti",          "Sanskrit",         "devanagari"),
    ("शान्तिः",          "Sanskrit (formal)","devanagari"),
    ("अमन",             "Hindi (also)",     "devanagari"),
    ("ঐক্য",            "Bengali",          "bengali"),
    ("Shanti",          "Nepali",           "devanagari"),
    ("शान्ति",           "Nepali",           "devanagari"),
    ("Shanti",          "Marathi",          "devanagari"),
    ("शांती",           "Marathi",          "devanagari"),
    ("Shaanti",         "Maithili",         "devanagari"),
    ("Santipheap",      "Khmer",            "latin"),
    ("Santi",           "Balinese",         "latin"),
    ("Tentrem",         "Javanese",         "latin"),
    ("Ketentreman",     "Sundanese",        "latin"),
    ("Katenteraman",    "Javanese (also)",  "latin"),
    ("Kedamaian",       "Indonesian (lit)", "latin"),
    ("Rahang",          "Batak Toba",       "latin"),
    ("Sasabi",          "Nias",             "latin"),
    # ── European minority ──
    ("Pax",             "Occitan",          "latin"),
    ("Bake",            "Basque",           "latin"),
    ("Cadernag",        "Cornish",          "latin"),
    ("Séréni",          "Sardinian",        "latin"),
    ("Miar",            "Aromanian",        "latin"),
    ("Mir",             "Sorbian (Upper)",  "latin"),
    ("Friede",          "Low German",       "latin"),
    ("Vred",            "Afrikaans",        "latin"),
    ("Fryd",            "Faroese",          "latin"),
    ("Friður",          "Icelandic",        "latin"),
    ("Rauha",           "Finnish",          "latin"),
    ("Rahue",           "Karelian",         "latin"),
    ("Rahu",            "Võro",             "latin"),
    ("Mier",            "Limburgish",       "latin"),
    ("Vrede",           "Flemish",          "latin"),
    ("Frieden",         "Alemannic",        "latin"),
    ("Friede",          "Plattdeutsch",     "latin"),
    ("Szimat",          "Romani",           "latin"),
    # ── Middle East / Caucasus ──
    ("Sülh",            "Azerbaijani",      "latin"),
    ("Asayiş",          "Zazaki",           "latin"),
    ("Israfil",         "Lezgian",          "latin"),
    ("Sulhu",           "Avar",             "latin"),
    ("Мир",             "Ossetian",         "cyrillic"),
    # ── Africa additional ──
    ("Salama",          "Malagasy (also 2)","latin"),
    ("Umoja",           "Swahili (unity)",  "latin"),
    ("Ubuntu",          "Nguni (humanity)", "latin"),
    ("Ukweli",          "Swahili (truth)",  "latin"),
    ("Nzere",           "Kongo",            "latin"),
    ("Biso",            "Lingala (also)",   "latin"),
    ("Imani",           "Swahili (faith)",  "latin"),
    ("Baraka",          "Swahili (blessing)","latin"),
    ("Furaha",          "Swahili (joy)",    "latin"),
    ("Heri",            "Swahili (blessed)","latin"),
    ("Zawadi",          "Swahili (gift)",   "latin"),
    ("Tumaini",         "Swahili (hope)",   "latin"),
    ("Muungano",        "Swahili (union)",  "latin"),
    ("Salama",          "Hausa (also)",     "latin"),
    ("Walama",          "Fula",             "latin"),
    ("Jama",            "Fula (peace)",     "latin"),
    ("Hankuri",         "Hausa (patience)", "latin"),
    ("Lumana",          "Hausa (goodwill)", "latin"),
    ("Sanu",            "Hausa (greeting)", "latin"),
    ("Alafia",          "Yoruba (wellbeing)","latin"),
    ("Iṣọkan",          "Yoruba (unity)",   "latin"),
    ("Égbé",            "Yoruba (together)","latin"),
]

# ──────────────────────────────────────────────────────────────────────────────
# FONT SEARCH PATHS
# ──────────────────────────────────────────────────────────────────────────────
_FONT_SEARCH_DIRS: list[str] = [
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/Library/Fonts"),
    "/Library/Fonts",
    "/System/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
    os.path.expanduser("~/.fonts"),
]

# script → ordered list of font filename substrings (case-insensitive)
_SCRIPT_FONT_PREFS: dict[str, list[str]] = {
    "latin":             ["NotoSans-Regular", "NotoSans_Condensed", "DejaVuSans",
                          "FreeSans", "LiberationSans", "Arial", "Helvetica",
                          "Ubuntu-R", "FiraSans-Regular", "OpenSans-Regular"],
    "cyrillic":          ["NotoSans-Regular", "DejaVuSans", "FreeSerif",
                          "FreeSans", "Liberation"],
    "cjk":               ["NotoSansCJK", "NotoSerifCJK", "WenQuanYi",
                          "AR PL UMing", "DroidSansFallback"],
    "korean":            ["NotoSansCJKkr", "NotoSansCJK", "UnDotum", "NanumGothic"],
    "arabic":            ["NotoSansArabic", "NotoNaskhArabic", "FreeMono",
                          "Amiri", "ScheherazadeNew"],
    "hebrew":            ["NotoSansHebrew", "NotoSerifHebrew", "FreeSerif",
                          "David", "Miriam"],
    "devanagari":        ["NotoSansDevanagari", "Lohit-Devanagari", "FreeSans",
                          "Nakula", "Gargi"],
    "bengali":           ["NotoSansBengali", "Lohit-Bengali", "FreeSans"],
    "gurmukhi":          ["NotoSansGurmukhi", "Lohit-Gurmukhi"],
    "telugu":            ["NotoSansTelugu", "Lohit-Telugu", "Pothana2000"],
    "tamil":             ["NotoSansTamil", "Lohit-Tamil", "FreeSans"],
    "kannada":           ["NotoSansKannada", "Lohit-Kannada"],
    "malayalam":         ["NotoSansMalayalam", "Lohit-Malayalam"],
    "gujarati":          ["NotoSansGujarati", "Lohit-Gujarati"],
    "thai":              ["NotoSansThai", "Garuda", "Norasi"],
    "lao":               ["NotoSansLao", "Phetsarath"],
    "khmer":             ["NotoSansKhmer", "Khmer OS"],
    "myanmar":           ["NotoSansMyanmar", "Padauk", "Myanmar3"],
    "tibetan":           ["NotoSansTibetan", "Jomolhari", "TibetanMachineUni"],
    "sinhala":           ["NotoSansSinhala", "Lklug", "LKLUG"],
    "georgian":          ["NotoSansGeorgian", "DejaVuSans", "FreeSerif"],
    "armenian":          ["NotoSansArmenian", "DejaVuSans", "FreeSerif"],
    "ethiopic":          ["NotoSansEthiopic", "Abyssinica", "Ethiopia Jiret"],
    "tifinagh":          ["NotoSansTifinagh", "DejaVuSans"],
    "cherokee":          ["NotoSansCherokee", "Plantagenet Cherokee",
                          "Digohweli", "DejaVuSans"],
    "canadian_syllabics":["NotoSansCanadianAboriginal", "OjibweSyllabics",
                          "Aboriginal Serif"],
    "greek":             ["NotoSans-Regular", "DejaVuSans", "FreeSerif", "FreeSans"],
}

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_NOTO_FONT_URLS: dict[str, str] = {
    "NotoSans-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
    "NotoSansCJKsc-Regular.otf":
        "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf",
    "NotoSansArabic-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf",
    "NotoSansHebrew-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf",
    "NotoSansDevanagari-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf",
    "NotoSansBengali-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansBengali/NotoSansBengali-Regular.ttf",
    "NotoSansThai-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansThai/NotoSansThai-Regular.ttf",
    "NotoSansTelugu-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTelugu/NotoSansTelugu-Regular.ttf",
    "NotoSansTamil-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf",
    "NotoSansKannada-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Regular.ttf",
    "NotoSansMalayalam-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansMalayalam/NotoSansMalayalam-Regular.ttf",
    "NotoSansGurmukhi-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansGurmukhi/NotoSansGurmukhi-Regular.ttf",
    "NotoSansGeorgian-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansGeorgian/NotoSansGeorgian-Regular.ttf",
    "NotoSansArmenian-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArmenian/NotoSansArmenian-Regular.ttf",
    "NotoSansEthiopic-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansEthiopic/NotoSansEthiopic-Regular.ttf",
    "NotoSansTifinagh-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTifinagh/NotoSansTifinagh-Regular.ttf",
    "NotoSansMyanmar-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansMyanmar/NotoSansMyanmar-Regular.ttf",
    "NotoSansKhmer-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKhmer/NotoSansKhmer-Regular.ttf",
    "NotoSansTibetan-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTibetan/NotoSansTibetan-Regular.ttf",
    "NotoSansSinhala-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansSinhala/NotoSansSinhala-Regular.ttf",
    "NotoSansCherokee-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansCherokee/NotoSansCherokee-Regular.ttf",
    "NotoSansCanadianAboriginal-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansCanadianAboriginal/NotoSansCanadianAboriginal-Regular.ttf",
    "NotoSansLao-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansLao/NotoSansLao-Regular.ttf",
    "NotoSansGujarati-Regular.ttf":
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansGujarati/NotoSansGujarati-Regular.ttf",
}

_FONT_CACHE_DIR: str = os.path.join(
    os.path.expanduser("~"), ".cache", "screenart_fonts"
)


def _ensure_fonts_cached(log: Optional[object] = None) -> None:
    """Download any missing Noto fonts to the local cache dir."""
    import urllib.request
    os.makedirs(_FONT_CACHE_DIR, exist_ok=True)
    for fname, url in _NOTO_FONT_URLS.items():
        dest = os.path.join(_FONT_CACHE_DIR, fname)
        if os.path.exists(dest):
            continue
        try:
            if log:
                log.debug(f"Peace: downloading {fname} …")  # type: ignore[union-attr]
            urllib.request.urlretrieve(url, dest)
        except Exception as e:
            if log:
                log.debug(f"Peace: could not download {fname}: {e}")  # type: ignore[union-attr]


def _find_fonts() -> dict[str, list[str]]:
    """Walk font dirs (system + cache) once; return dict of {script: [path, ...]}."""
    search_dirs = _FONT_SEARCH_DIRS + [_FONT_CACHE_DIR]
    all_ttf: list[str] = []
    for d in search_dirs:
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith((".ttf", ".otf")):
                        all_ttf.append(os.path.join(root, f))

    result: dict[str, list[str]] = {}
    for script, prefs in _SCRIPT_FONT_PREFS.items():
        found: list[str] = []
        for pref in prefs:
            pref_lower = pref.lower()
            matches = [p for p in all_ttf
                       if pref_lower in os.path.basename(p).lower()]
            found.extend(m for m in matches if m not in found)
        # Fallback: any Noto or DejaVu font for scripts without dedicated fonts
        if not found:
            found = [p for p in all_ttf
                     if "notosans" in p.lower() or "dejavusans" in p.lower()
                     or "liberation" in p.lower()]
        result[script] = found
    return result


# ── Module-level singletons (initialised once at import time) ─────────────────
_dummy_img  = Image.new("RGB", (1, 1))
_dummy_draw = ImageDraw.Draw(_dummy_img)

_FONT_MAP: dict[str, list[str]] | None = None

def _get_font_map() -> dict[str, list[str]]:
    """Return the font map, scanning the filesystem only on the first call."""
    global _FONT_MAP
    if _FONT_MAP is None:
        _FONT_MAP = _find_fonts()
    return _FONT_MAP


@lru_cache(maxsize=256)
def _load_font(path: str, size: int) -> Optional[ImageFont.FreeTypeFont]:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return None


def _text_bbox(draw: ImageDraw.ImageDraw,
               text: str,
               font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    """Return (width, height) of rendered text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wcag_contrast(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    """WCAG 2.1 contrast ratio between two sRGB colours."""
    def rel_lum(c: tuple[int, int, int]) -> float:
        vals = []
        for ch in c:
            s = ch / 255.0
            vals.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
        return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]
    l1, l2 = rel_lum(c1), rel_lum(c2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


# ──────────────────────────────────────────────────────────────────────────────
# Colour themes
# Each theme has ONE background and a curated fg_pool where every colour has
# WCAG contrast ≥ 4.5 against the background (AA level for normal text).
# Words randomly sample from the fg_pool so each image has multi-colour text
# on a single coherent background.
# ──────────────────────────────────────────────────────────────────────────────
_BG_THEMES: list[dict] = [
    {   # Deep navy night sky
        "name": "night",
        "bg":  (8, 12, 35),
        "fg_pool": [
            (255, 225, 100),   # warm gold
            (200, 240, 255),   # ice blue
            (180, 255, 185),   # mint
            (255, 160, 205),   # rose
            (210, 185, 255),   # lavender
            (255, 255, 255),   # white
            (255, 200, 140),   # peach
            (140, 255, 220),   # aquamarine
        ],
    },
    {   # Dark plum / dusk purple
        "name": "dusk",
        "bg":  (38, 16, 58),
        "fg_pool": [
            (255, 215, 80),    # golden
            (255, 255, 165),   # pale yellow
            (195, 255, 225),   # seafoam
            (255, 190, 255),   # pink-violet
            (200, 225, 255),   # periwinkle
            (255, 255, 255),   # white
            (255, 175, 120),   # warm coral
            (160, 255, 200),   # spring green
        ],
    },
    {   # Warm parchment / aged paper
        "name": "parchment",
        "bg":  (230, 215, 178),
        "fg_pool": [
            (70,  35,   5),    # dark umber
            (35,  55,  105),   # navy
            (110, 18,  18),    # deep crimson
            (20,  75,  38),    # forest green
            (75,  40, 110),    # purple
            (10,  10,  10),    # near-black
            (100, 55,   0),    # brown
            (40,  80,  90),    # teal dark
        ],
    },
    {   # Deep ocean blue
        "name": "ocean",
        "bg":  (14, 52, 98),
        "fg_pool": [
            (200, 242, 255),   # sky blue
            (255, 242, 155),   # pale yellow
            (175, 255, 205),   # sea foam
            (255, 205, 160),   # peach
            (255, 255, 255),   # white
            (225, 220, 255),   # lilac
            (255, 225, 100),   # warm gold
            (150, 255, 245),   # cyan
        ],
    },
    {   # Dark forest green
        "name": "forest",
        "bg":  (14, 44, 22),
        "fg_pool": [
            (205, 255, 155),   # lime
            (255, 242, 100),   # yellow
            (255, 205, 175),   # salmon
            (200, 242, 255),   # ice
            (255, 255, 255),   # white
            (255, 225, 100),   # amber
            (255, 180, 230),   # pink
            (175, 235, 210),   # mint
        ],
    },
    {   # Golden sunrise / amber
        "name": "sunrise",
        "bg":  (215, 148, 30),
        "fg_pool": [
            (15,  15,  15),    # near-black
            (20,  35, 110),    # deep navy
            (85,  12,  12),    # deep crimson
            (8,   55,  28),    # dark green
            (55,  15,  95),    # dark violet
            (10,  45,  60),    # dark teal
            (80,  35,   0),    # dark brown
            (55,  20,  45),    # dark maroon
        ],
    },
    {   # Slate blue-grey
        "name": "slate",
        "bg":  (42, 58, 72),
        "fg_pool": [
            (255, 242, 175),   # warm cream
            (195, 255, 228),   # seafoam
            (255, 205, 200),   # blush
            (200, 222, 255),   # cornflower
            (255, 255, 255),   # white
            (255, 222, 118),   # gold
            (205, 255, 165),   # yellow-green
            (255, 180, 140),   # peach
        ],
    },
    {   # Bright chalk / white
        "name": "chalk",
        "bg":  (245, 248, 252),
        "fg_pool": [
            (35,  38, 125),    # royal blue
            (120, 22,  22),    # crimson
            (22,  95,  52),    # emerald
            (78,  42, 125),    # grape
            (105, 62,   5),    # ochre
            (8,   8,    8),    # near-black
            (130, 28,  85),    # magenta
            (18,  78,  98),    # dark cyan
        ],
    },
    {   # Dark ember / deep red-brown
        "name": "ember",
        "bg":  (52, 12, 4),
        "fg_pool": [
            (255, 188,  78),   # amber
            (255, 225, 158),   # pale gold
            (255, 255, 205),   # cream
            (255, 148, 100),   # coral
            (255, 205,  80),   # yellow-gold
            (255, 255, 255),   # white
            (200, 228, 255),   # cool blue
            (215, 255, 195),   # pale green
        ],
    },
    {   # Soft lavender / lilac
        "name": "lavender",
        "bg":  (192, 182, 228),
        "fg_pool": [
            (52,  15,  78),    # deep purple
            (15,  35, 105),    # navy
            (78,  14,  28),    # dark rose
            (12,  68,  42),    # dark green
            (92,  52,   5),    # dark amber
            (8,   8,    8),    # near-black
            (38,  18,  88),    # indigo
            (55,  45,   5),    # dark olive
        ],
    },
    {   # Charcoal / near-black
        "name": "charcoal",
        "bg":  (22, 22, 26),
        "fg_pool": [
            (255, 212,  80),   # gold
            (98,  210, 255),   # azure
            (118, 255, 178),   # spring green
            (255, 128, 178),   # hot pink
            (178, 148, 255),   # violet
            (255, 255, 255),   # white
            (255, 165,  80),   # tangerine
            (80,  255, 228),   # turquoise
        ],
    },
    {   # Terracotta / clay — all light fg on mid-dark terracotta
        "name": "terracotta",
        "bg":  (170, 78, 42),
        "fg_pool": [
            (255, 248, 215),   # cream
            (255, 255, 255),   # white
            (255, 255, 210),   # pale yellow
            (220, 252, 255),   # ice blue
            (200, 252, 210),   # pale mint
            (255, 248, 255),   # pale violet
            (252, 255, 200),   # lime cream
            (255, 242, 148),   # warm yellow
        ],
    },
    {   # Midnight teal
        "name": "teal_dark",
        "bg":  (8, 48, 52),
        "fg_pool": [
            (255, 232, 100),   # gold
            (255, 255, 210),   # cream
            (255, 195, 155),   # peach
            (215, 255, 248),   # ice teal
            (255, 255, 255),   # white
            (255, 170, 215),   # pink
            (215, 255, 165),   # lime
            (205, 210, 255),   # periwinkle
        ],
    },
    {   # Old rose / dusty mauve (dark)
        "name": "rose_dark",
        "bg":  (88, 28, 48),
        "fg_pool": [
            (255, 228, 155),   # pale gold
            (255, 255, 210),   # cream
            (195, 248, 255),   # ice blue
            (215, 255, 195),   # mint
            (255, 205, 248),   # blush
            (255, 255, 255),   # white
            (255, 190,  95),   # amber
            (195, 215, 255),   # periwinkle
        ],
    },
    {   # Sage / olive green (light)
        "name": "sage",
        "bg":  (195, 208, 178),
        "fg_pool": [
            (28,  45,  12),    # dark green
            (52,  28,  88),    # dark purple
            (95,  18,  18),    # dark red
            (22,  55,  80),    # dark blue
            (88,  52,   8),    # dark brown
            (8,   8,    8),    # near-black
            (55,  18,  52),    # dark maroon
            (12,  62,  55),    # dark teal
        ],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Generator
# ──────────────────────────────────────────────────────────────────────────────
class Peace(DrawGenerator):
    """Renders the word 'peace' in num_words languages on a 1920×1080 canvas."""

    WIDTH  = 1920
    HEIGHT = 1080

    def __init__(self, out_dir: str):
        super().__init__(out_dir)

        self.file_count = self.config.get("file_counts", {}).get("peace", 4)
        self.num_words = random.randint(12, 108) 

        self.log.debug("Peace: ensuring Noto fonts …")
        _ensure_fonts_cached(self.log)
        self.log.debug("Peace: scanning fonts …")
        self._font_map: dict[str, list[str]] = _get_font_map()
        total = sum(len(v) for v in self._font_map.values())
        self.log.debug(f"Peace: {total} font paths indexed")

    # ── internal helpers ──────────────────────────────────────────────────────

    def _get_font(self, script: str, size: int) -> ImageFont.FreeTypeFont:
        """Return best available font for script at given size."""
        paths = self._font_map.get(script, [])
        if not paths:
            paths = self._font_map.get("latin", [])
        for p in paths:
            f = _load_font(p, size)
            if f is not None:
                return f
        # absolute fallback: PIL default (no size control but never raises)
        return ImageFont.load_default()

    def _pick_font_size(self, text: str, script: str,
                        max_w: int, max_h: int,
                        min_size: int = 12, max_size: int = 120) -> tuple[ImageFont.FreeTypeFont, int, int]:

        """Binary-search the largest font sze that fits within max_w × max_h."""
        lo, hi = min_size, max_size
        best_font = self._get_font(script, lo)
        best_w, best_h = _text_bbox(_dummy_draw, text, best_font)
        while lo < hi:
            mid  = (lo + hi + 1) // 2
            font = self._get_font(script, mid)
            tw, th = _text_bbox(_dummy_draw, text, font)
            if tw <= max_w and th <= max_h:
                lo, best_font, best_w, best_h = mid, font, tw, th
            else:
                hi = mid - 1
        return best_font, best_w, best_h

    def _make_canvas(self, theme: dict) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img  = Image.new("RGB", (self.WIDTH, self.HEIGHT), theme["bg"])
        draw = ImageDraw.Draw(img)
        return img, draw

    def _subtle_texture(self, img: Image.Image, theme: dict) -> Image.Image:
        """Add very faint noise to background to avoid flat look."""
        import numpy as np
        arr = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, 4, arr.shape).astype(np.float32)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    # ── main render ───────────────────────────────────────────────────────────

    def _render_one(self, idx: int) -> None:
        theme    = random.choice(_BG_THEMES)
        bg_color = theme["bg"]
        fg_pool  = theme["fg_pool"]

        img, draw = self._make_canvas(theme)

        # Sample words (with replacement if num_words > word list)
        pool = PEACE_WORDS.copy()
        random.shuffle(pool)
        if self.num_words <= len(pool):
            selected = pool[:self.num_words]
        else:
            selected = pool + random.choices(pool, k=self.num_words - len(pool))

        # Layout: scatter with slight grid bias to fill canvas
        placed: list[tuple[int, int, int, int]] = []  # (x1,y1,x2,y2)

        margin = 12
        cols   = max(1, int(math.sqrt(self.num_words * self.WIDTH / self.HEIGHT)))
        rows   = max(1, math.ceil(self.num_words / cols))
        cell_w = (self.WIDTH  - 2 * margin) // cols
        cell_h = (self.HEIGHT - 2 * margin) // rows

        word_items = list(selected)
        random.shuffle(word_items)

        for i, (word, lang, script) in enumerate(word_items):
            col = i % cols
            row = i // cols
            if row >= rows:
                break

            # Cell origin with jitter
            cx = margin + col * cell_w + random.randint(0, max(0, cell_w // 4))
            cy = margin + row * cell_h + random.randint(0, max(0, cell_h // 4))

            # Random size within cell
            max_w = int(cell_w * random.uniform(0.55, 0.95))
            max_h = int(cell_h * random.uniform(0.55, 0.85))
            max_w = max(max_w, 40)
            max_h = max(max_h, 20)

            font, tw, th = self._pick_font_size(
                word, script, max_w, max_h,
                min_size=11, max_size=min(120, max(20, cell_h - 4))
            )

            # Pick a random colour from the pre-vetted palette.
            # Every colour in fg_pool is guaranteed ≥ 4.5:1 contrast on bg.
            color: tuple[int, int, int] = random.choice(fg_pool)

            # Random rotation (mostly upright, occasional tilt)
            angle_choices = [0] * 6 + [
                random.uniform(-25, -5),
                random.uniform(5, 25),
                random.uniform(-45, 45),
            ]
            angle = random.choice(angle_choices)

            # Render rotated text onto a temporary surface then paste
            if angle != 0:
                pad = max(tw, th) + 20
                txt_img = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
                txt_drw = ImageDraw.Draw(txt_img)
                txt_drw.text((pad - tw // 2, pad - th // 2), word,
                             font=font, fill=(*color, 255))  # type: ignore[arg-type]
                rotated = txt_img.rotate(angle, expand=True,
                                         resample=Image.BICUBIC)
                rx, ry = rotated.size
                paste_x = cx - rx // 2
                paste_y = cy - ry // 2
                # Clamp to canvas
                paste_x = max(-rx // 2, min(self.WIDTH  - rx // 2, paste_x))
                paste_y = max(-ry // 2, min(self.HEIGHT - ry // 2, paste_y))
                img.paste(rotated, (paste_x, paste_y), rotated)
            else:
                draw.text((cx, cy), word, font=font, fill=color)  # type: ignore[arg-type]

        img = self._subtle_texture(img, theme)

        out_path = os.path.join(self.out_dir, f"peace_{idx}.jpeg")
        try:
            img.convert("RGB").save(out_path, quality=95)
            self.log.debug(f"Peace: saved {out_path}")
        except Exception as e:
            self.log.debug(f"Peace: failed to save {out_path}: {e}")

    # ── public API ────────────────────────────────────────────────────────────

    def run(self, *args, **kwargs) -> None:  # type: ignore[override]
        for i in range(self.file_count):
            self._render_one(i)
