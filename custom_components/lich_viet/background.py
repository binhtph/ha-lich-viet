"""Ảnh nền: thư mục ảnh theo dịp trên HA, kết hợp ảnh Unsplash."""

from __future__ import annotations

from datetime import date, timedelta
import hashlib
from http import HTTPStatus
import logging
from pathlib import Path
import random
from typing import Any
from urllib.parse import quote, urlsplit

from aiohttp import ClientError, web

from homeassistant.components.http import HomeAssistantView
from homeassistant.components.http.auth import async_sign_path
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BG_ENABLED,
    CONF_BG_FOLDER,
    CONF_BG_MODE,
    CONF_UNSPLASH_KEY,
    CONF_UNSPLASH_MIX,
    CONF_UNSPLASH_QUERY,
    DEFAULT_BG_MODE,
    DEFAULT_UNSPLASH_QUERY,
    DOMAIN,
    IMAGE_EXTENSIONS,
)
from .events import BACKGROUND_FOLDERS, background_folders_for

_LOGGER = logging.getLogger(__name__)
UNSPLASH_API = "https://api.unsplash.com/photos/random"
UNSPLASH_API_HOST = "api.unsplash.com"
UTM = "utm_source=home_assistant_lich_viet&utm_medium=referral"
LINK_TTL = timedelta(hours=12)


def default_base_dir(hass: HomeAssistant) -> str:
    """Thư mục ảnh mặc định: <thư mục media đầu tiên>/lich_viet (HAOS: /media/lich_viet)."""
    media = next(iter(hass.config.media_dirs.values()), hass.config.path("media"))
    return str(Path(media) / "lich_viet")


def title_from_filename(name: str) -> str:
    """'vinh-ha-long.jpg' -> 'Vinh ha long'; 'Vịnh Hạ Long.jpg' -> 'Vịnh Hạ Long'."""
    stem = Path(name).stem.replace("_", " ").replace("-", " ").strip()
    stem = " ".join(stem.split())
    return stem[:1].upper() + stem[1:] if stem else ""


def _list_images(base: Path, folder: str) -> list[str]:
    path = base / folder
    if not path.is_dir():
        return []
    return sorted(
        p.name for p in path.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS and not p.name.startswith(".")
    )


def _ensure_folders(base: Path) -> None:
    for folder in BACKGROUND_FOLDERS:
        (base / folder).mkdir(parents=True, exist_ok=True)


def _pick(items: list[Any], seed: str | None) -> Any:
    if seed is None:
        return random.choice(items)
    digest = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return items[digest % len(items)]


