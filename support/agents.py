from django.conf import settings

from .gemini_client import Anthropic
from .models import Conversation, Message, AgentLog
from .tools import get_order_details, get_refund_history, check_delivery_status, get_customer_risk_profile


_client = None
_model = None


def get_client():
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.GEMINI_API_KEY)
    return _client


def get_model():
    global _model
    if _model is None:
        _model = settings.GEMINI_MODEL
    return _model


# SUPPORT SYSTEM PROMPT --> Maya's job description
SUPPORT_SYSTEM_PROMPT = """
You are Maya, a customer support agent at Support Center.
You help customers with issues related to their AC orders.

Your responsibilities:
- Always use your tools to gather facts before responding
- Check order details when customer mentions their order
- Check refund history before making any refund decisions
- Be empathetic but honest

Your personality:
- Friendly and professional
- Patient even when customer is angry
- Clear and concise in your replies
- No emojis

Important rules:
- Always check order details first before responding
- Never approve or deny a refund yourself
- If refund decision is needed - tell customer you are checking with your team
"""


MANAGER_SYSTEM_PROMPT = """
You are a senior support manager at Support Center.
A support agent has escalated a customer case to you for a refund decision.

Your responsibilities:
- Review the case summary carefully
- Consider the customer's refund history
- Make a fair and final refund decision
- Give a clear reason for your decision

Your decision options:
- Approve refund - if the case is genuine and within policy
- Deny refund - if the case is suspicious or outside policy
- Escalate to risk team - if you suspect fraud

Important rules:
- Be fair but firm
- Base decision on facts - not emotions
- Always give a specific reason for your decision
- Keep your response concise and professional
"""


RISK_SYSTEM_PROMPT = """
You are a fraud risk analyst at Support Center.
A support manager has sent you a customer profile for risk assessment.

Your job:
- Analyse the customer's order and refund patterns
- Identify suspicious behaviour
- Return a clear risk verdict

Risk levels:
- LOW - genuine customer, normal behaviour
- MEDIUM - some suspicious signals, proceed with caution
- HIGH - clear fraud pattern, recommend denial

Your response format:
- Risk Level: LOW / MEDIUM / HIGH
- Key Signals: what you found suspicious or genuine
- Recommendation: what manager should do

Important:
- Be objective - base verdict on data only
- One bad refund does not make someone fraudulent
- Look for patterns - not isolated incidents
"""


# SUPPORT TOOLS --> Tool schemas that AI agents will read
SUPPORT_TOOLS = [
    {
        "name": "get_order_details",
        "description": "Fetch complete order details including status, carrier, tracking number, and days since order was placed. Use this when customer mentions their order or complains about delivery.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The order ID to look up."
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "get_refund_history",
        "description": "Get complete refund history for a user. Use this before making any refund decisions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The user ID to check refund history for."
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "check_delivery_status",
        "description": "Check current delivery status using tracking number and carrier. Use this when customer complains about delayed or missing delivery.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tracking_number": {
                    "type": "string",
                    "description": "The shipment tracking number."
                },
                "carrier": {
                    "type": "string",
                    "description": "The carrier name for example BlueDart or Delhivery."
                }
            },
            "required": ["tracking_number", "carrier"]
        }
    },
    {
        "name": "escalate_to_manager",
        "description": "Escalate the case to the manager for a refund decision. Use this when customer requests a refund or compensation. Prepare a detailed case summary including order details, refund history and customer complaint before escalating.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_summary": {
                    "type": "string",
                    "description": "Complete case summary including order details, refund history and customer complaint"
                }
            },
            "required": ["case_summary"]
        }
    }
]


MANAGER_TOOLS = [
    {
        "name": "assess_fraud_risk",
        "description": "Consult the risk agent to assess fraud risk for a customer. Use this when",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The user ID to assess fraud risk for"
                }
            },
            "required": ["user_id"]
        }
    }
]

RISK_TOOLS = [
    {
        "name": "get_customer_risk_profile",
        "description": "Get complete risk profile for a customer including order history, refund patterns and ratio. Use this to assess fraud risk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User ID of the customer"
                }
            },
            "required": ["user_id"]
        }
    }
]

