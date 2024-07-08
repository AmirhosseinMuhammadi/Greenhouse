import asyncio
import websockets
import threading

async def send_message_over_websocket(message, IP):
    try:
        async with websockets.connect(IP) as websocket:
            print("Connected to WebSocket server")
            await websocket.send(str(message))
            print(f"Sent message: {message}")
            response = await websocket.recv()
            print(f"Received response: {response}")
    except Exception as e:
        print(f"Error: {e}")

async def main(message , IP):
    while True:
        try:
            await send_message_over_websocket(message, IP)
            break
        except Exception as e:
            print(f"Error: {e}")


def send_data(message , IP):
    asyncio.run(main(message , IP))
    #await asyncio.run_coroutine_threadsafe(main(message, IP), asyncio.get_event_loop())


#send_data(1 , "ws://192.168.43.49:81")