class BackgroundManager:
    """Chọn ảnh nền cho trang Lịch Việt."""

    def __init__(self, hass: HomeAssistant, runtime: Any) -> None:
        self.hass = hass
        self.runtime = runtime
        self._override: tuple[date, dict[str, Any]] | None = None

    @property
    def options(self) -> dict[str, Any]:
        return self.runtime.options

    @property
    def base_dir(self) -> Path:
        return Path(self.options.get(CONF_BG_FOLDER) or default_base_dir(self.hass))

    async def async_setup(self) -> None:
        """Tạo sẵn các thư mục ảnh (chung, tet, trung_thu...) nếu được."""
        try:
            await self.hass.async_add_executor_job(_ensure_folders, self.base_dir)
        except OSError as err:
            _LOGGER.info("Không tạo được thư mục ảnh %s: %s", self.base_dir, err)

    # ------------------------------------------------------------ nguồn ảnh
    async def async_local_candidates(self, today: date) -> list[dict[str, Any]]:
        """Ảnh trong thư mục theo dịp (nếu có) hoặc thư mục chung."""
        base = self.base_dir
        for folder in [*background_folders_for(today), "chung"]:
            files = await self.hass.async_add_executor_job(_list_images, base, folder)
            if files:
                return [
                    {"source": "local", "folder": folder, "file": f, "title": title_from_filename(f)}
                    for f in files
                ]
        return []

    async def async_unsplash_candidates(self, today: date) -> list[dict[str, Any]]:
        key = (self.options.get(CONF_UNSPLASH_KEY) or "").strip()
        if not key:
            return []
        cache = self.runtime.unsplash_cache
        if cache.get("date") == today.isoformat() and cache.get("photos"):
            return cache["photos"]
        query = self.options.get(CONF_UNSPLASH_QUERY) or DEFAULT_UNSPLASH_QUERY
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                UNSPLASH_API,
                params={"query": query, "orientation": "landscape", "count": "30", "content_filter": "high"},
                headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"},
                timeout=15,
            ) as resp:
                if resp.status != HTTPStatus.OK:
                    _LOGGER.warning("Unsplash trả về lỗi %s", resp.status)
                    return cache.get("photos", [])
                data = await resp.json()
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.warning("Không lấy được ảnh Unsplash: %s", err)
            return cache.get("photos", [])
        photos = [_unsplash_item(p) for p in data if isinstance(p, dict) and p.get("urls")]
        self.runtime.unsplash_cache = {"date": today.isoformat(), "photos": photos}
        self.runtime.schedule_save()
        return photos

    # ------------------------------------------------------------ chọn ảnh
    async def async_get(self, *, change: bool = False) -> dict[str, Any] | None:
        """Ảnh nền cho hôm nay (đã có URL tải). None nếu tắt hoặc không có ảnh."""
        if not self.options.get(CONF_BG_ENABLED, True):
            return None
        today = self.runtime.today
        if not change and self._override and self._override[0] == today:
            return self._with_url(self._override[1])

        local = await self.async_local_candidates(today)
        candidates = list(local)
        if not local or self.options.get(CONF_UNSPLASH_MIX, False):
            candidates += await self.async_unsplash_candidates(today)
        if not candidates:
            return None

        daily = self.options.get(CONF_BG_MODE, DEFAULT_BG_MODE) == "daily"
        if change:
            if self._override and self._override[0] == today:
                current = self._override[1]
            else:
                current = _pick(candidates, today.isoformat()) if daily else None
            pool = [c for c in candidates if c != current] or candidates
            item = random.choice(pool)
            self._override = (today, item)
        else:
            item = _pick(candidates, today.isoformat() if daily else None)
        if item["source"] == "unsplash":
            self.hass.async_create_task(self._async_track_unsplash_download(item))
        return self._with_url(item)

    def _with_url(self, item: dict[str, Any]) -> dict[str, Any]:
        result = dict(item)
        if item["source"] == "local":
            path = f"/api/{DOMAIN}/background/{quote(item['folder'])}/{quote(item['file'])}"
            result["url"] = async_sign_path(self.hass, path, LINK_TTL)
        result.pop("download_location", None)
        return result

    async def _async_track_unsplash_download(self, item: dict[str, Any]) -> None:
        """Unsplash yêu cầu báo 'download' khi ảnh được dùng."""
        key = (self.options.get(CONF_UNSPLASH_KEY) or "").strip()
        url = item.get("download_location")
        if not key or not url:
            return
        if not _is_unsplash_api(url):
            # Không gửi access key tới host khác api.unsplash.com.
            _LOGGER.warning("Bỏ qua download_location không thuộc %s: %s", UNSPLASH_API_HOST, url)
            return
        try:
            async with async_get_clientsession(self.hass).get(
                url, headers={"Authorization": f"Client-ID {key}"}, timeout=10,
                allow_redirects=False,
            ):
                pass
        except (ClientError, TimeoutError):
            pass

    def resolve_file(self, folder: str, filename: str) -> Path | None:
        """Đường dẫn file ảnh hợp lệ (chống truy cập ngoài thư mục)."""
        if folder not in BACKGROUND_FOLDERS or "/" in filename or "\\" in filename or filename.startswith("."):
            return None
        if Path(filename).suffix.lower() not in IMAGE_EXTENSIONS:
            return None
        base = self.base_dir.resolve()
        path = (base / folder / filename).resolve()
        if base not in path.parents or not path.is_file():
            return None
        return path


def _is_unsplash_api(url: Any) -> bool:
    """URL là https://api.unsplash.com/... (không user/pass, cổng mặc định)."""
    if not isinstance(url, str):
        return False
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    return (
        parts.scheme == "https"
        and parts.hostname == UNSPLASH_API_HOST
        and parts.username is None
        and parts.password is None
        and port in (None, 443)
    )


def _unsplash_item(photo: dict[str, Any]) -> dict[str, Any]:
    user = photo.get("user") or {}
    location = (photo.get("location") or {}).get("name") or ""
    title = location or photo.get("description") or photo.get("alt_description") or ""
    regular = photo["urls"].get("regular") or photo["urls"].get("full")
    return {
        "source": "unsplash",
        "id": photo.get("id"),
        "title": (title[:1].upper() + title[1:])[:80] if title else "",
        "url": f"{regular}&w=2048" if regular and "?" in regular else regular,
        "credit": user.get("name", ""),
        "credit_url": f"{(user.get('links') or {}).get('html', 'https://unsplash.com')}?{UTM}",
        "photo_url": f"{(photo.get('links') or {}).get('html', 'https://unsplash.com')}?{UTM}",
        "unsplash_url": f"https://unsplash.com/?{UTM}",
        "download_location": (photo.get("links") or {}).get("download_location"),
    }


class BackgroundView(HomeAssistantView):
    """GET /api/lich_viet/background/<thư mục>/<file> (cần đăng nhập hoặc link ký)."""

    url = f"/api/{DOMAIN}/background/{{folder}}/{{filename}}"
    name = f"api:{DOMAIN}:background"
    requires_auth = True

    async def get(self, request: web.Request, folder: str, filename: str) -> web.StreamResponse:
        hass: HomeAssistant = request.app["hass"]
        runtime = hass.data.get(DOMAIN)
        if runtime is None or runtime.background is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)
        path = await hass.async_add_executor_job(runtime.background.resolve_file, folder, filename)
        if path is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)
        return web.FileResponse(path, headers={"Cache-Control": "private, max-age=86400"})
