import streamlit as st
from openai import OpenAI
import os
import json

from tools import search_patient, get_eligibility_history, tools

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="Dento", layout="wide")

st.markdown("""
    <style>
        body {
            background-color: #ffffff;
        }
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

st.markdown("### 🦷 Dento - Your Dental AI Assistant")

# ---------------------- OPENAI SETUP ----------------------
llm_model = os.getenv("LLM_MODEL", "gpt-4o")
if "client" not in st.session_state:
    st.session_state["client"] = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm Dento, your Dental AI Assistant."
            )
        },
    ]

client = st.session_state["client"]


def on_patient_selected():
    selected = st.session_state["patient_selector"]
    if selected and selected["patient_id"]:
        # Set a flag to trigger display logic later in main flow
        st.session_state["trigger_eligibility"] = True



# ---------------------- SIDEBAR ----------------------
st.sidebar.title("Model Parameters")
temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7)
max_tokens = st.sidebar.slider("Max Tokens", 1, 4096, 256)


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
                st.markdown(f"<div class='bot-bubble'>{msg['content']}</div>", unsafe_allow_html=True)

# ---------------------- HANDLE USER INPUT ----------------------
if prompt := st.chat_input("Ask about..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.container():
        col1, col2 = st.columns([5, 1])
        with col2:
            st.markdown(f"<div class='user-bubble'>{prompt}</div>", unsafe_allow_html=True)


    # Get OpenAI response
    response = client.chat.completions.create(
        model=llm_model,
        messages=[
    {
        "role": "system",
        "content": (
            "You are Dento, a helpful and friendly dental AI assistant. "
            "You help front-desk and billing staff with tasks like checking insurance eligibility, "
            "retrieving patient info, resolving ambiguities like duplicate names, "
            "and explaining dental coverage in simple terms."
        )
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

    # ---------------------- TOOL CALL DETECTED ----------------------
    if reply_msg.tool_calls:
        for tool_call in reply_msg.tool_calls:
            args = json.loads(tool_call.function.arguments)

            if tool_call.function.name == "search_patient":
                tool_result, patient_list = search_patient(args["patientName"])

                # Show the patient list markdown (optional if needed)
                st.session_state["messages"].append({"role": "assistant", "content": tool_result})
                with st.container():
                    col1, col2 = st.columns([1, 5])
                    with col2:
                        st.markdown(f"<div class='bot-bubble'><pre>{tool_result}</pre></div>", unsafe_allow_html=True)

                if len(patient_list) == 1:
                    patient_id = patient_list[0]["patient_id"]
                    tool_result = get_eligibility_history(patient_id)
                    st.session_state["messages"].append({"role": "assistant", "content": tool_result})
                    with st.container():
                        col1, col2 = st.columns([1, 5])
                        with col2:
                            st.markdown(f"<div class='bot-bubble'><pre>{tool_result}</pre></div>", unsafe_allow_html=True)

                elif len(patient_list) > 1:
                    
                    default_placeholder = {"patient_name": "-- Select a patient --", "patient_id": ""}
                    options_with_placeholder = [default_placeholder] + patient_list

                    selected = st.selectbox(
                        "🔎 Multiple patients found. Please select one to view eligibility:",
                        options=options_with_placeholder,
                        format_func=lambda x: f"{x['patient_name']}  - Patient ID: {x['patient_id']}" if x["patient_id"] else x["patient_name"],
                        key="patient_selector",
                        on_change=on_patient_selected
                    )


            elif tool_call.function.name == "get_eligibility_history":
                tool_result = get_eligibility_history(args["patientId"])
                st.session_state["messages"].append({"role": "assistant", "content": tool_result})
                with st.container():
                    col1, col2 = st.columns([1, 5])
                    with col2:
                        st.markdown(f"<div class='bot-bubble'><pre>{tool_result}</pre></div>", unsafe_allow_html=True)
                

    # ---------------------- REGULAR TEXT RESPONSE ----------------------
    elif reply_msg.content:
        reply = reply_msg.content
        st.session_state["messages"].append({"role": "assistant", "content": reply})
        with st.container():
            col1, col2 = st.columns([1, 5])
            with col2:
                st.markdown(f"<div class='bot-bubble'>{reply}</div>", unsafe_allow_html=True)


# Trigger only once
if st.session_state.get("trigger_eligibility", False):
    selected = st.session_state["patient_selector"]
    st.session_state["trigger_eligibility"] = False  # reset the flag

    # Show user bubble on right
    user_msg = f"👤 {selected['patient_name']} - Patient ID: {selected['patient_id']}"
    st.session_state["messages"].append({"role": "user", "content": user_msg})
    with st.container():
        col1, col2 = st.columns([5, 1])
        with col2:
            st.markdown(f"<div class='user-bubble'>{user_msg}</div>", unsafe_allow_html=True)

    # Call API
    tool_result = get_eligibility_history(selected["patient_id"])

    # Show response
    st.session_state["messages"].append({"role": "assistant", "content": tool_result})
    with st.container():
        col1, col2 = st.columns([1, 5])
        with col2:
            st.markdown(f"<div class='bot-bubble'><pre>{tool_result}</pre></div>", unsafe_allow_html=True)


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


