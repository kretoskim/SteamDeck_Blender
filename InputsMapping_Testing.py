import hid
import time
import struct

# --- Thresholds ---
ANALOG_THRESHOLD = 1000  # sticks (-32768..32767)
TRIGGER_THRESHOLD = 5    # triggers (0..255)

def decode_deck_report(data, last_analog=None):
    if len(data) < 16:
        return None

    data_bytes = bytes(data)

    # --- Analog sticks ---
    lx = struct.unpack_from("<h", data_bytes, 0)[0]
    ly = struct.unpack_from("<h", data_bytes, 2)[0]
    rx = struct.unpack_from("<h", data_bytes, 4)[0]
    ry = struct.unpack_from("<h", data_bytes, 6)[0]

    # --- Analog triggers (example, might need adjustment) ---
    lt = data_bytes[12]  # L2
    rt = data_bytes[13]  # R2

    analog_changed = False
    analog = {"lx": lx, "ly": ly, "rx": rx, "ry": ry, "lt": lt, "rt": rt}

    if last_analog:
        for key in analog:
            threshold = ANALOG_THRESHOLD if key in ["lx","ly","rx","ry"] else TRIGGER_THRESHOLD
            if abs(analog[key] - last_analog[key]) > threshold:
                analog_changed = True
                break
    else:
        analog_changed = True  # first read

    # --- Buttons ---
    buttons_triggers = data_bytes[8]
    buttons_dpad = data_bytes[9]

    pressed = []

    # Triggers + bumpers
    if buttons_triggers & 0x01: pressed.append("R2")
    if buttons_triggers & 0x02: pressed.append("L2")
    if buttons_triggers & 0x04: pressed.append("R1")
    if buttons_triggers & 0x08: pressed.append("L1")

    # Face buttons
    if buttons_triggers & 0x10: pressed.append("Y")
    if buttons_triggers & 0x20: pressed.append("B")
    if buttons_triggers & 0x40: pressed.append("X")
    if buttons_triggers & 0x80: pressed.append("A")

    # DPad
    if buttons_dpad & 0x01: pressed.append("DPad Up")
    if buttons_dpad & 0x02: pressed.append("DPad Right")
    if buttons_dpad & 0x04: pressed.append("DPad Left")
    if buttons_dpad & 0x08: pressed.append("DPad Down")

    return {
        "buttons": pressed,
        "analog": analog if analog_changed else None
    }

# --- Device setup ---
devices = hid.enumerate(0x28DE, 0x1205)
if not devices:
    print("No Steam Deck devices found")
    exit()

print("Devices:", [f"Interface {d['interface_number']}: {d['path'].decode()}" for d in devices])
h = hid.device()

# Connect to interface MI_02 first, then MI_01 if needed
for iface in [2, 1]:
    for device in devices:
        if device['interface_number'] == iface:
            try:
                h.open_path(device['path'])
                print(f"Connected to interface {iface}")
                break
            except Exception as e:
                print(f"Failed to open interface {iface}: {e}")
    else:
        continue
    break
else:
    raise Exception("No suitable interface found")

# Disable lizard mode (optional)
for report in [[0x87,0x00],[0x81,0x00],[0x8e,0x00]]:
    try: h.send_feature_report(report)
    except: pass

# Request gamepad report
try:
    h.write_report(0, [0x01,0x00] + [0]*62)
except: pass

h.set_nonblocking(True)
print("Test buttons and analog sticks. Analog only prints when moved.")

last_analog = None
last_buttons = None

try:
    for _ in range(5000):
        try:
            # Keep lizard mode disabled
            for report in [[0x87,0x00],[0x81,0x00],[0x8e,0x00]]:
                try: h.send_feature_report(report)
                except: pass
        except: pass

        try:
            data = h.read(64, timeout_ms=400)
            if data:
                decoded = decode_deck_report(data, last_analog)
                if decoded:
                    # Print buttons if changed
                    if decoded['buttons'] != last_buttons:
                        print(f"Buttons: {decoded['buttons']}")
                        last_buttons = decoded['buttons']

                    # Print analog only if moved
                    if decoded['analog']:
                        print(f"Analog: {decoded['analog']}")
                        last_analog = decoded['analog']
        except Exception as e:
            print(f"Read error: {e}")

        time.sleep(0.01)
finally:
    h.close()
    print("Device closed")
