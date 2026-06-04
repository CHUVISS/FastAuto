"""
Production seed: 32 car listings across 12 models (BMW + Audi).

Usage (on server, after all containers are healthy):
    docker exec app-backend-1 python scripts/seed_prod_listings.py

Re-run safely: existing listings by these sellers are skipped unless you pass --reset:
    docker exec app-backend-1 python scripts/seed_prod_listings.py --reset
"""

from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session_factory
from app.core.log import configure_logging
from app.core.storage import get_image_storage
from app.crud.users import create_user, get_user_by_email
from app.models.users import UserRole
from app.schemas.users import UserCreate
from app.services.images.image_service import process_image

configure_logging(settings)
log = structlog.get_logger(__name__)

_PHOTO_DIR = Path(__file__).resolve().parent.parent / "data" / "seed_photos"

_SELLERS: list[dict[str, str]] = [
    {
        "email": "alexander.petrov@example.com",
        "full_name": "Александр Петров",
        "phone": "79161112233",
    },
    {
        "email": "dmitry.sokolov@example.com",
        "full_name": "Дмитрий Соколов",
        "phone": "79162223344",
    },
    {
        "email": "mikhail.ivanov@example.com",
        "full_name": "Михаил Иванов",
        "phone": "79163334455",
    },
    {
        "email": "elena.gromova@example.com",
        "full_name": "Елена Громова",
        "phone": "79164445566",
    },
    {
        "email": "andrey.morozov@example.com",
        "full_name": "Андрей Морозов",
        "phone": "79165556677",
    },
    {
        "email": "sergey.volkov@example.com",
        "full_name": "Сергей Волков",
        "phone": "79166667788",
    },
    {
        "email": "natalia.kozlova@example.com",
        "full_name": "Наталья Козлова",
        "phone": "79167778899",
    },
    {
        "email": "pavel.novikov@example.com",
        "full_name": "Павел Новиков",
        "phone": "79168889900",
    },
]
_DEFAULT_PASSWORD = "DemoSeller123!"

