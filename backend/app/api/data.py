from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models.schemas import DataExportRequest, DataFileInfo, DataImportResponse, RecoilData

router = APIRouter()
DATA_DIR = Path(__file__).parents[3] / "data"


@router.get("", response_model=list[DataFileInfo])
async def list_data_files():
    DATA_DIR.mkdir(exist_ok=True)
    return [
        DataFileInfo(name=path.stem, path=path.name)
        for path in sorted(DATA_DIR.glob("*.lua"))
        if path.is_file()
    ]


@router.get("/{file_name}", response_model=DataImportResponse)
async def import_data_file(file_name: str):
    path = _resolve_data_file(file_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="data file not found")

    return DataImportResponse(name=path.stem, pattern=_parse_lua_pattern(path.read_text(encoding="utf-8")))


@router.post("", response_model=DataFileInfo)
async def export_data_file(request: DataExportRequest):
    DATA_DIR.mkdir(exist_ok=True)
    safe_name = _safe_file_name(request.name)
    path = DATA_DIR / f"{safe_name}.lua"
    path.write_text(_format_lua_pattern(request.pattern), encoding="utf-8")
    return DataFileInfo(name=safe_name, path=path.name)


def _resolve_data_file(file_name: str) -> Path:
    safe_name = Path(file_name).name
    if not safe_name.endswith(".lua"):
        safe_name = f"{safe_name}.lua"
    return DATA_DIR / safe_name


def _safe_file_name(name: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in name.strip())
    cleaned = cleaned.strip("-")
    if not cleaned:
        raise HTTPException(status_code=400, detail="file name is required")
    return cleaned[:80]


def _parse_lua_pattern(text: str) -> list[RecoilData]:
    import re

    pattern = re.compile(r"\{y\s*=\s*([-\d.]+)\s*,\s*x\s*=\s*([-\d.]+)\}")
    return [RecoilData(y=float(y), x=float(x)) for y, x in pattern.findall(text)]


def _format_lua_pattern(pattern: list[RecoilData]) -> str:
    lines = ["pattern = {"]
    for index, item in enumerate(pattern, start=1):
        lines.append(f"    {{y={round(item.y, 6)}, x={round(item.x, 6)}}},    -- 第{index}发")
    lines.append("}")
    return "\n".join(lines) + "\n"
