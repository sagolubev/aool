# AOOL

Лендинг посёлка АУЛ: Next.js, React, TypeScript. Публичный репозиторий
`sagolubev/aool`. Сайт: <https://aool.n1o.ru>.

## Проверки

```bash
npm ci
npm run lint
npm run build
npx playwright test
```

Сборка `next build` экспортирует статический сайт в `out/`. Серверные функции
Next.js несовместимы с GitHub Pages.

## Публикация

Workflow `.github/workflows/pages.yml` собирает `out/` и публикует его в ветку
`deployment`. GitHub Pages обслуживает эту ветку с CNAME `aool.n1o.ru`.

DNS CNAME хранится в `sigiuscom/infra-azure`, файл `dns_zone_n1o.ru.tf`.

Секреты в Git не добавляйте. Скрипты Sora в `spike/` читают ключи из локальной
конфигурации и не участвуют в сборке сайта. Сгенерированные видеофайлы в
`public/scroll/` игнорируются Git; проверки используют доступные постеры.
