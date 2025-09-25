import hid
import time
import struct

ANALOG_THRESHOLD = 1000  # for sticks (16-bit) or ~10 for triggers (0-255)
TRIGGER_THRESHOLD = 5

def decode_deck_buttons_and_sticks(data, last_analog=None):
    if len(data) < 16:
        return None

    data_bytes = bytes(data)

    # Analog sticks
    lx = struct.unpack_from("<h", data_bytes, 0)[0]
    ly = struct.unpack_from("<h", data_bytes, 2)[0]
    rx = struct.unpack_from("<h", data_bytes, 4)[0]
    ry = struct.unpack_from("<h", data_bytes, 6)[0]

    # Example analog triggers (if reported separately, e.g., data[12] and data[13])
    lt = data_bytes[12]  # L2
    rt = data_bytes[13]  # R2

    # Buttons
    buttons_triggers = data_bytes[8]
    buttons_dpad = data_bytes[9]
    buttons_abxy = data_bytes[10]
    buttons_alt = data_bytes[11]

    analog_changed = False
    sticks = {"lx": lx, "ly": ly, "rx": rx, "ry": ry, "lt": lt, "rt": rt}

    if last_analog:
        for key in sticks:
            if abs(sticks[key] - last_analog[key]) > (ANALOG_THRESHOLD if key in ["lx","ly","rx","ry"] else TRIGGER_THRESHOLD):
                analog_changed = True
                break
    else:
        analog_changed = True  # first read

    return {
        "sticks": sticks if analog_changed else None,  # only show if moved
        "raw_bytes": (buttons_triggers, buttons_dpad, buttons_abxy, buttons_alt),
        "triggers": buttons_triggers,
        "dpad": buttons_dpad,
        "abxy": buttons_abxy,
        "alt": buttons_alt,
        "analog_changed": analog_changed
    }

# --- Device setup ---
devices = hid.enumerate(0x28DE, 0x1205)
if not devices:
    print("No Steam Deck devices found")
else:
    print("Devices:", [f"Interface {d['interface_number']}" for d in devices])
    h = hid.device()
    for device in devices:
        if device['interface_number'] == 2:
            h.open_path(device['path'])
            print(f"Connected to interface {device['interface_number']}")
            break
    else:
        raise Exception("No suitable interface found")

    h.set_nonblocking(True)
    print("\n🎮 Button + Stick Test (analog only prints when moved)\n")

    last_decoded = None
    last_analog = None
    try:
        for _ in range(5000):
            data = h.read(64, timeout_ms=200)
            if data:
                decoded = decode_deck_buttons_and_sticks(data, last_analog)
                if decoded:
                    # Print buttons if changed
                    if not last_decoded or decoded['raw_bytes'] != last_decoded['raw_bytes']:
                        print(f"Buttons: Triggers {decoded['triggers']:02X}, DPad {decoded['dpad']:02X}, "
                              f"ABXY {decoded['abxy']:02X}, Alt {decoded['alt']:02X}")
                    # Print analog sticks if moved
                    if decoded['sticks']:
                        print(f"Analog: {decoded['sticks']}")
                        last_analog = decoded['sticks']

                    last_decoded = decoded
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        h.close()
        print("Device closed")
