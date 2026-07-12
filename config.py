# Секреты вынесены в credentials.py (в .gitignore). Скопируй credentials.example.py
# в credentials.py и впиши свои значения.
from credentials import (
    LEV_API_ID, LEV_API_HASH,
    BURNER_API_ID, BURNER_API_HASH, BURNER_PHONE,
    ANTHROPIC_API_KEY,
)

LEV_SESSION = "lev_session"
BURNER_SESSION = "burner_session"
AI_MODEL = "claude-haiku-4-5-20251001"

# Напоминания: шлём с расходного аккаунта на основной рабочий аккаунт — чтобы
# приходил нормальный пуш (в «Избранное» пуш не приходит).
NOTIFY_FROM_SESSION = "burner_session"
NOTIFY_TO = "levv_ddev"

# Пароль для публичного дашборда на GitHub Pages (вкладка «Заказы»).
# Клиентская заглушка — отсекает случайных, но не серьёзная защита (виден в исходнике).
# Публичная версия НЕ содержит вкладку «Ответы» с личными переписками.
PUBLIC_PASSWORD = "lead2026"

FOLDER_NAME = "вакансии"
DAYS_BACK = 2
MAX_MESSAGES_PER_CHAT = 500
OUTPUT_FILE = "вакансии_техспец.xlsx"

# Каналы папки «Вакансии» (97 публичных), выгружено 2026-07-11. Используется, когда
# парсер работает под расходным аккаунтом (в облаке) — он читает их как публичные.
CHANNELS = [
    "sova_freelance", "board_axolotl", "vakansii_dizaynerov", "sferadeytelnosti",
    "target_vakansii", "FrWork3", "WebWorkerr", "prostranstvowork",
    "workfreelan", "vakansiitelegramm", "ecareer", "workygram",
    "smm_vakansiii", "rabota_is_doma_vakansii", "GetClient", "vakansii_na_ydalenke",
    "proffreelancee", "workk_onstream", "Easy_wrk", "udafrii",
    "getwork25", "jobosphere", "runello_rus_frontend", "vacancyUral",
    "g00djob4all", "workremotejob", "frilanser_vacansii", "butukovuy_lux",
    "work_from_lina", "liberty_job", "dnative_job", "runello_rus_html",
    "ALLW0RK", "frilancekomfort", "worksvsem", "pixeltechspec",
    "workk_on", "smmtheworkkp", "freelance_joob", "jobtopchik",
    "ikmmarketing", "frilans_na_legke", "frilans", "whiteedtechwork",
    "freelance7", "TRemoters", "managwork", "worldeventjob",
    "FreeWorkFeed", "freelancetaverna", "search_techspec", "freelancce",
    "influencersoffuture", "Uyut_frilans", "MoscowWorkForYou", "targetsmmvakansii",
    "talentedpeoples", "rabotka_zdes", "vakansii_ai", "proadmin_job",
    "reclamaexpertov", "kr_job", "VakansiiMenedgeryWBOZONYM", "algoritm_schools",
    "Freelance_grooup", "vsem_po_rabote", "posibleworks", "monay_telegram",
    "proffreelancee_baraholca", "ewoxchat", "frilanc_topchat", "worknomer1",
    "workchatbuzines", "workk_onchat", "profiwork", "proffreelancee_chat",
    "vakansii_infobiz", "IT_jobs_group", "vakansist_workk", "freelance_chatik0",
    "poiskfreelance", "ggfreelancechat", "biznesassistentiii", "mari_otzyv",
    "mari_vakansiii", "jobospherechat", "freelance_vacancii", "zarabotaemchat",
    "verifka7", "remote_freework", "avitobust", "frilans2001002",
    "mari_vakansii", "solomonidin_chat", "JobDelivery", "frilancer_na_divane",
    "udalenka_chat_vakansii",
]

# Урезанный список для ОБЛАКА (расходный аккаунт): самые продуктивные по тех-заказам.
# Меньше каналов = меньше резолвов = Telegram реже душит новый аккаунт с серверного IP.
CHANNELS_CLOUD = [
    "mari_vakansii", "mari_vakansiii", "freelance_chatik0", "poiskfreelance",
    "profiwork", "jobospherechat", "influencersoffuture", "Freelance_grooup",
    "pixeltechspec", "workchatbuzines", "workk_onchat", "freelance_vacancii",
    "posibleworks", "JobDelivery", "board_axolotl", "FreeWorkFeed",
    "targetsmmvakansii", "vakansiitelegramm", "freelancetaverna", "frilancer_na_divane",
    "ewoxchat", "ggfreelancechat", "proffreelancee", "search_techspec",
    "vakansii_ai", "IT_jobs_group", "talentedpeoples", "remote_freework",
]

