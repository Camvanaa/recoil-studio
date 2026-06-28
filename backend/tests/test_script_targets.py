import pytest

from app.models.schemas import GunConfig, RecoilData
from app.scripts.defaults import DEFAULT_SCRIPT_TARGET, create_script_target_registry
from app.scripts.registry import ScriptTargetRegistry
from app.services.lua_generator import LuaGenerator


def test_default_script_target_registry_generates_ghub_lua():
    registry = create_script_target_registry()
    target = registry.get(DEFAULT_SCRIPT_TARGET)

    lua_code = target.generate([GunConfig(name="AK", pattern=[RecoilData(y=1, x=2)])])

    assert target.name == "Logitech G HUB Lua"
    assert 'name = "AK"' in lua_code


def test_script_target_registry_rejects_duplicate_targets():
    registry = ScriptTargetRegistry()

    registry.register(LuaGenerator())

    with pytest.raises(ValueError, match="already registered"):
        registry.register(LuaGenerator())


def test_script_target_registry_reports_unknown_targets():
    registry = ScriptTargetRegistry()

    with pytest.raises(KeyError, match="unknown script target"):
        registry.get("missing")
