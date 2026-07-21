import json
import sys
import urllib.error
import urllib.request

import mysql.connector


BASE_URL = "http://127.0.0.1:5055"


def post_command(message: str, sender_id: str = "demo_sales") -> dict:
    body = json.dumps(
        {"message": message, "sender_id": sender_id},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}/assistant/command",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_ok(result: dict, label: str) -> None:
    if not result.get("ok"):
        raise AssertionError(f"{label} failed: {result}")


def main() -> int:
    checks: list[str] = []

    health = get_json("/health")
    assert_ok(health, "health")
    assert health["database"]["db"] == "dify_crm", health
    checks.append("health")

    commands = [
        "/help",
        "/渠道创建 名称:测试渠道 类型:owned 成本:100",
        "/活动创建 名称:测试活动 渠道:测试渠道 预算:500 目标:验证获客链路",
        "/线索创建 名称:测试线索 公司:测试公司 来源:官网表单 意向:高 预算:12万 痛点:需要验证飞书获客闭环和销售跟进",
        "/线索列表",
        "/获客分析",
        "/来源分析",
        "/漏斗",
        "/面板",
    ]
    last_lead_id = None
    for command in commands:
        result = post_command(command)
        assert_ok(result, command)
        if result["intent"] == "create_lead":
            last_lead_id = result["data"]["id"]
            assert result["data"]["score"] >= 70, result
        checks.append(command)

    if not last_lead_id:
        raise AssertionError("lead creation did not return an id")

    scored = post_command(f"/线索评分 {last_lead_id}")
    assert_ok(scored, "score lead")
    checks.append("score lead")

    converted = post_command(f"/线索转客户 {last_lead_id}")
    assert_ok(converted, "convert lead")
    assert converted["data"]["customer"]["id"], converted
    assert converted["data"]["opportunity"]["id"], converted
    checks.append("convert lead")

    followup = post_command(
        f"/跟进 客户:{converted['data']['customer']['name']} 内容:客户希望先看获客营销模块，下周安排飞书会议演示"
    )
    assert_ok(followup, "add followup")
    assert followup["data"]["next_action"], followup
    checks.append("add followup")

    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="123456",
        database="dify_crm",
        charset="utf8mb4",
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM information_schema.tables WHERE table_schema='dify_crm'")
    table_count = cursor.fetchone()["count"]
    assert table_count == 13, table_count
    cursor.execute("SELECT HEX(name) AS name_hex FROM leads ORDER BY id LIMIT 1")
    name_hex = cursor.fetchone()["name_hex"]
    assert name_hex == "E5BCA0E6988E", name_hex
    cursor.close()
    conn.close()
    checks.append("mysql schema and utf8")

    print(json.dumps({"ok": True, "checks": checks}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, urllib.error.URLError, TimeoutError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
