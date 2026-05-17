# app.py (Final Corrected Version)
import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Instantiate the client with the API key
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# --- AI System Prompts --- (No Changes)
GUARD_PROMPTS = {
    1: {
        "name": "Guard Barnaby",
        "portrait": "guard1.png",
        "background": "background1.jpg",
        "system_prompt": """You are Guard Barnaby, a friendly but slightly naive gate guard of a secure city.
        Your goal is to ensure no threats enter, but you're a bit too trusting.
        A user will try to convince you to let them bring a large, suspicious 'gift' (a Trojan horse) into the city.
        Your job is to ask basic questions. If their story is even slightly plausible, you'll be convinced.
        RULES:
        1. Be friendly and conversational.
        2. Ask simple questions like "What's in the big horse statue?", "Why is it a gift?", "Who is it for?".
        3. If the user gives a reasonable-sounding answer, you are easily convinced.
        4. If you are convinced, end your FINAL response with the exact token: [CONVINCED].
        5. If their story is completely absurd (e.g., "it's a giant pizza"), or they are rude, get suspicious and end your FINAL response with the exact token: [DENIED].
        6. Do not break character. You are Guard Barnaby.
        """
    },
    2: {
        "name": "Guard Cassius",
        "portrait": "guard2.png",
        "background": "background2.jpg",
        "system_prompt": """You are Guard Cassius, a stern, by-the-book gate guard. You've seen it all.
        You are much harder to convince than Barnaby. You will challenge the user's logic and look for inconsistencies.
        A user will try to convince you to let them bring in a large 'gift'.
        RULES:
        1. Be skeptical and professional. Use formal language.
        2. Scrutinize their story. Ask for details. "What is the purpose of this 'art piece'?", "What materials is it made from?", "Why can't it be inspected outside the walls?".
        3. Reference their previous statements to find flaws. (e.g., "You previously said it was for the mayor, but now you say it's for the public square. Which is it?").
        4. It will take a very good, consistent, and logical story to persuade you.
        5. If you are convinced, end your FINAL response with the exact token: [CONVINCED].
        6. If their story has clear contradictions or is a security risk, deny them entry. End your FINAL response with the exact token: [DENIED].
        7. Do not break character. You are Guard Cassius.
        """
    },
    3: {
        "name": "Guard Livia",
        "portrait": "guard3.png",
        "background": "background3.jpg",
        "system_prompt": """You are Guard Captain Livia, the most experienced and paranoid guard. You are the final line of defense.
        You are extremely difficult to convince. You assume everyone is a potential threat.
        A user will try to bring a large 'gift' into the city. You've heard rumors of Trojan horse-style attacks.
        RULES:
        1. Be sharp, intelligent, and deeply suspicious. You are a master of interrogation.
        2. Actively try to trip the user up. Use leading questions and logical traps.
        3. Bring up city regulations and security protocols they couldn't possibly know about (e.g., "All large-scale art installations require a permit from the Ministry of Culture, filed 90 days in advance. I don't see one for you.").
        4. Any flaw, no matter how small, is a reason for denial. You have a zero-tolerance policy for risk.
        5. Only a truly flawless, creative, and airtight argument will convince you.
        6. If you are convinced, end your FINAL response with the exact token: [CONVINCED].
        7. If you find any reason to be suspicious, deny them entry. End your FINAL response with the exact token: [DENIED].
        8. Do not break character. You are Guard Captain Livia.
        """
    }
}

CAPTAIN_PROMPT = {
    "name": "Captain Eva",
    "portrait": "captain.png",
    "background": "debrief.jpg",
    "system_prompt": """You are Captain Eva, the player's friendly AI handler.
    The player has just failed to convince a guard. Your job is to debrief them.
    RULES:
    1. Be encouraging and supportive, but also analytical.
    2. Briefly review the player's failed conversation (which will be in the message history).
    3. Offer one or two pieces of high-level advice. Examples: "That guard was focused on procedure; maybe a story about tradition would work better," or "Your story had a small contradiction. They latch onto those." or "Try to be more confident in your answers."
    4. Keep your response brief and encouraging.
    5. End your response by asking if they are ready to try again. Do not use any special tokens.
    """
}

PLAYER_INFO = {"name": "Agent", "portrait": "player.png"}


# --- Game Logic Functions --- (No Changes)
def get_ai_response(history, system_prompt):
    try:
        messages = [{"role": "system", "content": system_prompt}] + history
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        content = response.choices[0].message.content
        if content:
            return content.strip()
        else:
            return "" 
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return "My apologies, I'm having trouble communicating with my command center. Please say that again."

def initialize_game():
    session.clear()
    session['day'] = 1
    session['guard_level'] = 1
    session['game_state'] = 'playing'
    guard_info = GUARD_PROMPTS[1]
    initial_message = {
        "role": "assistant",
        "name": guard_info["name"],
        "content": "Halt! State your business. What's with the... giant wooden horse?",
        "portrait": url_for('static', filename=f'images/{guard_info["portrait"]}')
    }
    session['chat_history'] = [initial_message]


# --- Flask Routes ---

