"""
Configuration de l'interface utilisateur.
"""

DEFAULT_API_URL = "http://localhost:8000"

# Limites et valeurs par défaut
MAX_FILE_SIZE_MB = 5
DEFAULT_PAGE_SIZE = 12
DEFAULT_TOP_N = 10
MAX_TOP_N = 50
DEFAULT_DAYS_LIMIT = 30

PAGE_CONFIG = {
    "page_title": "CV-Optimizer",
    "page_icon": "🧭",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

NAV_ITEMS = [
    {
        "key": "home",
        "label": "Accueil",
        "nav_label": "Accueil",
        "icon": "🏠",
        "description": "Vue d'ensemble de la plateforme et des actions prioritaires.",
    },
    {
        "key": "matching",
        "label": "Matching CV",
        "nav_label": "Matching",
        "icon": "🎯",
        "description": "Comparer un CV aux opportunites deja collectees.",
    },
    {
        "key": "jobs",
        "label": "Opportunites",
        "nav_label": "Offres d'emploi",
        "icon": "🔎",
        "description": "Explorer, filtrer et analyser les offres du marche.",
    },
    {
        "key": "advice",
        "label": "Coach IA",
        "nav_label": "Coach IA",
        "icon": "✍️",
        "description": "Ameliorer une candidature a partir d'une offre cible.",
    },
    {
        "key": "cover_letter",
        "label": "Lettre de motivation",
        "nav_label": "Lettre de Motivation",
        "icon": "✉️",
        "description": "Generer une lettre de motivation a partir du CV et d'une offre.",
    },
    {
        "key": "admin",
        "label": "Pilotage",
        "nav_label": "Pilotage",
        "icon": "⚙️",
        "description": "Suivre la collecte, la fraicheur et la qualite des donnees.",
    },
]

PAGE_META = {item["key"]: item for item in NAV_ITEMS}

ERROR_MESSAGES = {
    "api_unavailable": "L'API n'est pas accessible pour le moment.",
    "invalid_api_key": "API key invalide.",
    "file_required": "Veuillez ajouter un CV PDF.",
    "keywords_required": "Ajoutez au moins un mot-clé.",
}

SUCCESS_MESSAGES = {
    "collection_started": "Collecte lancée avec succès.",
    "reindex_started": "Réindexation lancée.",
    "stats_loaded": "Statistiques chargées.",
}

CUSTOM_CSS = """
<style>
    :root {
        --bg: #fbf4ea;
        --surface: rgba(255, 250, 243, 0.96);
        --surface-strong: #fffdf9;
        --line: #ebddca;
        --ink: #3d4c45;
        --muted: #6f7668;
        --accent: #e48a49;
        --accent-soft: #f7d6b8;
        --sage: #89a788;
        --sage-soft: #e5efe0;
        --gold: #efc06d;
        --gold-soft: #fae8c0;
        --success: #547d59;
        --error: #bb6a56;
        --warning: #b4832f;
    }

    html, body, [class*="css"]  {
        font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top right, rgba(239, 192, 109, 0.22), transparent 28%),
            radial-gradient(circle at 15% 15%, rgba(137, 167, 136, 0.14), transparent 24%),
            radial-gradient(circle at 50% 100%, rgba(228, 138, 73, 0.10), transparent 28%),
            linear-gradient(180deg, #fffaf3 0%, #fbf4ea 100%);
        color: var(--ink);
    }

    .block-container {
        padding-top: 0.85rem;
        padding-bottom: 3rem;
        max-width: 1320px;
    }

    [data-testid="stSidebar"] {
        background:
            radial-gradient(circle at top right, rgba(228, 138, 73, 0.16), transparent 34%),
            linear-gradient(180deg, #fff7ee 0%, #f9efdf 54%, #eef3e6 100%);
        border-right: 1px solid rgba(228, 138, 73, 0.12);
    }

    [data-testid="stSidebar"] * {
        color: var(--ink);
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: var(--ink) !important;
    }

    .app-frame {
        background: rgba(255, 255, 255, 0.42);
        border: 1px solid rgba(255, 255, 255, 0.52);
        backdrop-filter: blur(16px);
        border-radius: 26px;
        padding: 0.7rem;
    }

    .hero-panel {
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(circle at top right, rgba(255, 255, 255, 0.42), transparent 28%),
            linear-gradient(135deg, #fff2df 0%, #f7cfac 48%, #e4efdd 100%);
        color: var(--ink);
        border: 1px solid rgba(228, 138, 73, 0.14);
        border-radius: 28px;
        padding: 2rem 2rem 1.75rem 2rem;
        box-shadow: 0 20px 42px rgba(202, 150, 101, 0.14);
        margin-bottom: 1.5rem;
    }

    .hero-panel::after {
        content: "";
        position: absolute;
        width: 240px;
        height: 240px;
        right: -60px;
        top: -70px;
        background: radial-gradient(circle, rgba(228, 138, 73, 0.26), transparent 70%);
        pointer-events: none;
    }

    .hero-eyebrow {
        margin: 0 0 0.85rem 0;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        font-size: 0.74rem;
        color: rgba(61, 76, 69, 0.62);
    }

    .hero-title {
        font-size: 2.7rem;
        line-height: 1.04;
        margin: 0;
        font-weight: 750;
        letter-spacing: -0.03em;
    }

    .hero-copy {
        margin: 0.9rem 0 0 0;
        max-width: 760px;
        color: rgba(61, 76, 69, 0.84);
        font-size: 1.02rem;
        line-height: 1.65;
    }

    .marketing-hero {
        position: relative;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        background:
            radial-gradient(circle at 82% 18%, rgba(228, 138, 73, 0.16), transparent 22%),
            radial-gradient(circle at 18% 20%, rgba(137, 167, 136, 0.10), transparent 18%),
            linear-gradient(180deg, rgba(255, 253, 248, 0.99), rgba(252, 245, 235, 0.98));
        border: 1px solid rgba(228, 138, 73, 0.12);
        border-radius: 34px;
        padding: 3.4rem 2.2rem 2.6rem 2.2rem;
        box-shadow: 0 20px 48px rgba(198, 164, 125, 0.10);
        margin-bottom: 1.35rem;
    }

    .marketing-eyebrow {
        margin: 0;
        width: 100%;
        text-align: center;
        font-size: 0.78rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: rgba(61, 76, 69, 0.62);
    }

    .marketing-title {
        margin: 1rem auto 0 auto;
        max-width: 900px;
        text-align: center;
        color: var(--ink);
        font-size: 3.45rem;
        line-height: 1.06;
        font-weight: 790;
        letter-spacing: -0.05em;
    }

    .marketing-title span {
        color: var(--accent);
    }

    .marketing-copy {
        margin: 1.1rem auto 0 auto;
        max-width: 760px;
        text-align: center;
        color: rgba(61, 76, 69, 0.84);
        font-size: 1.08rem;
        line-height: 1.72;
    }

    .marketing-badges {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.7rem;
        margin-top: 1.45rem;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.6rem 0.9rem;
        border-radius: 999px;
        background: rgba(255, 252, 246, 0.96);
        border: 1px solid rgba(228, 138, 73, 0.14);
        color: var(--ink);
        font-size: 0.9rem;
        box-shadow: 0 12px 24px rgba(198, 164, 125, 0.08);
    }

    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1.25rem;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        padding: 0.46rem 0.8rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.62);
        border: 1px solid rgba(228, 138, 73, 0.14);
        color: var(--ink);
        font-size: 0.86rem;
    }

    .section-heading {
        margin: 0.6rem 0 0.8rem 0;
    }

    .section-title {
        margin: 0;
        font-size: 1.35rem;
        font-weight: 720;
        letter-spacing: -0.02em;
        color: var(--ink);
    }

    .section-copy {
        margin: 0.35rem 0 0 0;
        color: var(--muted);
        font-size: 0.96rem;
        line-height: 1.6;
    }

    .surface-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 1.2rem;
        box-shadow: 0 16px 34px rgba(198, 164, 125, 0.12);
        margin-bottom: 1rem;
        overflow: hidden;
    }

    .metric-card {
        background: linear-gradient(180deg, rgba(255, 253, 248, 0.98), rgba(252, 241, 230, 0.95));
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1rem 1.05rem;
        box-shadow: 0 14px 28px rgba(198, 164, 125, 0.10);
        min-height: 144px;
        overflow: hidden;
    }

    .metric-card.accent {
        background: linear-gradient(180deg, rgba(228, 138, 73, 0.18), rgba(255, 252, 246, 0.98));
    }

    .metric-card.sage {
        background: linear-gradient(180deg, rgba(137, 167, 136, 0.18), rgba(255, 252, 246, 0.98));
    }

    .metric-card.gold {
        background: linear-gradient(180deg, rgba(239, 192, 109, 0.20), rgba(255, 252, 246, 0.98));
    }

    .metric-label {
        margin: 0;
        color: var(--muted);
        font-size: 0.84rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }

    .metric-value {
        margin: 0.7rem 0 0 0;
        color: var(--ink);
        font-size: 2rem;
        font-weight: 760;
        letter-spacing: -0.04em;
    }

    .metric-detail {
        margin: 0.45rem 0 0 0;
        color: var(--muted);
        font-size: 0.93rem;
        line-height: 1.5;
    }

    .info-card {
        border-radius: 22px;
        padding: 1.15rem;
        border: 1px solid var(--line);
        background: var(--surface);
        margin-bottom: 1rem;
        overflow: hidden;
    }

    .info-card.sage {
        background: linear-gradient(180deg, rgba(137, 167, 136, 0.16), rgba(255, 252, 246, 0.96));
    }

    .info-card.accent {
        background: linear-gradient(180deg, rgba(228, 138, 73, 0.16), rgba(255, 252, 246, 0.96));
    }

    .info-card.gold {
        background: linear-gradient(180deg, rgba(239, 192, 109, 0.18), rgba(255, 252, 246, 0.96));
    }

    .info-title {
        margin: 0;
        color: var(--ink);
        font-size: 1.02rem;
        font-weight: 720;
    }

    .info-body {
        margin: 0.55rem 0 0 0;
        color: var(--muted);
        line-height: 1.65;
        font-size: 0.95rem;
    }

    .status-banner {
        border-radius: 18px;
        padding: 0.95rem 1rem;
        border: 1px solid transparent;
        margin: 0.8rem 0 1rem 0;
        font-weight: 600;
        line-height: 1.5;
    }

    .status-success {
        background: rgba(84, 125, 89, 0.14);
        border-color: rgba(84, 125, 89, 0.18);
        color: var(--success);
    }

    .status-warning {
        background: rgba(239, 192, 109, 0.18);
        border-color: rgba(239, 192, 109, 0.20);
        color: var(--warning);
    }

    .status-error {
        background: rgba(187, 106, 86, 0.14);
        border-color: rgba(187, 106, 86, 0.20);
        color: var(--error);
    }

    .tag-cloud {
        display: flex;
        flex-wrap: wrap;
        gap: 0.62rem;
        margin-top: 0.8rem;
        align-items: center;
    }

    .tag {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 0.78rem;
        border-radius: 999px;
        background: var(--surface-strong);
        border: 1px solid var(--line);
        color: var(--ink);
        font-size: 0.86rem;
        line-height: 1.4;
        text-align: left;
        white-space: normal;
    }

    .tag.sage {
        background: rgba(137, 167, 136, 0.16);
    }

    .tag.accent {
        background: rgba(228, 138, 73, 0.16);
    }

    .tag.gold {
        background: rgba(239, 192, 109, 0.18);
    }

    .job-card {
        background: linear-gradient(180deg, rgba(255, 253, 248, 0.98), rgba(252, 244, 236, 0.95));
    }

    .job-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        min-width: 0;
    }

    .job-main {
        min-width: 0;
        flex: 1 1 auto;
    }

    .job-company {
        margin: 0;
        color: var(--accent);
        font-size: 0.86rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 700;
    }

    .job-title {
        margin: 0.35rem 0 0 0;
        color: var(--ink);
        font-size: 1.2rem;
        line-height: 1.35;
        font-weight: 750;
        overflow-wrap: anywhere;
    }

    .job-meta-row {
        margin-top: 0.95rem;
    }

    .job-description {
        margin: 0.9rem 0 0 0;
        color: var(--muted);
        line-height: 1.65;
        font-size: 0.94rem;
        overflow-wrap: anywhere;
    }

    .score-pill {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        min-width: 96px;
        padding: 0.5rem 0.75rem;
        border-radius: 16px;
        font-weight: 700;
        color: white;
        background: linear-gradient(135deg, #6e9b72, #8eb28d);
    }

    .score-pill.medium {
        background: linear-gradient(135deg, #db9550, #efc06d);
    }

    .score-pill.low {
        background: linear-gradient(135deg, #c47f67, #d59b84);
    }

    .top-nav-sentinel {
        display: none;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.top-nav-sentinel) {
        position: sticky;
        top: 0.45rem;
        z-index: 1000;
        background: rgba(255, 248, 239, 0.94);
        backdrop-filter: blur(18px);
        border: 1px solid rgba(235, 221, 202, 0.96);
        box-shadow: 0 12px 30px rgba(198, 164, 125, 0.12);
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.top-nav-sentinel) > div {
        padding: 0.4rem 0.85rem 0.65rem 0.85rem;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.top-nav-sentinel) p {
        margin-bottom: 0;
    }

    .utility-strip {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 1.15rem;
        margin-bottom: 0.7rem;
        padding: 0.55rem 0.8rem;
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(255, 250, 243, 0.98), rgba(248, 239, 227, 0.96));
        border: 1px solid rgba(235, 221, 202, 0.96);
    }

    .utility-item {
        color: var(--muted);
        font-size: 0.82rem;
        font-weight: 600;
        white-space: nowrap;
    }

    .utility-rating {
        color: var(--accent);
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.top-nav-sentinel) .stButton > button {
        min-height: 2.85rem;
        white-space: nowrap;
        font-size: 0.94rem;
        padding: 0.5rem 1rem;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.top-nav-sentinel) .stButton > button[kind="primary"] {
        border-color: rgba(228, 138, 73, 0.22);
        background: linear-gradient(135deg, #ea9555, #db7e49);
        box-shadow: 0 12px 22px rgba(228, 138, 73, 0.20);
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.top-nav-sentinel) .stButton > button[kind="secondary"] {
        border: none;
        background: transparent;
        color: var(--ink);
        box-shadow: none;
        font-weight: 670;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.top-nav-sentinel) .stButton > button[kind="secondary"]:hover {
        background: rgba(228, 138, 73, 0.08);
        color: var(--accent);
        box-shadow: none;
        border: none;
    }

    .top-nav-brand {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        justify-content: center;
        min-height: 2.85rem;
        padding: 0.12rem 0.15rem;
    }

    .brand-wordmark {
        display: flex;
        align-items: center;
        gap: 0.78rem;
        min-height: 2.85rem;
        padding: 0.08rem 0.1rem;
    }

    .brand-wordmark-icon {
        width: 3rem;
        height: 3rem;
        flex: 0 0 auto;
        filter: drop-shadow(0 10px 18px rgba(198, 164, 125, 0.16));
    }

    .brand-wordmark-copy {
        min-width: 0;
    }

    .brand-wordmark-title {
        margin: 0;
        color: var(--ink);
        font-size: 1.14rem;
        font-weight: 780;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }

    .brand-wordmark-subtitle {
        margin: 0.16rem 0 0 0;
        color: var(--muted);
        font-size: 0.78rem;
        line-height: 1.35;
        white-space: nowrap;
    }

    .top-nav-logo {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 16px;
        background: linear-gradient(135deg, rgba(247, 214, 184, 0.82), rgba(250, 232, 192, 0.9));
        color: var(--accent);
        font-size: 0.98rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        border: 1px solid rgba(228, 138, 73, 0.12);
    }

    .top-nav-brand-copy {
        min-width: 0;
    }

    .top-nav-kicker {
        margin: 0;
        font-size: 0.7rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: rgba(111, 118, 104, 0.72);
    }

    .top-nav-title {
        margin: 0.18rem 0 0 0;
        color: var(--ink);
        font-size: 1.12rem;
        font-weight: 760;
        letter-spacing: -0.02em;
    }

    .top-nav-active {
        margin: 0.14rem 0 0 0;
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.4;
    }

    .top-nav-status {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        margin-bottom: 0.5rem;
        min-height: 2.85rem;
        padding: 0.55rem 0.8rem;
        border-radius: 999px;
        font-size: 0.84rem;
        font-weight: 700;
        border: 1px solid transparent;
    }

    .top-nav-status.live {
        background: rgba(137, 167, 136, 0.14);
        border-color: rgba(137, 167, 136, 0.20);
        color: var(--success);
    }

    .top-nav-status.demo {
        background: rgba(239, 192, 109, 0.18);
        border-color: rgba(239, 192, 109, 0.22);
        color: var(--warning);
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 252, 246, 0.9);
        border: 1px solid var(--line);
        border-radius: 24px;
        box-shadow: 0 14px 30px rgba(198, 164, 125, 0.10);
    }

    [data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 0.8rem 0.95rem 0.6rem 0.95rem;
    }

    .stButton > button[kind="primary"],
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        border-radius: 999px;
        border: 1px solid rgba(228, 138, 73, 0.18);
        background: linear-gradient(135deg, #ea9555, #db7e49);
        color: white;
        font-weight: 700;
        padding: 0.62rem 1.05rem;
        box-shadow: 0 12px 26px rgba(228, 138, 73, 0.20);
        transition: transform 0.16s ease, box-shadow 0.16s ease;
    }

    .stButton > button[kind="secondary"] {
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(255, 252, 246, 0.96);
        color: var(--ink);
        font-weight: 650;
        padding: 0.62rem 1.05rem;
        box-shadow: none;
        transition: transform 0.16s ease, box-shadow 0.16s ease;
    }

    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover,
    .stButton > button[kind="secondary"]:hover {
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        box-shadow: 0 16px 32px rgba(228, 138, 73, 0.24);
        border-color: rgba(255, 255, 255, 0.28);
    }

    .stButton > button[kind="secondary"]:hover {
        box-shadow: 0 10px 20px rgba(198, 164, 125, 0.10);
        border-color: rgba(228, 138, 73, 0.22);
    }

    .marketing-actions-sentinel {
        display: none;
    }

    [data-testid="stVerticalBlock"]:has(.marketing-actions-sentinel) .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ea9555, #db7e49);
        border-color: rgba(228, 138, 73, 0.18);
        box-shadow: 0 14px 28px rgba(228, 138, 73, 0.22);
    }

    [data-testid="stVerticalBlock"]:has(.marketing-actions-sentinel) .stButton > button[kind="secondary"] {
        background: rgba(255, 252, 246, 0.98);
        border-color: rgba(235, 221, 202, 0.96);
        color: var(--ink);
        box-shadow: 0 10px 24px rgba(198, 164, 125, 0.08);
    }

    @media (max-width: 1100px) {
        [data-testid="stVerticalBlockBorderWrapper"]:has(.top-nav-sentinel) .stButton > button {
            font-size: 0.85rem;
            padding-left: 0.72rem;
            padding-right: 0.72rem;
        }

        .brand-wordmark-title {
            font-size: 1rem;
        }

        .brand-wordmark-subtitle {
            font-size: 0.78rem;
        }

        .marketing-title {
            font-size: 2.7rem;
        }
    }

    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stNumberInput input {
        border-radius: 16px !important;
        border: 1px solid var(--line) !important;
        background: rgba(255, 252, 246, 0.95) !important;
        color: var(--ink) !important;
    }

    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border-radius: 16px !important;
        border: 1px solid var(--line) !important;
        background: rgba(255, 252, 246, 0.95) !important;
    }

    .stSlider [data-baseweb="slider"] {
        padding-top: 0.65rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 252, 246, 0.88);
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 0.55rem 0.95rem;
        color: var(--ink);
        font-weight: 650;
    }

    .stTabs [aria-selected="true"] {
        background: #e48a49 !important;
        color: white !important;
    }

    .stExpander {
        border: 1px solid var(--line);
        border-radius: 18px !important;
        background: rgba(255, 252, 246, 0.92);
        box-shadow: 0 10px 24px rgba(27, 41, 48, 0.04);
    }

    .stAlert {
        border-radius: 18px;
        border: 1px solid var(--line);
    }

    .stFileUploader {
        background: rgba(255, 252, 246, 0.94);
        border-radius: 18px;
        border: 1px dashed rgba(109, 133, 116, 0.42);
        padding: 0.35rem 0.45rem;
    }

    .upload-shell {
        padding: 1rem;
        border-radius: 18px;
        border: 1px dashed rgba(137, 167, 136, 0.40);
        background: linear-gradient(180deg, rgba(137, 167, 136, 0.12), rgba(255, 252, 246, 0.96));
        margin-bottom: 0.8rem;
    }

    .upload-title {
        margin: 0;
        color: var(--ink);
        font-size: 1rem;
        font-weight: 700;
    }

    .upload-copy {
        margin: 0.45rem 0 0 0;
        color: var(--muted);
        font-size: 0.93rem;
        line-height: 1.55;
    }

    .small-note {
        margin: 0.4rem 0 0 0;
        color: var(--muted);
        font-size: 0.86rem;
    }

    .timeline {
        display: grid;
        gap: 0.7rem;
        margin-top: 0.8rem;
    }

    .timeline-shell {
        padding: 1.25rem;
    }

    .timeline-step {
        display: grid;
        grid-template-columns: 34px 1fr;
        gap: 0.85rem;
        align-items: start;
    }

    .timeline-content {
        min-width: 0;
    }

    .timeline-index {
        width: 34px;
        height: 34px;
        border-radius: 12px;
        display: flex;
        justify-content: center;
        align-items: center;
        background: rgba(228, 138, 73, 0.16);
        color: var(--accent);
        font-weight: 800;
    }

    .timeline-title {
        margin: 0;
        color: var(--ink);
        font-weight: 700;
        font-size: 0.96rem;
        overflow-wrap: anywhere;
    }

    .timeline-copy {
        margin: 0.18rem 0 0 0;
        color: var(--muted);
        line-height: 1.55;
        font-size: 0.92rem;
        overflow-wrap: anywhere;
    }

    [data-testid="column"] {
        min-width: 0;
    }

    @media (max-width: 900px) {
        .hero-title {
            font-size: 2.1rem;
        }

        .marketing-title {
            font-size: 2.2rem;
        }

        .marketing-copy {
            font-size: 0.98rem;
        }

        .block-container {
            padding-top: 1.2rem;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:has(.top-nav-sentinel) {
            top: 0.4rem;
        }
    }
</style>
"""