# 32 listings — 2–3 per model, all 12 models covered
_LISTINGS: list[dict[str, Any]] = [
    # ── BMW 3er ───────────────────────────────────────────────────────────────
    {
        "seller_idx": 0,
        "model_id": "BMW_3ER",
        "photo": "bmw_3.jpg",
        "year": 2021,
        "price": 3_450_000,
        "mileage": 54_000,
        "condition": "excellent",
        "vin": "WBA8B7G55KNT10001",
        "license_plate": "А001АА77",
        "color_id": "black",
        "description": (
            "BMW 3 серии в идеальном состоянии. Один владелец по ПТС, "
            "все ТО у официального дилера. Гаражное хранение, ДТП не было. "
            "Зимняя резина на литых дисках в подарок. Торг при осмотре."
        ),
        "sale_address": "Москва, Ленинский проспект, 10",
        "days_ago": 1,
        "windows": 8,
    },
    {
        "seller_idx": 3,
        "model_id": "BMW_3ER",
        "photo": "bmw_3.jpg",
        "year": 2019,
        "price": 2_650_000,
        "mileage": 87_000,
        "condition": "good",
        "vin": "WBA8B7G55KNT10002",
        "license_plate": "А002АА77",
        "color_id": "white",
        "description": (
            "BMW 3 серии 2019 года, Sport Line. Два владельца по ПТС, "
            "сервисная книжка с момента покупки. Свежая диагностика без замечаний. "
            "Кожаный салон без потёртостей, все опции исправны."
        ),
        "sale_address": "Москва, Садовое кольцо, 15",
        "days_ago": 4,
        "windows": 6,
    },
    {
        "seller_idx": 6,
        "model_id": "BMW_3ER",
        "photo": "bmw_3.jpg",
        "year": 2023,
        "price": 4_100_000,
        "mileage": 18_000,
        "condition": "excellent",
        "vin": "WBA8B7G55KNT10003",
        "license_plate": "А003АА77",
        "color_id": "blue",
        "description": (
            "BMW 3 серии G20 рестайлинг 2023 года. Один владелец, на гарантии до 2026. "
            "Полный пакет M-Sport: спортивный обвес, руль и педали. "
            "Пробег минимальный, состояние нового автомобиля."
        ),
        "sale_address": "Москва, Мичуринский проспект, 8",
        "days_ago": 2,
        "windows": 10,
    },
    # ── BMW 5er ───────────────────────────────────────────────────────────────
    {
        "seller_idx": 4,
        "model_id": "BMW_5ER",
        "photo": "bmw_5.jpg",
        "year": 2020,
        "price": 4_200_000,
        "mileage": 82_000,
        "condition": "good",
        "vin": "WBAJC5102LN10001",
        "license_plate": "В001ВВ77",
        "color_id": "silver",
        "description": (
            "BMW 5 серии G30, Luxury Line. Кожаный салон Dakota, "
            "Harman/Kardon, адаптивная подвеска. Все ТО пройдены, "
            "история обслуживания доступна для проверки."
        ),
        "sale_address": "Москва, Ленинградский проспект, 31",
        "days_ago": 14,
        "windows": 4,
    },
    {
        "seller_idx": 1,
        "model_id": "BMW_5ER",
        "photo": "bmw_5.jpg",
        "year": 2022,
        "price": 5_500_000,
        "mileage": 35_000,
        "condition": "excellent",
        "vin": "WBAJC5102LN10002",
        "license_plate": "В002ВВ77",
        "color_id": "black",
        "description": (
            "BMW 5 серии LCI 2022 года, M-Sport. Один владелец, дилерское ТО. "
            "Панорамная крыша, камера 360°, система помощи при смене полосы. "
            "Гарантия BMW до 2025 года, полный пакет документов."
        ),
        "sale_address": "Москва, Кутузовский проспект, 12",
        "days_ago": 6,
        "windows": 8,
    },
    {
        "seller_idx": 5,
        "model_id": "BMW_5ER",
        "photo": "bmw_5.jpg",
        "year": 2018,
        "price": 3_200_000,
        "mileage": 121_000,
        "condition": "good",
        "vin": "WBAJC5102LN10003",
        "license_plate": "В003ВВ77",
        "color_id": "gray",
        "description": (
            "BMW 5 серии 530i 2018 года. Четыре владельца по ПТС, пробег "
            "реальный подтверждается диагностикой. Расходники обновлены, "
            "кузов в хорошем состоянии. Цена с учётом пробега."
        ),
        "sale_address": "Москва, Нагатинская набережная, 2",
        "days_ago": 20,
        "windows": 2,
    },
    # ── BMW X5 ────────────────────────────────────────────────────────────────
    {
        "seller_idx": 2,
        "model_id": "BMW_X5",
        "photo": "bmw_x5.jpg",
        "year": 2021,
        "price": 6_500_000,
        "mileage": 68_000,
        "condition": "good",
        "vin": "WBAJC5103LB10001",
        "license_plate": "С001СС77",
        "color_id": "white",
        "description": (
            "BMW X5 xDrive40i, M-пакет, панорамная крыша, кожаный салон Vernasca. "
            "Два владельца по ПТС, обслуживание по регламенту у дилера. "
            "Полная диагностика перед продажей доступна."
        ),
        "sale_address": "Москва, Большая Дмитровка, 7",
        "days_ago": 5,
        "windows": 6,
    },
    {
        "seller_idx": 7,
        "model_id": "BMW_X5",
        "photo": "bmw_x5.jpg",
        "year": 2023,
        "price": 8_900_000,
        "mileage": 12_000,
        "condition": "excellent",
        "vin": "WBAJC5103LB10002",
        "license_plate": "С002СС77",
        "color_id": "black",
        "description": (
            "BMW X5 G05 2023 года, xDrive50e Plug-in Hybrid. Один владелец, "
            "гарантия до 2027. Полный фарш: адаптивный круиз, Head-Up Display, "
            "Bowers & Wilkins, ночное видение. Возможен обмен."
        ),
        "sale_address": "Москва, Рублёвское шоссе, 22",
        "days_ago": 1,
        "windows": 12,
    },
    {
        "seller_idx": 0,
        "model_id": "BMW_X5",
        "photo": "bmw_x5.jpg",
        "year": 2019,
        "price": 5_100_000,
        "mileage": 103_000,
        "condition": "good",
        "vin": "WBAJC5103LB10003",
        "license_plate": "С003СС77",
        "color_id": "gray",
        "description": (
            "BMW X5 третьего поколения G05, первый год выпуска. Два владельца, "
            "сервисная история в наличии. Подвеска в порядке, кузов без следов "
            "ДТП, ЛКП заводское. Адекватный торг при живом осмотре."
        ),
        "sale_address": "Москва, Варшавское шоссе, 34",
        "days_ago": 10,
        "windows": 5,
    },
    # ── BMW X3 ────────────────────────────────────────────────────────────────
    {
        "seller_idx": 3,
        "model_id": "BMW_X3",
        "photo": "bmw_x3.jpg",
        "year": 2022,
        "price": 4_900_000,
        "mileage": 38_000,
        "condition": "excellent",
        "vin": "WBAXZ91010LM10001",
        "license_plate": "Е001ЕЕ77",
        "color_id": "blue",
        "description": (
            "BMW X3 xDrive30i, xLine. Один владелец, не битый, ЛКП заводское. "
            "Москва с момента покупки, только асфальт. Гарантия BMW до 2027."
        ),
        "sale_address": "Москва, Профсоюзная, 7",
        "days_ago": 2,
        "windows": 8,
    },
    {
        "seller_idx": 6,
        "model_id": "BMW_X3",
        "photo": "bmw_x3.jpg",
        "year": 2020,
        "price": 3_700_000,
        "mileage": 67_000,
        "condition": "good",
        "vin": "WBAXZ91010LM10002",
        "license_plate": "Е002ЕЕ77",
        "color_id": "silver",
        "description": (
            "BMW X3 20d xDrive 2020 года. Дизель, расход 6 л/100 км. "
            "Один владелец, всё ТО у дилера. Зимняя и летняя резина в комплекте. "
            "Состояние отличное для своих лет и пробега."
        ),
        "sale_address": "Москва, Новопесчаная, 16",
        "days_ago": 8,
        "windows": 5,
    },
    # ── BMW M3 ────────────────────────────────────────────────────────────────
    {
        "seller_idx": 4,
        "model_id": "BMW_M3",
        "photo": "bmw_m3.jpg",
        "year": 2022,
        "price": 8_200_000,
        "mileage": 18_000,
        "condition": "excellent",
        "vin": "WBSJF0102LR10001",
        "license_plate": "Н001НН77",
        "color_id": "white",
        "description": (
            "BMW M3 Competition G80, Carbon пакет. Карбоновые элементы экстерьера, "
            "ковши, керамика. Гарантия до 2027 года. Второй автомобиль — пробег минимальный."
        ),
        "sale_address": "Москва, Ленинский проспект, 99",
        "days_ago": 2,
        "windows": 12,
    },
    {
        "seller_idx": 1,
        "model_id": "BMW_M3",
        "photo": "bmw_m3.jpg",
        "year": 2021,
        "price": 7_400_000,
        "mileage": 32_000,
        "condition": "excellent",
        "vin": "WBSJF0102LR10002",
        "license_plate": "Н002НН77",
        "color_id": "black",
        "description": (
            "BMW M3 2021 года, базовая Competition. Один владелец, только дилерское ТО. "
            "Машина с трека не выезжала, эксплуатация исключительно городская. "
            "Полная история. Торг уместен при быстрой сделке."
        ),
        "sale_address": "Москва, Смоленская, 5",
        "days_ago": 7,
        "windows": 8,
    },
    # ── BMW X6 ────────────────────────────────────────────────────────────────
    {
        "seller_idx": 4,
        "model_id": "BMW_X6",
        "photo": "bmw_x6.jpg",
        "year": 2020,
        "price": 5_800_000,
        "mileage": 75_000,
        "condition": "good",
        "vin": "WBAFG8102LP10001",
        "license_plate": "Р001РР77",
        "color_id": "black",
        "description": (
            "BMW X6 G06, M-Sport. 21-дюймовые диски, панорамная крыша, премиальная акустика. "
            "Кузов и салон в очень хорошем состоянии. Полностью обслужен перед продажей."
        ),
        "sale_address": "Москва, Звенигородское шоссе, 4",
        "days_ago": 14,
        "windows": 4,
    },
    {
        "seller_idx": 5,
        "model_id": "BMW_X6",
        "photo": "bmw_x6.jpg",
        "year": 2022,
        "price": 7_100_000,
        "mileage": 41_000,
        "condition": "excellent",
        "vin": "WBAFG8102LP10002",
        "license_plate": "Р002РР77",
        "color_id": "gray",
        "description": (
            "BMW X6 40i xDrive 2022 года. Один владелец, гарантия до 2025. "
            "Лазерные фары, панорамный люк Sky Lounge, Bowers & Wilkins 1500 Вт. "
            "Документы в порядке, к продаже готов."
        ),
        "sale_address": "Москва, Можайское шоссе, 8",
        "days_ago": 5,
        "windows": 8,
    },
    # ── Audi A3 ───────────────────────────────────────────────────────────────
    {
        "seller_idx": 3,
        "model_id": "AUDI_A3",
        "photo": "audi_a3.jpg",
        "year": 2019,
        "price": 2_150_000,
        "mileage": 97_000,
        "condition": "good",
        "vin": "WAUZZZ8V1KA10001",
        "license_plate": "Т001ТТ77",
        "color_id": "red",
        "description": (
            "Audi A3 Sportback, один владелец, регулярное обслуживание. "
            "Шумоизоляция усилена, камера заднего вида, парктроник по кругу. "
            "Идеальна для города, лёгкая в управлении."
        ),
        "sale_address": "Москва, Дмитровское шоссе, 89",
        "days_ago": 7,
        "windows": 4,
    },
    {
        "seller_idx": 7,
        "model_id": "AUDI_A3",
        "photo": "audi_a3.jpg",
        "year": 2021,
        "price": 2_700_000,
        "mileage": 52_000,
        "condition": "excellent",
        "vin": "WAUZZZ8V1KA10002",
        "license_plate": "Т002ТТ77",
        "color_id": "white",
        "description": (
            "Audi A3 четвёртого поколения 2021 года. Один владелец, дилерское ТО. "
            "Цифровая приборная панель, MMI Navigation, матричные фары. "
            "Машина в отличном состоянии, все опции работают."
        ),
        "sale_address": "Москва, Большая Якиманка, 11",
        "days_ago": 3,
        "windows": 6,
    },
    # ── Audi A4 ───────────────────────────────────────────────────────────────
    {
        "seller_idx": 3,
        "model_id": "AUDI_A4",
        "photo": "audi_a4.jpg",
        "year": 2020,
        "price": 2_800_000,
        "mileage": 89_000,
        "condition": "good",
        "vin": "WAUZZZ8K1LA10001",
        "license_plate": "У001УУ77",
        "color_id": "black",
        "description": (
            "Audi A4 B9 рестайлинг 2020, 2.0 TFSI, S tronic. Сервисная книжка у дилера. "
            "Подвеска без замечаний, расходники свежие. Готова к долгой эксплуатации без вложений."
        ),
        "sale_address": "Москва, Варшавское шоссе, 18",
        "days_ago": 7,
        "windows": 4,
    },
    {
        "seller_idx": 2,
        "model_id": "AUDI_A4",
        "photo": "audi_a4.jpg",
        "year": 2022,
        "price": 3_500_000,
        "mileage": 33_000,
        "condition": "excellent",
        "vin": "WAUZZZ8K1LA10002",
        "license_plate": "У002УУ77",
        "color_id": "gray",
        "description": (
            "Audi A4 allroad quattro 2022 года. Полный привод, клиренс увеличен. "
            "Один владелец, гарантия Audi до конца 2025. "
            "Адаптивный круиз, ассистент полосы, парковочный пакет."
        ),
        "sale_address": "Москва, Хорошёвское шоссе, 25",
        "days_ago": 4,
        "windows": 8,
    },
    {
        "seller_idx": 6,
        "model_id": "AUDI_A4",
        "photo": "audi_a4.jpg",
        "year": 2018,
        "price": 2_200_000,
        "mileage": 112_000,
        "condition": "good",
        "vin": "WAUZZZ8K1LA10003",
        "license_plate": "У003УУ77",
        "color_id": "silver",
        "description": (
            "Audi A4 2018 года, 1.4 TFSI. Экономичный двигатель, расход 7 л/100 км. "
            "Три владельца по ПТС, сервисная история частично. "
            "Торг уместен, срочная продажа."
        ),
        "sale_address": "Москва, Азовская, 7",
        "days_ago": 18,
        "windows": 2,
    },
    # ── Audi A6 ───────────────────────────────────────────────────────────────
    {
        "seller_idx": 2,
        "model_id": "AUDI_A6",
        "photo": "audi_a6.jpg",
        "year": 2021,
        "price": 3_900_000,
        "mileage": 71_000,
        "condition": "good",
        "vin": "WAUZZZF45MN10001",
        "license_plate": "Ф001ФФ77",
        "color_id": "silver",
        "description": (
            "Audi A6 C8, матричные фары, проекция на лобовое, виртуальная панель. "
            "Полная сервисная история у дилера. Комфорт длительных поездок."
        ),
        "sale_address": "Москва, Тверская, 4",
        "days_ago": 5,
        "windows": 5,
    },
    {
        "seller_idx": 0,
        "model_id": "AUDI_A6",
        "photo": "audi_a6.jpg",
        "year": 2023,
        "price": 5_200_000,
        "mileage": 21_000,
        "condition": "excellent",
        "vin": "WAUZZZF45MN10002",
        "license_plate": "Ф002ФФ77",
        "color_id": "black",
        "description": (
            "Audi A6 2023 года, 55 TFSI quattro, S line. Один владелец, гарантия до 2026. "
            "Пневматическая подвеска, Bang & Olufsen, ночное видение. "
            "Идеальный бизнес-седан в максимальной комплектации."
        ),
        "sale_address": "Москва, Остоженка, 3",
        "days_ago": 2,
        "windows": 10,
    },
    {
        "seller_idx": 7,
        "model_id": "AUDI_A6",
        "photo": "audi_a6.jpg",
        "year": 2019,
        "price": 3_100_000,
        "mileage": 94_000,
        "condition": "good",
        "vin": "WAUZZZF45MN10003",
        "license_plate": "Ф003ФФ77",
        "color_id": "gray",
        "description": (
            "Audi A6 C8 2019 года, первое поколение нового кузова. "
            "Три владельца, сервисная книжка. Расходники обновлены. "
            "Машина без сюрпризов, цена рыночная."
        ),
        "sale_address": "Москва, Коломенское, 18",
        "days_ago": 12,
        "windows": 3,
    },
    # ── Audi Q5 ───────────────────────────────────────────────────────────────
    {
        "seller_idx": 4,
        "model_id": "AUDI_Q5",
        "photo": "audi_q5.jpg",
        "year": 2021,
        "price": 4_500_000,
        "mileage": 56_000,
        "condition": "excellent",
        "vin": "WAUZZZFY1MA10001",
        "license_plate": "Х001ХХ77",
        "color_id": "gray",
        "description": (
            "Audi Q5 второго поколения. Полный привод quattro, MMI Navigation plus. "
            "Матричная оптика. Обслуживание у дилера. Без аварий, без окрасов."
        ),
        "sale_address": "Москва, Рублёвское шоссе, 16",
        "days_ago": 5,
        "windows": 6,
    },
    {
        "seller_idx": 5,
        "model_id": "AUDI_Q5",
        "photo": "audi_q5.jpg",
        "year": 2023,
        "price": 5_800_000,
        "mileage": 14_000,
        "condition": "excellent",
        "vin": "WAUZZZFY1MA10002",
        "license_plate": "Х002ХХ77",
        "color_id": "white",
        "description": (
            "Audi Q5 Sportback 2023, 40 TFSI quattro. Купе-кроссовер в люксовой комплектации. "
            "Один владелец, на гарантии. Panorama, B&O, 20-дюймовые диски. "
            "Самый красивый кузов модели."
        ),
        "sale_address": "Москва, Красная Пресня, 7",
        "days_ago": 1,
        "windows": 12,
    },
    {
        "seller_idx": 1,
        "model_id": "AUDI_Q5",
        "photo": "audi_q5.jpg",
        "year": 2019,
        "price": 3_400_000,
        "mileage": 88_000,
        "condition": "good",
        "vin": "WAUZZZFY1MA10003",
        "license_plate": "Х003ХХ77",
        "color_id": "blue",
        "description": (
            "Audi Q5 FY 2019 года. Два владельца, подтверждённый пробег. "
            "Подвеска в порядке, кузов чистый. Зимняя резина в подарок. "
            "Хорошая альтернатива новому за значительно меньшие деньги."
        ),
        "sale_address": "Москва, Нахимовский проспект, 52",
        "days_ago": 15,
        "windows": 3,
    },
    # ── Audi Q7 ───────────────────────────────────────────────────────────────
    {
        "seller_idx": 4,
        "model_id": "AUDI_Q7",
        "photo": "audi_q7.jpg",
        "year": 2020,
        "price": 5_400_000,
        "mileage": 92_000,
        "condition": "good",
        "vin": "WAUZZZ4M1LA10001",
        "license_plate": "Ц001ЦЦ77",
        "color_id": "blue",
        "description": (
            "Audi Q7 семиместный, 3.0 TFSI, tiptronic. Пневмоподвеска обслужена. "
            "Кожаный салон без потёртостей, два комплекта колёс в подарок."
        ),
        "sale_address": "Москва, Можайское шоссе, 12",
        "days_ago": 7,
        "windows": 5,
    },
    {
        "seller_idx": 2,
        "model_id": "AUDI_Q7",
        "photo": "audi_q7.jpg",
        "year": 2022,
        "price": 7_200_000,
        "mileage": 38_000,
        "condition": "excellent",
        "vin": "WAUZZZ4M1LA10002",
        "license_plate": "Ц002ЦЦ77",
        "color_id": "black",
        "description": (
            "Audi Q7 60 TFSI e quattro 2022, гибрид. Один владелец, гарантия до 2025. "
            "Максимальная комплектация: ночное видение, Head-Up, B&O. "
            "Экономия на топливе до 40% в городе."
        ),
        "sale_address": "Москва, Кутузовский проспект, 41",
        "days_ago": 3,
        "windows": 10,
    },
    {
        "seller_idx": 7,
        "model_id": "AUDI_Q7",
        "photo": "audi_q7.jpg",
        "year": 2018,
        "price": 4_100_000,
        "mileage": 115_000,
        "condition": "good",
        "vin": "WAUZZZ4M1LA10003",
        "license_plate": "Ц003ЦЦ77",
        "color_id": "silver",
        "description": (
            "Audi Q7 4M 2018 года, рестайлинг. Три владельца, пробег подтверждён. "
            "Пневмоподвеска исправна, двигатель работает ровно. "
            "Хорошее состояние для своих лет. Торг при осмотре."
        ),
        "sale_address": "Москва, Алтуфьевское шоссе, 5",
        "days_ago": 22,
        "windows": 2,
    },
    # ── Audi RS6 ──────────────────────────────────────────────────────────────
    {
        "seller_idx": 1,
        "model_id": "AUDI_RS6",
        "photo": "audi_rs6.jpg",
        "year": 2022,
        "price": 11_500_000,
        "mileage": 22_000,
        "condition": "excellent",
        "vin": "WAUZZZ4G5NN10001",
        "license_plate": "Ч001ЧЧ77",
        "color_id": "gray",
        "description": (
            "Audi RS6 Avant Performance, Black Optic, керамика. Гарантия Audi до 2026. "
            "Зимний и летний комплекты на оригинальных дисках. Покупался у дилера."
        ),
        "sale_address": "Москва, Кутузовский проспект, 22",
        "days_ago": 3,
        "windows": 12,
    },
    {
        "seller_idx": 6,
        "model_id": "AUDI_RS6",
        "photo": "audi_rs6.jpg",
        "year": 2021,
        "price": 10_200_000,
        "mileage": 44_000,
        "condition": "excellent",
        "vin": "WAUZZZ4G5NN10002",
        "license_plate": "Ч002ЧЧ77",
        "color_id": "black",
        "description": (
            "Audi RS6 Avant C8 2021 года. 600 л.с., 4.0 TFSI V8. Два владельца. "
            "Обслуживание у официального дилера, все документы в порядке. "
            "Динамика суперкара с практичностью универсала."
        ),
        "sale_address": "Москва, Пречистенка, 10",
        "days_ago": 8,
        "windows": 8,
    },
    {
        "seller_idx": 5,
        "model_id": "AUDI_RS6",
        "photo": "audi_rs6.jpg",
        "year": 2023,
        "price": 13_500_000,
        "mileage": 9_000,
        "condition": "excellent",
        "vin": "WAUZZZ4G5NN10003",
        "license_plate": "Ч003ЧЧ77",
        "color_id": "white",
        "description": (
            "Audi RS6 Avant Performance 2023 года. Один владелец, на гарантии до 2027. "
            "Пакет Dynamik Plus: регулируемые амортизаторы, активный задний дифференциал. "
            "Редкий цвет Glacier White Metallic. Состояние идеальное."
        ),
        "sale_address": "Москва, Арбат, 2",
        "days_ago": 1,
        "windows": 12,
    },
]

