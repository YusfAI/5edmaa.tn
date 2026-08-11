import httpx
import sys

BASE_URL = "http://127.0.0.1:8001"

def test_wallet_flow():
    print(f"Testing Wallet Flow against {BASE_URL}...")
    
    # 1. Login as Admin
    # Admin credentials from create_admin.py
    login_data = {
        "username": "admin@5edma.tn",
        "password": "AdminStrong123!"
    }
    
    try:
        print("Logging in...")
        response = httpx.post(f"{BASE_URL}/auth/login", data=login_data)
        
        if response.status_code != 200:
            print(f"[FAIL] Login failed: {response.text}")
            print("Ensure create_admin.py ran successfully.")
            return

        token_data = response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("[PASS] Login successful")

        # 2. Get Wallet
        print("Getting Wallet...")
        response = httpx.get(f"{BASE_URL}/wallet/me", headers=headers)
        if response.status_code == 200:
            wallet = response.json()
            print(f"[PASS] Get Wallet: Balance = {wallet['balance']} {wallet['currency']}")
        else:
            print(f"[FAIL] Get Wallet: {response.text}")
            return

        # 3. Request Top-Up
        print("Requesting Top-Up of 100.00 TND...")
        response = httpx.post(
            f"{BASE_URL}/wallet/top-up",
            json={"amount": 100.00, "method": "test_script"},
            headers=headers
        )
        if response.status_code == 200:
            tx = response.json()
            print(f"[PASS] Top-Up Request: Status = {tx['status']}, ID = {tx['id']}")
            
            # 4. Admin Approve
            tx_id = tx['id']
            print(f"Approving Transaction {tx_id}...")
            response = httpx.post(
                f"{BASE_URL}/wallet/admin/transactions/{tx_id}/approve",
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                print(f"[PASS] Transaction Approved. New Balance: {result.get('new_balance')}")
            else:
                print(f"[FAIL] Approve Transaction: {response.text}")

        else:
            print(f"[FAIL] Top-Up Request: {response.text}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_wallet_flow()
