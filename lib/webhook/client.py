from aiohttp import web
import os
from lib.odoo.cache import invalidate_roles
import json

async def handle_roles_changed(request: web.Request):
    if request.headers.get("Authorization") != f"Bearer {os.getenv('WEBHOOK_SECRET')}":
        return web.Response(status=401)
    data = await request.json()
    invalidate_roles(data.get("guild_id")) 
    return web.Response(status=204)

async def ping(request: web.Request):
    if request.headers.get("Authorization") != f"Bearer {os.getenv('WEBHOOK_SECRET')}":
        return web.Response(status=401)
    body = json.dumps({'message': 'Pong, the connection is working!'})
    return web.Response(body=body, status=200)

async def start_webhook_server():
    app = web.Application()
    app.router.add_post("/odoo/roles-changed", handle_roles_changed)
    app.router.add_get("/ping", ping)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("WEBHOOK_PORT", 8080))).start()