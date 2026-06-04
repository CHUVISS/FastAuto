from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import class_mapper
from sqlmodel import Field, SQLModel


class CatalogBase(SQLModel):
    def to_public_dict(self) -> dict[str, Any]:
        return {
            col.name: getattr(self, key)
            for key, col in class_mapper(type(self)).columns.items()
        }


class CatalogSeedState(SQLModel, table=True):
    __tablename__ = "_seed_state"
    __table_args__ = {"schema": "catalog"}

    source_name: str = Field(primary_key=True, max_length=50)
    source_sha256: str = Field(max_length=64)
    applied_at: datetime = Field(
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    row_count: int | None = None


class CatalogColor(SQLModel, table=True):
    __tablename__ = "colors"
    __table_args__ = {"schema": "catalog"}

    id: str = Field(primary_key=True, max_length=30)
    name_ru: str = Field(max_length=50)
    name_en: str | None = Field(default=None, max_length=50)
    hex_code: str | None = Field(default=None, max_length=7)
    sort_order: int = Field(default=0)


class Mark(CatalogBase, table=True):
    __tablename__ = "marks"
    __table_args__ = {"schema": "catalog"}

    id: str = Field(primary_key=True)
    name: str | None = None
    cyrillic_name: str | None = None
    numeric_id: int | None = None
    year_from: int | None = None
    year_to: int | None = None
    popular: bool | None = None
    country: str | None = None
    updated_at: datetime | None = None


class Model(CatalogBase, table=True):
    __tablename__ = "models"
    __table_args__ = {"schema": "catalog"}

    id: str = Field(primary_key=True)
    mark_id: str | None = None
    name: str | None = None
    cyrillic_name: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    class_: str | None = Field(default=None, sa_column=Column("class", String))
    updated_at: datetime | None = None


class Generation(CatalogBase, table=True):
    __tablename__ = "generations"
    __table_args__ = {"schema": "catalog"}

    id: str = Field(primary_key=True)
    model_id: str | None = None
    mark_id: str | None = None
    name: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    updated_at: datetime | None = None


class Configuration(CatalogBase, table=True):
    __tablename__ = "configurations"
    __table_args__ = {"schema": "catalog"}

    id: str = Field(primary_key=True)
    generation_id: str | None = None
    model_id: str | None = None
    mark_id: str | None = None
    name: str | None = None
    body_type: str | None = None
    doors_count: int | None = None
    updated_at: datetime | None = None


class Modification(CatalogBase, table=True):
    __tablename__ = "modifications"
    __table_args__ = {"schema": "catalog"}

    id: str = Field(primary_key=True)
    configuration_id: str | None = None
    generation_id: str | None = None
    model_id: str | None = None
    mark_id: str | None = None
    name: str | None = None
    group_name: str | None = None
    offers_price_from: int | None = None
    offers_price_to: int | None = None
    is_closed: bool | None = None
    updated_at: datetime | None = None


class Specification(CatalogBase, table=True):
    __tablename__ = "specifications"
    __table_args__ = {"schema": "catalog"}

    id: str = Field(primary_key=True)
    acceleration: str | None = None
    auto_class: str | None = None
    back_brake: str | None = None
    back_suspension: str | None = None
    back_wheel_base: str | None = None
    battery_capacity: str | None = None
    battery_capacity_useful: str | None = None
    battery_charge_cycles: str | None = None
    battery_temp: str | None = None
    body_size: str | None = None
    boot_volume: str | None = None
    charge_time: str | None = None
    charging_port_types: str | None = None
    clearance: str | None = None
    compression: str | None = None
    consumption: str | None = None
    consumption_calc: str | None = None
    consumption_kwt: str | None = None
    consumption_mixed: str | None = None
    country: str | None = None
    cylinders_order: str | None = None
    cylinders_value: str | None = None
    diameter: str | None = None
    disk_size: str | None = None
    displacement: str | None = None
    doors_count: str | None = None
    electric_range: str | None = None
    emission_euro_class: str | None = None
    engine_feeding: str | None = None
    engine_list: str | None = None
    engine_list1: str | None = None
    engine_order: str | None = None
    engine_type: str | None = None
    ev_battery_type: str | None = None
    feeding: str | None = None
    front_brake: str | None = None
    front_suspension: str | None = None
    front_wheel_base: str | None = None
    fuel_emission: str | None = None
    full_weight: str | None = None
    gear_type: str | None = None
    gear_value: str | None = None
    height: str | None = None
    landing_wheels_size: str | None = None
    max_power: str | None = None
    max_power_in: str | None = None
    max_speed: str | None = None
    moment: str | None = None
    origin_tires_size: str | None = None
    petrol_type: str | None = None
    power: str | None = None
    quickcharge_description: str | None = None
    quickcharge_time: str | None = None
    seats: str | None = None
    steering_wheel: str | None = None
    tank_volume: str | None = None
    total_range: str | None = None
    transmission: str | None = None
    valves: str | None = None
    valvetrain: str | None = None
    weight: str | None = None
    wheel_base: str | None = None
    width: str | None = None
    updated_at: datetime | None = None


class Options(CatalogBase, table=True):
    __tablename__ = "options"
    __table_args__ = {"schema": "catalog"}

    id: str = Field(primary_key=True)
    n_12v_socket: bool | None = Field(
        default=None, sa_column=Column("12v_socket", Boolean)
    )
    n_14_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("14_inch_wheels", Boolean)
    )
    n_15_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("15_inch_wheels", Boolean)
    )
    n_16_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("16_inch_wheels", Boolean)
    )
    n_17_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("17_inch_wheels", Boolean)
    )
    n_18_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("18_inch_wheels", Boolean)
    )
    n_19_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("19_inch_wheels", Boolean)
    )
    n_20_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("20_inch_wheels", Boolean)
    )
    n_21_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("21_inch_wheels", Boolean)
    )
    n_22_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("22_inch_wheels", Boolean)
    )
    n_220v_socket: bool | None = Field(
        default=None, sa_column=Column("220v_socket", Boolean)
    )
    n_23_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("23_inch_wheels", Boolean)
    )
    n_24_inch_wheels: bool | None = Field(
        default=None, sa_column=Column("24_inch_wheels", Boolean)
    )
    n_360_camera: bool | None = Field(
        default=None, sa_column=Column("360_camera", Boolean)
    )
    abs: bool | None = None
    activ_suspension: bool | None = None
    adaptive_light: bool | None = None
    adj_pedals: bool | None = None
    air_suspension: bool | None = None
    airbag_curtain: bool | None = None
    airbag_driver: bool | None = None
    airbag_passenger: bool | None = None
    airbag_rear_side: bool | None = None
    airbag_side: bool | None = None
    alarm: bool | None = None
    alcantara: bool | None = None
    android_auto: bool | None = None
    apple_carplay: bool | None = None
    aroma: bool | None = None
    ashtray_and_cigarette_lighter: bool | None = None
    asr: bool | None = None
    athermal_glass: bool | None = None
    audiopreparation: bool | None = None
    audiosystem_cd: bool | None = None
    audiosystem_tv: bool | None = None
    auto_cruise: bool | None = None
    auto_dimming_mirror: bool | None = None
    auto_mirrors: bool | None = None
    auto_park: bool | None = None
    automatic_lighting_control: bool | None = None
    aux: bool | None = None
    bas: bool | None = None
    black_roof: bool | None = None
    blind_spot: bool | None = None
    bluetooth: bool | None = None
    body_kit: bool | None = None
    body_mouldings: bool | None = None
    cap_seats_rear: bool | None = None
    central_airbag: bool | None = None
    clean_air: bool | None = None
    climate_control_1: bool | None = None
    climate_control_2: bool | None = None
    collision_prevention_assist: bool | None = None
    combo_interior: bool | None = None
    computer: bool | None = None
    condition: bool | None = None
    cooling_box: bool | None = None
    cruise_control: bool | None = None
    decorative_interior_lighting: bool | None = None
    dha: bool | None = None
    digital_mirror: bool | None = None
    door_sill_panel: bool | None = None
    drive_mode_sys: bool | None = None
    driver_seat_electric: bool | None = None
    driver_seat_memory: bool | None = None
    driver_seat_support: bool | None = None
    driver_seat_updown: bool | None = None
    drl: bool | None = None
    drowsy_driver_alert_system: bool | None = None
    duo_body_color: bool | None = None
    e_adjustment_wheel: bool | None = None
    easy_trunk_opening: bool | None = None
    eco_leather: bool | None = None
    electro_mirrors: bool | None = None
    electro_rear_seat: bool | None = None
    electro_trunk: bool | None = None
    electro_window_back: bool | None = None
    electro_window_front: bool | None = None
    electronic_gage_panel: bool | None = None
    entertainment_system_for_rear_seat_passengers: bool | None = None
    esp: bool | None = None
    fabric_seats: bool | None = None
    fake_complect: bool | None = None
    fcw: bool | None = None
    feedback_alarm: bool | None = None
    folding_front_passenger_seat: bool | None = None
    folding_tables_rear: bool | None = None
    follow_me_home: bool | None = None
    front_camera: bool | None = None
    front_centre_armrest: bool | None = None
    front_seat_support: bool | None = None
    front_seats_heat: bool | None = None
    front_seats_heat_vent: bool | None = None
    glonass: bool | None = None
    hatch: bool | None = None
    hcc: bool | None = None
    heated_wash_system: bool | None = None
    high_beam_assist: bool | None = None
    ignor_cme: bool | None = None
    immo: bool | None = None
    isofix: bool | None = None
    isofix_front: bool | None = None
    keyless_entry: bool | None = None
    knee_airbag: bool | None = None
    knee_airbag_pass: bool | None = None
    laminated_safety_glass: bool | None = None
    lane_keeping_assist: bool | None = None
    laser_lights: bool | None = None
    ldw: bool | None = None
    leather: bool | None = None
    leather_gear_stick: bool | None = None
    led_lights: bool | None = None
    lidar: bool | None = None
    light_cleaner: bool | None = None
    light_sensor: bool | None = None
    lock: bool | None = None
    massage_seats: bool | None = None
    migration_flag: bool | None = None
    mirrors_heat: bool | None = None
    mirrors_memory: bool | None = None
    multi_wheel: bool | None = None
    multizone_climate_control: bool | None = None
    music_super: bool | None = None
    navigation: bool | None = None
    night_vision: bool | None = None
    paint_metallic: bool | None = None
    panorama_roof: bool | None = None
    park_assist_f: bool | None = None
    park_assist_r: bool | None = None
    passenger_seat_electric: bool | None = None
    passenger_seat_updown: bool | None = None
    pedestrian_detection: bool | None = None
    power_child_locks_rear_doors: bool | None = None
    power_latching_doors: bool | None = None
    programmed_block_heater: bool | None = None
    projection_display: bool | None = None
    ptf: bool | None = None
    rain_sensor: bool | None = None
    rcta: bool | None = None
    rear_armrest: bool | None = None
    rear_camera: bool | None = None
    rear_seat_heat_vent: bool | None = None
    rear_seat_memory: bool | None = None
    rear_seats_heat: bool | None = None
    rec: bool | None = None
    reduce_spare_wheel: bool | None = None
    remote_car_services: bool | None = None
    remote_engine_start: bool | None = None
    roller_blind_for_rear_window: bool | None = None
    roller_blinds_for_rear_side_windows: bool | None = None
    roof_rails: bool | None = None
    seat_memory: bool | None = None
    seat_transformation: bool | None = None
    servo: bool | None = None
    side_camera: bool | None = None
    spare_wheel: bool | None = None
    sport_pedals: bool | None = None
    sport_seats: bool | None = None
    sport_suspension: bool | None = None
    start_button: bool | None = None
    start_stop_function: bool | None = None
    steel_wheels: bool | None = None
    steering_wheel_gear_shift_paddles: bool | None = None
    third_rear_headrest: bool | None = None
    third_row_seats: bool | None = None
    tinted_glass: bool | None = None
    tja: bool | None = None
    traffic_sign_recognition: bool | None = None
    tyre_pressure: bool | None = None
    usb: bool | None = None
    velvet_seats: bool | None = None
    voice_recognition: bool | None = None
    volume_sensor: bool | None = None
    vsm: bool | None = None
    wheel_configuration1: bool | None = None
    wheel_configuration2: bool | None = None
    wheel_heat: bool | None = None
    wheel_leather: bool | None = None
    wheel_memory: bool | None = None
    wheel_power: bool | None = None
    windcleaner_heat: bool | None = None
    windscreen_heat: bool | None = None
    wireless_charger: bool | None = None
    xenon: bool | None = None
    ya_auto: bool | None = None
    updated_at: datetime | None = None
