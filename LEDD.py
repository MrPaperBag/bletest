import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bleak import BleakClient

MAC = "41:42:AB:CD:01:52"
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

CMD_ON  = bytes.fromhex("7BFF0401FFFFFFFFBF")
CMD_OFF = bytes.fromhex("7BFF0400FFFFFFFFBF")

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

async def send_ble(payload: bytes):
    async with BleakClient(MAC) as client:
        await client.write_gatt_char(CHAR_UUID, payload, response=False)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/on")
async def led_on():
    await send_ble(CMD_ON)
    return {"status": "LED ON"}

@app.get("/off")
async def led_off():
    await send_ble(CMD_OFF)
    return {"status": "LED OFF"}
