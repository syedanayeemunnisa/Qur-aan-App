"""Roman Urdu Generator — converts Urdu Nastaliq text to Roman (Latin) script.

Uses a multi-strategy approach:
  1. Word-level dictionary lookup (comprehensive)
  2. Pattern-based phonetic conversion for unknown words
  3. Post-processing for natural Roman Urdu output

Example:
    Urdu: آپ کہہ دیجئے کہ وہ اللہ تعالیٰ ایک (ہی) ہے
    Roman Urdu: Aap keh dijiye ke woh Allah ta'ala ek (hi) hai
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RomanUrduGenerator:
    """Generate Roman Urdu from Urdu Nastaliq text."""

    # ═══════════════════════════════════════════════════════════════
    # WORD DICTIONARY — Urdu → Roman Urdu
    # ═══════════════════════════════════════════════════════════════
    # Covers all common words from the Quran Urdu translation.
    # Words are matched by longest-prefix-first.
    # ═══════════════════════════════════════════════════════════════

    WORD_DICT: dict[str, str] = {
        # ── Pronouns ────────────────────────────────────────────
        "آپ": "Aap",
        "وہ": "woh",
        "یہ": "yeh",
        "جو": "jo",
        "جس": "jis",
        "جن": "jin",
        "جنہیں": "jinhen",
        "جنہوں": "jinhon",
        "جنھیں": "jinhen",
        "جنھوں": "jinhon",
        "کس": "kis",
        "کن": "kin",
        "اس": "is",
        "ان": "in",
        "انہوں": "unhon",
        "انہیں": "unhen",
        "انھوں": "unhon",
        "انھیں": "unhen",
        "اسی": "isi",
        "انہی": "unhi",
        "انھی": "unhi",
        "اسی": "usi",
        "کوئی": "koi",
        "کسی": "kisi",
        "کسی": "kisi",
        "میں": "mein",
        "تو": "tu",
        "تم": "tum",
        "ہم": "hum",
        "تمہارا": "tumhara",
        "تمہاری": "tumhari",
        "تمہارے": "tumharay",
        "تمہیں": "tumhein",
        "ہمیں": "hamein",
        "ہم کو": "hum ko",
        "مجھ": "mujh",
        "مجھے": "mujhe",
        "تجھ": "tujh",
        "تجھے": "tujhe",
        "میرا": "mera",
        "میری": "meri",
        "میرے": "meray",
        "تیرا": "tera",
        "تیری": "teri",
        "تیرے": "teray",
        "ہمارا": "hamara",
        "ہماری": "hamari",
        "ہمارے": "hamaray",
        "تمہارا": "tumhara",
        "تمہاری": "tumhari",
        "تمہارے": "tumharay",
        "ان کا": "un ka",
        "ان کی": "un ki",
        "ان کے": "un ke",
        "اس کا": "us ka",
        "اس کی": "us ki",
        "اس کے": "us ke",
        "میں نے": "mein ne",
        "تم نے": "tum ne",
        "ہم نے": "hum ne",
        "اس نے": "us ne",
        "انہوں نے": "unhon ne",
        "انھوں نے": "unhon ne",

        # ── Postpositions ───────────────────────────────────────
        "کا": "ka",
        "کی": "ki",
        "کے": "ke",
        "کو": "ko",
        "سے": "se",
        "میں": "mein",
        "پر": "par",
        "تک": "tak",
        "نے": "ne",
        "والا": "wala",
        "والی": "wali",
        "والے": "walay",
        "والوں": "walon",
        "والي": "wali",
        "کے لیے": "ke liye",
        "کے لئے": "ke liye",
        "لیے": "liye",
        "لئے": "liye",
        "کے باوجود": "ke bawajood",
        "کے بعد": "ke baad",
        "کے پاس": "ke paas",
        "کی طرف": "ki taraf",
        "کی قسم": "ki qasam",
        "کے طور": "ke taur",
        "کی طرح": "ki tarah",
        "کی وجہ": "ki wajah",
        "کے بغیر": "ke baghair",
        "کی خاطر": "ki khatir",
        "کی بابت": "ki babat",

        # ── Conjunctions ────────────────────────────────────────
        "اور": "aur",
        "پھر": "phir",
        "تب": "tab",
        "جب": "jab",
        "تو": "to",
        "اگر": "agar",
        "مگر": "magar",
        "لیکن": "lekin",
        "بلکہ": "balke",
        "کیونکہ": "kyonke",
        "کیوں": "kyon",
        "کہ": "ke",
        "یا": "ya",
        "نہ": "na",
        "نہیں": "nahin",
        "نہ": "na",
        "نہ ہی": "na hi",
        "بھی": "bhi",
        "ہی": "hi",
        "تاہم": "taham",
        "چنانچہ": "chunanche",
        "البتہ": "albata",
        "حتیٰ": "hatta",
        "اگرچہ": "agarche",
        "جبکہ": "jabke",
        "حالانکہ": "halanke",
        "تاکہ": "take",

        # ── Interrogatives ──────────────────────────────────────
        "کیا": "kya",
        "کیسے": "kaise",
        "کیسی": "kaisi",
        "کیسا": "kaisa",
        "کب": "kab",
        "کہاں": "kahan",
        "کیوں": "kyon",
        "کتنا": "kitna",
        "کتنی": "kitni",
        "کتنے": "kitnay",
        "کس طرح": "kis tarah",
        "کس قدر": "kis qadar",
        "کس لیے": "kis liye",
        "کس میں": "kis mein",
        "کس پر": "kis par",
        "کس سے": "kis se",
        "کس کو": "kis ko",

        # ── Numbers ─────────────────────────────────────────────
        "ایک": "ek",
        "دو": "do",
        "تین": "teen",
        "چار": "chaar",
        "پانچ": "paanch",
        "چھ": "chhah",
        "سات": "saat",
        "آٹھ": "aath",
        "نو": "no",
        "دس": "das",
        "سو": "so",
        "ہزار": "hazaar",
        "لاکھ": "laakh",
        "کروڑ": "karod",
        "پہلا": "pehla",
        "پہلی": "pehli",
        "پہلے": "pehlay",
        "دوسرا": "doosra",
        "دوسری": "doosri",
        "دوسرے": "doosray",

        # ── Verbs — doing/making ────────────────────────────────
        "کیا": "kiya",
        "کی": "ki",
        "کئے": "kiye",
        "کر": "kar",
        "کرو": "karo",
        "کرتا": "karta",
        "کرتی": "karti",
        "کرتے": "karte",
        "کرتیں": "karteen",
        "کرنا": "karna",
        "کرنے": "karne",
        "کریں": "karein",
        "کرے": "kare",
        "کر کے": "kar ke",
        "کرکے": "karke",
        "کیجئے": "kijiye",
        "کیجیے": "kijiye",
        "فرمایا": "farmaya",
        "فرمائی": "farmai",
        "فرمائے": "farmaye",
        "فرماؤ": "farmao",
        "فرماتے": "farmate",
        "فرماتا": "farmata",
        "فرماتی": "farmati",

        # ── Verbs — speaking/saying ─────────────────────────────
        "کہا": "kaha",
        "کہی": "kahi",
        "کہے": "kahe",
        "کہہ": "keh",
        "کہو": "kaho",
        "کہتے": "kahte",
        "کہتا": "kahta",
        "کہتی": "kahti",
        "کہیں": "kahein",
        "کہے گا": "kahe ga",
        "کہہ دے": "keh de",
        "کہہ دو": "keh do",
        "دیجئے": "dijiye",
        "دیجیے": "dijiye",
        "دے": "de",
        "دو": "do",
        "دیتا": "deta",
        "دیتی": "deti",
        "دیتے": "dete",
        "دیا": "diya",
        "دی": "di",
        "دئے": "diye",
        "دے گا": "de ga",
        "دے گی": "de gi",
        "بتا": "bata",
        "بتاؤ": "batao",
        "بتایا": "bataya",
        "بتائی": "batayi",
        "بتائے": "bataye",
        "بتاتے": "batate",
        "بتاتا": "batata",
        "بتاتی": "batati",

        # ── Verbs — taking ──────────────────────────────────────
        "لے": "le",
        "لو": "lo",
        "لیا": "liya",
        "لی": "li",
        "لئے": "liye",
        "لے گا": "le ga",
        "لے گی": "le gi",
        "لینا": "lena",
        "لے لو": "le lo",
        "لیجئے": "lijiye",
        "لیجیے": "lijiye",

        # ── Verbs — coming/going ────────────────────────────────
        "آ": "aa",
        "آؤ": "aao",
        "آیا": "aaya",
        "آئے": "aaye",
        "آئی": "aayi",
        "آتا": "aata",
        "آتی": "aati",
        "آتے": "aate",
        "آ کر": "aa kar",
        "آکر": "aakar",
        "جا": "ja",
        "جاؤ": "jao",
        "گیا": "gaya",
        "گئے": "gaye",
        "گئی": "gayi",
        "جاتا": "jata",
        "جاتی": "jati",
        "جاتے": "jate",
        "جانا": "jana",
        "جاؤ گے": "jao ge",

        # ── Verbs — being/becoming ──────────────────────────────
        "ہے": "hai",
        "ہیں": "hain",
        "ہوں": "hoon",
        "ہو": "ho",
        "ہو گا": "ho ga",
        "ہو گی": "ho gi",
        "ہوگا": "hoga",
        "ہوگی": "hogee",
        "تھا": "tha",
        "تھی": "thi",
        "تھے": "thay",
        "تھیں": "thin",
        "ہوا": "hua",
        "ہوئے": "huwe",
        "ہوئی": "huwi",
        "ہو کر": "ho kar",
        "ہوکر": "hokar",
        "رہا": "raha",
        "رہی": "rahi",
        "رہے": "rahe",
        "رہیں": "rahein",
        "رہتا": "rehta",
        "رہتی": "rehti",
        "رہتے": "rehte",
        "رکھا": "rakha",
        "رکھی": "rakhi",
        "رکھے": "rakhe",
        "رکھ": "rakh",
        "رکھو": "rakho",
        "رکھتا": "rakhta",
        "رکھتی": "rakhti",
        "رکھتے": "rakhte",
        "رکھنا": "rakhna",
        "رکھنے": "rakhne",
        "چاہئے": "chahiye",
        "چاہیے": "chahiye",
        "چاہتا": "chahta",
        "چاہتی": "chahti",
        "چاہتے": "chahte",
        "چاہوں": "chahoon",
        "آئے گا": "aayega",
        "آئے گی": "aayegi",
        "ہو جاتا": "ho jata",
        "ہو جاتی": "ho jati",
        "ہو جاتے": "ho jate",
        "ہو گیا": "ho gaya",
        "ہو گئے": "ho gaye",
        "ہو گئی": "ho gayi",
        "ہو جائے": "ho jaye",

        # ── Time / Sequence ─────────────────────────────────────
        "دن": "din",
        "رات": "raat",
        "دنوں": "dinon",
        "راتوں": "raton",
        "صبح": "subah",
        "شام": "shaam",
        "آج": "aaj",
        "کل": "kal",
        "آج کل": "aaj kal",
        "اب": "ab",
        "ابھی": "abhi",
        "پھر": "phir",
        "پہلے": "pehle",
        "پہلے ہی": "pehle hi",
        "بعد": "baad",
        "بعد میں": "baad mein",
        "دوران": "dauran",
        "درمیان": "darmiyan",
        "ہمیشہ": "hamesha",
        "کبھی": "kabhi",
        "کبھی": "kabhi",
        "ہر": "har",
        "ہر ایک": "har ek",
        "بار": "baar",
        "بار بار": "baar baar",
        "پہلی بار": "pehli baar",
        "ایک دن": "ek din",
        "ایک بار": "ek baar",
        "اس وقت": "is waqt",
        "اس دن": "us din",
        "اس روز": "us roz",
        "آخر": "aakhir",
        "آخر کار": "aakhir kar",
        "آخر میں": "aakhir mein",
        "پھر بھی": "phir bhi",
        "اب تک": "ab tak",
        "تب تک": "tab tak",
        "جب تک": "jab tak",
        "اب سے": "ab se",
        "اب کے": "ab ke",

        # ── Place / Direction ───────────────────────────────────
        "یہاں": "yahan",
        "وہاں": "wahan",
        "جہاں": "jahan",
        "کہیں": "kahin",
        "کہیں اور": "kahin aur",
        "ادھر": "idhar",
        "ادھر": "udhar",
        "جِدھر": "jidhar",
        "اوپر": "upar",
        "نیچے": "neeche",
        "اندر": "andar",
        "باہر": "bahar",
        "آگے": "aage",
        "پیچھے": "peeche",
        "سامنے": "samne",
        "دائیں": "dain",
        "بائیں": "bain",
        "دور": "door",
        "قریب": "qareeb",
        "پاس": "paas",
        "درمیان": "darmiyan",
        "آس": "aas",
        "آس پاس": "aas paas",

        # ── Quantifiers ─────────────────────────────────────────
        "بہت": "bahut",
        "زیادہ": "zyada",
        "کم": "kam",
        "کچھ": "kuchh",
        "کچھ نہیں": "kuchh nahin",
        "کچھ بھی": "kuchh bhi",
        "سب": "sab",
        "تمام": "tamam",
        "سارا": "sara",
        "ساری": "sari",
        "سارے": "saray",
        "کافی": "kaafi",
        "تھوڑا": "thora",
        "تھوڑی": "thori",
        "تھوڑے": "thoray",
        "کئی": "kai",
        "متعدد": "mutadid",
        "مختصر": "mukhtasar",
        "خالی": "khali",
        "بھرا": "bhara",
        "پورا": "pura",
        "پوری": "puri",
        "پورے": "puray",
        "کُل": "kul",
        "باقی": "baqi",
        "علاوہ": "ilawa",
        "سوا": "siwa",

        # ── Religious / Islamic Terms ───────────────────────────
        "اللہ": "Allah",
        "الله": "Allah",
        "اللہ تعالیٰ": "Allah ta'ala",
        "رب": "Rabb",
        "پروردگار": "Parwardigaar",
        "خدا": "Khuda",
        "مالک": "Malik",
        "الرحمٰن": "al-Rehman",
        "الرحیم": "al-Raheem",
        "رحمٰن": "Rehman",
        "رحم": "rahem",
        "رحیم": "Raheem",
        "رحمة": "rahemat",
        "رحمتیں": "rahmatein",
        "مہربان": "meharban",
        "کریم": "Kareem",
        "عزیز": "Aziz",
        "حکیم": "Hakeem",
        "علیم": "Aleem",
        "قدیر": "Qadeer",
        "سمیع": "Sami",
        "بصیر": "Baseer",
        "غفور": "Ghafoor",
        "شکور": "Shakoor",
        "وہاب": "Wahab",
        "جبار": "Jabbar",
        "قہار": "Qahhar",
        "غفار": "Ghaffar",
        "ستار": "Sattar",
        "خلاق": "Khallaq",
        "رزاق": "Razzaq",
        "فتاح": "Fattah",
        "واسع": "Wasi",
        "مغفرت": "maghfirat",
        "بخشش": "bakhshish",
        "توبہ": "tauba",
        "بخش": "bakhsh",
        "بخش دے": "bakhsh de",
        "بخش دے گا": "bakhsh de ga",
        "معاف": "maaf",
        "معاف کر": "maaf kar",
        "رحم کر": "rahem kar",
        "عبادت": "ibadat",
        "بندگی": "bandagi",
        "اطاعت": "ita'at",
        "فرمانبرداری": "farmabardari",
        "پرستش": "parastish",
        "خضوع": "khozu",
        "خشوع": "khushu",
        "دعا": "dua",
        "دعائیں": "duayein",
        "پکار": "pukaar",
        "پکارو": "pukaaro",
        "پکارے": "pukaray",
        "پکارتا": "pukarta",
        "پکارتے": "pukarte",
        "نماز": "namaz",
        "روزہ": "roza",
        "حج": "hajj",
        "زکوٰۃ": "zakat",
        "زکاۃ": "zakat",
        "خیرات": "khairat",
        "صدقہ": "sadaqa",
        "صدقات": "sadaqat",

        # ── Quran / Revelation ──────────────────────────────────
        "قرآن": "Quran",
        "قرآن مجید": "Quran Majeed",
        "قرآن کریم": "Quran Kareem",
        "کتاب": "kitab",
        "کتابیں": "kitabein",
        "کتابوں": "kitabon",
        "صحیفے": "sahifay",
        "آیات": "ayat",
        "آیت": "ayat",
        "آیات": "ayat",
        "سورت": "surah",
        "سورہ": "surah",
        "سورۂ": "surah",
        "نازل": "nazil",
        "نازل کی": "nazil ki",
        "نازل کیا": "nazil kiya",
        "وحی": "wahi",
        "وحی بھیجی": "wahi bheji",
        "الہام": "ilham",
        "متن": "matn",
        "آسمانی": "aasmani",
        "آسمان سے": "aasman se",
        "آسمانوں": "aasmanon",

        # ── Prophets / Messengers ───────────────────────────────
        "رسول": "Rasool",
        "رسولوں": "Rasoolon",
        "نبی": "Nabi",
        "نبیوں": "Nabiyon",
        "انبیاء": "Anbiya",
        "مرسل": "Mursal",
        "محمّد": "Muhammad",
        "محمد": "Muhammad",
        "ابراہیم": "Ibrahim",
        "موسیٰ": "Mosa",
        "عيسیٰ": "Eesa",
        "عیسیٰ": "Eesa",
        "نوح": "Nooh",
        "یوسف": "Yousuf",
        "ایوب": "Ayyub",
        "یونس": "Younus",
        "ہود": "Hud",
        "صالح": "Saleh",
        "شعیب": "Shuaib",
        "الیاس": "Ilyas",
        "ذوالکفل": "Zul-kifl",
        "ذوالقرنین": "Zulqarnain",
        "لقمان": "Luqman",
        "داؤد": "Dawood",
        "سلیمان": "Sulaiman",
        "یعقوب": "Yaqoob",
        "اسحاق": "Ishaq",
        "اسماعیل": "Ismail",
        "ہارون": "Haroon",
        "یحییٰ": "Yahya",
        "زکریا": "Zakariya",
        "ادریس": "Idrees",
        "یسع": "Yasa",
        "لوط": "Loot",
        "خضر": "Khidr",
        "آدم": "Adam",

        # ── Afterlife / Judgment ────────────────────────────────
        "آخرت": "aakhirat",
        "آخرت والے": "aakhirat walay",
        "آخرت میں": "aakhirat mein",
        "قیامت": "qayamat",
        "قیامت کا دن": "qayamat ka din",
        "قیامت والے دن": "qayamat walay din",
        "حشر": "hashr",
        "جنت": "jannat",
        "جنتوں": "jannaton",
        "بہشت": "behesht",
        "باغ": "baagh",
        "باغوں": "baghon",
        "نعمت": "nemat",
        "نعمتیں": "nematein",
        "دوزخ": "dozakh",
        "جہنم": "jahannam",
        "جہنم کی آگ": "jahannam ki aag",
        "آگ": "aag",
        "آگ میں": "aag mein",
        "عذاب": "azaab",
        "عذابوں": "azaabon",
        "سزا": "saza",
        "جزا": "jaza",
        "بدلہ": "badla",
        "بدلے": "badlay",
        "ثواب": "sawaab",
        "گناہ": "gunaah",
        "گناہوں": "gunaahon",
        "بخشی": "bakhshi",
        "بخش دیا": "bakhsh diya",
        "بخش دے": "bakhsh de",
        "بخش دو": "bakhsh do",

        # ── Worldly Life ────────────────────────────────────────
        "دنیا": "duniya",
        "دنیا میں": "duniya mein",
        "دنیا کی": "duniya ki",
        "دنیا کے": "duniya ke",
        "زندگی": "zindagi",
        "موت": "maut",
        "مرنے": "marne",
        "مر": "mar",
        "جینے": "jeene",
        "جی": "ji",
        "زندہ": "zinda",
        "مردہ": "murda",
        "زمین": "zameen",
        "زمین پر": "zameen par",
        "زمین میں": "zameen mein",
        "آسمان": "aasmaan",
        "آسمانوں": "aasmanon",
        "آسمان میں": "aasmaan mein",
        "آسمان پر": "aasmaan par",
        "پانی": "paani",
        "پانیوں": "panion",
        "پانی سے": "paani se",
        "پانی میں": "paani mein",
        "ہوا": "hawa",
        "آندھی": "aandhi",
        "بادل": "baadal",
        "بارش": "baarish",
        "سورج": "suraj",
        "چاند": "chaand",
        "ستارے": "sitaray",
        "ستاروں": "sitaron",
        "رات": "raat",
        "دن": "din",
        "صبح": "subah",
        "شام": "shaam",
        "پہاڑ": "pahaar",
        "پہاڑوں": "pahaaron",
        "دریا": "darya",
        "سمندر": "samandar",
        "ندی": "nadi",
        "ندیوں": "nadiyon",

        # ── People / Society ────────────────────────────────────
        "لوگ": "log",
        "لوگو": "logo",
        "لوگوں": "logon",
        "آدمی": "aadmi",
        "آدمیوں": "aadmiyon",
        "مرد": "mard",
        "عورت": "aurat",
        "عورتیں": "auratein",
        "بچے": "bachay",
        "بچوں": "bachon",
        "لڑکا": "larka",
        "لڑکی": "larki",
        "ماں": "maan",
        "باپ": "baap",
        "والد": "walid",
        "والدہ": "walida",
        "بیٹا": "beta",
        "بیٹی": "beti",
        "بیٹے": "betay",
        "بہن": "behen",
        "بہنیں": "behenein",
        "بھائی": "bhai",
        "بھائیوں": "bhaiyon",
        "بھائی بند": "bhai band",
        "شوہر": "shohar",
        "بیوی": "biwi",
        "بیبی": "bibi",
        "خاوند": "khawand",
        "میاں": "miyan",
        "محرم": "mahram",
        "رشتہ": "rishta",
        "رشتے": "rishtay",
        "رشتہ دار": "rishtedar",
        "دوست": "dost",
        "دشمن": "dushman",

        # ── Good / Bad ──────────────────────────────────────────
        "نیک": "nek",
        "نیکی": "neki",
        "نیکیاں": "nekiyan",
        "بد": "bad",
        "برا": "bura",
        "بری": "buri",
        "برے": "bure",
        "برائی": "buraai",
        "برائیاں": "buraiyan",
        "اچھا": "acha",
        "اچھی": "achi",
        "اچھے": "achay",
        "بھلا": "bhala",
        "بھلائی": "bhalai",
        "صبر": "sabar",
        "صبور": "saboor",
        "شکر": "shukar",
        "شکرگزار": "shukarguzar",
        "شکرانہ": "shukrana",
        "احسان": "ehsaan",
        "نعمت": "nemat",
        "نعمتیں": "nematein",
        "فضل": "fazal",
        "فضل": "fazl",
        "برکت": "barkat",
        "برکتیں": "barkatein",
        "رحمت": "rahemat",
        "رحمتیں": "rahmatein",
        "ہدایت": "hidayat",
        "ہدایت یافتہ": "hidayat yafta",
        "گمراہ": "gumrah",
        "گمراہی": "gumrahi",
        "گناہ": "gunaah",
        "گناہ گار": "gunaahgaar",
        "پاک": "pak",
        "پاکیزہ": "pakeeza",
        "صفائی": "safai",
        "طہارت": "taharat",
        "نور": "noor",
        "روشنی": "roshni",
        "اندھیرا": "andhera",
        "اندھیروں": "andheron",
        "سچ": "sach",
        "سچا": "sacha",
        "سچی": "sachi",
        "سچے": "sachay",
        "سچائی": "sachai",
        "جھوٹ": "jhooth",
        "جھوٹا": "jhootha",
        "جھوٹی": "jhoothi",
        "جھوٹے": "jhoothay",
        "حق": "haqq",
        "حق پر": "haqq par",
        "باطل": "batil",
        "عدل": "adl",
        "انصاف": "insaaf",
        "ظلم": "zulm",
        "ظالم": "zalim",
        "ظالموں": "zalimon",
        "ظالمی": "zalimi",
        "مظلوم": "mazloom",
        "مظلوموں": "mazloomon",
        "کفر": "kufr",
        "کافر": "kaafir",
        "کافروں": "kaafiron",
        "شرک": "shirk",
        "مشرک": "mushrik",
        "مشرکوں": "mushrikon",
        "منافق": "munafiq",
        "منافقوں": "munafiqon",
        "نفاق": "nifaq",
        "ایمان": "iman",
        "ایمان والے": "iman walay",
        "ایمان والو": "iman walo",
        "مومن": "momin",
        "مومنو": "mominon",
        "مومنوں": "mominon",
        "مسلم": "muslim",
        "مسلمانو": "musulmano",
        "مسلمانوں": "muslimon",
        "مسلمان": "musulman",
        "مؤمن": "momin",
        "مؤمنو": "mominon",
        "مؤمنین": "mominin",

        # ── Nature / Elements ───────────────────────────────────
        "آگ": "aag",
        "پانی": "paani",
        "مٹی": "mitti",
        "ہوا": "hawa",
        "آندھی": "aandhi",
        "بادل": "baadal",
        "بارش": "baarish",
        "پانی": "paani",
        "برف": "barf",
        "سونا": "sona",
        "چاندی": "chaandi",
        "لوہا": "loha",
        "تانبا": "tanba",
        "پیتل": "peetal",
        "سنگ": "sang",
        "پتھر": "patthar",
        "پتھروں": "pattharon",
        "چٹان": "chattan",
        "ریگ": "reg",
        "ریت": "ret",
        "سمندر": "samandar",
        "دریا": "darya",
        "جھیل": "jheel",
        "کنواں": "kuwan",
        "چشمہ": "chashma",
        "چشموں": "chashmon",
        "درخت": "darakht",
        "درختوں": "darakhton",
        "پھل": "phal",
        "پھلوں": "phalon",
        "پھول": "phool",
        "پھولوں": "phoolon",
        "گھاس": "ghaas",
        "کھیت": "khet",
        "کھیتوں": "kheton",
        "کھیتی": "kheti",
        "جانور": "janwar",
        "جانوروں": "janwaron",
        "پرندے": "parinday",
        "پرندوں": "parindon",
        "مویشی": "maweshi",
        "مویشیوں": "maweshiyon",
        "گائے": "gaay",
        "بکری": "bakri",
        "بکریاں": "bakriyan",
        "اونٹ": "oonth",
        "اونٹنی": "oonthni",
        "گھوڑا": "ghora",
        "گھوڑے": "ghoray",
        "خچر": "khachar",
        "گدھا": "gadha",

        # ── Body / Senses ──────────────────────────────────────
        "آنکھ": "aankh",
        "آنکھیں": "aankhein",
        "کان": "kaan",
        "کانوں": "kanon",
        "ناک": "naak",
        "منہ": "munh",
        "دانت": "daant",
        "ہاتھ": "haath",
        "ہاتھوں": "haathon",
        "پاؤں": "paon",
        "پیر": "pair",
        "سر": "sar",
        "دل": "dil",
        "دلوں": "dilon",
        "جگر": "jigar",
        "کلیجہ": "kaleja",
        "پیٹ": "pet",
        "چہرہ": "chehra",
        "چہروں": "chehron",
        "منہ": "munh",
        "زبان": "zaban",
        "ہونٹ": "honth",
        "ہونٹوں": "honthon",
        "ہڈی": "haddi",
        "ہڈیاں": "haddiyan",
        "گوشت": "gosht",
        "خون": "khoon",
        "پسلی": "pasli",
        "پسلیاں": "pasliyan",
        "پشت": "pisht",
        "کمر": "kamar",
        "شانہ": "shana",
        "سینہ": "seenah",
        "پیٹھ": "peeth",

        # ── Family / Relationships ──────────────────────────────
        "باپ": "baap",
        "ماں": "maan",
        "والد": "walid",
        "والدہ": "walida",
        "بیٹا": "beta",
        "بیٹے": "betay",
        "بیٹی": "beti",
        "بیٹیاں": "betiyan",
        "بھائی": "bhai",
        "بھائیوں": "bhaiyon",
        "بہن": "behen",
        "بہنیں": "behenein",
        "چچا": "chacha",
        "تایا": "taya",
        "ماموں": "mamun",
        "خالہ": "khala",
        "پھوپھی": "phoopi",
        "دادی": "dadi",
        "نانی": "nani",
        "دادا": "dada",
        "نانا": "nana",
        "پوتا": "pota",
        "پوتی": "poti",
        "نواسہ": "nawasa",
        "نواسی": "nawasi",
        "بیوی": "biwi",
        "شوہر": "shohar",
        "بیوہ": "bewa",
        "طلاق": "talaq",
        "نکاح": "nikah",
        "شادی": "shaadi",
        "کنوارہ": "kunwara",
        "کنواری": "kunwari",
        "رشتہ": "rishta",
        "رشتے دار": "rishtedar",
        "رشتہ داری": "rishtedari",
        "خاندان": "khandan",
        "خاندانوں": "khandanon",
        "قبیلہ": "qabeela",
        "قبیلوں": "qabeelon",
        "نسل": "nasl",
        "نسلوں": "naslon",
        "اولاد": "aulaad",
        "والدین": "walidain",
        "شریک": "shareek",
        "ساتھی": "sathi",
        "ساتھیوں": "sathiyon",
        "رفیق": "rafeeq",
        "ہم نشین": "hamnasheen",
        "پڑوسی": "padosi",
        "پڑوسیوں": "padosiyon",
        "مہمان": "mehman",
        "مہمانوں": "mehmanon",

        # ── War / Conflict / Justice ────────────────────────────
        "جنگ": "jung",
        "جنگی": "jungi",
        "لڑائی": "larai",
        "لڑ": "lar",
        "لڑو": "laro",
        "قتال": "qital",
        "قتل": "qatal",
        "قتل کیا": "qatal kiya",
        "مار": "maar",
        "مارو": "maro",
        "مارے": "maray",
        "مارا": "mara",
        "ماری": "mari",
        "دشمن": "dushman",
        "دشمنوں": "dushmanon",
        "دشمنی": "dushmani",
        "منافق": "munafiq",
        "جھگڑا": "jhagra",
        "جھگڑے": "jhagray",
        "جھگڑتے": "jhagarte",
        "فیصلہ": "faisla",
        "فیصلے": "faislay",
        "انصاف": "insaaf",
        "عدل": "adl",
        "عدالت": "adalat",
        "قاضی": "qazi",
        "حکم": "hukm",
        "حکم": "hukm",
        "حکم دے": "hukm de",
        "حکم دیتا": "hukm deta",
        "حکم دیا": "hukm diya",
        "حکم نافذ": "hukm nafiz",
        "حکومت": "hukumat",
        "بادشاہ": "badshah",
        "بادشاہوں": "badshahon",
        "سلطنت": "saltanat",
        "سلطنتیں": "saltanatein",
        "ملک": "mulk",
        "ملکوں": "mulkon",
        "شہر": "sheher",
        "شہروں": "shehron",
        "بستی": "basti",
        "بستیوں": "bastiyon",
        "گاؤں": "gaon",
        "گاؤں والے": "gaon walay",
        "دیہات": "dehaat",
        "محل": "mahal",
        "محلوں": "mahalon",
        "گھر": "ghar",
        "گھروں": "gharon",
        "در": "dar",
        "دروازہ": "darwaza",
        "دروازے": "darwazay",
        "دیوار": "dewaar",
        "دیواریں": "dewaarein",

        # ── Abstract / Knowledge ────────────────────────────────
        "علم": "ilm",
        "علمی": "ilmi",
        "عالم": "aalam",
        "عالمین": "aalamein",
        "جہاں": "jahan",
        "جہانوں": "jahanon",
        "حکمت": "hikmat",
        "حکمتیں": "hikmatein",
        "دانش": "danash",
        "عقل": "aql",
        "عقلمند": "aqlmand",
        "سمجھ": "samajh",
        "سمجھو": "samjho",
        "سمجھتا": "samajhta",
        "سمجھتے": "samajhte",
        "سمجھتے": "samajhte",
        "سوچ": "soch",
        "سوچو": "socho",
        "سوچتا": "sochta",
        "سوچتے": "sochte",
        "خیال": "khayal",
        "خیالات": "khayalat",
        "فکر": "fikr",
        "فکریں": "fikrein",
        "دلچسپی": "dilchasp",
        "یاد": "yaad",
        "یاد رکھو": "yaad rakho",
        "یاد رکھ": "yaad rakh",
        "بھول": "bhool",
        "بھولے": "bhoole",
        "بھولنا": "bhoolna",
        "بھول جاؤ": "bhool jao",

        # ── Emphasis / Assertion ────────────────────────────────
        "یقیناً": "yaqinan",
        "بے شک": "beshak",
        "بےشک": "beshak",
        "ضرور": "zaroor",
        "البتہ": "albata",
        "حقیقت": "haqeeqat",
        "حقیقت میں": "haqeeqat mein",
        "واقعی": "waqai",
        "سچ مچ": "sach much",
        "بالکل": "bilkul",
        "ہرگز": "hargiz",
        "ہرگز نہیں": "hargiz nahin",
        "ہاں": "haan",
        "نہیں": "nahin",
        "جی ہاں": "ji haan",
        "جی نہیں": "ji nahin",

        # ── Intensifiers ────────────────────────────────────────
        "بہت": "bahut",
        "بہت بڑا": "bahut bara",
        "بہت زیادہ": "bahut zyada",
        "انتہائی": "intihai",
        "نہایت": "nihayat",
        "بے حد": "be had",
        "بے شمار": "be shumar",
        "بے پایاں": "be payan",
        "بے نظیر": "be nazir",
        "بے مثال": "be misal",
        "بے مثل": "be misl",
        "بے کس": "be kas",
        "بے یار": "be yar",
        "بے سہارا": "be sahara",
        "بے غرض": "be gharaz",
        "بے لوث": "be los",
        "بے شک": "beshak",
        "بے خوف": "be khof",
        "بے پرواہ": "be parwah",
        "بے نیاز": "be niyaz",
        "بے انتہا": "be intiha",

        # ── Status / Quality ────────────────────────────────────
        "اعلیٰ": "aala",
        "ادنیٰ": "adna",
        "بہتر": "behtar",
        "بہتری": "behtari",
        "بہترین": "behtareen",
        "بڑا": "bara",
        "بڑی": "bari",
        "بڑے": "baray",
        "چھوٹا": "chhota",
        "چھوٹی": "chhoti",
        "چھوٹے": "chhotay",
        "لمبا": "lamba",
        "لمبی": "lambi",
        "لمبے": "lambay",
        "چوڑا": "chora",
        "موٹا": "mota",
        "گہرا": "gahra",
        "گہری": "gahri",
        "گہرے": "gahray",
        "اونچا": "ooncha",
        "اونچی": "oonchi",
        "اونچے": "oonchay",
        "نیچا": "neecha",
        "نیچی": "neechi",
        "نیچے": "neechay",
        "مہنگا": "mehnga",
        "سستا": "sasta",
        "نرم": "naram",
        "سخت": "sakht",
        "کمزور": "kamzor",
        "طاقتور": "taqatwar",
        "زبردست": "zabardast",
        "غریب": "ghareeb",
        "امیر": "ameer",
        "غنی": "ghani",
        "فقر": "faqr",
        "فقیر": "faqeer",
        "تھوڑا": "thora",
        "زیادہ": "zyada",
        "کافی": "kaafi",
        "بھرپور": "bharpoor",
        "مکمل": "mukammal",
        "نامکمل": "namukammal",
        " پورا": "pura",
        "ادھورا": "adhura",

        # ── Direction / Position ────────────────────────────────
        "اوپر": "upar",
        "نیچے": "neeche",
        "آگے": "aage",
        "پیچھے": "peeche",
        "دائیں": "dain",
        "بائیں": "bain",
        "دائیں طرف": "dain taraf",
        "بائیں طرف": "bain taraf",
        "سامنے": "samne",
        "پیچھے": "peeche",
        "اندر": "andar",
        "باہر": "bahar",
        "درمیان": "darmiyan",
        "بیچ": "beech",
        "بیچ میں": "beech mein",
        "آس پاس": "aas paas",
        "پاس": "paas",
        "دور": "door",
        "قریب": "qareeb",
        "نزدیک": "nazdeek",
        "کنارے": "kinaray",
        "کناروں": "kinaron",
        "اوپر والا": "upar wala",
        "نیچے والا": "neeche wala",
        "پیچھے والا": "peeche wala",
        "آگے والا": "aage wala",
        "پار": "paar",
        "آر پار": "aara paar",
        "ادھر": "idhar",
        "ادھر": "udhar",
        "جِدھر": "jidhar",
        "جہاں": "jahan",
        "تہہ": "teh",
        "تہوں": "tehon",
        "تخت": "takht",
        "تخت پر": "takht par",
        "عرش": "arsh",
        "عرش پر": "arsh par",
        "عرش کا": "arsh ka",
        "عرش عظیم": "arsh azeem",

        # ── Worship / Religion ─────────────────────────────────
        "مسجد": "masjid",
        "مسجدوں": "masjidon",
        "مسجدوں میں": "masjidon mein",
        "مسجد میں": "masjid mein",
        "محراب": "mehrab",
        "منبر": "mimbar",
        "قبلہ": "qibla",
        "قبلے": "qiblay",
        "کعبہ": "kabah",
        "حرم": "haram",
        "حرم شریف": "haram shareef",
        "مکہ": "Makkah",
        "مدینہ": "Madina",
        "بیت اللہ": "Baitullah",
        "بیت المقدس": "Baitul Muqaddas",
        "مسجد اقصیٰ": "Masjid Aqsa",
        "مسجد حرام": "Masjid Haram",
        "مسجد نبوی": "Masjid Nabawi",
        "صفا": "Safa",
        "مروہ": "Marwah",
        "عرفات": "Arafat",
        "مزدلفہ": "Muzdalifah",
        "منیٰ": "Mina",

        # ── Additional common words ────────────────────────────
        "طور": "taur",
        "طرف": "taraf",
        "طرح": "tarah",
        "طرح": "tarah",
        "طرح سے": "tarah se",
        "طرح طرح": "tarah tarah",
        "بابت": "babat",
        "بارے": "baray",
        "بارے میں": "baray mein",
        "خاطر": "khatir",
        "خاطر": "khatir",
        "خاطر": "khatir",
        "واسطے": "wastay",
        "واسطہ": "wasta",
        "پیمانہ": "paimana",
        "پیمانے": "paimanay",
        "میزان": "meezaan",
        "وزن": "wazan",
        "تول": "tol",
        "تولنا": "tolna",
        "نہ تولو": "na tolo",
        "ماپ": "maap",
        "ماپو": "maapo",
        "ناپ": "naap",
        "ناپو": "naapo",
        "پیمانہ پورا": "paimana pura",
        "انصاف سے": "insaaf se",
        "عدل سے": "adl se",
        "حق سے": "haqq se",
        "بے انصافی": "be insafi",
        "بے جا": "be ja",
        "بجا": "baja",
        "بے موقع": "be mauqa",
        "موقع": "mauqa",
        "موقع پر": "mauqa par",
        "موقعے": "mauqay",
        "مقرر": "muqarrar",
        "مقرر کیا": "muqarrar kiya",
        "مقرر کی": "muqarrar ki",
        "مقرر کر": "muqarrar kar",
        "جو کچھ": "jo kuchh",
        "جو کچھ بھی": "jo kuchh bhi",
        "جیسا": "jaisa",
        "جیسی": "jaisi",
        "جیسے": "jaise",
        "ویسا": "waisa",
        "ویسی": "waisi",
        "ویسے": "waise",
        "ایسا": "aisa",
        "ایسی": "aisi",
        "ایسے": "aise",
        "کیونکہ": "kyonke",
        "اس لیے": "is liye",
        "اس وجہ": "is wajah",
        "اس بنا": "is bina",
        "اس سبب": "is sabab",
        "اس طرح": "is tarah",
        "اس طور": "is taur",
        "اسی طرح": "isi tarah",
        "اسی وجہ": "isi wajah",
        "سوائے": "siwaye",
        "علاوہ": "ilawa",
        "بغیر": "baghair",
        "بغیر کسی": "baghair kisi",
        "بغیر": "baghair",
        "سوا": "siwa",
        "سوائے": "siwaye",
        "پس": "pas",
        "چنانچہ": "chunanche",
        "غرض": "gharaz",
        "غرض کہ": "gharaz ke",
        "خلاصہ": "khulasa",
        "نتیجہ": "nateeja",
        "نتیجے": "nateejay",
        "سبب": "sabab",
        "اسباب": "asbab",
        "وجہ": "wajah",
        "وجوہات": "wujuhuat",
        "باعث": "baais",
        "ذریعہ": "zariya",
        "ذریعے": "zariyay",
        "واسطہ": "wasta",
        "مادہ": "madah",
        "مادے": "maday",
        "مطلب": "matlab",
        "مراد": "murad",
        "منشا": "mansha",
        "ارادہ": "irada",
        "ارادے": "iraday",
        "نیت": "niyat",
        "نیتیں": "niyatein",
        "قصد": "qasad",
        "قصداً": "qasdan",
        "جان بوجھ": "jaan boojh",
        "جان بوجھ کر": "jaan boojh kar",
        "ارادتاً": "iradatan",
        "برابر": "barabar",
        "برابر میں": "barabar mein",
        "مساوی": "masawi",
        "برابری": "barabari",
        "ٹھیک": "theek",
        "صحیح": "sahi",
        "غلط": "ghalat",
        "سیدھا": "seedha",
        "سیدھی": "seedhi",
        "سیدھے": "seedhay",
        "ٹیڑھا": "tedha",
        "ٹیڑھی": "tedhi",
        "ٹیڑھے": "tedhay",
        "صاف": "saaf",
        "صاف صاف": "saaf saaf",
        "واضح": "waazih",
        "ظاہر": "zaahir",
        "ظاہر ہے": "zaahir hai",
        "مخفی": "makhfi",
        "پوشیدہ": "posheeda",
        "چھپا": "chhupa",
        "چھپی": "chhupi",
        "چھپے": "chhupe",
        "آشکار": "aashkaar",
        "عیاں": "ayaan",
        "رواں": "rawan",
        "جاری": "jaari",
        "لگاتار": "lagataar",
        "مسلسل": "musalsal",
        "ہمیشہ": "hamesha",
        "صبح": "subah",
        "صبح صبح": "subah subah",
        "شام": "shaam",
        "شام کو": "shaam ko",
        "صبح کو": "subah ko",
        "صبح ہوتے": "subah hote",
        "رات کو": "raat ko",
        "دن کو": "din ko",
        "دوپہر": "dopeher",
        "دوپہر کو": "dopeher ko",
        "رات": "raat",
        "راتوں": "raton",
        "دن": "din",
        "دنوں": "dinon",
        "روز": "roz",
        "روزانہ": "rozana",
        "ہفتہ": "hafta",
        "مہینہ": "maheena",
        "سال": "saal",
        "برس": "baras",
        "مدت": "muddat",
        "عرصہ": "arsa",
        "زمانہ": "zamana",
        "زمانوں": "zamanon",
        "دور": "daur",
        "دوران": "dauran",
        "عہد": "ahd",
        "عہدے": "ahday",
        "مدت": "muddat",
        "لمحہ": "lamha",
        "لمحوں": "lamhon",
        "پل": "pal",
        "پلوں": "palon",
        "ساعت": "sa'at",
        "گھڑی": "ghari",
        "گھڑیاں": "ghariyan",
        "وقت": "waqt",
        "اوقات": "auqaat",
        "وقتاً": "waqtan",
        "فوراً": "fauran",
        "فوری": "fori",
        "فوری طور": "fori taur",
        "جلدی": "jaldi",
        "جلد": "jald",
        "دیر": "deir",
        "دیر سے": "deir se",
        "جلد": "jald",
        "جلد ہی": "jald hi",
        "ابھی": "abhi",
        "ابھی تک": "abhi tak",
        "دیر تک": "deir tak",
        "کب": "kab",
        "کب سے": "kab se",
        "کب تک": "kab tak",
        "جب سے": "jab se",
        "تب سے": "tab se",
        "اب سے": "ab se",
        "آج سے": "aaj se",
        "کل سے": "kal se",
        "گزرا": "guzra",
        "گزرے": "guzray",
        "گزری": "guzri",
        "بیتا": "beta",
        "بیتی": "beti",
        "بیتے": "betay",
        "آنے": "aane",
        "جانے": "jane",
        "آنے والا": "aane wala",
        "جانے والا": "jane wala",
        "آنے والی": "aane wali",
        "جانے والی": "jane wali",
        "آنے والے": "aane walay",
        "جانے والے": "jane walay",
        "آنے والوں": "aane walon",
        "جانے والوں": "jane walon",
        "خوب": "khoob",
        "خوبی": "khoobi",
        "خوبیاں": "khoobiyan",
        "خوبصورت": "khoobsurat",
        "خوبصورتی": "khoobsurti",
        "بری": "buri",
        "برائی": "buraai",
        "برائیاں": "buraiyan",
        "نیک": "nek",
        "نیک": "nek",
        "نیکی": "neki",
        "نیکیاں": "nekiyan",
        "بد": "bad",
        "بدی": "badi",
        "بدخواہ": "badkhwah",
        "بدنظامی": "badnazmi",
        "بھلائی": "bhalai",
        "بھلائیاں": "bhalaiyan",
        "اچھائی": "achai",
        "اچھائیاں": "achaiyan",
        "اچھال": "acha",
        "برا": "bura",
        "بری": "buri",
        "برے": "bure",
        "بہتر": "behtar",
        "بہترین": "behtareen",
        "بہتری": "behtari",
        "خراب": "kharaab",
        "خرابی": "kharabi",
        "صحت": "sehat",
        "صحت مند": "sehat mand",
        "بیمار": "bemaar",
        "بیماری": "bemari",
        "علاج": "ilaaj",
        "دوا": "dawa",
        "دوائیں": "dawayein",
        "شفا": "shifa",
        "صحت": "sehat",
        "تندرست": "tandrust",
        "تندرستی": "tandrusti",
        "طاقت": "taqat",
        "طاقتوں": "taqaton",
        "زور": "zor",
        "قوت": "quwwat",
        "توانائی": "tawanai",
        "بل": "bal",
        "بلند": "buland",
        "بلندی": "bulandi",
        "برتری": "bartari",
        "فضیلت": "fazeelat",
        "افضل": "afzal",
        "افضلیت": "afzaliyat",
        "برکت": "barkat",
        "برکتیں": "barkatein",
        "بابرکت": "babarkat",

        # ── Additional short common words ────────────────────────
        "بھر": "bhar",
        "بھرے": "bhare",
        "بھری": "bhari",
        "بھرا": "bhara",
        "بھرے ہوئے": "bhare huwe",
        "پُر": "pur",
        "پُر": "pur",
        "مملو": "mamloo",
        "لبریز": "labrez",
        "بھرا ہوا": "bhara hua",
        "بھرپور": "bharpoor",
        "لگا": "laga",
        "لگی": "lagi",
        "لگے": "lagay",
        "لگتا": "lagta",
        "لگتی": "lagti",
        "لگتے": "lagte",
        "لگ کر": "lag kar",
        "لگاؤ": "lagao",
        "پڑا": "para",
        "پڑی": "pari",
        "پڑے": "paray",
        "پڑتا": "parta",
        "پڑتی": "parti",
        "پڑتے": "parte",
        "پڑ گیا": "par gaya",
        "پڑ گئے": "par gaye",
        "پڑ گئی": "par gayi",
        "ڈال": "daal",
        "ڈالو": "daalo",
        "ڈالا": "daala",
        "ڈالی": "daali",
        "ڈالے": "daalay",
        "ڈالتا": "daalta",
        "ڈالتی": "daalti",
        "ڈالتے": "daalte",
        "نکال": "nikaal",
        "نکالو": "nikaalo",
        "نکالا": "nikaala",
        "نکالی": "nikaali",
        "نکالے": "nikaalay",
        "نکالتا": "nikaalta",
        "نکالتی": "nikaalti",
        "نکالتے": "nikaalte",
        "نظر": "nazar",
        "نظر آتے": "nazar aate",
        "نظر آتا": "nazar aata",
        "نظر آتی": "nazar aati",
        "نظر آیا": "nazar aaya",
        "نظر آئے": "nazar aaye",
        "نظر ڈال": "nazar daal",
        "نظر رکھ": "nazar rakh",
        "سمجھ": "samajh",
        "سمجھو": "samjho",
        "سمجھے": "samjhe",
        "سمجھا": "samjha",
        "سمجھی": "samjhi",
        "سمجھتے": "samajhte",
        "سمجھتا": "samajhta",
        "سمجھتی": "samajhti",
        "جان": "jaan",
        "جان": "jaan",
        "جان کر": "jaan kar",
        "جان بوجھ کر": "jaan boojh kar",
        "جاننا": "jaanna",
        "جانتے": "jaante",
        "جانتا": "jaanta",
        "جانتے": "jaante",
        "جانیں": "jaanein",
        "جانو": "jaano",
        "مان": "maan",
        "مانو": "mano",
        "مانا": "mana",
        "مانی": "mani",
        "مانے": "manay",
        "مانتا": "maanta",
        "مانتی": "maanti",
        "مانتے": "maante",
    }

    # ── Pattern-based replacements for common constructs ─────────
    WORD_PATTERNS: list[tuple[re.Pattern, str]] = [
        # Common suffixes
        (re.compile(r'وں$'), 'on'),
        (re.compile(r'ؤں$'), 'on'),
        (re.compile(r'وٴں$'), 'on'),
        (re.compile(r'یں$'), 'ein'),
        (re.compile(r'ات$'), 'aat'),
        (re.compile(r'ا$'), 'a'),
    ]

    def __init__(self):
        self._cache: dict[str, str] = {}
        # Pre-sort dictionary by word length (longest first) for greedy matching
        self._sorted_words = sorted(
            self.WORD_DICT.keys(),
            key=lambda w: (-len(w), w)
        )

    # ═══════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════

    def convert(self, urdu_text: str) -> str:
        """Convert Urdu Nastaliq text to Roman Urdu.

        Args:
            urdu_text: Urdu text in Nastaliq script.

        Returns:
            Roman Urdu (Latin script) representation.
        """
        if not urdu_text or not urdu_text.strip():
            return ""

        # Normalize and cache
        normalized = self._normalize(urdu_text)
        if normalized in self._cache:
            return self._cache[normalized]

        result = self._convert_text(normalized)
        result = self._post_process(result)

        self._cache[normalized] = result
        return result

    def convert_batch(self, texts: dict[str, str]) -> dict[str, str]:
        """Convert a batch of verse translations.

        Args:
            texts: Dict mapping verse_key → urdu_text.

        Returns:
            Dict mapping verse_key → roman_urdu_text.
        """
        return {key: self.convert(text) for key, text in texts.items()}

    def clear_cache(self):
        self._cache.clear()

    # ═══════════════════════════════════════════════════════════════
    # CORE ENGINE
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _normalize(text: str) -> str:
        """Clean up the text before conversion."""
        # Remove zero-width and invisible chars
        for c in ['\u200B', '\u200C', '\u200D', '\uFEFF', '\u200E', '\u200F']:
            text = text.replace(c, '')
        # Remove diacritics that are irrelevant for Urdu reading
        # Includes the dagger alif (U+0670) which appears in تعالیٰ
        diacritics = "ًٌٍَُِّْٰ"
        for d in diacritics:
            text = text.replace(d, '')
        # Remove tatweel/kashida (U+0640)
        text = text.replace('\u0640', '')
        return text.strip()

    def _convert_text(self, text: str) -> str:
        """Main conversion pipeline."""
        # Tokenize preserving whitespace
        tokens = re.split(r'(\s+)', text)
        result_parts = []

        for token in tokens:
            if not token.strip():
                result_parts.append(token)
                continue

            # Check if token contains any Arabic/Urdu char
            has_urdu = any(0x0600 <= ord(c) <= 0x06FF or
                          0xFB50 <= ord(c) <= 0xFDFF or
                          0xFE70 <= ord(c) <= 0xFEFF
                          for c in token)

            if has_urdu:
                result_parts.append(self._convert_urdu_token(token))
            else:
                result_parts.append(token)

        return "".join(result_parts)

    def _convert_urdu_token(self, token: str) -> str:
        """Convert a token containing Urdu characters."""
        # Handle mixed tokens (Urdu + non-Urdu)
        parts = []
        current_urdu = []

        for c in token:
            is_urdu = (0x0600 <= ord(c) <= 0x06FF or
                       0xFB50 <= ord(c) <= 0xFDFF or
                       0xFE70 <= ord(c) <= 0xFEFF)
            if is_urdu:
                current_urdu.append(c)
            else:
                if current_urdu:
                    parts.append(self._convert_word("".join(current_urdu)))
                    current_urdu = []
                parts.append(c)

        if current_urdu:
            parts.append(self._convert_word("".join(current_urdu)))

        return "".join(parts)

    def _convert_word(self, word: str) -> str:
        """Convert a single Urdu word to Roman Urdu.

        Strategy (in order):
        1. Greedy longest-match from the WORD_DICT
        2. If partial match, convert prefix + suffix using fallback
        """
        if not word:
            return ""

        result = []
        remaining = word

        while remaining:
            matched = False
            # Try to match against the word dictionary (longest first)
            for dict_word in self._sorted_words:
                if remaining.startswith(dict_word):
                    result.append(self.WORD_DICT[dict_word])
                    remaining = remaining[len(dict_word):]
                    matched = True
                    break

            if not matched:
                # Fallback: convert first character using mapping
                char = remaining[0]
                roman = self._fallback_char(char)
                result.append(roman)
                remaining = remaining[1:]

        word_str = "".join(result)

        # Handle special characters
        word_str = self._fix_special_sounds(word_str)

        return word_str

    # ═══════════════════════════════════════════════════════════════
    # FALLBACK CHARACTER MAPPING
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _fallback_char(char: str) -> str:
        """Map a single Urdu character to Roman.

        This is a best-effort phonetic mapping for words not in the dictionary.
        Key rules for Urdu:
        - و (waw) → 'o' or 'u' in middle of words, 'w' at start
        - ع (ain) → silent (removed) in most Urdu contexts
        - ی (yeh) → 'i' or 'y' depending on context
        """
        cp = ord(char)

        # Check for presentation form characters
        if 0xFE70 <= cp <= 0xFEFF:
            # Try to map from presentation form to base character
            base = {
                0xFE8D: 'a', 0xFE8F: 'b', 0xFE91: 'b',
                0xFE93: 't', 0xFE95: 't', 0xFE97: 't',
                0xFE99: 's', 0xFE9B: 's',
                0xFE9D: 'j', 0xFE9F: 'j',
                0xFEA1: 'h', 0xFEA3: 'h',
                0xFEA5: 'kh', 0xFEA7: 'kh',
                0xFEA9: 'd', 0xFEAB: 'z',
                0xFEAD: 'r', 0xFEAF: 'z',
                0xFEB1: 's', 0xFEB3: 's',
                0xFEB5: 'sh', 0xFEB7: 'sh',
                0xFEB9: 's', 0xFEBB: 's',
                0xFEBD: 'z', 0xFEBF: 'z',
                0xFEC1: 't', 0xFEC3: 't',
                0xFEC5: 'z', 0xFEC7: 'z',
                0xFEC9: '', 0xFECB: '',   # Ain → silent
                0xFECD: 'gh', 0xFECF: 'gh',
                0xFED1: 'f', 0xFED3: 'f',
                0xFED5: 'q', 0xFED7: 'q',
                0xFED9: 'k', 0xFEDB: 'k',
                0xFEDD: 'l', 0xFEDF: 'l',
                0xFEE1: 'm', 0xFEE3: 'm',
                0xFEE5: 'n', 0xFEE7: 'n',
                0xFEE9: 'h', 0xFEEB: 'h',
                0xFEED: 'o',  # Waw → 'o' (most common vowel in Urdu)
                0xFEEF: 'a',
                0xFEF1: 'y', 0xFEF3: 'y',
                0xFEF5: 'la', 0xFEF7: 'la',
                0xFEF9: 'la', 0xFEFB: 'la', 0xFEFC: 'la',
            }.get(cp)
            if base is not None:
                return base
            return ''

        # Direct character mapping
        mapping = {
            # Urdu-specific consonants
            0x067E: 'p',       # پ Peh
            0x0686: 'ch',      # چ Che
            0x0688: 'd',       # ڈ Dal
            0x0691: 'r',       # ڑ Re
            0x0699: 'r',       # ڙ 
            0x06AF: 'g',       # گ Gaf
            0x06A9: 'k',       # ک Keheh
            0x06AA: 'k',
            0x06AB: 'k',
            0x06AC: 'k',
            0x06B3: 'k',
            0x06B4: 'k',
            0x06BA: 'n',       # ں Noon Ghunna
            0x06BB: 'n',
            0x06BE: 'h',       # ھ Do-chashmi He
            0x06C1: 'h',       # ہ Heh
            0x06C2: 'h',
            0x06CC: 'y',       # ی Yeh
            0x06CD: 'y',
            0x06CE: 'y',
            0x06D2: 'e',       # ے Yeh Barree
            0x06D3: 'ai',      # ۓ

            # Standard Arabic (also used in Urdu)
            0x0621: '',        # ء Hamza → silent in Roman Urdu
            0x0622: 'aa',      # آ Alif Madda
            0x0623: 'a',       # أ 
            0x0624: 'o',       # ؤ → 'o'
            0x0625: 'e',       # إ → 'e'
            0x0626: 'y',       # ئ
            0x0627: 'a',       # ا Alif
            0x0628: 'b',       # ب
            0x0629: 't',       # ة
            0x062A: 't',       # ت
            0x062B: 's',       # ث
            0x062C: 'j',       # ج
            0x062D: 'h',       # ح → 'h' in Urdu
            0x062E: 'kh',      # خ
            0x062F: 'd',       # د
            0x0630: 'z',       # ذ → 'z' in Urdu
            0x0631: 'r',       # ر
            0x0632: 'z',       # ز
            0x0633: 's',       # س
            0x0634: 'sh',      # ش
            0x0635: 's',       # ص → 's' in Urdu
            0x0636: 'z',       # ض → 'z' in Urdu
            0x0637: 't',       # ط → 't' in Urdu
            0x0638: 'z',       # ظ → 'z' in Urdu
            0x0639: '',        # ع → SILENT in Urdu (key fix!)
            0x063A: 'gh',      # غ
            0x0641: 'f',       # ف
            0x0642: 'q',       # ق
            0x0643: 'k',       # ك (Arabic Kaf)
            0x0644: 'l',       # ل
            0x0645: 'm',       # م
            0x0646: 'n',       # ن
            0x0647: 'h',       # ه
            0x0648: 'o',       # و → 'o' (NOT 'w' — key fix for Urdu!)
            0x0649: 'a',       # ى
            0x064A: 'y',       # ي

            # Digits
            0x0660: '0', 0x0661: '1', 0x0662: '2', 0x0663: '3',
            0x0664: '4', 0x0665: '5', 0x0666: '6', 0x0667: '7',
            0x0668: '8', 0x0669: '9',

            # Punctuation
            0x060C: ', ', 0x061B: '; ', 0x061F: '? ',
            0x06D4: '. ',
        }

        return mapping.get(cp, char)

    # ═══════════════════════════════════════════════════════════════
    # POST-PROCESSING
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _fix_special_sounds(word: str) -> str:
        """Fix common phonetic issues in the converted word."""
        # و at the end of word is often 'o' or 'u' (already mapped to 'o')
        # Fix: 'w' between consonants should be 'u' or 'o'
        word = re.sub(r'([bcdfghjklmnpqrstvxyz])o([bcdfghjklmnpqrstvxyz])',
                      r'\1u\2', word)

        # 'o' at very end after consonant → keep as 'o' (like "ko")
        # Already handled

        # 'aa' followed by 'a' → just 'aa'
        word = word.replace('aaa', 'aa')
        word = word.replace('iii', 'ii')
        word = word.replace('ooo', 'oo')

        # Fix: 'e' at end of word after consonant often needs 'h'
        # Only for certain patterns

        return word

        def _post_process(self, text: str) -> str:
        """Final post-processing for readability."""
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)

        # Space before punctuation
        text = re.sub(r'\s+([.,!?;:\)\]]+)', r'\1', text)
        text = re.sub(r'([\(\[{])\s+', r'\1', text)

        # Clean up empty quotes/apostrophes
        text = text.replace("''", '')

        # Fix 'oh' → 'woh' (standalone word وہ)
        text = re.sub(r'\boh\b', 'woh', text, flags=re.IGNORECASE)

        # Fix 'o' at start of word → 'w' (Urdu و at start = consonant 'w')
        text = re.sub(r'\bo([aâeiou])', lambda m: 'w' + m.group(1), text, flags=re.IGNORECASE)

        # Fix 'o' between two consonants → 'u'
        text = re.sub(r'([bcdfghjklmnpqrstvxz])o([bcdfghjklmnpqrstvxz])',
                      r'\1u\2', text, flags=re.IGNORECASE)

        # Fix 'y' between consonants → 'i' for readability
        text = re.sub(r'([bcdfghjklmnpqrstvxz])y([bcdfghjklmnpqrstvxz])',
                      r'\1i\2', text, flags=re.IGNORECASE)

        # Fix 'w' between two consonants → 'u'
        text = re.sub(r'([bcdfghjklmnpqrstvxz])w([bcdfghjklmnpqrstvxz])',
                      r'\1u\2', text, flags=re.IGNORECASE)

        # Common word-specific fixes
        text = re.sub(r'\bShro\b', 'Shuru', text)
        text = re.sub(r'\bshro\b', 'shuru', text)
        text = re.sub(r'\bkhob\b', 'khoob', text, flags=re.IGNORECASE)
        text = re.sub(r'\bnyaz\b', 'niyaz', text, flags=re.IGNORECASE)
        text = re.sub(r"\btaala\b", "ta'ala", text, flags=re.IGNORECASE)
        text = re.sub(r"\btali\b", "ta'ala", text, flags=re.IGNORECASE)

        # Fix common short words
        text = re.sub(r'\bky\b', 'kya', text)
        text = re.sub(r'\bny\b', 'ne', text)
        text = re.sub(r'\bpy\b', 'pe', text)
        text = re.sub(r'\bty\b', 'te', text)

        # Capitalize first letter of text
        if text and text[0].isalpha():
            text = text[0].upper() + text[1:]

        return text.strip()


