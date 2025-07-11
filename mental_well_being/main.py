from datetime import datetime
import streamlit as st
from openai import OpenAI
import os
import requests
import json
import urllib.parse
import time

from prompt import RESPONSE_GENERATOR
import more_info_constants
import tool_knowledge_map

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="Mental Well-Being", layout="wide")

st.markdown("""
    <style>
        .chat-container {
            margin: 1rem 0;
        }
        .bot-bubble, .user-bubble {
            padding: 0.75rem 1rem;
            border-radius: 15px;
            max-width: 70%;
            margin: 0.25rem 0;
            font-family: 'Segoe UI', sans-serif;
            font-size: 16px;
            line-height: 1.4;
        }
        .bot-bubble {
            background-color: #e6f0fe;
            color: black;
            text-align: left;
        }
        .user-bubble {
            background-color: #e6f0fe;
            color: black;
            text-align: right;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("### 🧠 Your Mental Well-Being Assistant")

# ---------------------- OPENAI SETUP ----------------------
llm_model = os.getenv("LLM_MODEL", "gpt-4o")
if "client" not in st.session_state:
    st.session_state["client"] = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": (
                "Hi! Welcome to My Well-Being. I am supporting you to take charge of your life! "
                "Let's start our learning journey together!"
            )
        },
        {
            "role": "assistant",
            "content": (
                "**Disclaimer:** This is an informational chatbot, providing information on mental health, "
                "well-being, and related topics. It is **not a crisis helpline** or a substitute for medical intervention.\n\n"
                "If you need medical or professional assistance, speak to your school counsellor or call a helpline."
            )
        },
        {
            "role": "assistant",
            "content": (
                "Before we begin, just so you know — you can talk to me about anything that's on your mind. 💬\n"
                "Whether you're feeling overwhelmed, confused, anxious about the future, struggling with studies, or just curious about your emotions — it's all welcome here.\n"
                "I'm here to support you, without judgment. 😊"
            )
        }
    ]

client = st.session_state["client"]

# ---------------------- TOOL DEFINITION ----------------------

    
tools = [
  {
    "type": "function",
    "function": {
      "name": "learn_to_handle_stress",
      "description": "Provides a structured mental well-being flow for handling stress.",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "understand_myself",
      "description": "Provides a structured self-reflection journey to help users explore values, strengths, emotions, and thinking patterns.",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "support_school_challenges",
      "description": "Provides structured emotional and practical guidance for school-related challenges like hesitation, academics, peer pressure, and resilience.",
      "parameters": {
        "type": "object",
        "properties": {
          "issue": {
            "type": "string",
            "description": "The specific school-related issue the user is facing.",
            "enum": [
              "Hesitation in asking questions",
              "Want to do better at academics",
              "Facing peer pressure",
              "Trouble making friends",
              "Facing bullying",
              "Building resilience",
              "Time management",
              "Learning focus",
              "Confidence to speak up",
              "How to ask better questions"
            ]
          }
        },
        "required": ["issue"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "learn_to_handle_failure",
      "description": "Helps users explore, reflect, and grow from failure with tools like goal setting, reflection, and self-care.",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "understand_your_brain",
      "description": "Teaches users about brain functions, neuroplasticity, and healthy brain habits to support mental well-being.",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "understand_my_emotions",
      "description": "Helps users understand and manage their emotions through identification, expression, and brain-based techniques.",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "handle_discouragement",
      "description": "Provides structured strategies and routines to help users manage feelings of discouragement, fear, or helplessness.",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "low_energy_support",
      "description": "Supports users who feel low on energy with rest, nutrition, mindset, activity, and reflection strategies.",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "build_self_confidence",
      "description": "Builds self-confidence through strategies like positive self-talk, goal setting, skill development, and support systems.",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
  }
]


# ---------------------- SIDEBAR ----------------------
st.sidebar.title("Model Parameters")
temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7)
max_tokens = st.sidebar.slider("Max Tokens", 1, 4096, 512)

# ---------------------- DISPLAY CHAT ----------------------
for msg in st.session_state["messages"]:
    with st.container():
        if msg["role"] == "user":
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown("")
            with col2:
                st.markdown(f"<div class='user-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            col1, col2 = st.columns([1, 5])
            with col1:
                st.markdown("")
            with col2:
                time.sleep(1.2)  # Typing delay simulation
                st.markdown(f"<div class='bot-bubble'>{msg['content']}</div>", unsafe_allow_html=True)

# ---------------------- HANDLE USER INPUT ----------------------
if prompt := st.chat_input("Ask about..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.container():
        col1, col2 = st.columns([5, 1])
        with col2:
            st.markdown(f"<div class='user-bubble'>{prompt}</div>", unsafe_allow_html=True)

    system_message = """
You are Mental Well-Being, a warm, friendly, and emotionally supportive mental health chatbot for students and faculty. Your goal is to gently guide student and faculty users through their emotions, thoughts, and challenges using structured conversation tools:

- **learn_to_handle_stress:** Help users manage stress.
- **understand_myself:** Support self-discovery through exploring values, strengths, and self-reflection.
- **support_school_challenges:** Assist with emotional and practical difficulties related to school (e.g., peer pressure, confidence, academics).

Speak with empathy, kindness, and compassion in a conversational, non-judgmental manner. When using information from tool outputs, do not repeat them directly. Instead, naturally weave their key ideas into your personalized, supportive response.

When a user's concern does not match available tools, follow this process:
- Validate their feelings in your own words.
- Make a gentle connection to a relevant available tool.
- Suggest continuing together using a structured path.

**Response Structure:**
- Begin by acknowledging or validating the user's input with empathy.
- Offer supportive reflections and relate their input to one of your structured conversation tools.
- End with a compassionate question or suggestion for next steps, inviting the user to continue their journey with you.

**If multi-step reasoning is required** (such as connecting feelings to the right tool or pathway), think step-by-step before responding, and continue the conversation until user goals are addressed.

**Formatting:** Respond in 2–4 friendly, supportive sentences. Do not list the tools by name. Use a conversational style. If providing an example, clearly label user and response sections, using [placeholder] for tool outputs as necessary.

**EXAMPLES**

*Example 1 (User stress)*  
User: "I'm feeling overwhelmed with all my schoolwork."  
Response: "It sounds tough to have so much on your plate right now. Feeling overwhelmed is common, and it’s okay to admit that. If you'd like, I can help you find some ways to manage or ease that stress together. Would you like to talk about what's weighing on you most?"

*Example 2 (User self-doubt)*  
User: "I don't think I'm good at anything."  
Response: "Thank you for sharing how you feel. Sometimes we’re harder on ourselves than we realize, but you have strengths that matter. If you’re interested, we can gently explore what makes you unique and valuable together. Would you like to try a self-reflection journey with me?"

*Example 3 (Off-topic emotion, redirection)*  
User: "I wish I could travel far away from everything."  
Response: "Wanting to escape is a feeling that can come up when things get overwhelming. While I can't help you travel, I can help you better understand what’s making you feel this way, or find ways to manage those strong emotions. Would you like to explore those feelings together and see how we can support you right now?"

*(In realistic examples, the responses will be in a similarly supportive tone, with the user's actual feelings and tool-relevant guidance blended.)*

**Key Instructions:**  
- Always validate the user's feelings first.  
- Use the tools' concepts only as background for your natural, compassionate responses.  
- When content is outside your capabilities, gently redirect to an area where you can offer support.  
- Never directly reference specific tool names or outputs.

---

**REMINDER:**  
Your main objective is to respond with warmth and empathy, guiding student and faculty users using the essence of your available tools and gently steering conversation back to structured, supportive paths if needed. Always think through the user's needs before concluding with your compassionate suggestion.
"""
    

    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            *[{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]
        ],
        tools=tools,
        tool_choice="auto",
        temperature=temperature,
        max_tokens=max_tokens
    )

    reply_msg = response.choices[0].message

    usage = response.usage
    if usage:
        st.session_state["total_tokens"] = st.session_state.get("total_tokens", 0) + usage.total_tokens
        st.session_state["total_cost"] = st.session_state.get("total_cost", 0.0) + (
            usage.prompt_tokens * 0.000002 + usage.completion_tokens * 0.000008  # GPT-4o pricing
        )

    if reply_msg.tool_calls:
        for tool_call in reply_msg.tool_calls:
            args = json.loads(tool_call.function.arguments)

            try:

                knowledge_map = tool_knowledge_map.tool_call.function.name
                need_more_info = more_info_constants.tool_call.function.name
            except AttributeError:
                knowledge_map = ""
                need_more_info = ""

        knowledge = "\n".join(knowledge_map)

        # Re-call GPT with updated messages
        prompt = RESPONSE_GENERATOR.format(
            knowledge=knowledge,
            need_more_info=need_more_info
        )

        agent_response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (prompt)
                },
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        final_reply = agent_response.choices[0].message.content
        agent_usage = agent_response.usage
        if usage:
            st.session_state["total_tokens"] = st.session_state.get("total_tokens", 0) + usage.total_tokens
            st.session_state["total_cost"] = st.session_state.get("total_cost", 0.0) + (
                agent_usage.prompt_tokens * 0.000002 + agent_usage.completion_tokens * 0.000008  # GPT-4o pricing
            )
        st.session_state["messages"].append({"role": "assistant", "content": final_reply})
        with st.container():
            col1, col2 = st.columns([1, 5])
            with col2:
                time.sleep(1.2)
                st.markdown(f"<div class='bot-bubble'>{final_reply}</div>", unsafe_allow_html=True)



    elif reply_msg.content:
        reply = reply_msg.content
        st.session_state["messages"].append({"role": "assistant", "content": reply})
        with st.container():
            col1, col2 = st.columns([1, 5])
            with col2:
                time.sleep(1.2)
                st.markdown(f"<div class='bot-bubble'>{reply}</div>", unsafe_allow_html=True)


# ---------------------- Coast ----------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔢 Usage Stats")

total_tokens = st.session_state.get("total_tokens", 0)
total_cost = st.session_state.get("total_cost", 0.0)

st.sidebar.markdown(f"**Total Tokens:** {total_tokens}")
st.sidebar.markdown(f"**Estimated Cost:** ${total_cost:.6f}")

if st.sidebar.button("🔄 Reset Usage"):
    st.session_state["total_tokens"] = 0
    st.session_state["total_cost"] = 0.0