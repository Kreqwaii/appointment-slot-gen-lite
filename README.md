# appointment-slot-gen-lite (`slot_gen.py`)

Zero-dependency Python 3.9+ CLI utility for generating available appointment slots based on working hours, service duration, grid step, buffer time, breaks, and existing bookings.

---

## Features / Возможности

- **Zero dependencies** — pure Python 3.9+ standard library.
- **Flexible scheduling** — working hours, custom service duration, custom grid step, and buffer time around bookings.
- **Breaks & bookings** — repeatable `--break` and `--booked` intervals (`HH:MM-HH:MM`).
- **JSON output** — `--json` flag for easy integration with bots, APIs, and scripts.
- **Built-in self-test** — `--self-test` verifies core logic.

---

## Quick Start / Быстрый старт

### 1. Basic usage / Базовый запуск

```bash
python slot_gen.py --work 09:00-18:00 --duration 60 --break 13:00-14:00 --booked 10:00-11:30 --booked 15:00-16:00
```

Output:
```text
09:00-10:00
12:00-13:00
14:00-15:00
16:00-17:00
17:00-18:00
```

### 2. Custom step, buffer, and JSON output / Шаг сетки, буфер и JSON

```bash
python slot_gen.py --work 10:00-14:00 --duration 45 --step 30 --buffer 15 --booked 11:00-11:30 --json
```

### 3. Self-test / Самопроверка

```bash
python slot_gen.py --self-test
```

---

## CLI Options / Параметры CLI

| Flag | Default | Description |
|---|---|---|
| `--work` | `09:00-18:00` | Working hours (`HH:MM-HH:MM`) / Рабочие часы |
| `--duration` | `60` | Service duration in minutes / Длительность услуги (мин) |
| `--step` | `duration` | Grid step in minutes / Шаг сетки (мин) |
| `--buffer` | `0` | Buffer minutes around bookings / Буфер вокруг броней (мин) |
| `--break` | `[]` | Break interval (`HH:MM-HH:MM`, repeatable) / Перерыв |
| `--booked` | `[]` | Booked interval (`HH:MM-HH:MM`, repeatable) / Занятые слоты |
| `--min-start` | `None` | Earliest allowed start time (`HH:MM`) / Минимальное время старта |
| `--json` | `false` | Output as JSON / Вывод в формате JSON |
| `--self-test` | `false` | Run built-in tests / Запустить встроенные тесты |

---

## Need Full Telegram Bot with SQLite, Admin Panel & 24h/2h Auto-Reminders?

If you need a production-ready **Telegram Appointment & Booking Bot** with:
- SQLite database & persistent bookings
- Interactive inline calendar & slot picker
- Admin panel (manage services, schedules, cancellations)
- Automatic **24h and 2h client reminders**

Check out the full Pro version on FunPay:
- **Pro Bot Offer:** https://funpay.com/lots/offer?id=82600835
- **All Solutions / Storefront:** https://funpay.com/users/20096179/

---

## License

MIT License — see [LICENSE](LICENSE).
