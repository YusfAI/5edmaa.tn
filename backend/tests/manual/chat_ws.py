import asyncio
import websockets

async def test_ws():
    uri = "ws://127.0.0.1:8001/chat/ws/1"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            await websocket.send("Hello")
            print("Sent Hello")
            # We don't expect a response in current impl, so just disconnect
            return True
    except Exception as e:
        print(f"Failed to connect: {e}")
        return False

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(test_ws())
    if success:
        print("WebSocket Test PASSED")
    else:
        print("WebSocket Test FAILED")
