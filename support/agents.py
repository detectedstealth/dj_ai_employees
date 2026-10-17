from django.conf import settings

from .gemini_client import Anthropic
from .models import Conversation, Message, AgentLog
from .tools import get_order_details, get_refund_history, check_delivery_status

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
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


# Agent Loop -> Agent loop that will execute the agent until task is done
def run_support_agent(user_message, conversation_id, order_id, user_id):
    # Only using GEMINI FREE to test will swap to CLAUDE later
    client = Anthropic(api_key=settings.GEMINI_API_KEY)
    llm_model = settings.GEMINI_MODEL

    conversation = Conversation.objects.get(id=conversation_id)

    conversation_messages = []
    for message in conversation.messages.order_by("created_at"):
        conversation_messages.append({
            "role": message.role,
            "content": message.content
        })

    while True:
        # send this conversation to LLM
        response = client.messages.create(
            model=llm_model,
            max_tokens=1024,
            system=SUPPORT_SYSTEM_PROMPT + f"\n\nContext: This conversation is about Order #{order_id}, user: {user_id}",
            tools=SUPPORT_TOOLS,
            messages=conversation_messages
        )

        print("stop reason==>", response.stop_reason)

        if response.stop_reason == 'tool_use':
            tool_results = []
            for block in response.content:
                if block.type == 'tool_use':
                    tool_name = block.name
                    tool_input = block.input
                    print(tool_name, tool_input)

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

