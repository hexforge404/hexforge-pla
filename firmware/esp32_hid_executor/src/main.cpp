// ESP32-S2/S3 HID executor with CDC JSON protocol, bounds enforcement, and heartbeat.

#include <Arduino.h>
#include <Adafruit_TinyUSB.h>
#include <ArduinoJson.h>

// Hardware config
constexpr int ARM_PIN = 5;           // configurable; INPUT_PULLUP expected
constexpr bool ARM_ACTIVE_STATE = HIGH;
constexpr uint16_t MIN_ACTION_DELAY_MS = 100;  // contract const
constexpr size_t MAX_TEXT = 1024;              // contract const
constexpr uint32_t HEARTBEAT_MS = 1000;
constexpr char DEVICE_ID[] = "esp32-hid";

Adafruit_USBD_HID usb_hid;

static bool armed = false;
static unsigned long last_action_ms = 0;
static unsigned long last_hb = 0;

uint8_t const desc_hid[] = {
    TUD_HID_REPORT_DESC_KEYBOARD(HID_REPORT_ID(1)),
    TUD_HID_REPORT_DESC_MOUSE(HID_REPORT_ID(2)),
};

void setup_usb() {
  usb_hid.setPollInterval(2);
  usb_hid.setReportDescriptor(desc_hid, sizeof(desc_hid));
  usb_hid.begin();
}

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
  serializeJson(doc, Serial);
  Serial.println();
}

void send_err(const char *msg) {
  StaticJsonDocument<128> doc;
  doc["type"] = "err";
  doc["message"] = msg;
  serializeJson(doc, Serial);
  Serial.println();
}

void send_status() {
  StaticJsonDocument<192> doc;
  doc["event_type"] = "device_status";
  doc["device_id"] = DEVICE_ID;
  doc["mode"] = armed ? "EXECUTE" : "SUGGEST";
  doc["led_state"] = armed;
  doc["kill_switch_state"] = physical_ok();
  doc["ts"] = (uint32_t)(millis() / 1000);
  serializeJson(doc, Serial);
  Serial.println();
}

bool enforce_action_bounds(const JsonVariantConst &payload, const String &type) {
  if (type == "TYPE_TEXT") {
    auto text = payload["text"].as<const char *>();
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

uint8_t mod_from_key(const char *k) {
  if (strcmp(k, "CTRL") == 0) return KEYBOARD_MODIFIER_LEFTCTRL;
  if (strcmp(k, "ALT") == 0) return KEYBOARD_MODIFIER_LEFTALT;
  if (strcmp(k, "SHIFT") == 0) return KEYBOARD_MODIFIER_LEFTSHIFT;
  return 0;
}

uint8_t keycode_from_key(const char *k) {
  if (strcmp(k, "ENTER") == 0) return HID_KEY_ENTER;
  if (strcmp(k, "ESC") == 0) return HID_KEY_ESCAPE;
  if (strcmp(k, "UP") == 0) return HID_KEY_ARROW_UP;
  if (strcmp(k, "DOWN") == 0) return HID_KEY_ARROW_DOWN;
  if (strcmp(k, "LEFT") == 0) return HID_KEY_ARROW_LEFT;
  if (strcmp(k, "RIGHT") == 0) return HID_KEY_ARROW_RIGHT;
  return 0;
}

void perform_action(const String &type, const JsonVariantConst &payload) {
  if (type == "TYPE_TEXT") {
    const char *text = payload["text"] | "";
    if (!text || strlen(text) == 0) return;
    for (const char *p = text; *p; ++p) {
      usb_hid.keyboardReport(1, 0, (uint8_t[]){(uint8_t)*p});
      delay(5);
      usb_hid.keyboardRelease(1);
      delay(5);
    }
    return;
  }

  if (type == "KEY_COMBO") {
    uint8_t mods = 0;
    uint8_t keys[6] = {0};
    uint8_t ki = 0;
    for (JsonVariantConst k : payload["keys"].as<JsonArrayConst>()) {
      const char *ks = k.as<const char *>();
      if (!ks) continue;
      uint8_t mod = mod_from_key(ks);
      if (mod) {
        mods |= mod;
        continue;
      }
      uint8_t code = keycode_from_key(ks);
      if (code && ki < 6) {
        keys[ki++] = code;
      }
    }
    usb_hid.keyboardReport(1, mods, keys);
    delay(10);
    usb_hid.keyboardRelease(1);
    return;
  }

  if (type == "MOUSE_MOVE") {
    int x = payload["x"] | 0;
    int y = payload["y"] | 0;
    usb_hid.mouseMove(2, x, y, 0, 0);
    return;
  }

  if (type == "MOUSE_CLICK") {
    const char *btn = payload["button"] | "left";
    uint8_t mask = MOUSE_BUTTON_LEFT;
    if (strcmp(btn, "right") == 0) mask = MOUSE_BUTTON_RIGHT;
    else if (strcmp(btn, "middle") == 0) mask = MOUSE_BUTTON_MIDDLE;
    usb_hid.mouseButtonPress(2, mask);
    delay(10);
    usb_hid.mouseButtonRelease(2);
    return;
  }
}

void setup() {
  pinMode(ARM_PIN, INPUT_PULLUP);
  Serial.begin(115200);
  delay(200);
  setup_usb();
  Serial.println(F("esp32_hid_executor ready"));
}

void loop() {
  unsigned long now = millis();
  if (now - last_hb > HEARTBEAT_MS) {
    last_hb = now;
    send_status();
  }

  if (!Serial.available()) {
    delay(5);
    return;
  }

  String line = Serial.readStringUntil('\n');
  if (line.length() == 0) return;

  StaticJsonDocument<768> doc;
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
