import hid
import time

def decode_deck_report(data):
       if len(data) < 64:
           print(f"Invalid report length: {len(data)}")
           return None
       # Buttons
       buttons_triggers = data[8]   # L1, L2, R1, R2
       buttons_dpad = data[9]       # D-Pad
       buttons_abxy = data[10]      # A, B, X, Y
       buttons_alt = data[11]       # Additional buttons
       pressed = []
       if buttons_triggers & 0x01: pressed.append("R2")  # Was A
       if buttons_triggers & 0x02: pressed.append("L2")  # Was B
       if buttons_triggers & 0x04: pressed.append("R1")  # Was X
       if buttons_triggers & 0x08: pressed.append("L1")  # Was Y
       if buttons_dpad & 0x01: pressed.append("DPad-Up")
       if buttons_dpad & 0x02: pressed.append("DPad-Right")   # Remapped
       if buttons_dpad & 0x04: pressed.append("DPad-Left")   # Remapped
       if buttons_dpad & 0x08: pressed.append("DPad-Down")  # Remapped
       if buttons_abxy & 0x01: pressed.append("A")
       if buttons_abxy & 0x02: pressed.append("B")
       if buttons_abxy & 0x04: pressed.append("X")
       if buttons_abxy & 0x08: pressed.append("Y")
       if buttons_alt != 0: pressed.append(f"Alt-{buttons_alt:02x}")
       # Sticks
       lx = (data[13] << 8) | data[12]
       ly = (data[15] << 8) | data[14]
       rx = (data[19] << 8) | data[18]
       ry = (data[21] << 8) | data[20]
       lx_norm = (lx - 32768) / 32768 if lx != 0 else 0.0
       ly_norm = (ly - 32768) / 32768 if ly != 0 else 0.0
       rx_norm = (rx - 32768) / 32768 if rx != 0 else 0.0
       ry_norm = (ry - 32768) / 32768 if ry != 0 else 0.0
       # Triggers
       lt = data[26] | (data[27] << 8)  # L2
       rt = data[24] | (data[25] << 8)  # R2
       lt = lt >> 8 if lt > 255 else lt
       rt = rt >> 8 if rt > 255 else rt
       return {
           "buttons": pressed,
           "left_stick": (round(lx_norm, 2), round(ly_norm, 2)),
           "right_stick": (round(rx_norm, 2), round(ry_norm, 2)),
           "left_trigger": lt,
           "right_trigger": rt,
           "raw_sticks": (lx, ly, rx, ry),
           "raw_triggers": (data[22] | (data[23] << 8), data[24] | (data[25] << 8), data[26] | (data[27] << 8)),
           "raw_buttons": (buttons_triggers, buttons_dpad, buttons_abxy, buttons_alt)
       }

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

           # Disable lizard mode
           try:
               h.send_feature_report([0x87, 0x00])
               h.send_feature_report([0x81, 0x00])
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
           print("Connected. Test one input at a time (A, B, X, Y, D-Pad Up/Down/Left/Right, L1, R1, left stick up/down/left/right, right stick up/down/left/right, L2, R2). Press normally and hard.")
           last_report = None
           for _ in range(5000):
               try:
                   h.send_feature_report([0x87, 0x00])
                   h.send_feature_report([0x81, 0x00])
               except:
                   pass
               try:
                   data = h.read(64, timeout_ms=200)  # Increased timeout
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