assert len(_LISTINGS) == 32, f"Expected 32 listings, got {len(_LISTINGS)}"


async def _pick_modifications(session: AsyncSession) -> dict[str, dict[str, str]]:
    needed = sorted({spec["model_id"] for spec in _LISTINGS})
    rows = (
        await session.execute(
            text(
                "SELECT DISTINCT ON (mo.id) mo.id AS model_id, "
                "  mod.id AS modification_id, m.id AS mark_id, "
                "  c.body_type AS body_type, s.engine_type AS engine_type "
                "FROM catalog.modifications mod "
                "JOIN catalog.marks m ON m.id = mod.mark_id "
                "JOIN catalog.models mo ON mo.id = mod.model_id "
                "JOIN catalog.configurations c ON c.id = mod.configuration_id "
                "JOIN catalog.specifications s ON s.id = mod.id "
                "WHERE mo.id = ANY(:ids) "
                "  AND c.body_type IS NOT NULL "
                "  AND s.engine_type IS NOT NULL "
                "ORDER BY mo.id, mod.id"
            ),
            {"ids": needed},
        )
    ).all()
    return {r._mapping["model_id"]: dict(r._mapping) for r in rows}


async def _ensure_city(session: AsyncSession) -> str | None:
    moscow = (
        await session.execute(
            text("SELECT id FROM geo.cities WHERE id = '7700000000000'")
        )
    ).scalar()
    if moscow:
        return moscow
    return (
        await session.execute(
            text(
                "SELECT id FROM geo.cities "
                "WHERE is_popular = true ORDER BY population DESC NULLS LAST LIMIT 1"
            )
        )
    ).scalar()


