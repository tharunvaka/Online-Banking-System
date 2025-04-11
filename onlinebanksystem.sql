-- Drop tables if they exist
DROP TABLE IF EXISTS `transaction_details`;
DROP TABLE IF EXISTS `transactions`;
DROP TABLE IF EXISTS `login`;
DROP TABLE IF EXISTS `wallet`;
DROP TABLE IF EXISTS `user_details`;

-- Drop triggers if they exist
DROP TRIGGER IF EXISTS `wallet_create`;
DROP TRIGGER IF EXISTS `transaction_deduct`;
DROP TRIGGER IF EXISTS `transaction_credit`;

-- Create the user_details table
CREATE TABLE IF NOT EXISTS `user_details` (
  `user_name` varchar(100) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `wallet_id` int NOT NULL,
  `contact` bigint NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `date_of_birth` datetime NOT NULL,
  `verified_mobile` char(1) NOT NULL DEFAULT 'N',
  `user_timestamp` datetime NOT NULL,
  `country` varchar(4) NOT NULL,
  `verified_mail` char(1) NOT NULL,
  PRIMARY KEY (`user_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create the wallet table
CREATE TABLE IF NOT EXISTS `wallet` (
  `wallet_id` int NOT NULL,
  `user_name` varchar(50) NOT NULL,
  `amount` int NOT NULL,
  PRIMARY KEY (`wallet_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create the login table
CREATE TABLE IF NOT EXISTS `login` (
  `user_id` bigint NOT NULL,
  `user_name` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `login_timestamp` datetime DEFAULT NULL,
  `logout_timestamp` datetime DEFAULT NULL,
  `locked` char(1) DEFAULT 'N',
  `lock_limit` int DEFAULT '3',
  PRIMARY KEY (`user_id`),
  KEY `user_name` (`user_name`),
  CONSTRAINT `login_ibfk_1` FOREIGN KEY (`user_name`) REFERENCES `user_details` (`user_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create the transactions table
CREATE TABLE IF NOT EXISTS `transactions` (
  `transaction_id` int NOT NULL,
  `from_wallet_id` int NOT NULL,
  `amt` int NOT NULL,
  `to_wallet_id` int NOT NULL,
  `transaction_timestamp` datetime NOT NULL,
  `failed` char(1) DEFAULT 'N',
  PRIMARY KEY (`transaction_id`),
  KEY `from_wallet_id` (`from_wallet_id`),
  CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`from_wallet_id`) REFERENCES `wallet` (`wallet_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create the transaction_details table
CREATE TABLE IF NOT EXISTS `transaction_details` (
  `transaction_id` int DEFAULT NULL,
  `remarks` varchar(200) DEFAULT 'Transaction was done Successfully'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create triggers
CREATE TRIGGER `wallet_create` AFTER INSERT ON `user_details` FOR EACH ROW
  INSERT INTO `wallet` VALUES (NEW.wallet_id, NEW.user_name, 0);

CREATE TRIGGER `transaction_deduct` AFTER INSERT ON `transactions` FOR EACH ROW
  UPDATE wallet SET amount = amount - NEW.amt WHERE wallet_id = NEW.from_wallet_id;

CREATE TRIGGER `transaction_credit` AFTER INSERT ON `transactions` FOR EACH ROW
  UPDATE wallet SET amount = amount + NEW.amt WHERE wallet_id = NEW.to_wallet_id;
