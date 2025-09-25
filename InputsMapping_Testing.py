import hid
import time

def decode_deck_report(data):
    # data is a bytes object from the HID device
    buttons_triggers = data[8]
    buttons_dpad = data[9]

    pressed = []

    # --- Triggers + bumpers ---
    if buttons_triggers & 0x01: pressed.append("R2")
    if buttons_triggers & 0x02: pressed.append("L2")
    if buttons_triggers & 0x04: pressed.append("R1")
    if buttons_triggers & 0x08: pressed.append("L1")

    # --- Face buttons ---
    if buttons_triggers & 0x10: pressed.append("Y")
    if buttons_triggers & 0x20: pressed.append("B")
    if buttons_triggers & 0x40: pressed.append("X")
    if buttons_triggers & 0x80: pressed.append("A")

    # --- DPad ---
    if buttons_dpad & 0x01: pressed.append("DPad Up")
    if buttons_dpad & 0x02: pressed.append("DPad Right")
    if buttons_dpad & 0x04: pressed.append("DPad Left")
    if buttons_dpad & 0x08: pressed.append("DPad Down")

    return pressed
   

devices = hid.enumerate(0x28DE, 0x1205)
if not devices:
    print("No Steam Deck devices found")
else:
    print("Devices:", [f"Interface {d['interface_number']}: {d['path'].decode()}" for d in devices])
    h = hid.device()
    try:
        # Try MI_02 first
        for device in devices:
            if device['interface_number'] == 2:
                try:
                    h.open_path(device['path'])
                    print(f"Connected to interface {device['interface_number']}")
                    break
                except Exception as e:
                    print(f"Failed to open interface {device['interface_number']}: {e}")
                    continue
        else:
            print("Could not connect to MI_02, trying MI_01")
            for device in devices:
                if device['interface_number'] == 1:
                    try:
                        h.open_path(device['path'])
                        print(f"Connected to interface {device['interface_number']}")
                        break
                    except Exception as e:
                        print(f"Failed to open interface {device['interface_number']}: {e}")
                        continue
            else:
                raise Exception("No suitable interface found")

        # Disable lizard mode (stronger attempt)
        try:
            h.send_feature_report([0x87, 0x00])
            h.send_feature_report([0x81, 0x00])
            h.send_feature_report([0x8e, 0x00])  # Additional disable
            print("Sent feature reports to disable lizard mode")
        except Exception as e:
            print("Failed to send feature reports:", e)

        # Request gamepad report
        try:
            h.write_report(0, [0x01, 0x00] + [0] * 62)
            print("Sent report request for ID 1")
        except Exception as e:
            print("Failed to send report request:", e)

        h.set_nonblocking(True)
        print("Connected. Test one input at a time (A, B, X, Y, D-Pad Up/Down/Left/Right, L1, R1, left stick up/down/left/right, right stick up/down/left/right, L2, R2, right touchpad left-click, left touchpad middle-click/scroll, Quick Access button). Press normally and hard.")
        last_report = None
        for _ in range(5000):
            try:
                h.send_feature_report([0x87, 0x00])
                h.send_feature_report([0x81, 0x00])
                h.send_feature_report([0x8e, 0x00])
            except:
                pass
            try:
                data = h.read(64, timeout_ms=400)  # Increased timeout
                if data:
                    decoded = decode_deck_report(data)
                    if decoded and decoded != last_report:
                        print(f"Raw (interface {device['interface_number']}): {data}")
                        print(f"Decoded (interface {device['interface_number']}): {decoded}")
                        last_report = decoded
                else:
                    print("No data read")
            except Exception as e:
                print(f"Read error: {e}")
            time.sleep(0.01)
    except Exception as e:
        print("Error:", e)
    finally:
        h.close()
        print("Device closed")