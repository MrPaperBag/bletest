import asyncio
from bleak import BleakClient

# Replace with your LED strip MAC address
MAC = "41:42:AB:CD:01:52"

# FFE1 characteristic
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Commands
CMD_ON  = bytes.fromhex("7BFF0401FFFFFFFFBF")
CMD_OFF = bytes.fromhex("7BFF0400FFFFFFFFBF")

async def main():
    print(f"🔌 Connecting to {MAC}...")
    async with BleakClient(MAC) as client:
        if await client.is_connected():
            print("✅ Connected!")

            # Turn ON LED
            print("💡 Sending ON command...")
            await client.write_gatt_char(CHAR_UUID, CMD_ON, response=False)

            # Wait 2 seconds
            await asyncio.sleep(2)

            # Turn OFF LED
            print("🌑 Sending OFF command...")
            await client.write_gatt_char(CHAR_UUID, CMD_OFF, response=False)

            print("🏁 Test finished!")

        else:
            print("❌ Failed to connect.")

asyncio.run(main())
