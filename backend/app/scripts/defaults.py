from app.scripts.registry import ScriptTargetRegistry
from app.services.lua_generator import LuaGenerator

DEFAULT_SCRIPT_TARGET = "logitech-ghub-lua"


def create_script_target_registry() -> ScriptTargetRegistry:
    registry = ScriptTargetRegistry()
    registry.register(LuaGenerator())
    return registry
