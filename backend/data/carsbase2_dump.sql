-- Minimal catalog dump: BMW + Audi (12 models) for local development
-- MySQL format — converted to PostgreSQL by import_catalog.py

CREATE TABLE `marks` (
  `id` varchar(50) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `cyrillic_name` varchar(100) DEFAULT NULL,
  `numeric_id` int(11) DEFAULT NULL,
  `year_from` int(11) DEFAULT NULL,
  `year_to` int(11) DEFAULT NULL,
  `popular` tinyint(1) DEFAULT 0,
  `country` varchar(50) DEFAULT NULL,
  `updated_at` timestamp DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

INSERT INTO `marks` (`id`, `name`, `cyrillic_name`, `numeric_id`, `year_from`, `popular`, `country`) VALUES
('AUDI', 'Audi', 'Ауди', 2, 1909, 1, 'Германия'),
('BMW', 'BMW', 'БМВ', 1, 1916, 1, 'Германия');

CREATE TABLE `models` (
  `id` varchar(50) NOT NULL,
  `mark_id` varchar(50) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `cyrillic_name` varchar(100) DEFAULT NULL,
  `year_from` int(11) DEFAULT NULL,
  `year_to` int(11) DEFAULT NULL,
  `class` varchar(10) DEFAULT NULL,
  `updated_at` timestamp DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

INSERT INTO `models` (`id`, `mark_id`, `name`, `cyrillic_name`, `year_from`) VALUES
('AUDI_A3', 'AUDI', 'A3', 'А3', 1996),
('AUDI_A4', 'AUDI', 'A4', 'А4', 1994),
('AUDI_A6', 'AUDI', 'A6', 'А6', 1994),
('AUDI_Q5', 'AUDI', 'Q5', 'Ку5', 2008),
('AUDI_Q7', 'AUDI', 'Q7', 'Ку7', 2005),
('AUDI_RS6', 'AUDI', 'RS6', 'РС6', 2002),
('BMW_3ER', 'BMW', '3 серии', '3 серии', 1975),
('BMW_5ER', 'BMW', '5 серии', '5 серии', 1972),
('BMW_M3', 'BMW', 'M3', 'М3', 1986),
('BMW_X3', 'BMW', 'X3', 'Х3', 2003),
('BMW_X5', 'BMW', 'X5', 'Х5', 1999),
('BMW_X6', 'BMW', 'X6', 'Х6', 2008);

CREATE TABLE `generations` (
  `id` varchar(50) NOT NULL,
  `model_id` varchar(50) DEFAULT NULL,
  `mark_id` varchar(50) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `year_from` int(11) DEFAULT NULL,
  `year_to` int(11) DEFAULT NULL,
  `updated_at` timestamp DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

INSERT INTO `generations` (`id`, `model_id`, `mark_id`, `name`, `year_from`) VALUES
('GEN_AUDI_A3', 'AUDI_A3', 'AUDI', '8Y', 2020),
('GEN_AUDI_A4', 'AUDI_A4', 'AUDI', 'B9', 2016),
('GEN_AUDI_A6', 'AUDI_A6', 'AUDI', 'C8', 2018),
('GEN_AUDI_Q5', 'AUDI_Q5', 'AUDI', 'FY', 2017),
('GEN_AUDI_Q7', 'AUDI_Q7', 'AUDI', '4M', 2015),
('GEN_AUDI_RS6', 'AUDI_RS6', 'AUDI', 'C8', 2019),
('GEN_BMW_3ER', 'BMW_3ER', 'BMW', 'G20', 2019),
('GEN_BMW_5ER', 'BMW_5ER', 'BMW', 'G30', 2017),
('GEN_BMW_M3', 'BMW_M3', 'BMW', 'G80', 2021),
('GEN_BMW_X3', 'BMW_X3', 'BMW', 'G01', 2018),
('GEN_BMW_X5', 'BMW_X5', 'BMW', 'G05', 2019),
('GEN_BMW_X6', 'BMW_X6', 'BMW', 'G06', 2020);

CREATE TABLE `configurations` (
  `id` varchar(50) NOT NULL,
  `generation_id` varchar(50) DEFAULT NULL,
  `model_id` varchar(50) DEFAULT NULL,
  `mark_id` varchar(50) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `body_type` varchar(50) DEFAULT NULL,
  `doors_count` int(11) DEFAULT NULL,
  `updated_at` timestamp DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

INSERT INTO `configurations` (`id`, `generation_id`, `model_id`, `mark_id`, `name`, `body_type`, `doors_count`) VALUES
('CONF_AUDI_A3', 'GEN_AUDI_A3', 'AUDI_A3', 'AUDI', 'Хэтчбек 5 дв.', 'HATCHBACK', 5),
('CONF_AUDI_A4', 'GEN_AUDI_A4', 'AUDI_A4', 'AUDI', 'Седан', 'SEDAN', 4),
('CONF_AUDI_A6', 'GEN_AUDI_A6', 'AUDI_A6', 'AUDI', 'Седан', 'SEDAN', 4),
('CONF_AUDI_Q5', 'GEN_AUDI_Q5', 'AUDI_Q5', 'AUDI', 'Внедорожник 5 дв.', 'SUV', 5),
('CONF_AUDI_Q7', 'GEN_AUDI_Q7', 'AUDI_Q7', 'AUDI', 'Внедорожник 5 дв.', 'SUV', 5),
('CONF_AUDI_RS6', 'GEN_AUDI_RS6', 'AUDI_RS6', 'AUDI', 'Универсал', 'WAGON', 5),
('CONF_BMW_3ER', 'GEN_BMW_3ER', 'BMW_3ER', 'BMW', 'Седан', 'SEDAN', 4),
('CONF_BMW_5ER', 'GEN_BMW_5ER', 'BMW_5ER', 'BMW', 'Седан', 'SEDAN', 4),
('CONF_BMW_M3', 'GEN_BMW_M3', 'BMW_M3', 'BMW', 'Седан', 'SEDAN', 4),
('CONF_BMW_X3', 'GEN_BMW_X3', 'BMW_X3', 'BMW', 'Внедорожник 5 дв.', 'SUV', 5),
('CONF_BMW_X5', 'GEN_BMW_X5', 'BMW_X5', 'BMW', 'Внедорожник 5 дв.', 'SUV', 5),
('CONF_BMW_X6', 'GEN_BMW_X6', 'BMW_X6', 'BMW', 'Внедорожник 5 дв.', 'SUV', 5);

CREATE TABLE `modifications` (
  `id` varchar(50) NOT NULL,
  `configuration_id` varchar(50) DEFAULT NULL,
  `generation_id` varchar(50) DEFAULT NULL,
  `model_id` varchar(50) DEFAULT NULL,
  `mark_id` varchar(50) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `group_name` varchar(100) DEFAULT NULL,
  `offers_price_from` int(11) DEFAULT NULL,
  `offers_price_to` int(11) DEFAULT NULL,
  `is_closed` tinyint(1) DEFAULT 0,
  `updated_at` timestamp DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

INSERT INTO `modifications` (`id`, `configuration_id`, `generation_id`, `model_id`, `mark_id`, `name`) VALUES
('MOD_AUDI_A3', 'CONF_AUDI_A3', 'GEN_AUDI_A3', 'AUDI_A3', 'AUDI', '35 TFSI'),
('MOD_AUDI_A4', 'CONF_AUDI_A4', 'GEN_AUDI_A4', 'AUDI_A4', 'AUDI', '40 TFSI'),
('MOD_AUDI_A6', 'CONF_AUDI_A6', 'GEN_AUDI_A6', 'AUDI_A6', 'AUDI', '45 TFSI'),
('MOD_AUDI_Q5', 'CONF_AUDI_Q5', 'GEN_AUDI_Q5', 'AUDI_Q5', 'AUDI', '40 TFSI quattro'),
('MOD_AUDI_Q7', 'CONF_AUDI_Q7', 'GEN_AUDI_Q7', 'AUDI_Q7', 'AUDI', '55 TFSI quattro'),
('MOD_AUDI_RS6', 'CONF_AUDI_RS6', 'GEN_AUDI_RS6', 'AUDI_RS6', 'AUDI', '4.0 TFSI quattro'),
('MOD_BMW_3ER', 'CONF_BMW_3ER', 'GEN_BMW_3ER', 'BMW_3ER', 'BMW', '320i'),
('MOD_BMW_5ER', 'CONF_BMW_5ER', 'GEN_BMW_5ER', 'BMW_5ER', 'BMW', '530i'),
('MOD_BMW_M3', 'CONF_BMW_M3', 'GEN_BMW_M3', 'BMW_M3', 'BMW', 'Competition'),
('MOD_BMW_X3', 'CONF_BMW_X3', 'GEN_BMW_X3', 'BMW_X3', 'BMW', 'xDrive30i'),
('MOD_BMW_X5', 'CONF_BMW_X5', 'GEN_BMW_X5', 'BMW_X5', 'BMW', 'xDrive40i'),
('MOD_BMW_X6', 'CONF_BMW_X6', 'GEN_BMW_X6', 'BMW_X6', 'BMW', 'xDrive40i');

CREATE TABLE `specifications` (
  `id` varchar(50) NOT NULL,
  `acceleration` varchar(50) DEFAULT NULL,
  `auto_class` varchar(50) DEFAULT NULL,
  `back_brake` varchar(100) DEFAULT NULL,
  `back_suspension` varchar(100) DEFAULT NULL,
  `back_wheel_base` varchar(50) DEFAULT NULL,
  `battery_capacity` varchar(50) DEFAULT NULL,
  `battery_capacity_useful` varchar(50) DEFAULT NULL,
  `battery_charge_cycles` varchar(50) DEFAULT NULL,
  `battery_temp` varchar(50) DEFAULT NULL,
  `body_size` varchar(50) DEFAULT NULL,
  `boot_volume` varchar(50) DEFAULT NULL,
  `charge_time` varchar(50) DEFAULT NULL,
  `charging_port_types` varchar(100) DEFAULT NULL,
  `clearance` varchar(50) DEFAULT NULL,
  `compression` varchar(50) DEFAULT NULL,
  `consumption` varchar(50) DEFAULT NULL,
  `consumption_calc` varchar(50) DEFAULT NULL,
  `consumption_kwt` varchar(50) DEFAULT NULL,
  `consumption_mixed` varchar(50) DEFAULT NULL,
  `country` varchar(50) DEFAULT NULL,
  `cylinders_order` varchar(50) DEFAULT NULL,
  `cylinders_value` varchar(50) DEFAULT NULL,
  `diameter` varchar(50) DEFAULT NULL,
  `disk_size` varchar(50) DEFAULT NULL,
  `displacement` varchar(50) DEFAULT NULL,
  `doors_count` varchar(50) DEFAULT NULL,
  `electric_range` varchar(50) DEFAULT NULL,
  `emission_euro_class` varchar(50) DEFAULT NULL,
  `engine_feeding` varchar(50) DEFAULT NULL,
  `engine_list` varchar(100) DEFAULT NULL,
  `engine_list1` varchar(100) DEFAULT NULL,
  `engine_order` varchar(50) DEFAULT NULL,
  `engine_type` varchar(50) DEFAULT NULL,
  `ev_battery_type` varchar(50) DEFAULT NULL,
  `feeding` varchar(50) DEFAULT NULL,
  `front_brake` varchar(100) DEFAULT NULL,
  `front_suspension` varchar(100) DEFAULT NULL,
  `front_wheel_base` varchar(50) DEFAULT NULL,
  `fuel_emission` varchar(50) DEFAULT NULL,
  `full_weight` varchar(50) DEFAULT NULL,
  `gear_type` varchar(50) DEFAULT NULL,
  `gear_value` varchar(50) DEFAULT NULL,
  `height` varchar(50) DEFAULT NULL,
  `landing_wheels_size` varchar(50) DEFAULT NULL,
  `max_power` varchar(50) DEFAULT NULL,
  `max_power_in` varchar(50) DEFAULT NULL,
  `max_speed` varchar(50) DEFAULT NULL,
  `moment` varchar(50) DEFAULT NULL,
  `origin_tires_size` varchar(50) DEFAULT NULL,
  `petrol_type` varchar(50) DEFAULT NULL,
  `power` varchar(50) DEFAULT NULL,
  `quickcharge_description` varchar(100) DEFAULT NULL,
  `quickcharge_time` varchar(50) DEFAULT NULL,
  `seats` varchar(50) DEFAULT NULL,
  `steering_wheel` varchar(50) DEFAULT NULL,
  `tank_volume` varchar(50) DEFAULT NULL,
  `total_range` varchar(50) DEFAULT NULL,
  `transmission` varchar(50) DEFAULT NULL,
  `valves` varchar(50) DEFAULT NULL,
  `valvetrain` varchar(50) DEFAULT NULL,
  `weight` varchar(50) DEFAULT NULL,
  `wheel_base` varchar(50) DEFAULT NULL,
  `width` varchar(50) DEFAULT NULL,
  `updated_at` timestamp DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

INSERT INTO `specifications` (`id`, `engine_type`, `transmission`, `power`, `displacement`, `seats`) VALUES
('MOD_AUDI_A3', 'GASOLINE', 'ROBOT', '150', '1395', '5'),
('MOD_AUDI_A4', 'GASOLINE', 'ROBOT', '190', '1984', '5'),
('MOD_AUDI_A6', 'GASOLINE', 'ROBOT', '245', '1984', '5'),
('MOD_AUDI_Q5', 'GASOLINE', 'ROBOT', '204', '1984', '5'),
('MOD_AUDI_Q7', 'GASOLINE', 'ROBOT', '340', '2995', '7'),
('MOD_AUDI_RS6', 'GASOLINE', 'ROBOT', '600', '3996', '5'),
('MOD_BMW_3ER', 'GASOLINE', 'ROBOT', '184', '1998', '5'),
('MOD_BMW_5ER', 'GASOLINE', 'ROBOT', '252', '1998', '5'),
('MOD_BMW_M3', 'GASOLINE', 'ROBOT', '510', '2993', '5'),
('MOD_BMW_X3', 'GASOLINE', 'ROBOT', '252', '1998', '5'),
('MOD_BMW_X5', 'GASOLINE', 'ROBOT', '340', '2998', '5'),
('MOD_BMW_X6', 'GASOLINE', 'ROBOT', '340', '2998', '5');
