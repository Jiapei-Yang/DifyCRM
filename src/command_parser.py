import re
from typing import Any

from . import crm_service as crm


HELP_TEXT = """DifyCRM 获客营销助手

【获客营销】

1. /渠道创建 名称:官网表单 类型:owned 成本:3000 备注:官网落地页

2. /活动创建 名称:6月直播课 渠道:飞书社群 预算:4000 目标:获取高意向线索

3. /线索创建 名称:张明 公司:长沙智造 电话:13800000001 来源:官网表单 意向:高 预算:30万 痛点:想用AI做获客和跟进

4. /线索列表

5. /线索评分 1

6. /线索转客户 1

7. /来源分析

8. /获客分析

【客户销售】

1. /客户创建 名称:XX科技 电话:13800000001 来源:转介绍

2. /我的客户

3. /跟进 客户:张明 内容:客户希望先看获客营销模块

4. /漏斗

【辅助】

1. /面板

2. /help
"""


INTENT_ALIASES = {
    "渠道创建": "create_channel",
    "活动创建": "create_campaign",
    "营销活动创建": "create_campaign",
    "线索创建": "create_lead",
    "线索列表": "list_leads",
    "我的线索": "list_my_leads",
    "线索评分": "score_lead",
    "线索转客户": "convert_lead",
    "客户创建": "create_customer",
    "我的客户": "list_customers",
    "跟进": "add_followup",
    "跟进总结": "add_followup",
    "来源分析": "source_stats",
    "获客分析": "acquisition_stats",
    "渠道分析": "acquisition_stats",
    "漏斗": "funnel_stats",
    "面板": "dashboard",
    "help": "help",
    "帮助": "help",
}


def parse_message(message: str) -> tuple[str, dict[str, Any]]:
    text = message.strip()
    if text.startswith("@"):
        text = re.sub(r"^@\S+\s*", "", text)
    if text.startswith("/"):
        text = text[1:]
    parts = text.split(maxsplit=1)
    raw_intent = parts[0] if parts else "help"
    body = parts[1] if len(parts) > 1 else ""
    params = parse_params(body)
    if body and not params and raw_intent in {"线索评分", "线索转客户"}:
        params["id"] = body.strip()
    return INTENT_ALIASES.get(raw_intent, "unknown"), params


def parse_params(body: str) -> dict[str, Any]:
    params: dict[str, Any] = {}
    pattern = re.compile(r"([A-Za-z_][\w_]*|[\u4e00-\u9fffA-Za-z]+):")
    matches = list(pattern.finditer(body))
    if not matches:
        return params
    for index, match in enumerate(matches):
        key = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        params[key] = body[start:end].strip()
    return normalize_keys(params)


def normalize_keys(params: dict[str, Any]) -> dict[str, Any]:
    aliases = {
        "名称": "name",
        "姓名": "name",
        "公司": "company",
        "电话": "phone",
        "邮箱": "email",
        "来源": "source",
        "渠道": "channel",
        "活动": "campaign",
        "意向": "intent_level",
        "预算": "budget",
        "痛点": "pain_point",
        "备注": "remark",
        "内容": "content",
        "客户": "customer",
        "目标": "goal",
        "成本": "cost",
        "类型": "type",
        "状态": "status",
        "线索ID": "lead_id",
        "商机ID": "opportunity_id",
    }
    normalized = dict(params)
    for zh, en in aliases.items():
        if zh in params and en not in normalized:
            normalized[en] = params[zh]
    return normalized


