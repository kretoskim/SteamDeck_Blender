# Serial test for COM6 — paste & Run in Blender Text Editor
bl_info = {"name":"SteamDeck Serial Test"}

import bpy, threading, queue, time
try:
    import serial
except Exception as e:
    print("serial import failed:", e)
    raise

PORT = "COM6"     # change if your COM port differs
BAUDS = [115200, 57600, 38400, 19200, 9600]

SER = None
for b in BAUDS:
    try:
        SER = serial.Serial(PORT, b, timeout=0.1)
        print(f"Opened {PORT} @ {b}")
        break
    except Exception as e:
        print(f"Failed {PORT} @ {b}: {e}")
if SER is None:
    raise RuntimeError("Could not open serial port. Check COM number and VirtualHere settings.")

Q = queue.Queue()
STOP_EV = threading.Event()

def reader():
    while not STOP_EV.is_set():
        try:
            data = SER.readline()
            if data:
                Q.put(data)
        except Exception as e:
            Q.put(b"ERR:" + str(e).encode("utf-8"))
            time.sleep(0.2)

t = threading.Thread(target=reader, daemon=True)
t.start()

class SERIAL_OT_modal(bpy.types.Operator):
    bl_idname = "wm.steamdeck_serial_modal"
    bl_label = "SteamDeck Serial Modal"

    _timer = None

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        print("Serial listener started (F3 -> Stop or use Cancel operator later)")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            while not Q.empty():
                line = Q.get()
                try:
                    # Print to the System Console so you can see raw bytes
                    print("SER:", line)
                except Exception:
                    print("SER (raw repr):", repr(line))
        return {'PASS_THROUGH'}

    def cancel(self, context):
        STOP_EV.set()
        try:
            SER.close()
        except Exception:
            pass
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        print("Serial listener stopped")

def register():
    bpy.utils.register_class(SERIAL_OT_modal)

def unregister():
    bpy.utils.unregister_class(SERIAL_OT_modal)

if __name__ == "__main__":
    register()
    # After running script, press F3 -> "SteamDeck Serial Modal" to start
