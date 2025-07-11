import requests
import os
from datetime import datetime
import urllib.parse


def search_patient(patientName: str, platform: str = "googlehealth", customer: str = "alpha-dental", practitionerId: str = "7487280b-a89e-495e-9cad-9dd72ca4ecd6"):
    url = "https://api.dev.med-x.ai/api/v1/dentalxchange/search-patient"
    headers = {
        "Authorization": f"Bearer {os.getenv('MEDX_API_TOKEN')}"
    }

    data = {
        "patientName": patientName,
        "platform": platform,
        "customer": customer,
        "practitionerId": practitionerId
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        result = response.json()

        if not result.get("success") or not result.get("data"):
            return f"⚠️ No results found for **{patientName}**.", []

        formatted_list = []
        formatted_list.append("\n\n")

        for idx, entry in enumerate(result["data"], 1):
            formatted_list.append(f"""**🧾 Patient #{idx}**
- 👤 **Name:** {entry.get('patient_name', 'N/A')}
- 🧬 **Patient ID:** `{entry.get('patient_id', 'N/A')}`
- 🆔 **Member ID:** `{entry.get('member_id', 'N/A')}`
- 📄 **Insurance Carrier:** {entry.get('ins_carrier', 'N/A')}
- 📝 **Plan Name:** {entry.get('ins_plan_name', 'N/A')}
- 🏷️ **Plan Type:** {entry.get('ins_plan_type', 'N/A')}
- 🔗 **External Patient ID:** `{entry.get('external_patient_id', 'N/A')}`
- 🌐 **FHIR Platform:** {entry.get('Fhir', 'N/A')}
\n---\n""")

        return "\n".join(formatted_list), result["data"]

    except requests.exceptions.RequestException as e:
        return f"❌ API error: {str(e)}", []
    

# ---------------------- get_eligibility_history FUNCTION ----------------------

def get_eligibility_history(patientId: str, customer: str = "alpha-dental", practitionerId: str = "7487280b-a89e-495e-9cad-9dd72ca4ecd6") -> str:
    url = "https://api.dev.med-x.ai/api/v1/dentalxchange/patient/eligibility-history"
    headers = {
        "Authorization": f"Bearer {os.getenv('MEDX_API_TOKEN')}"
    }

    data = {
        "patientId": patientId,
        "customer": customer,
        "practitionerId": practitionerId
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        result = response.json()

        histories = result.get("data", {}).get("histories", [])
        if not histories:
            return f"⚠️ No eligibility history found for patient ID: `{patientId}`."

        formatted = []
        formatted.append("\n\n")
        

        block = f"""**## 📄 Eligibility History**  
- Patient ID: {patientId}  
- Total Records Found: {len(histories)}  
"""
        formatted.append(block.strip())
        formatted.append("\n\n---\n\n")


        for idx, item in enumerate(histories, 1):
            created_date = datetime.fromtimestamp(item["created_at"] / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
            eligibility_link = (
                f"[📄 Download PDF]({item['eligibility_file']})"
                if item.get("eligibility_file")
                else "❌ No file"
            )

            block = f"""**History #{idx}**
- 🕒 Created: {created_date}
- 🧾 Insurance: {item.get("ins_carrier", "N/A")}
- 🏥 Appointment ID: {item.get("appointment_id", "N/A")}
- 🔗 External Patient ID: {item.get("external_patient_id", "N/A")}
- ✅ Uploaded: {"Yes" if item.get("is_uploaded") else "No"}
- 🧠 Manual Upload Required: {"Yes" if item.get("is_manual_upload_required") else "No"}
- 📎 File: {eligibility_link}
"""
            

            formatted.append(block.strip() + "\n\n")
                    
            

        eligibility = result.get("data", {}).get("eligibility", [])
        response_data = eligibility.get("response", {})


        # ---------------- ACTIVE COVERAGE ----------------
        active_coverage = response_data.get("activeCoverage", [])
        if active_coverage:
            block = "\n**🏥 Active Coverage:**\n"
            for cov in active_coverage:
                url_msg = urllib.parse.unquote(cov.get("message", ""))
                block += f"- Plan: {cov.get('planCoverageDescription', 'N/A')}, Level: {cov.get('coverageLevel', 'N/A')}, Type: {cov.get('insuranceType', 'N/A')}\n"
                block += f"  {url_msg}\n"
            formatted.append(block.strip() + "\n\n")



        # ---------------- CO-INSURANCE ----------------
        co_insurance = response_data.get("coInsurance", [])
        if co_insurance:
            block = "\n**💳 Co-Insurance:**\n"
            for co in co_insurance:
                code_or_service = co.get("code") or co.get("serviceType", "N/A")
                network = co.get("network", "N/A")
                percent = co.get("percent", "0")
                block += f"- {code_or_service} ({network}): {percent}%\n"
            formatted.append(block.strip() + "\n\n")

        

        # ---------------- DEDUCTIBLES ----------------
        deductibles = response_data.get("deductible", [])
        if deductibles:
            block = "\n**💰 Deductibles:**\n"
            for d in deductibles:
                service = d.get("serviceType", "N/A")
                network = d.get("network", "N/A")
                amount = d.get("amount", "N/A")
                msg = d.get("message", "")
                line = f"- {service} ({network}): ${amount}"
                if msg:
                    line += f" ({msg})"
                block += line + "\n"
            formatted.append(block.strip() + "\n\n")

        

        # ---------------- LIMITATION & MAXIMUM ----------------
        limits = response_data.get("limitationAndMaximum", [])
        if limits:
            block = "\n**📊 Limitations & Maximums:**\n"
            for lm in limits:
                amount = lm.get("amount", "N/A")
                service = lm.get("serviceType", "N/A")
                level = lm.get("coverageLevel", "N/A")
                period = lm.get("planPeriod", "N/A")
                network = lm.get("network", "N/A")
                block += f"- {service} ({level}, {network}, {period}): ${amount}\n"
            formatted.append(block.strip() + "\n\n")


        # ---------------- PATIENT INFO ----------------
        patient = response_data.get("patient", {})
        if patient:
            full_name = f"{patient.get('firstName', '')} {patient.get('lastName', '')}".strip()
            dob = patient.get("dateOfBirth", "N/A")
            gender = patient.get("gender", "N/A")
            relation = patient.get("relationship", "N/A")
            addr = patient.get("address", {})
            address_line = f"{addr.get('address1', '')}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zipCode', '')}".strip()

            block = f"""\n**👤 Patient Info:**
            - Name: {full_name}
            - DOB: {dob}
            - Gender: {gender}
            - Relationship: {relation}
            - Address: {address_line}
            """
            formatted.append(block.strip() + "\n\n")

        # ---------------- PLAN INFO ----------------
        plan = patient.get("plan", {})
        if plan:
            block = f"""\n**📅 Plan Info:**
            - Group: {plan.get("groupName", "N/A")} ({plan.get("groupNumber", "N/A")})
            - Effective: {plan.get("effectiveDateFrom", "N/A")} to {plan.get("effectiveDateTo", "N/A")}
            - Subscriber ID: {plan.get("subscriberId", "N/A")}
            """
            formatted.append(block.strip() + "\n\n")

        # ---------------- PAYER INFO ----------------
        payer = response_data.get("payer", {})
        if payer:
            block = f"""\n**🏦 Payer Info:**
            - Name: {payer.get("name", "N/A")}
            - ID: {payer.get("id", "N/A")}
            - Contact: {payer.get("contact", "N/A")}
            """
            formatted.append(block.strip() + "\n\n")

        # ---------------- COVERAGE STATUS ----------------
        status = response_data.get("status")
        if status:
            emoji = "🟢" if status.lower() == "active" else "🔴"
            block = f"\n**{emoji} Coverage Status:** {status}\n"
            formatted.append(block.strip() + "\n\n")

        

        # ---------------- SUBSCRIBER INFO ----------------
        subscriber = response_data.get("subscriber", {})
        if subscriber:
            sub_name = f"{subscriber.get('firstName', '')} {subscriber.get('lastName', '')}".strip()
            sub_dob = subscriber.get("dateOfBirth", "N/A")
            sub_gender = subscriber.get("gender", "N/A")
            sub_addr = subscriber.get("address", {})
            sub_address_line = f"{sub_addr.get('address1', '')}, {sub_addr.get('city', '')}, {sub_addr.get('state', '')} {sub_addr.get('zipCode', '')}".strip()

            block = f"""\n**👤 Subscriber Info:**
        - Name: {sub_name}
        - DOB: {sub_dob}
        - Gender: {sub_gender}
        - Address: {sub_address_line}
        """

            sub_plan = subscriber.get("plan", {})
            if sub_plan:
                block += f"""- Group: {sub_plan.get("groupName", "N/A")} ({sub_plan.get("groupNumber", "N/A")})
        - Effective: {sub_plan.get("effectiveDateFrom", "N/A")} to {sub_plan.get("effectiveDateTo", "N/A")}
        - Subscriber ID: {sub_plan.get("subscriberId", "N/A")}
        """
            formatted.append(block.strip() + "\n\n")


        return "".join(formatted)

    except requests.exceptions.RequestException as e:
        return f"❌ API error: {str(e)}"   


# ---------------------- TOOL DEFINITION ----------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_patient",
            "description": "Search patient info using patient name",
            "parameters": {
                "type": "object",
                "properties": {
                    "patientName": {
                        "type": "string",
                        "description": "Full name of the patient"
                    }
                },
                "required": ["patientName"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "get_eligibility_history",
        "description": "Fetch eligibility history for a given patient ID",
        "parameters": {
            "type": "object",
            "properties": {
                "patientId": {
                    "type": "string",
                    "description": "Patient ID from Medx system"
                }
            },
            "required": ["patientId"]
        }
    }
}   
]