# === ТОЛЬКО ЭТИ ТЕМЫ НАС ИНТЕРЕСУЮТ ===
TECH_KEYWORDS = [
    # техспец
    "техспец", "техспециалист", "тех спец", "тех. спец",
    "тех специалист", "тех. специалист", "технический специалист",
    # боты
    "тг бот", "tg бот", "telegram бот", "телеграм бот", "телеграм-бот",
    "чат-бот", "чатбот", "telegram-бот", "телеграм бота", "тг бота",
    "создание бота", "создание ботов", "разработка бота", "разработка ботов",
    "написать бота", "сделать бота", "настройка бота", "настройка ботов",
    # программирование
    "программист", "программирование",
    "разработчик", "разработчика", "разработчику",
    "python", "питон",
    "скрипт", "парсер", "парсинг",
    "бэкенд", "backend",
    # автоматизация / no-code
    "автоматизация", "автоматизировать",
    "n8n", "make.com", "zapier", "no-code", "nocode",
    # вебинары
    "вебинар", "техническое сопровождение", "техподдержка вебинара",
    "сопровождение вебинара", "провести вебинар",
    # интеграции
    "интеграция", "api интеграция",
]

VACANCY_HASHTAGS = [
    "#ищу", "#вакансия", "#вакансии", "#требуется", "#нужен",
    "#ищуспециалиста", "#ищуразработчика", "#ищуисполнителя",
    "#ищукоманду", "#ищуспеца", "#ищупрограммиста", "#ищубота",
    "#ищутехспеца", "#нужентехспец", "#нужен_техспец",
]

EXCLUDE_HASHTAGS = [
    "#помогу", "#резюме", "#ищуработу", "#ищузаказ", "#ищузаказы",
    "#ищупроект", "#ищупроекты", "#ищуподработку", "#портфолио",
    "#исполнитель", "#фрилансер", "#фриланс", "#услуги",
    "#готовпомочь", "#предлагаю", "#предлагаюуслуги",
    "#сделаю", "#выполню", "#разработаю", "#моиуслуги", "#ищуклиентов",
]

# Темы, которые мне НЕ нужны — жёсткий стоп при совпадении
TOPIC_EXCLUDE = [
    "таргетолог", "таргетированн", "таргет реклам",
    "smm", "smmщик", "smm-специалист", "smm специалист",
    "контент-менеджер", "контент менеджер", "контент план",
    "трафик менеджер", "трафик-менеджер", "менеджер по трафику",
    "back вокал", "бэк вокал", "беквокал", "бэк-вокал",
    "модельный скаут", "модель скаут",
    "монтажер", "монтажёр", "видеомонтаж", "видео монтаж",
    "фотограф", "фотосъемка", "фото съемка",
    "дизайнер логотип", "дизайнер сайт", "графический дизайн",
    "администратор инстаграм", "администратор соцсет",
    "тikтoк", "tiktok", "reels", "рилс",
    "озвучк", "голосовые", "диктор",
    "менеджер продаж", "менеджер по продажам",
    "hr менеджер", "рекрутер",
]

VACANCY_KEYWORDS = [
    "ищу", "ищем", "нужен", "нужна", "нужны", "требуется", "требуются",
    "ищется", "в команду", "на проект", "вакансия", "вакансию", "вакансии",
    "кто может", "кто сделает", "кто возьмется", "кто возьмётся", "кто сможет",
    "ищу специалиста", "ищу разработчика", "ищу программиста", "ищу подрядчика",
    "ищу того кто", "ищу спеца", "нужен спец", "нужен специалист",
    "нужен разработчик", "нужен программист", "нужен подрядчик", "нужен исполнитель",
    "в поиске", "посоветуйте кого", "помогите найти", "разыскивается",
    "открыта вакансия", "вакансия открыта",
    "оплата", "бюджет", "заплачу", "оплачу", "за оплату",
    "тз", "техзадание", "хочу заказать", "нужно сделать", "нужно написать",
    "ищем в команду",
]

STRONG_PROMO_KEYWORDS = [
    "ищу заказы", "ищу работу", "ищу проекты", "ищу подработку",
    "ищу клиентов", "ищу заказчиков",
    "я разработчик", "я программист", "я техспец", "я — техспец",
    "я тех специалист", "ваш техспец", "ваш разработчик",
    "мой опыт", "опыт работы", "лет опыта", "опыт более",
    "мой стек", "стек:", "мои навыки",
    "мои услуги", "предлагаю услуги", "предлагаю свои услуги",
    "услуги по разработке", "портфолио", "резюме", "мои кейсы", "кейсы:",
    "помогаю запускать", "я помогаю", "я занимаюсь", "что я делаю",
    "с чем чаще всего приходят", "с чем ко мне приходят",
    "возьму заказ", "возьму проект", "беру заказы", "беру проекты",
    "делаю ботов на заказ", "сделаю бота под ключ",
    "я делаю ботов", "сопровождаю проекты",
]

SELF_PROMO_KEYWORDS = [
    "сделаю", "выполню", "разрабатываю", "пишу ботов",
    "готов взять", "цена от", "стоимость работ", "стоимость от",
]
