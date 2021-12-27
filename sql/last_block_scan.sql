CREATE TABLE `last_block_scan` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `address` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `block` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `last_block_scan_UN` (`address`)
) ENGINE=InnoDB AUTO_INCREMENT=729 DEFAULT CHARSET=utf8mb3 COLLATE=utf8_unicode_ci