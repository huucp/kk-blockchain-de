 CREATE TABLE `lending_liquity_eth_lending_data` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `debt_change` double DEFAULT NULL,
  `collateral_change` double DEFAULT NULL,
  `market_price` double DEFAULT NULL,
  `action_type` varchar(20) DEFAULT NULL,
  `time_recorded` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4157 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci