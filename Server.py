import socket
import json
import time
from enum import Enum
import vgamepad as vg
from vgamepad import XUSB_BUTTON

# https://wut.devkitpro.org/group__vpad__input.html
class VPADButtons(Enum):
    VPAD_BUTTON_A = 0x8000
    VPAD_BUTTON_B = 0x4000
    VPAD_BUTTON_X = 0x2000
    VPAD_BUTTON_Y = 0x1000
    VPAD_BUTTON_LEFT = 0x0800
    VPAD_BUTTON_RIGHT = 0x0400
    VPAD_BUTTON_UP = 0x0200
    VPAD_BUTTON_DOWN = 0x0100
    VPAD_BUTTON_ZL = 0x0080
    VPAD_BUTTON_ZR = 0x0040
    VPAD_BUTTON_L = 0x0020
    VPAD_BUTTON_R = 0x0010
    VPAD_BUTTON_PLUS = 0x0008
    VPAD_BUTTON_MINUS = 0x0004
    VPAD_BUTTON_HOME = 0x0002
    VPAD_BUTTON_SYNC = 0x0001
    VPAD_BUTTON_STICK_R = 0x00020000
    VPAD_BUTTON_STICK_L = 0x00040000
    VPAD_BUTTON_TV = 0x00010000
    VPAD_STICK_R_EMULATION_LEFT = 0x04000000
    VPAD_STICK_R_EMULATION_RIGHT = 0x02000000
    VPAD_STICK_R_EMULATION_UP = 0x01000000
    VPAD_STICK_R_EMULATION_DOWN = 0x00800000
    VPAD_STICK_L_EMULATION_LEFT = 0x40000000
    VPAD_STICK_L_EMULATION_RIGHT = 0x20000000
    VPAD_STICK_L_EMULATION_UP = 0x10000000
    VPAD_STICK_L_EMULATION_DOWN = 0x08000000
    
VPADMappingToXbox = {
    VPADButtons.VPAD_BUTTON_A: XUSB_BUTTON.XUSB_GAMEPAD_A,
    VPADButtons.VPAD_BUTTON_B: XUSB_BUTTON.XUSB_GAMEPAD_B,
    VPADButtons.VPAD_BUTTON_X: XUSB_BUTTON.XUSB_GAMEPAD_X,
    VPADButtons.VPAD_BUTTON_Y: XUSB_BUTTON.XUSB_GAMEPAD_Y,
    VPADButtons.VPAD_BUTTON_LEFT: XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    VPADButtons.VPAD_BUTTON_RIGHT: XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    VPADButtons.VPAD_BUTTON_UP: XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    VPADButtons.VPAD_BUTTON_DOWN: XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    VPADButtons.VPAD_BUTTON_L: XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    VPADButtons.VPAD_BUTTON_R: XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    VPADButtons.VPAD_BUTTON_PLUS: XUSB_BUTTON.XUSB_GAMEPAD_START,
    VPADButtons.VPAD_BUTTON_MINUS: XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    VPADButtons.VPAD_BUTTON_STICK_L: XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    VPADButtons.VPAD_BUTTON_STICK_R: XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    VPADButtons.VPAD_BUTTON_HOME: XUSB_BUTTON.XUSB_GAMEPAD_GUIDE
}

PORT = 4242
TIMEOUT = 5 

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    finally:
        s.close()
    return ip_address


print("\nMiiSendU Server -- by Trock and Slushi\n")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (get_local_ip(), PORT)
print('starting server on {} port {}'.format(*server_address))
sock.bind(server_address)

clients = {}

print("\nWaiting for clients...")

while True:
    try:
        sock.settimeout(1)
        try:
            data, address = sock.recvfrom(4096)
            current_time = time.time()
            if address not in clients:
                gamepad = vg.VX360Gamepad()
                clients[address] = {"gamepad": gamepad, "lastButtons": [], "last_time": current_time}
                print("Client {} connected".format(address))
            else:
                clients[address]["last_time"] = current_time

            gamepad = clients[address]["gamepad"]
            decodedData = json.loads(data)
            vpad = decodedData["wiiUGamePad"]

            gamepad.left_joystick_float(x_value_float=vpad["lStickX"], y_value_float=vpad["lStickY"])
            gamepad.right_joystick_float(x_value_float=vpad["rStickX"], y_value_float=vpad["rStickY"])

            gamepad.left_trigger_float(1 if vpad["hold"] & VPADButtons.VPAD_BUTTON_ZL.value else 0)
            gamepad.right_trigger_float(1 if vpad["hold"] & VPADButtons.VPAD_BUTTON_ZR.value else 0)

            for vpadButton, xboxButton in VPADMappingToXbox.items():
                if vpad["hold"] & vpadButton.value:
                    if xboxButton not in clients[address]["lastButtons"]:
                        gamepad.press_button(xboxButton)
                        clients[address]["lastButtons"].append(xboxButton)
                else:
                    if xboxButton in clients[address]["lastButtons"]:
                        gamepad.release_button(xboxButton)
                        clients[address]["lastButtons"].remove(xboxButton)

            gamepad.update()

        except socket.timeout:
            pass

        current_time = time.time()
        disconnected_clients = [addr for addr, client in clients.items() if current_time - client["last_time"] > TIMEOUT]
        for addr in disconnected_clients:
            print(f"Client {addr} disconnected due to timeout.")
            time.sleep(1)
            print("Finishing program...")
            exit(1)

    except KeyboardInterrupt:
        print("Finished program!")
        sock.close()
        break