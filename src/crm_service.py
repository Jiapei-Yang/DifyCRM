from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from .db import execute, fetch_all, fetch_one


STAGES = ["初步接触", "需求分析", "方案报价", "谈判", "赢单", "输单"]


def money(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    text = str(value).replace("万", "0000").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def compact(rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return rows[:limit]


def lead_score(params: dict[str, Any]) -> tuple[int, str]:
    score = 20
    reasons: list[str] = []
    source = str(params.get("source") or params.get("来源") or "")
    intent = str(params.get("intent_level") or params.get("意向") or "")
    pain = str(params.get("pain_point") or params.get("痛点") or params.get("备注") or "")
    budget = money(params.get("budget") or params.get("预算"))

    if source in {"官网表单", "转介绍", "行业展会"}:
        score += 18
        reasons.append(f"{source}来源质量较高")
    if intent in {"high", "高", "高意向"}:
        score += 25
        reasons.append("意向强")
    elif intent in {"medium", "中", "中意向"}:
        score += 12
        reasons.append("有初步意向")
    if budget >= 200000:
        score += 18
        reasons.append("预算明确且较高")
    elif budget >= 50000:
        score += 10
        reasons.append("有可验证预算")
    for keyword in ["痛点", "获客", "预算", "决策", "演示", "上线", "报价", "POC"]:
        if keyword in pain:
            score += 4
    score = min(score, 100)
    if not reasons:
        reasons.append("信息不足，建议补充预算、痛点和时间表")
    return score, "；".join(reasons)


def create_channel(params: dict[str, Any], sender_id: str) -> dict[str, Any]:
    name = params.get("name") or params.get("名称")
    if not name:
        raise ValueError("缺少渠道名称")
    existing = fetch_one("SELECT * FROM channels WHERE name=%s", (name,))
    if existing:
        return existing
    channel_id = execute(
        "INSERT INTO channels (name, type, owner_id, cost, remark) VALUES (%s,%s,%s,%s,%s)",
        (
            name,
            params.get("type") or params.get("类型") or "other",
            sender_id,
            money(params.get("cost") or params.get("成本")),
            params.get("remark") or params.get("备注"),
        ),
    )
    return fetch_one("SELECT * FROM channels WHERE id=%s", (channel_id,)) or {}


def create_campaign(params: dict[str, Any], sender_id: str) -> dict[str, Any]:
    name = params.get("name") or params.get("名称")
    if not name:
        raise ValueError("缺少活动名称")
    channel_name = params.get("channel") or params.get("渠道")
    channel = fetch_one("SELECT * FROM channels WHERE name=%s", (channel_name,)) if channel_name else None
    campaign_id = execute(
        """
        INSERT INTO campaigns (name, channel_id, goal, budget, start_date, end_date, status, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            name,
            channel["id"] if channel else None,
            params.get("goal") or params.get("目标"),
            money(params.get("budget") or params.get("预算")),
            params.get("start_date") or params.get("开始"),
            params.get("end_date") or params.get("结束"),
            params.get("status") or params.get("状态") or "active",
            sender_id,
        ),
    )
    return fetch_one("SELECT * FROM campaigns WHERE id=%s", (campaign_id,)) or {}


def create_lead(params: dict[str, Any], sender_id: str) -> dict[str, Any]:
    name = params.get("name") or params.get("名称")
    if not name:
        raise ValueError("缺少线索名称")
    channel_name = params.get("channel") or params.get("渠道") or params.get("source") or params.get("来源")
    campaign_name = params.get("campaign") or params.get("活动")
    channel = fetch_one("SELECT * FROM channels WHERE name=%s", (channel_name,)) if channel_name else None
    campaign = fetch_one("SELECT * FROM campaigns WHERE name=%s", (campaign_name,)) if campaign_name else None
    score, reason = lead_score(params)
    lead_id = execute(
        """
        INSERT INTO leads
          (name, company, phone, email, source, channel_id, campaign_id, status, intent_level,
           budget, pain_point, owner_id, score, score_reason)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            name,
            params.get("company") or params.get("公司"),
            params.get("phone") or params.get("电话"),
            params.get("email") or params.get("邮箱"),
            channel_name,
            channel["id"] if channel else None,
            campaign["id"] if campaign else None,
            params.get("status") or params.get("状态") or "new",
            params.get("intent_level") or params.get("意向") or "unknown",
            money(params.get("budget") or params.get("预算")),
            params.get("pain_point") or params.get("痛点") or params.get("remark") or params.get("备注"),
            sender_id,
            score,
            reason,
        ),
    )
    return fetch_one("SELECT * FROM leads WHERE id=%s", (lead_id,)) or {}


def list_leads(params: dict[str, Any], sender_id: str) -> list[dict[str, Any]]:
    status = params.get("status") or params.get("状态")
    where = ["1=1"]
    values: list[Any] = []
    if status:
        where.append("status=%s")
        values.append(status)
    if params.get("mine") or params.get("我的"):
        where.append("owner_id=%s")
        values.append(sender_id)
    return fetch_all(
        f"""
        SELECT id, name, company, source, status, intent_level, budget, score, score_reason, created_at
        FROM leads WHERE {' AND '.join(where)}
        ORDER BY score DESC, created_at DESC LIMIT 20
        """,
        tuple(values),
    )


def get_lead(lead_id: int) -> dict[str, Any]:
    lead = fetch_one("SELECT * FROM leads WHERE id=%s", (lead_id,))
    if not lead:
        raise ValueError(f"未找到线索 {lead_id}")
    return lead


def rescore_lead(lead_id: int) -> dict[str, Any]:
    lead = get_lead(lead_id)
    score, reason = lead_score(
        {
            "source": lead.get("source"),
            "intent_level": lead.get("intent_level"),
            "budget": lead.get("budget"),
            "pain_point": lead.get("pain_point"),
        }
    )
    execute("UPDATE leads SET score=%s, score_reason=%s WHERE id=%s", (score, reason, lead_id))
    return get_lead(lead_id)


def convert_lead(lead_id: int, sender_id: str) -> dict[str, Any]:
    lead = get_lead(lead_id)
    if lead.get("converted_customer_id"):
        customer = fetch_one("SELECT * FROM customers WHERE id=%s", (lead["converted_customer_id"],))
        return {"customer": customer, "opportunity": None, "already_converted": True}
    customer_id = execute(
        """
        INSERT INTO customers (name, phone, company, source, lead_id, owner_id, lifecycle_stage, remark)
        VALUES (%s,%s,%s,%s,%s,%s,'customer',%s)
        """,
        (
            lead["name"],
            lead.get("phone"),
            lead.get("company"),
            lead.get("source"),
            lead_id,
            lead.get("owner_id") or sender_id,
            f"由线索转化：{lead.get('pain_point') or ''}",
        ),
    )
    opp_id = execute(
        """
        INSERT INTO opportunities (customer_id, lead_id, name, stage, amount, probability, expected_close_date, owner_id)
        VALUES (%s,%s,%s,'初步接触',%s,%s,%s,%s)
        """,
        (
            customer_id,
            lead_id,
            f"{lead['name']} - 获客营销试点",
            money(lead.get("budget")),
            max(10, min(int(lead.get("score") or 0), 80)),
            (date.today() + timedelta(days=30)).isoformat(),
            lead.get("owner_id") or sender_id,
        ),
    )
    execute("UPDATE leads SET status='converted', converted_customer_id=%s WHERE id=%s", (customer_id, lead_id))
    return {
        "customer": fetch_one("SELECT * FROM customers WHERE id=%s", (customer_id,)),
        "opportunity": fetch_one("SELECT * FROM opportunities WHERE id=%s", (opp_id,)),
        "already_converted": False,
    }


def create_customer(params: dict[str, Any], sender_id: str) -> dict[str, Any]:
    name = params.get("name") or params.get("名称")
    if not name:
        raise ValueError("缺少客户名称")
    customer_id = execute(
        """
        INSERT INTO customers (name, phone, company, source, owner_id, lifecycle_stage, remark)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            name,
            params.get("phone") or params.get("电话"),
            params.get("company") or params.get("公司"),
            params.get("source") or params.get("来源"),
            sender_id,
            params.get("stage") or params.get("阶段") or "customer",
            params.get("remark") or params.get("备注"),
        ),
    )
    return fetch_one("SELECT * FROM customers WHERE id=%s", (customer_id,)) or {}


def list_customers(sender_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, name, company, source, lifecycle_stage, owner_id, created_at
        FROM customers WHERE deleted=0 AND owner_id=%s
        ORDER BY updated_at DESC LIMIT 20
        """,
        (sender_id,),
    )


def add_followup(params: dict[str, Any], sender_id: str) -> dict[str, Any]:
    content = params.get("content") or params.get("内容")
    if not content:
        raise ValueError("缺少跟进内容")
    lead_id = int(params.get("lead_id") or params.get("线索ID") or 0)
    customer_name = params.get("customer") or params.get("客户")
    customer = fetch_one("SELECT * FROM customers WHERE name LIKE %s AND deleted=0 LIMIT 1", (f"%{customer_name}%",)) if customer_name else None
    summary = summarize_followup(content)
    next_date = (date.today() + timedelta(days=3)).isoformat()
    followup_id = execute(
        """
        INSERT INTO followups (customer_id, lead_id, opportunity_id, content, summary, next_action, next_date, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            customer["id"] if customer else None,
            lead_id or None,
            params.get("opportunity_id") or params.get("商机ID"),
            content,
            summary,
            infer_next_action(content),
            next_date,
            sender_id,
        ),
    )
    return fetch_one("SELECT * FROM followups WHERE id=%s", (followup_id,)) or {}


def summarize_followup(content: str) -> str:
    text = content.strip()
    if len(text) <= 45:
        return text
    return text[:45] + "..."


def infer_next_action(content: str) -> str:
    if "报价" in content:
        return "准备报价方案并确认预算口径"
    if "演示" in content or "demo" in content.lower():
        return "预约产品演示并确认参会角色"
    if "预算" in content:
        return "补充预算、决策人和采购时间表"
    return "安排下一次跟进并补全线索关键信息"


def source_stats() -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT
          COALESCE(source, '未知') AS source,
          COUNT(*) AS lead_count,
          SUM(status='converted') AS converted_count,
          ROUND(AVG(score), 1) AS avg_score,
          ROUND(SUM(COALESCE(budget, 0)), 2) AS potential_amount
        FROM leads
        GROUP BY COALESCE(source, '未知')
        ORDER BY lead_count DESC, avg_score DESC
        """
    )


def acquisition_stats() -> dict[str, Any]:
    channels = fetch_all(
        """
        SELECT
          ch.name AS channel,
          ch.type,
          ch.cost,
          COUNT(l.id) AS lead_count,
          SUM(l.status='converted') AS converted_count,
          ROUND(AVG(l.score), 1) AS avg_score,
          ROUND(SUM(COALESCE(l.budget, 0)), 2) AS potential_amount
        FROM channels ch
        LEFT JOIN leads l ON l.channel_id = ch.id
        GROUP BY ch.id, ch.name, ch.type, ch.cost
        ORDER BY lead_count DESC, avg_score DESC
        """
    )
    top = channels[0] if channels else None
    insight = "暂无渠道数据"
    if top and top["lead_count"]:
        insight = f"{top['channel']} 当前线索量最高，平均评分 {top['avg_score']}，建议优先配置跟进资源。"
    return {"channels": channels, "insight": insight}


def funnel_stats() -> dict[str, Any]:
    lead_rows = fetch_all("SELECT status, COUNT(*) AS count FROM leads GROUP BY status ORDER BY count DESC")
    opp_rows = fetch_all(
        """
        SELECT stage, COUNT(*) AS count, ROUND(SUM(amount), 2) AS amount
        FROM opportunities GROUP BY stage ORDER BY FIELD(stage, '初步接触','需求分析','方案报价','谈判','赢单','输单')
        """
    )
    bottleneck = "线索量不足，建议先补充获客活动数据"
    if lead_rows:
        nurturing = next((r for r in lead_rows if r["status"] == "nurturing"), None)
        if nurturing and nurturing["count"] > 0:
            bottleneck = "培育中线索仍需明确预算、痛点和时间表，可通过飞书私域活动推进。"
    return {"leads": lead_rows, "opportunities": opp_rows, "insight": bottleneck}


def dashboard(sender_id: str) -> dict[str, Any]:
    return {
        "my_leads": fetch_one("SELECT COUNT(*) AS count FROM leads WHERE owner_id=%s AND status<>'converted'", (sender_id,))["count"],
        "high_score_leads": fetch_all(
            "SELECT id, name, company, score, score_reason FROM leads WHERE score>=70 ORDER BY score DESC LIMIT 5"
        ),
        "pending_tasks": fetch_all(
            "SELECT id, title, due_date FROM tasks WHERE owner_id=%s AND status='pending' ORDER BY due_date ASC LIMIT 5",
            (sender_id,),
        ),
        "acquisition": acquisition_stats(),
    }
