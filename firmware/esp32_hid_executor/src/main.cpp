// ESP32-S2/S3 PLA HID executor bring-up firmware.
// Native ESP32 Arduino USB HID path. No Adafruit TinyUSB dependency.

#include <Arduino.h>
#include <ArduinoJson.h>
#include "USB.h"
#include "USBCDC.h"
#include "USBHIDKeyboard.h"
#include "USBHIDMouse.h"


// Hardware config
constexpr int ARM_PIN = 5;                  // INPUT_PULLUP expected
constexpr bool ARM_ACTIVE_STATE = LOW;     // adjust after physical wiring test
constexpr uint16_t MIN_ACTION_DELAY_MS = 100;
constexpr size_t MAX_TEXT = 1024;
constexpr uint32_t HEARTBEAT_MS = 1000;
constexpr char DEVICE_ID[] = "esp32-hid";

USBHIDKeyboard Keyboard;
USBHIDMouse Mouse;
USBCDC ControlSerial;

static bool armed = false;
static unsigned long last_action_ms = 0;
static unsigned long last_hb = 0;

bool physical_ok() {
  return digitalRead(ARM_PIN) == ARM_ACTIVE_STATE;
}

bool rate_limited() {
  unsigned long now = millis();
  if (now - last_action_ms < MIN_ACTION_DELAY_MS) {
    return true;
  }
  last_action_ms = now;
  return false;
}

void send_ack(const String &exec_id) {
  StaticJsonDocument<128> doc;
  doc["type"] = "ack";
  doc["execution_id"] = exec_id;
  doc["ok"] = true;
  serializeJson(doc, ControlSerial);
  ControlSerial.println();
}

void send_err(const char *msg) {
  StaticJsonDocument<128> doc;
  doc["type"] = "err";
  doc["message"] = msg;
  serializeJson(doc, ControlSerial);
  ControlSerial.println();
}

void send_status() {
  StaticJsonDocument<192> doc;
  doc["event_type"] = "device_status";
  doc["device_id"] = DEVICE_ID;
  doc["mode"] = armed ? "EXECUTE" : "SUGGEST";
  doc["led_state"] = armed;
  doc["kill_switch_state"] = physical_ok() ? "ARMED" : "DISABLED";
  doc["uptime_seconds"] = (uint32_t)(millis() / 1000);
  serializeJson(doc, ControlSerial);
  ControlSerial.println();
}

bool enforce_action_bounds(const JsonVariantConst &payload, const String &type) {
  if (type == "TYPE_TEXT") {
    const char *text = payload["text"].as<const char *>();
    if (!text) return false;
    return strlen(text) <= MAX_TEXT;
  }

  if (type == "KEY_COMBO") {
    if (!payload["keys"].is<JsonArrayConst>()) return false;
    JsonArrayConst keys = payload["keys"].as<JsonArrayConst>();
    size_t count = 0;
    for (auto k : keys) {
      if (!k.is<const char *>()) return false;
      ++count;
    }
    return count >= 1 && count <= 5;
  }

  if (type == "MOUSE_MOVE") {
    if (!payload["x"].is<int>() || !payload["y"].is<int>()) return false;
    int x = payload["x"].as<int>();
    int y = payload["y"].as<int>();
    return x >= -1000 && x <= 5000 && y >= -1000 && y <= 5000;
  }

  if (type == "MOUSE_CLICK") {
    const char *btn = payload["button"].as<const char *>();
    if (!btn) return false;
    return strcmp(btn, "left") == 0 || strcmp(btn, "right") == 0 || strcmp(btn, "middle") == 0;
  }

  return false;
}

uint8_t keycode_from_key(const char *k) {
  if (strcmp(k, "ENTER") == 0) return KEY_RETURN;
  if (strcmp(k, "ESC") == 0) return KEY_ESC;
  if (strcmp(k, "UP") == 0) return KEY_UP_ARROW;
  if (strcmp(k, "DOWN") == 0) return KEY_DOWN_ARROW;
  if (strcmp(k, "LEFT") == 0) return KEY_LEFT_ARROW;
  if (strcmp(k, "RIGHT") == 0) return KEY_RIGHT_ARROW;
  if (strcmp(k, "TAB") == 0) return KEY_TAB;
  if (strcmp(k, "BACKSPACE") == 0) return KEY_BACKSPACE;
  if (strcmp(k, "DELETE") == 0) return KEY_DELETE;
  return 0;
}

