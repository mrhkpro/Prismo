from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_supabase_startup_has_no_schema_mutation_or_seed_path():
    source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    lifespan = source.split("async def lifespan", 1)[1].split("# ============================================================\n# APPLICATION", 1)[0]
    assert "if not config.IS_POSTGRES" in lifespan
    assert lifespan.count("Base.metadata.create_all") == 1
    assert lifespan.count("seed_admin(db)") == 1
    # Both operations must be inside the SQLite-only branch; no Postgres schema work.
    assert lifespan.index("Base.metadata.create_all") > lifespan.index("if not config.IS_POSTGRES")
    assert lifespan.index("seed_admin(db)") > lifespan.index("if not config.IS_POSTGRES")


def test_language_switch_pauses_observer_and_does_not_translate_parent_for_each_character_mutation():
    js = (ROOT / "frontend" / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
    assert "translationObserver.disconnect()" in js
    assert "translationObserver.observe(document.body" in js
    # Regression guard for the old O(n^2) observer behavior that re-translated the whole parent.
    assert "translateNode(m.target.parentElement)" not in js
    assert "isTranslating" in js