async def _ensure_seller(session: AsyncSession, seller: dict[str, str]) -> uuid.UUID:
    existing = await get_user_by_email(session, seller["email"])
    if existing:
        await session.execute(
            text(
                "UPDATE users SET phone = :p, phone_verified = true, "
                "phone_visible = true, full_name = :n WHERE id = :id"
            ),
            {"id": str(existing.id), "p": seller["phone"], "n": seller["full_name"]},
        )
        return existing.id
    user = await create_user(
        session,
        UserCreate(
            email=seller["email"],
            password=_DEFAULT_PASSWORD,
            full_name=seller["full_name"],
            role=UserRole.user,
        ),
    )
    await session.flush()
    await session.execute(
        text(
            "UPDATE users SET phone = :p, phone_verified = true, "
            "phone_visible = true WHERE id = :id"
        ),
        {"id": str(user.id), "p": seller["phone"]},
    )
    return user.id


async def _save_photo(seller_id: uuid.UUID, photo_name: str) -> tuple[str, str]:
    path = _PHOTO_DIR / photo_name
    if not path.exists():
        raise FileNotFoundError(f"Seed photo missing: {path}")
    raw = path.read_bytes()
    original_bytes, thumb_bytes = await asyncio.to_thread(process_image, raw)
    stem = uuid.uuid4().hex
    storage = get_image_storage()
    url = await storage.save(seller_id, f"{stem}.jpg", original_bytes)
    thumb_url = await storage.save(seller_id, f"{stem}_thumb.jpg", thumb_bytes)
    return url, thumb_url


