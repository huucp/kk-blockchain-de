CREATE TABLE `dex_liquity_trove_updated_event` (
  `index` bigint DEFAULT NULL,
  `block` double DEFAULT NULL,
  `tnx_hash` text,
  `log_index` double DEFAULT NULL,
  `borrower` text,
  `debt` double DEFAULT NULL,
  `collateral` double DEFAULT NULL,
  `stake` double DEFAULT NULL,
  `operation` double DEFAULT NULL,
  `contract` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `contract_name` varchar(100) DEFAULT NULL,
  KEY `ix_dex_Liquity_TroveManager_deposit_data_index` (`index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci