import sys
import os
# Add backend to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token
from app.user import UserRole

# Create client
client = TestClient(app)

def test_wallet_flow():
    print("Testing Wallet Flow...")
    
    # 1. Login/Create User (Simulated by creating token)
    # We need a user in DB. For simplicity, we assume user_id=1 exists or we use admin.
    # Let's use the admin we created in `create_admin.py` (email="admin@5edma.tn")
    
    access_token = create_access_token(
        data={"sub": "1", "role": "admin"}
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Get Wallet
    response = client.get("/wallet/me", headers=headers)
    if response.status_code == 200:
        wallet = response.json()
        print(f"[PASS] Get Wallet: Balance = {wallet['balance']} {wallet['currency']}")
    else:
        print(f"[FAIL] Get Wallet: {response.text}")
        return

    # 3. Request Top-Up
    print("Requesting Top-Up of 100.00 TND...")
    response = client.post(
        "/wallet/top-up",
        json={"amount": 100.00, "method": "test_script"},
        headers=headers
    )
    if response.status_code == 200:
        tx = response.json()
        print(f"[PASS] Top-Up Request: Status = {tx['status']}, ID = {tx['id']}")
        
        # 4. Admin Approve (Self-approve since we are admin)
        tx_id = tx['id']
        print(f"Approving Transaction {tx_id}...")
        response = client.post(
            f"/wallet/admin/transactions/{tx_id}/approve",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print(f"[PASS] Transaction Approved. New Balance: {result.get('new_balance')}")
        else:
            print(f"[FAIL] Approve Transaction: {response.text}")

    else:
        print(f"[FAIL] Top-Up Request: {response.text}")

if __name__ == "__main__":
    try:
        test_wallet_flow()
    except Exception as e:
        print(f"An error occurred: {e}")
