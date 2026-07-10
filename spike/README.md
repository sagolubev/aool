# Sora-2 спайк — результаты (aool scroll landing)

Валидация генерации видео-пролётов для лендинга АУЛ через **Azure OpenAI** (ресурс
g42-openai-sweden-central). Итог: пайплайн работает, идём на полный объём.

## Доступ

- Endpoint: `https://g42-openai-sweden-central.openai.azure.com`
- Ключ: `api-key` активного `[model_providers.azure]` из `~/.codex/config.toml`.
- `api-version=preview` (v1 API surface).

## Важнейший готча по API

Роут — **нативная OpenAI-схема**, НЕ документированный Azure `/video/generations/jobs`
(он даёт 404 на этом ресурсе):

```
POST /openai/v1/videos                 -> {id, status:queued}     (json или multipart)
GET  /openai/v1/videos/{id}            -> poll status/progress
GET  /openai/v1/videos/{id}/content    -> mp4 (h264, 30fps)
GET  /openai/v1/videos                 -> список (восстановление id)
POST /openai/v1/videos/{id}/remix      -> стилевая вариация
```

- **image-to-video**: multipart, поле `input_reference` (файл). Размер референса
  ДОЛЖЕН совпадать с `size` видео (иначе `Inpaint image must match ...`).
- Параметры: `model`, `prompt`, `size` (`1280x720` / `720x1280`), `seconds` (`4/8/12`).

## Что доступно

- `sora-2` (база). **`sora-2-pro` НЕ задеплоен** -> потолок нативно **720p**, выше
  только пост-апскейлом.
- Image-модели: `gpt-image-2`, `gpt-image-1.5`, `dall-e-3` -> для управляемых стиллов.
- **remix** поддерживается (поле `remixed_from_video_id`).

## Подтверждённые приёмы

| Приём | Результат |
|-------|-----------|
| t2v сцена (лес/въезд) | ок, стиль держит |
| i2v из реального рендера дома с сайта | архитектуру сохраняет, photoreal НЕ блокируется |
| Управляемый интерьер: gpt-image-2 стилл -> i2v | контроль мебели/раскладки |
| Единый 12s дубль экстерьер->сквозь стекло->интерьер | бесшовно, без склейки |
| Art-direction lock (единая преамбула `STYLE`) | связный «один мир» по сценам |
| Пост: 1080p lanczos + grade + зерно + webm | заметно чище |

Тайминги: 4s ~60-90с, 8s ~90-120с, 12s ~2-3мин генерации. Вес: 720p 4s ~2.6МБ.

## Файлы

- `sora_lib.py` — хелперы (create/poll/download video, gen_image, `STYLE`).
- `sora_spike.py` — t2v одиночный клип.
- `sora_i2v.py` — image-to-video из референса.
- `iterate_quality.py` — батч (непрерывный дубль + интерьер + след. сцена).
- `out/` — сырые mp4 (gitignored). `final/` — пост (1080p mp4/webm).
- `ref/` — референсы с сайта (gitignored).

## Открытые артефакты

Лёгкий морфинг/артефакты на быстрых участках. Митигация: медленнее камера,
best-of-N (генерить 2-3, брать лучший), seed-вариации, remix проблемных клипов.

## Дальше (Plan 2)

Генерация 6 сцен «путь в дом» + коннекторы этим пайплайном, замена плейсхолдеров
в `scenes.ts`, финальный пост и webm для веба.
