bl_info = {
    "name": "AI_GET",
    "author": "tranminhhuydn@gmail.com",
    "version": (1, 0),
    "blender": (5, 1, 0), # Thay đổi theo phiên bản Blender của bạn (ví dụ: 3, 6, 0)
    "location": "View3D > Sidebar > AI_GET",
    "description": "Điều khiển Blender bằng câu lệnh tự nhiên thông qua Gemini or ChatGPT",
    "category": "Development",
}

import bpy
import asyncio
import threading
import queue
import json
# import websockets
from . import websockets
import re
import traceback

# =====================================================
# GLOBAL
# =====================================================

message_queue = queue.Queue()
error_queue = queue.Queue()

server = None
loop = None
server_thread = None
server_running = False


# =====================================================
# ERROR
# =====================================================

def report_error(msg):
    error_queue.put(str(msg))


# =====================================================
# MESSAGE HANDLER
# =====================================================

async def handler(ws):

    async for msg in ws:
        print("WS:", msg)
        message_queue.put(msg)


# =====================================================
# SERVER THREAD
# =====================================================

def start_server_loop():

    global loop
    global server
    global server_running

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run_server():

        global server

        server = await websockets.serve(
            handler,
            "127.0.0.1",
            8765
        )

        print("🚀 WS STARTED")

        while server_running:
            await asyncio.sleep(0.2)

        print("🛑 WS SHUTDOWN")

        server.close()
        await server.wait_closed()

    try:
        loop.run_until_complete(run_server())

    except Exception:
        traceback.print_exc()

    finally:

        pending = asyncio.all_tasks(loop)

        for task in pending:
            task.cancel()

        if pending:
            try:
                loop.run_until_complete(
                    asyncio.gather(
                        *pending,
                        return_exceptions=True
                    )
                )
            except:
                pass

        loop.close()

        print("✅ LOOP CLOSED")


# =====================================================
# CODE EXTRACT
# =====================================================

def extract_code(text):

    if not text:
        return ""

    m = re.search(
        r"```python([\s\S]*?)```",
        text
    )

    if m:
        return m.group(1).strip()

    m = re.search(
        r"(import bpy[\s\S]*)",
        text
    )

    return m.group(1).strip() if m else ""


# =====================================================
# EXECUTE
# =====================================================

def execute_code(code):

    try:

        global_namespace = {
            "__name__": "__main__"
        }

        exec(code, global_namespace)

    except Exception as e:

        traceback.print_exc()

        report_error(
            f"{type(e).__name__}: {e}"
        )


# =====================================================
# TIMER
# =====================================================

def process_queue():

    while not error_queue.empty():

        msg = error_queue.get()

        def draw(self, context):
            self.layout.label(text=msg)

        bpy.context.window_manager.popup_menu(
            draw,
            title="ERROR",
            icon='ERROR'
        )

    while not message_queue.empty():

        raw = message_queue.get()

        try:

            data = json.loads(raw)

            if isinstance(data, dict):
                text = data.get("text", "")
            else:
                text = str(data)

        except:
            text = raw

        code = extract_code(text)

        if not code:
            continue

        print("▶ EXEC")

        execute_code(code)

    return 0.1


def register_timer():

    if not bpy.app.timers.is_registered(
        process_queue
    ):
        bpy.app.timers.register(
            process_queue,
            first_interval=0.1,
            persistent=True
        )


def unregister_timer():

    try:
        if bpy.app.timers.is_registered(
            process_queue
        ):
            bpy.app.timers.unregister(
                process_queue
            )
    except:
        pass


# =====================================================
# START
# =====================================================

class GPT_OT_Start(bpy.types.Operator):

    bl_idname = "gpt.start"
    bl_label = "Start"

    def execute(self, context):

        global server_running
        global server_thread

        if server_running:

            self.report(
                {'INFO'},
                "Already running"
            )

            return {'FINISHED'}

        server_running = True

        register_timer()

        server_thread = threading.Thread(
            target=start_server_loop,
            daemon=True
        )

        server_thread.start()

        print("✅ STARTED")

        return {'FINISHED'}


# =====================================================
# STOP
# =====================================================

class GPT_OT_Stop(bpy.types.Operator):

    bl_idname = "gpt.stop"
    bl_label = "Stop"

    def execute(self, context):

        global server_running
        global server_thread

        if not server_running:
            return {'FINISHED'}

        print("🛑 STOPPING")

        server_running = False

        if server_thread:

            server_thread.join(timeout=3)

            server_thread = None

        unregister_timer()

        print("✅ STOPPED")

        return {'FINISHED'}


# =====================================================
# UI
# =====================================================

class GPT_PT_Panel(bpy.types.Panel):

    bl_label = "AI_GET"
    bl_idname = "GPT_PT_PANEL"

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AI_GET'

    def draw(self, context):

        layout = self.layout

        layout.operator(
            "gpt.start",
            icon='PLAY'
        )

        layout.operator(
            "gpt.stop",
            icon='CANCEL'
        )

        layout.label(
            text=f"Port: 8765"
        )
        layout.label(
            text=f"Running: {server_running}"
        )

# =====================================================
# REGISTER
# =====================================================

classes = (
    GPT_OT_Start,
    GPT_OT_Stop,
    GPT_PT_Panel,
)

def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    global server_running

    server_running = False

    unregister_timer()

    for cls in reversed(classes):

        try:
            bpy.utils.unregister_class(cls)
        except:
            pass

if __name__ == "__main__":
    # unregister()
    register()