def handle_command(message: str, sender_id: str = "demo_sales") -> dict[str, Any]:
    intent, params = parse_message(message)
    try:
        if intent == "help":
            return ok(intent, HELP_TEXT)
        if intent == "create_channel":
            channel = crm.create_channel(params, sender_id)
            return ok(intent, f"渠道已创建/存在\n\nID：#{channel['id']}\n\n名称：{channel['name']}\n\n类型：{channel['type']}", channel)
        if intent == "create_campaign":
            campaign = crm.create_campaign(params, sender_id)
            return ok(intent, f"营销活动已创建\n\nID：#{campaign['id']}\n\n名称：{campaign['name']}\n\n预算：{campaign['budget']}", campaign)
        if intent == "create_lead":
            lead = crm.create_lead(params, sender_id)
            return ok(intent, format_lead_created(lead), lead)
        if intent in {"list_leads", "list_my_leads"}:
            if intent == "list_my_leads":
                params["mine"] = True
            leads = crm.list_leads(params, sender_id)
            return ok(intent, format_lead_list(leads), {"items": leads})
        if intent == "score_lead":
            lead_id = int(params.get("id") or params.get("lead_id") or params.get("线索ID"))
            lead = crm.rescore_lead(lead_id)
            return ok(intent, f"线索评分结果\n\n线索：#{lead['id']} {lead['name']}\n\n评分：{lead['score']}\n\n原因：{lead['score_reason']}", lead)
        if intent == "convert_lead":
            lead_id = int(params.get("id") or params.get("lead_id") or params.get("线索ID"))
            result = crm.convert_lead(lead_id, sender_id)
            customer = result["customer"]
            opportunity = result.get("opportunity")
            if result.get("already_converted"):
                return ok(intent, f"线索已转为客户\n\n客户：#{customer['id']} {customer['name']}", result)
            return ok(intent, f"线索已转客户\n\n客户：#{customer['id']} {customer['name']}\n\n商机：#{opportunity['id']} {opportunity['name']}", result)
        if intent == "create_customer":
            customer = crm.create_customer(params, sender_id)
            return ok(intent, f"客户已创建\n\nID：#{customer['id']}\n\n名称：{customer['name']}", customer)
        if intent == "list_customers":
            customers = crm.list_customers(sender_id)
            return ok(intent, format_customers(customers), {"items": customers})
        if intent == "add_followup":
            followup = crm.add_followup(params, sender_id)
            return ok(intent, f"跟进已记录\n\nID：#{followup['id']}\n\n摘要：{followup['summary']}\n\n下一步：{followup['next_action']}\n\n建议日期：{followup['next_date']}", followup)
        if intent == "source_stats":
            rows = crm.source_stats()
            return ok(intent, format_source_stats(rows), {"items": rows})
        if intent == "acquisition_stats":
            data = crm.acquisition_stats()
            return ok(intent, format_acquisition(data), data)
        if intent == "funnel_stats":
            data = crm.funnel_stats()
            return ok(intent, format_funnel(data), data)
        if intent == "dashboard":
            data = crm.dashboard(sender_id)
            return ok(intent, format_dashboard(data), data)
        return fail("unknown", "未知指令。发送 `/help` 查看可用指令。")
    except Exception as exc:
        return fail(intent, f"处理失败：{exc}")


def ok(intent: str, text: str, data: Any | None = None) -> dict[str, Any]:
    return {"ok": True, "intent": intent, "reply": text, "data": data}


def fail(intent: str, text: str) -> dict[str, Any]:
    return {"ok": False, "intent": intent, "reply": text, "data": None}


def format_lead_created(lead: dict[str, Any]) -> str:
    return (
        f"线索已创建\n\n"
        f"ID：#{lead['id']}\n\n"
        f"姓名：{lead['name']}\n\n"
        f"公司：{lead.get('company') or '-'}\n\n"
        f"来源：{lead.get('source') or '-'}\n\n"
        f"评分：{lead['score']}\n\n"
        f"原因：{lead['score_reason']}"
    )


def format_lead_list(leads: list[dict[str, Any]]) -> str:
    if not leads:
        return "暂无线索。"
    lines = ["线索列表（按评分排序）"]
    for item in leads:
        lines.append(
            f"#{item['id']} {item['name']}\n"
            f"公司：{item.get('company') or '-'}\n"
            f"来源：{item.get('source') or '-'}\n"
            f"状态：{item['status']}\n"
            f"评分：{item['score']}"
        )
    return "\n\n".join(lines)


def format_customers(customers: list[dict[str, Any]]) -> str:
    if not customers:
        return "暂无客户。"
    return "\n\n".join([f"#{c['id']} {c['name']}\n公司：{c.get('company') or '-'}\n来源：{c.get('source') or '-'}" for c in customers])


def format_source_stats(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "暂无来源数据。"
    lines = ["客户来源 / 线索来源分析"]
    for row in rows:
        lines.append(
            f"{row['source']}\n"
            f"线索数：{row['lead_count']}\n"
            f"转化数：{row['converted_count']}\n"
            f"平均分：{row['avg_score']}\n"
            f"潜在金额：{row['potential_amount']}"
        )
    return "\n\n".join(lines)


def format_acquisition(data: dict[str, Any]) -> str:
    lines = ["获客渠道分析"]
    for row in data["channels"]:
        lines.append(
            f"{row['channel']}\n"
            f"线索数：{row['lead_count']}\n"
            f"转化数：{row['converted_count']}\n"
            f"成本：{row['cost']}\n"
            f"平均分：{row['avg_score']}"
        )
    lines.append(f"建议\n{data['insight']}")
    return "\n\n".join(lines)


def format_funnel(data: dict[str, Any]) -> str:
    lines = ["获客 - 销售漏斗", "线索状态"]
    for row in data["leads"]:
        lines.append(f"- {row['status']}：{row['count']}")
    lines.append("\n商机阶段")
    for row in data["opportunities"]:
        lines.append(f"- {row['stage']}：{row['count']}，金额 {row['amount']}")
    lines.append(f"\n解读\n{data['insight']}")
    return "\n".join(lines)


def format_dashboard(data: dict[str, Any]) -> str:
    lines = [f"个人面板\n\n待跟进线索：{data['my_leads']} 条", "高分线索"]
    for lead in data["high_score_leads"]:
        lines.append(f"- #{lead['id']} {lead['name']} 评分 {lead['score']}：{lead['score_reason']}")
    lines.append("\n待办")
    for task in data["pending_tasks"]:
        lines.append(f"- #{task['id']} {task['title']} 截止 {task['due_date']}")
    lines.append(f"\n获客建议\n{data['acquisition']['insight']}")
    return "\n".join(lines)
