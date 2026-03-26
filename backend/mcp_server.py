#!/usr/bin/env python3
"""MCP 服务器 - 旅行规划"""
import json
import sys
import os

# 强制 UTF-8
os.environ["PYTHONIOENCODING"] = "utf-8"
# 直接使用 buffer 操作，避免编码问题

def read_line():
    return sys.stdin.buffer.readline().decode("utf-8", errors="replace")

def write_line(data):
    line = json.dumps(data, ensure_ascii=False) + "\n"
    sys.stdout.buffer.write(line.encode("utf-8"))
    sys.stdout.buffer.flush()

def log(msg):
    sys.stderr.buffer.write(f"[MCP] {msg}\n".encode("utf-8", errors="replace"))
    sys.stderr.buffer.flush()

# 工具定义
TOOLS = [{
    "name": "trip_plan",
    "description": "生成智能旅行计划。根据目的地、日期、偏好等信息，自动规划完整的旅行行程，包括景点、酒店、餐饮和预算。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "目的地城市，如：北京、上海、杭州"},
            "start_date": {"type": "string", "description": "开始日期，格式：YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "结束日期，格式：YYYY-MM-DD"},
            "days": {"type": "integer", "description": "旅行天数，1-14 天", "minimum": 1, "maximum": 14},
            "preferences": {"type": "string", "description": "旅行偏好", "enum": ["历史文化", "自然风光", "现代都市", "美食体验", "休闲娱乐"], "default": "历史文化"},
            "budget": {"type": "string", "description": "预算等级", "enum": ["经济", "中等", "高端"], "default": "中等"},
            "transportation": {"type": "string", "description": "交通方式", "enum": ["公共交通", "自驾", "打车"], "default": "公共交通"},
            "accommodation": {"type": "string", "description": "住宿类型", "enum": ["经济型酒店", "舒适型酒店", "高档酒店", "民宿"], "default": "经济型酒店"}
        },
        "required": ["city", "start_date", "end_date", "days"]
    }
}]

def call_trip_plan(arguments):
    """调用旅行规划功能"""
    try:
        from app.models.schemas import TripPlanRequest
        from app.agents.trip_planner import get_trip_planner_agent
        
        request = TripPlanRequest(
            city=arguments.get("city", ""),
            start_date=arguments.get("start_date", ""),
            end_date=arguments.get("end_date", ""),
            days=arguments.get("days", 3),
            preferences=arguments.get("preferences", "历史文化"),
            budget=arguments.get("budget", "中等"),
            transportation=arguments.get("transportation", "公共交通"),
            accommodation=arguments.get("accommodation", "经济型酒店")
        )
        
        agent = get_trip_planner_agent()
        plan = agent.plan_trip(request)
        return format_trip_plan(plan)
    except Exception as e:
        log(f"Trip plan error: {e}")
        return f"旅行规划失败：{str(e)}"

def format_trip_plan(plan):
    """格式化旅行计划"""
    lines = [f"# {plan.city} {len(plan.days)}日游旅行计划"]
    lines.append(f"\n**日期**: {plan.start_date} 至 {plan.end_date}")
    lines.append(f"\n**总体建议**: {plan.overall_suggestions}")
    
    if plan.budget:
        lines.append(f"\n## 预算明细")
        lines.append(f"- 景点门票：¥{plan.budget.total_attractions}")
        lines.append(f"- 酒店住宿：¥{plan.budget.total_hotels}")
        lines.append(f"- 餐饮费用：¥{plan.budget.total_meals}")
        lines.append(f"- 交通费用：¥{plan.budget.total_transportation}")
        lines.append(f"- **总计：¥{plan.budget.total}**")
    
    for day in plan.days:
        lines.append(f"\n## 第{day.day_index + 1}天 ({day.date})")
        lines.append(f"{day.description}")
        
        if day.attractions:
            lines.append("\n### 景点安排")
            for i, attr in enumerate(day.attractions, 1):
                lines.append(f"{i}. **{attr.name}**")
                lines.append(f"   - 地址：{attr.address}")
                lines.append(f"   - 游览时间：{attr.visit_duration}分钟")
                if attr.ticket_price:
                    lines.append(f"   - 门票：¥{attr.ticket_price}")
        
        if day.meals:
            lines.append("\n### 餐饮安排")
            for meal in day.meals:
                meal_type = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}.get(meal.type, meal.type)
                lines.append(f"- {meal_type}: {meal.name} (约¥{meal.estimated_cost})")
        
        if day.hotel:
            lines.append(f"\n### 住宿：{day.hotel.name} (约¥{day.hotel.estimated_cost}/晚)")
    
    if plan.weather_info:
        lines.append(f"\n## 天气预报")
        for w in plan.weather_info:
            lines.append(f"- {w.date}: {w.day_weather} {w.day_temp}°C / {w.night_weather} {w.night_temp}°C")
    
    return "\n".join(lines)

def handle_request(req):
    method = req.get("method", "")
    req_id = req.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "trip-planner", "version": "1.0.0"}
            }
        }
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    elif method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "trip_plan":
            result = call_trip_plan(arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": result}]}
            }
        else:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}}
    elif method == "notifications/initialized":
        return None
    else:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}

def main():
    log("Trip planner MCP server starting...")
    while True:
        try:
            line = read_line()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            req = json.loads(line)
            log(f"Request: {req.get('method')}")
            resp = handle_request(req)
            if resp:
                write_line(resp)
        except Exception as e:
            log(f"Error: {e}")

if __name__ == "__main__":
    main()
