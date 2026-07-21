USE dify_crm;

INSERT INTO users (feishu_user_id, display_name, role) VALUES
  ('demo_sales', '销售A', 'sales'),
  ('demo_manager', '销售经理', 'manager'),
  ('demo_marketing', '市场运营', 'marketing')
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name), role = VALUES(role);

INSERT INTO channels (name, type, owner_id, cost, remark) VALUES
  ('官网表单', 'owned', 'demo_marketing', 3000, '官网咨询和落地页表单'),
  ('飞书社群', 'community', 'demo_marketing', 1200, '私域社群与活动群'),
  ('行业展会', 'event', 'demo_marketing', 15000, '线下展会获客'),
  ('转介绍', 'referral', 'demo_sales', 0, '客户和伙伴推荐'),
  ('广告投放', 'paid', 'demo_marketing', 8000, '搜索与信息流广告')
ON DUPLICATE KEY UPDATE type = VALUES(type), cost = VALUES(cost), remark = VALUES(remark);

INSERT INTO campaigns (name, channel_id, goal, budget, start_date, end_date, status, created_by)
SELECT '6月AI CRM获客活动', id, '收集高意向企业线索并推动预约演示', 12000, '2026-06-01', '2026-06-30', 'active', 'demo_marketing'
FROM channels WHERE name = '官网表单'
ON DUPLICATE KEY UPDATE budget = VALUES(budget);

INSERT INTO campaigns (name, channel_id, goal, budget, start_date, end_date, status, created_by)
SELECT '飞书私域直播课', id, '通过飞书社群直播获取中小企业销售负责人', 4000, '2026-06-03', '2026-06-20', 'active', 'demo_marketing'
FROM channels WHERE name = '飞书社群'
ON DUPLICATE KEY UPDATE budget = VALUES(budget);

INSERT INTO leads (name, company, phone, email, source, channel_id, campaign_id, status, intent_level, budget, pain_point, owner_id, score, score_reason)
SELECT '张明', '长沙智造科技', '13800000001', 'zhangming@example.com', '官网表单', c.id, ca.id, 'qualified', 'high', 300000,
       '销售线索分散，跟进靠人工表格，想用AI做自动分级和跟进提醒。', 'demo_sales', 86,
       '预算明确、痛点强、来自高转化官网渠道'
FROM channels c JOIN campaigns ca ON ca.channel_id = c.id
WHERE c.name = '官网表单'
ON DUPLICATE KEY UPDATE score = VALUES(score);

INSERT INTO leads (name, company, phone, email, source, channel_id, campaign_id, status, intent_level, budget, pain_point, owner_id, score, score_reason)
SELECT '李芳', '湘江云服', '13800000002', 'lifang@example.com', '飞书社群', c.id, ca.id, 'nurturing', 'medium', 80000,
       '对CRM感兴趣，但当前还在比较低代码和SaaS方案。', 'demo_sales', 62,
       '有明确兴趣但预算和时间表不够清晰'
FROM channels c JOIN campaigns ca ON ca.channel_id = c.id
WHERE c.name = '飞书社群'
ON DUPLICATE KEY UPDATE score = VALUES(score);

INSERT INTO leads (name, company, phone, email, source, channel_id, status, intent_level, budget, pain_point, owner_id, score, score_reason)
SELECT '王强', '华中贸易集团', '13800000003', 'wangqiang@example.com', '转介绍', id, 'new', 'medium', 180000,
       '希望把销售跟进、客户资料和报价流程整合起来。', 'demo_sales', 74,
       '转介绍来源质量高，预算初步明确'
FROM channels WHERE name = '转介绍'
ON DUPLICATE KEY UPDATE score = VALUES(score);

INSERT INTO customers (name, phone, company, source, lead_id, owner_id, lifecycle_stage, remark)
SELECT name, phone, company, source, id, owner_id, 'customer', '由高意向线索转入，重点跟进AI获客闭环。'
FROM leads WHERE name = '张明'
ON DUPLICATE KEY UPDATE remark = VALUES(remark);

INSERT INTO contacts (customer_id, name, title, phone, email, is_main)
SELECT c.id, '张明', '销售总监', c.phone, 'zhangming@example.com', 1
FROM customers c WHERE c.name = '张明';

INSERT INTO tags (name, category) VALUES
  ('高意向', 'customer'),
  ('价格敏感', 'customer'),
  ('AI获客', 'customer'),
  ('需要演示', 'lead'),
  ('预算明确', 'lead'),
  ('私域运营', 'lead'),
  ('转介绍优先', 'lead')
ON DUPLICATE KEY UPDATE category = VALUES(category);

INSERT INTO opportunities (customer_id, lead_id, name, stage, amount, probability, expected_close_date, owner_id)
SELECT c.id, l.id, 'AI CRM试点项目', '需求分析', 300000, 45, '2026-07-20', c.owner_id
FROM customers c JOIN leads l ON l.id = c.lead_id
WHERE c.name = '张明';

INSERT INTO followups (customer_id, lead_id, opportunity_id, content, summary, next_action, next_date, created_by)
SELECT c.id, c.lead_id, o.id,
       '客户希望先看获客营销模块，重点关注线索来源、评分、跟进提醒和飞书展示。',
       '客户关注获客营销闭环，已进入方案验证阶段。',
       '准备获客营销演示脚本并约飞书会议',
       '2026-06-07',
       'demo_sales'
FROM customers c JOIN opportunities o ON o.customer_id = c.id
WHERE c.name = '张明';

INSERT INTO tasks (title, related_type, related_id, due_date, owner_id)
SELECT '准备张明客户获客营销演示', 'opportunity', id, '2026-06-07', owner_id
FROM opportunities WHERE name = 'AI CRM试点项目';

INSERT INTO tickets (ticket_no, customer_id, description, priority, status, assignee_id, satisfaction)
SELECT 'T20260604001', id, '客户反馈演示环境偶发登录慢，需要确认网络与Docker资源。', '中', '处理中', 'demo_sales', NULL
FROM customers WHERE name = '张明';

INSERT INTO knowledge_assets (title, asset_type, rag_scope, content) VALUES
  ('获客营销话术库', 'playbook', 'dify_knowledge', '面对官网表单线索，优先确认预算、决策人、当前获客痛点和期望上线时间。'),
  ('AI CRM演示FAQ', 'faq', 'dify_knowledge', '系统可将关键业务数据落入MySQL，将临时协作和看板放入飞书多维表格，通过Dify生成智能建议。'),
  ('线索评分规则说明', 'policy', 'dify_knowledge', '高意向线索通常具备明确预算、近期上线计划、关键痛点和可触达决策人。');
