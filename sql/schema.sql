CREATE DATABASE IF NOT EXISTS dify_crm
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE dify_crm;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  feishu_user_id VARCHAR(128) NOT NULL UNIQUE,
  display_name VARCHAR(100) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'sales',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channels (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL UNIQUE,
  type VARCHAR(50) NOT NULL DEFAULT 'other',
  owner_id VARCHAR(128),
  cost DECIMAL(12,2) NOT NULL DEFAULT 0,
  remark TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaigns (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(150) NOT NULL,
  channel_id BIGINT,
  goal VARCHAR(255),
  budget DECIMAL(12,2) NOT NULL DEFAULT 0,
  start_date DATE,
  end_date DATE,
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  created_by VARCHAR(128),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (channel_id) REFERENCES channels(id)
);

CREATE TABLE IF NOT EXISTS leads (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(150) NOT NULL,
  company VARCHAR(150),
  phone VARCHAR(50),
  email VARCHAR(120),
  source VARCHAR(100),
  channel_id BIGINT,
  campaign_id BIGINT,
  status VARCHAR(30) NOT NULL DEFAULT 'new',
  intent_level VARCHAR(30) NOT NULL DEFAULT 'unknown',
  budget DECIMAL(12,2),
  pain_point TEXT,
  owner_id VARCHAR(128),
  score INT NOT NULL DEFAULT 0,
  score_reason TEXT,
  converted_customer_id BIGINT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (channel_id) REFERENCES channels(id),
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
  INDEX idx_leads_source (source),
  INDEX idx_leads_status (status),
  INDEX idx_leads_owner (owner_id)
);

CREATE TABLE IF NOT EXISTS customers (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(150) NOT NULL,
  phone VARCHAR(50),
  company VARCHAR(150),
  source VARCHAR(100),
  lead_id BIGINT,
  owner_id VARCHAR(128),
  lifecycle_stage VARCHAR(30) NOT NULL DEFAULT 'customer',
  remark TEXT,
  deleted TINYINT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (lead_id) REFERENCES leads(id),
  INDEX idx_customers_name (name),
  INDEX idx_customers_owner (owner_id)
);

CREATE TABLE IF NOT EXISTS contacts (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  customer_id BIGINT NOT NULL,
  name VARCHAR(100) NOT NULL,
  title VARCHAR(100),
  phone VARCHAR(50),
  email VARCHAR(120),
  is_main TINYINT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS tags (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL UNIQUE,
  category VARCHAR(50) NOT NULL DEFAULT 'customer'
);

CREATE TABLE IF NOT EXISTS customer_tags (
  customer_id BIGINT NOT NULL,
  tag_id BIGINT NOT NULL,
  PRIMARY KEY (customer_id, tag_id),
  FOREIGN KEY (customer_id) REFERENCES customers(id),
  FOREIGN KEY (tag_id) REFERENCES tags(id)
);

CREATE TABLE IF NOT EXISTS opportunities (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  customer_id BIGINT NOT NULL,
  lead_id BIGINT,
  name VARCHAR(150) NOT NULL,
  stage VARCHAR(50) NOT NULL DEFAULT '初步接触',
  amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  probability INT NOT NULL DEFAULT 10,
  expected_close_date DATE,
  owner_id VARCHAR(128),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id),
  FOREIGN KEY (lead_id) REFERENCES leads(id),
  INDEX idx_opportunities_stage (stage)
);

CREATE TABLE IF NOT EXISTS followups (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  customer_id BIGINT,
  lead_id BIGINT,
  opportunity_id BIGINT,
  content TEXT NOT NULL,
  summary TEXT,
  next_action VARCHAR(255),
  next_date DATE,
  created_by VARCHAR(128),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id),
  FOREIGN KEY (lead_id) REFERENCES leads(id),
  FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);

CREATE TABLE IF NOT EXISTS tasks (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(200) NOT NULL,
  related_type VARCHAR(50),
  related_id BIGINT,
  due_date DATE,
  status VARCHAR(30) NOT NULL DEFAULT 'pending',
  owner_id VARCHAR(128),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  ticket_no VARCHAR(50) NOT NULL UNIQUE,
  customer_id BIGINT,
  description TEXT NOT NULL,
  priority VARCHAR(20) NOT NULL DEFAULT '中',
  status VARCHAR(30) NOT NULL DEFAULT '新建',
  assignee_id VARCHAR(128),
  satisfaction VARCHAR(30),
  first_response_at DATETIME,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS knowledge_assets (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(200) NOT NULL,
  asset_type VARCHAR(50) NOT NULL DEFAULT 'playbook',
  rag_scope VARCHAR(50) NOT NULL DEFAULT 'dify_knowledge',
  content TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
