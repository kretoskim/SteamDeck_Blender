import hid
import time

def decode_deck_buttons(data):
    if len(data) < 64:
        return None

    buttons_triggers = data[8]   # L1, L2, R1, R2
    buttons_dpad = data[9]       # D-Pad
    buttons_abxy = data[10]      # A, B, X, Y
    buttons_alt = data[11]       # Extra buttons

    return {
        "raw_bytes": (buttons_triggers, buttons_dpad, buttons_abxy, buttons_alt),
        "triggers": buttons_triggers,
        "dpad": buttons_dpad,
        "abxy": buttons_abxy,
        "alt": buttons_alt
    }

devices = hid.enumerate(0x28DE, 0x1205)
if not devices:
    print("No Steam Deck devices found")
else:
    print("Devices:", [f"Interface {d['interface_number']}" for d in devices])
    h = hid.device()

    for device in devices:
        if device['interface_number'] == 2:  # Try MI_02 first
            h.open_path(device['path'])
            print(f"Connected to interface {device['interface_number']}")
            break
    else:
        raise Exception("No suitable interface found")

    h.set_nonblocking(True)
    print("\n🎮 Button Map Test: Press one button at a time (A, B, X, Y, D-Pad, bumpers, triggers).")
    print("Watch which raw bytes change.\n")

    last = None
    try:
        for _ in range(5000):
            data = h.read(64, timeout_ms=200)
            if data:
                decoded = decode_deck_buttons(data)
                if decoded and decoded != last:
                    print(f"Raw Bytes: {decoded['raw_bytes']} | Triggers: {decoded['triggers']:02X}, "
                          f"DPad: {decoded['dpad']:02X}, ABXY: {decoded['abxy']:02X}, Alt: {decoded['alt']:02X}")
                    last = decoded
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        h.close()
        print("Device closed")