def _spread_windows(count: int) -> list[tuple[date, time, time]]:
    today = date.today()
    slots = [
        (time(10, 0), time(11, 0)),
        (time(11, 30), time(12, 30)),
        (time(14, 0), time(15, 0)),
        (time(16, 0), time(17, 0)),
        (time(18, 0), time(19, 0)),
    ]
    out: list[tuple[date, time, time]] = []
    day_offset = 1
    while len(out) < count:
        wdate = today + timedelta(days=day_offset)
        per_day = min(len(slots), count - len(out))
        for i in range(per_day):
            out.append((wdate, slots[i][0], slots[i][1]))
        day_offset += 1
    return out


async def _insert_listing(
    session: AsyncSession,
    *,
    seller_id: uuid.UUID,
    spec: dict[str, Any],
    mod: dict[str, str],
    city_id: str,
    photo_url: str,
    thumb_url: str,
) -> None:
    listing_id = uuid.uuid4()
    now = datetime.now(UTC)
    published_at = now - timedelta(days=spec["days_ago"])
    expires_at = published_at + timedelta(days=settings.LISTING_LIFETIME_DAYS)

    await session.execute(
        text(
            "INSERT INTO listings (id, seller_id, modification_id, mark_id, "
            "model_id, body_type, engine_type, year, price, mileage, color_id, "
            "vin, license_plate, license_plate_edit_count, description, "
            "sale_address, accepts_cash, accepts_transfer, status, "
            "viewing_enabled, condition, city_id, published_at, expires_at) VALUES "
            "(:id, :seller_id, :modification_id, :mark_id, :model_id, "
            ":body_type, :engine_type, :year, :price, :mileage, :color_id, "
            ":vin, :license_plate, 0, :description, :sale_address, "
            "true, true, 'active', true, :condition, :city_id, "
            ":published_at, :expires_at)"
        ),
        {
            "id": str(listing_id),
            "seller_id": str(seller_id),
            "modification_id": mod["modification_id"],
            "mark_id": mod["mark_id"],
            "model_id": mod["model_id"],
            "body_type": mod["body_type"],
            "engine_type": mod["engine_type"],
            "year": spec["year"],
            "price": spec["price"],
            "mileage": spec["mileage"],
            "color_id": spec["color_id"],
            "vin": spec["vin"],
            "license_plate": spec["license_plate"],
            "description": spec["description"],
            "sale_address": spec["sale_address"],
            "condition": spec["condition"],
            "city_id": city_id,
            "published_at": published_at,
            "expires_at": expires_at,
        },
    )

    await session.execute(
        text(
            "INSERT INTO listing_images (id, listing_id, url, thumbnail_url, "
            "is_primary, sort_order) VALUES (:id, :lid, :u, :t, true, 0)"
        ),
        {
            "id": str(uuid.uuid4()),
            "lid": str(listing_id),
            "u": photo_url,
            "t": thumb_url,
        },
    )

    for wdate, tf, tt in _spread_windows(spec["windows"]):
        await session.execute(
            text(
                "INSERT INTO viewing_windows (id, listing_id, window_date, "
                "time_from, time_to) VALUES (:id, :lid, :d, :tf, :tt)"
            ),
            {
                "id": str(uuid.uuid4()),
                "lid": str(listing_id),
                "d": wdate,
                "tf": tf,
                "tt": tt,
            },
        )