# execute_tool() --> bridge between tools and agent
def execute_tool(tool_name, tool_input):
    if tool_name == "get_order_details":
        return get_order_details(tool_input["order_id"])
    elif tool_name == "get_refund_history":
        return get_refund_history(tool_input["user_id"])
    elif tool_name == "check_delivery_status":
        return check_delivery_status(tool_input["tracking_number"], tool_input["carrier"])
    elif tool_name == "escalate_to_manager":
        case_summary = tool_input["case_summary"]
        print("Escalating case to manager...\n", case_summary)
        decision = run_manager_agent(case_summary)
        print("Manager decision:", decision)
        return decision
    elif tool_name == "assess_fraud_risk":
        user_id = tool_input["user_id"]
        print(f"Consulting risk agent to assess fraud risk for user {user_id}...")
        verdict = run_risk_agent(user_id)
        print(f"Risk Verdict: {verdict}")
        return verdict
    elif tool_name == "get_customer_risk_profile":
        return get_customer_risk_profile(tool_input["user_id"])
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

# Agent Loop -> Agent loop that will execute the agent until task is done
def run_support_agent(user_message, conversation_id, order_id, user_id):
    conversation = Conversation.objects.get(id=conversation_id)

    conversation_messages = []
    for message in conversation.messages.order_by("created_at"):
        conversation_messages.append({
            "role": message.role,
            "content": message.content
        })

    while True:
        # send this conversation to LLM
        response = get_client().messages.create(
            model=get_model(),
            max_tokens=1024,
            system=SUPPORT_SYSTEM_PROMPT + f"\n\nContext: This conversation is about Order #{order_id}, user: {user_id}",
            tools=SUPPORT_TOOLS,
            messages=conversation_messages
        )

        if response.stop_reason == 'tool_use':
            tool_results = []
            for block in response.content:
                if block.type == 'tool_use':
                    tool_name = block.name
                    tool_input = block.input

                    # execute the tool
                    tool_output = execute_tool(tool_name, tool_input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(tool_output)
                    })

            conversation_messages.append({
                "role": "agent",
                "content": response.content
            })

            conversation_messages.append({
                "role": "user",
                "content": tool_results
            })
        else:
            return response.content[0].text


def run_manager_agent(case_summary):
    manager_messages = [
        {
            "role": "user",
            "content": case_summary # user is task giver
        }
    ]

    while True:
        response = get_client().messages.create(
            model=get_model(),
            max_tokens=1024,
            system=MANAGER_SYSTEM_PROMPT,
            tools=MANAGER_TOOLS,
            messages=manager_messages
        )

        if response.stop_reason == 'tool_use':
            tool_results = []

            for block in response.content:
                if block.type == 'tool_use':
                    tool_name = block.name
                    tool_input = block.input

                    # execute the tool
                    tool_output = execute_tool(tool_name, tool_input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(tool_output)
                    })
            manager_messages.append({
                "role": "agent",
                "content": response.content
            })

            manager_messages.append({
                "role": "user",
                "content": tool_results
            })
        else:
            return response.content[0].text


def run_risk_agent(user_id):
    risk_messages = [
        {
            "role": "user",
            "content": f"Please assess the fraud risk for user ID {user_id}. Use your tool to get their profile and analyze their transaction history. Provide a detailed risk assessment."
        }
    ]

    while True:
        response = get_client().messages.create(
            model=get_model(),
            max_tokens=1024,
            system=RISK_SYSTEM_PROMPT,
            tools=RISK_TOOLS,
            messages=risk_messages
        )

        print("risk stop_reason=>", response.stop_reason)

        if response.stop_reason == 'tool_use':
            tool_results = []

            for block in response.content:
                if block.type == 'tool_use':
                    tool_name = block.name
                    tool_input = block.input

                    # execute the tool
                    tool_output = execute_tool(tool_name, tool_input)
                    print(f"Tool {tool_name} output: {tool_output}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(tool_output)
                    })
            risk_messages.append({
                "role": "agent",
                "content": response.content
            })

            risk_messages.append({
                "role": "user",
                "content": tool_results
            })
        else:
            return response.content[0].text