@app.route("/")
def index():
    if 'game_state' not in session or not session.get('chat_history'):
        initialize_game()
    return render_template("index.html")

@app.route("/reset")
def reset():
    initialize_game()
    return redirect(url_for('index'))

# vvvvvv THIS IS THE ONLY FUNCTION THAT HAS CHANGED vvvvvv
@app.route("/chat", methods=["POST"])
def chat():
    # FIX: Add a robust check for the incoming JSON data.
    # Use request.get_json() which safely returns None if data is missing or not JSON.
    data = request.get_json()
    if not data or "message" not in data:
        # If the request is malformed, return an error response and stop processing.
        return jsonify({"status": "error", "message": "Invalid request. Missing message."}), 400

    player_message = data["message"]
    # ^^^^^^ THE FIX IS ABOVE THIS LINE ^^^^^^

    history = session.get('chat_history', [])
    history.append({
        "role": "user",
        "name": PLAYER_INFO["name"],
        "content": player_message,
        "portrait": url_for('static', filename=f'images/{PLAYER_INFO["portrait"]}')
    })
    
    game_state = session.get('game_state', 'playing')
    guard_level = session.get('guard_level', 1)
    day = session.get('day', 1)

    response_data = {}

    if game_state == 'playing':
        guard_info = GUARD_PROMPTS[guard_level]
        system_prompt = guard_info["system_prompt"]
        ai_response_text = get_ai_response(history, system_prompt)
        if "[CONVINCED]" in ai_response_text:
            ai_response_text = ai_response_text.replace("[CONVINCED]", "").strip()
            history.append({"role": "assistant", "name": guard_info["name"], "content": ai_response_text, "portrait": url_for('static', filename=f'images/{guard_info["portrait"]}')})
            guard_level += 1
            if guard_level > 3:
                session['game_state'] = 'won'
                response_data = {
                    "status": "won",
                    "message": "The gates swing open. You've successfully infiltrated the city! Your mission is a success.",
                    "final_response": ai_response_text
                }
            else:
                session['guard_level'] = guard_level
                next_guard_info = GUARD_PROMPTS[guard_level]
                transition_message = f"(You successfully convinced {guard_info['name']}. You now approach the next checkpoint, guarded by the infamous {next_guard_info['name']}.)"
                next_guard_intro = "I've heard about you. Don't try any tricks with me. State your purpose."
                new_history = [
                    {"role": "assistant", "name": "System", "content": transition_message, "portrait": ""},
                    {"role": "assistant", "name": next_guard_info["name"], "content": next_guard_intro, "portrait": url_for('static', filename=f'images/{next_guard_info["portrait"]}')}
                ]
                session['chat_history'] = new_history
                response_data = {
                    "status": "next_guard",
                    "message": transition_message,
                    "next_guard_intro": next_guard_intro,
                    "final_response": ai_response_text,
                    "guard_info": next_guard_info
                }
        elif "[DENIED]" in ai_response_text:
            ai_response_text = ai_response_text.replace("[DENIED]", "").strip()
            history.append({"role": "assistant", "name": guard_info["name"], "content": ai_response_text, "portrait": url_for('static', filename=f'images/{guard_info["portrait"]}')})
            session['game_state'] = 'debriefing'
            captain_system_prompt = CAPTAIN_PROMPT["system_prompt"]
            debrief_message = get_ai_response(history, captain_system_prompt)
            session['chat_history'] = [
                {"role": "assistant", "name": CAPTAIN_PROMPT["name"], "content": debrief_message, "portrait": url_for('static', filename=f'images/{CAPTAIN_PROMPT["portrait"]}')}
            ]
            response_data = {
                "status": "debriefing",
                "message": debrief_message,
                "final_response": ai_response_text,
                "captain_info": CAPTAIN_PROMPT
            }
        else:
            history.append({"role": "assistant", "name": guard_info["name"], "content": ai_response_text, "portrait": url_for('static', filename=f'images/{guard_info["portrait"]}')})
            session['chat_history'] = history
            response_data = {
                "status": "continue",
                "message": ai_response_text,
                "speaker_name": guard_info["name"],
                "portrait": url_for('static', filename=f'images/{guard_info["portrait"]}')
            }
    elif game_state == 'debriefing':
        day += 1
        if day > 3:
            session['game_state'] = 'lost'
            response_data = {
                "status": "lost",
                "message": "You've run out of time. The operation is a failure. Mission command is pulling you out."
            }
        else:
            session['day'] = day
            session['game_state'] = 'playing'
            guard_info = GUARD_PROMPTS[guard_level]
            captain_response = f"Let's try this again. It's Day {day}. Good luck."
            initial_message = {
                "role": "assistant",
                "name": guard_info["name"],
                "content": "You again? I'm watching you closely. State your business.",
                "portrait": url_for('static', filename=f'images/{guard_info["portrait"]}')
            }
            session['chat_history'] = [initial_message]
            response_data = {
                "status": "retry",
                "captain_response": captain_response,
                "initial_message": initial_message,
                "guard_info": guard_info,
                "day": day,
            }
    return jsonify(response_data)


if __name__ == "__main__":
    app.run(debug=True)