async def _wipe_existing(session: AsyncSession, seller_ids: list[uuid.UUID]) -> None:
    ids = [str(sid) for sid in seller_ids]
    for table, fk in [
        ("viewing_bookings", "listing_id"),
        ("reservations", "listing_id"),
        ("listing_images", "listing_id"),
        ("viewing_windows", "listing_id"),
    ]:
        await session.execute(
            text(
                f"DELETE FROM {table} WHERE {fk} IN "
                "(SELECT id FROM listings WHERE seller_id = ANY(:ids))"
            ),
            {"ids": ids},
        )
    await session.execute(
        text("DELETE FROM listings WHERE seller_id = ANY(:ids)"),
        {"ids": ids},
    )


async def main(reset: bool = False) -> None:
    async with async_session_factory() as session:
        city_id = await _ensure_city(session)
        if city_id is None:
            log.error("seed_prod_no_city", hint="Run seed_catalog.py first")
            sys.exit(1)

        mods = await _pick_modifications(session)
        missing = [s["model_id"] for s in _LISTINGS if s["model_id"] not in mods]
        if missing:
            log.error("seed_prod_missing_models", models=missing)
            sys.exit(1)

        seller_ids: list[uuid.UUID] = []
        for seller in _SELLERS:
            seller_ids.append(await _ensure_seller(session, seller))
        await session.flush()

        existing_count = (
            await session.execute(
                text("SELECT count(*) FROM listings WHERE seller_id = ANY(:ids)"),
                {"ids": [str(sid) for sid in seller_ids]},
            )
        ).scalar_one()

        if existing_count and not reset:
            log.info(
                "seed_prod_skip_already_present",
                existing=int(existing_count),
                hint="Pass --reset to wipe and re-seed",
            )
            await session.commit()
            return

        if existing_count and reset:
            log.info("seed_prod_reset", wiping=int(existing_count))
            await _wipe_existing(session, seller_ids)

        for i, spec in enumerate(_LISTINGS, 1):
            seller_id = seller_ids[spec["seller_idx"]]
            photo_url, thumb_url = await _save_photo(seller_id, spec["photo"])
            await _insert_listing(
                session,
                seller_id=seller_id,
                spec=spec,
                mod=mods[spec["model_id"]],
                city_id=city_id,
                photo_url=photo_url,
                thumb_url=thumb_url,
            )
            log.info("seed_prod_listing_inserted", n=i, model=spec["model_id"])

        await session.commit()
        log.info(
            "seed_prod_done",
            sellers=len(seller_ids),
            listings=len(_LISTINGS),
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed 32 production listings")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe existing listings by seed sellers before re-seeding",
    )
    args = parser.parse_args()
    asyncio.run(main(reset=args.reset))
