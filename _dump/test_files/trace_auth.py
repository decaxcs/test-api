import asyncio
import json
from pathlib import Path
from ultima_scraper_api import OnlyFansAPI, UltimaScraperAPIConfig
from ultima_scraper_api.apis.onlyfans.authenticator import OnlyFansAuthenticator
from ultima_scraper_api.managers.session_manager import AuthedSession, SessionManager
from ultima_scraper_api.apis.onlyfans.classes.extras import endpoint_links, create_headers
import aiohttp

async def trace_authentication():
    print("=== OnlyFans Authentication Trace ===\n")
    
    # Load auth.json
    auth_data = json.loads(Path("auth.json").read_text())
    auth_details = auth_data["auth"]
    
    print(f"1. Loaded auth.json:")
    print(f"   - User ID: {auth_details['id']}")
    print(f"   - Has cookie: {'cookie' in auth_details}")
    print(f"   - Has x_bc: {'x_bc' in auth_details}")
    print(f"   - Has user_agent: {'user_agent' in auth_details}")
    
    # Create API
    config = UltimaScraperAPIConfig()
    api = OnlyFansAPI(config)
    
    # Create authenticator manually to trace
    print("\n2. Creating authenticator...")
    authenticator = OnlyFansAuthenticator(api)
    authenticator.auth_details.id = auth_details["id"]
    authenticator.auth_details.cookie.parse(auth_details["cookie"])
    authenticator.auth_details.x_bc = auth_details["x_bc"]
    authenticator.auth_details.user_agent = auth_details["user_agent"]
    
    print(f"   - Auth ID from cookie: {authenticator.auth_details.cookie.auth_id}")
    print(f"   - Session from cookie: {authenticator.auth_details.cookie.sess[:20]}...")
    
    # Test the customer endpoint directly
    print("\n3. Testing customer endpoint...")
    link = endpoint_links().customer
    print(f"   - URL: {link}")
    
    # Create session
    session_manager = SessionManager(config, proxies=[], max_threads=1)
    auth_session = AuthedSession(authenticator, session_manager)
    authenticator.auth_session = auth_session
    
    # Setup headers
    dynamic_rules = session_manager.dynamic_rules
    auth_id = str(authenticator.auth_details.cookie.auth_id)
    headers = create_headers(
        dynamic_rules, 
        auth_id, 
        authenticator.auth_details.x_bc, 
        authenticator.auth_details.user_agent, 
        link
    )
    auth_session.headers = headers
    
    print("\n4. Making request to check auth status...")
    try:
        json_resp = await auth_session.json_request(link)
        print(f"   - Response type: {type(json_resp)}")
        
        if isinstance(json_resp, dict):
            print(f"   - Response keys: {list(json_resp.keys())[:10]}")
            
            # Check isAuth field
            if "isAuth" in json_resp:
                print(f"   - isAuth: {json_resp['isAuth']}")
            else:
                print("   - isAuth field not found!")
                
            # Check for error
            if "error" in json_resp:
                print(f"   - Error: {json_resp['error']}")
                
            # Show first few fields
            for key in list(json_resp.keys())[:5]:
                value = json_resp[key]
                if isinstance(value, (str, int, bool, type(None))):
                    print(f"   - {key}: {value}")
                    
    except Exception as e:
        print(f"   - Request failed: {type(e).__name__}: {str(e)}")
    
    # Close session
    await auth_session.close()
    
    print("\n5. Summary:")
    print("   - The authentication checks the 'isAuth' field from the API")
    print("   - If isAuth is False or missing, authentication fails")
    print("   - Common issues: expired cookies, wrong user agent, IP mismatch")

if __name__ == "__main__":
    asyncio.run(trace_authentication())