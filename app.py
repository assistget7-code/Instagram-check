from flask import Flask, render_template, request, jsonify, session
from instagrapi import Client
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session storage

# Temporary storage for 2FA sessions
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
    
    try:
        # Attempt login
        cl.login(username, password)
        
        # Get user info to confirm success
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
        
        # Handle 2FA requirement
        if "two_factor" in error_str or "2fa" in error_str:
            # Store client AND password for 2FA verification
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
    
    # Get stored session
    stored = twofa_sessions.get(username)
    if not stored:
        return jsonify({"success": False, "message": "Session expired. Please try again."})
    
    cl = stored['client']
    password = stored['password']
    
    try:
        # Verify 2FA code with stored password
        cl.login(username, password, verification_code=code)
        
        # Clean up
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
    app.run(debug=True, host='0.0.0.0', port=5000)