void perform_action(const String &type, const JsonVariantConst &payload) {
  if (type == "TYPE_TEXT") {
    const char *text = payload["text"] | "";
    if (!text || strlen(text) == 0) return;
    Keyboard.print(text);
    return;
  }

  if (type == "KEY_COMBO") {
    JsonArrayConst keys = payload["keys"].as<JsonArrayConst>();

    for (JsonVariantConst k : keys) {
      const char *ks = k.as<const char *>();
      if (!ks) continue;

      if (strcmp(ks, "CTRL") == 0) Keyboard.press(KEY_LEFT_CTRL);
      else if (strcmp(ks, "ALT") == 0) Keyboard.press(KEY_LEFT_ALT);
      else if (strcmp(ks, "SHIFT") == 0) Keyboard.press(KEY_LEFT_SHIFT);
      else {
        uint8_t code = keycode_from_key(ks);
        if (code) Keyboard.press(code);
      }
      delay(5);
    }

    delay(20);
    Keyboard.releaseAll();
    return;
  }

  if (type == "MOUSE_MOVE") {
    int x = payload["x"] | 0;
    int y = payload["y"] | 0;

    // Native mouse movement is relative. Send in chunks.
    while (x != 0 || y != 0) {
      int step_x = constrain(x, -127, 127);
      int step_y = constrain(y, -127, 127);
      Mouse.move(step_x, step_y);
      x -= step_x;
      y -= step_y;
      delay(5);
    }
    return;
  }

  if (type == "MOUSE_CLICK") {
    const char *btn = payload["button"] | "left";
    if (strcmp(btn, "right") == 0) Mouse.click(MOUSE_RIGHT);
    else if (strcmp(btn, "middle") == 0) Mouse.click(MOUSE_MIDDLE);
    else Mouse.click(MOUSE_LEFT);
    return;
  }
}

void setup() {
  pinMode(ARM_PIN, INPUT_PULLUP);

  ControlSerial.begin(115200);
  Keyboard.begin();
  Mouse.begin();
  USB.begin();

  delay(500);
  ControlSerial.println("esp32_hid_executor native-usb ready");
}

void loop() {
  unsigned long now = millis();

  if (now - last_hb > HEARTBEAT_MS) {
    last_hb = now;
    send_status();
  }

  if (!ControlSerial.available()) {
    delay(5);
    return;
  }

  String line = ControlSerial.readStringUntil('\n');
  if (line.length() == 0) return;

  StaticJsonDocument<1024> doc;
  auto err = deserializeJson(doc, line);
  if (err) {
    send_err("invalid_json");
    return;
  }

  const char *msg_type = doc["type"] | "";

  if (strcmp(msg_type, "arm") == 0) {
    bool enable = doc["enabled"] | false;
    bool phys = physical_ok();

    if (enable && !phys) {
      armed = false;
      send_err("physical_arm_off");
      return;
    }

    armed = enable && phys;
    send_status();
    return;
  }

  if (!armed) {
    send_err("not_armed");
    return;
  }

  if (rate_limited()) {
    send_err("rate_limited");
    return;
  }

  const char *mode = doc["mode"] | "";
  if (strcmp(mode, "EXECUTE") != 0) {
    send_err("mode_not_execute");
    return;
  }

  const char *action_type = doc["action_type"] | "";
  JsonVariantConst payload = doc["payload"];
  const char *exec_id = doc["execution_id"] | "";

  if (!action_type || !payload || strlen(exec_id) == 0) {
    send_err("invalid_message");
    return;
  }

  if (!enforce_action_bounds(payload, action_type)) {
    send_err("bounds_rejected");
    return;
  }

  perform_action(action_type, payload);
  send_ack(exec_id);
}
