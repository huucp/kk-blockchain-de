CREATE TABLE `token_price_data` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `token_name` varchar(32) NOT NULL,
  `time_record` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `market_price` double NOT NULL,
  `record_at` varchar(32) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci