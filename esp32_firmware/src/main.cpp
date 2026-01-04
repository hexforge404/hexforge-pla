#include <WiFi.h>
#include <HTTPClient.h>
#include <esp_wifi.h>
#include <cstring>
#include "secrets.h"

// Pins (D2 LED, D4 button)
#define PIN_BUTTON 4
#define PIN_LED 2

// Pin assignments
static constexpr int LED_PIN = 2;    // D2 LED to GND (active HIGH)
static constexpr int BUTTON_PIN = 4; // Button to GND with INPUT_PULLUP

static constexpr TickType_t BUTTON_POLL_MS = 20;
static constexpr uint32_t WIFI_RETRY_DELAY_MS = 750;
static constexpr uint8_t HEALTH_MAX_RETRIES = 10;
static constexpr uint32_t HTTP_TIMEOUT_MS = 5000;
static constexpr unsigned long BUTTON_DEBOUNCE_MS = 50;

static QueueHandle_t gButtonQueue = nullptr;
static bool gReady = false;
static int gLastDiscReason = WIFI_REASON_UNSPECIFIED;
static int gLastRawButton = HIGH;
static int gStableButton = HIGH;
static bool gLedState = false;
static unsigned long gLastButtonChangeMs = 0;

void onWiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
    // Capture disconnect reasons for post-mortem logging.
    if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
        gLastDiscReason = static_cast<int>(info.wifi_sta_disconnected.reason);
        Serial.print("[wifi] disconnect reason=");
        Serial.println(gLastDiscReason);
    }
}

// LED helpers (active high to GND)
inline void setLed(bool on) { digitalWrite(LED_PIN, on ? HIGH : LOW); }
inline void blinkOnce(uint16_t on_ms, uint16_t off_ms) {
    setLed(true);
    vTaskDelay(pdMS_TO_TICKS(on_ms));
    setLed(false);
    vTaskDelay(pdMS_TO_TICKS(off_ms));
}

void slowBlinkWhileConnecting() {
    setLed(true);
    vTaskDelay(pdMS_TO_TICKS(150));
    setLed(false);
    vTaskDelay(pdMS_TO_TICKS(850));
}

void quickFlashSuccess() { blinkOnce(80, 40); }

void tripleFlashFailure() {
    for (int i = 0; i < 3; ++i) {
        blinkOnce(120, 120);
    }
}

void logStatus(const char* msg) { Serial.println(msg); }

void handleButtonAndLed() {
    int raw = digitalRead(PIN_BUTTON);
    unsigned long now = millis();

    if (raw != gLastRawButton) {
        gLastRawButton = raw;
        gLastButtonChangeMs = now;
    }

    if ((now - gLastButtonChangeMs) >= BUTTON_DEBOUNCE_MS && raw != gStableButton) {
        gStableButton = raw;
        if (gStableButton == LOW) {
            Serial.println("[button] pressed");
            if (!gLedState) {
                gLedState = true;
                setLed(true);
                Serial.println("[led] ON");
            }
        } else {
            Serial.println("[button] released");
            if (gLedState) {
                gLedState = false;
                setLed(false);
                Serial.println("[led] OFF");
            }
        }
    }
}

bool ensureWiFiConnected() {
    if (WiFi.status() == WL_CONNECTED) {
        return true;
    }

    gLastDiscReason = WIFI_REASON_UNSPECIFIED;
    logStatus("[wifi] starting");
    WiFi.mode(WIFI_STA);
    WiFi.persistent(false);   // avoid writing creds repeatedly to flash
    WiFi.setAutoReconnect(true);
    WiFi.setSleep(false); // avoid router incompatibility when Wi-Fi sleep is enabled
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && (millis() - start) < 40000) {
        slowBlinkWhileConnecting();
        Serial.print(".");
    }

    if (WiFi.status() != WL_CONNECTED) {
        logStatus("[wifi] giving up after ~40s");
        Serial.print("[wifi] status=");
        Serial.print(WiFi.status());
        Serial.print(" reason=");
        Serial.println(static_cast<int>(gLastDiscReason));
        return false;
    }

    Serial.print("[wifi] connected, IP: ");
    Serial.println(WiFi.localIP());
    return true;
}

bool checkHealth() {
    HTTPClient http;
    http.setTimeout(HTTP_TIMEOUT_MS);
    http.setReuse(false);
    String url = String("http://") + PLA_HOST + ":" + PLA_PORT + "/health";
    http.begin(url);
    if (strlen(PLA_API_KEY) > 0) {
        http.addHeader("X-API-Key", PLA_API_KEY);
    }

    int code = http.GET();
    String body = http.getString();
    Serial.print("[health] status=");
    Serial.print(code);
    Serial.print(" body=");
    Serial.println(body);

    http.end();
    return code == 200;
}

bool postIngest() {
    HTTPClient http;
    http.setTimeout(HTTP_TIMEOUT_MS);
    http.setReuse(false);
    String url = String("http://") + PLA_HOST + ":" + PLA_PORT + PLA_INGEST_PATH;
    const char* deviceId = (PLA_DEVICE_ID[0] != '\0') ? PLA_DEVICE_ID : "esp32-hands-001";
    String payload = String("{") +
                     "\"event_version\":\"1.0\"," +
                     "\"device_id\":\"" + deviceId + "\"," +
                     "\"event_type\":\"button_press\"," +
                     "\"ts_ms\":" + String(millis()) + "}";

    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    if (strlen(PLA_API_KEY) > 0) {
        http.addHeader("X-API-Key", PLA_API_KEY);
    }

    int code = http.POST(payload);
    String body = http.getString();
    Serial.print("[ingest] status=");
    Serial.print(code);
    Serial.print(" body=");
    Serial.println(body);

    http.end();
    return code >= 200 && code < 300;
}

void buttonTask(void* param) {
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    bool lastState = digitalRead(BUTTON_PIN);

    while (true) {
        bool current = digitalRead(BUTTON_PIN);
        if (lastState == HIGH && current == LOW) { // falling edge = press
            bool msg = true;
            xQueueSend(gButtonQueue, &msg, 0);
        }
        lastState = current;
        vTaskDelay(pdMS_TO_TICKS(BUTTON_POLL_MS));
    }
}

void setup() {
    Serial.begin(115200);
    pinMode(LED_PIN, OUTPUT);
    setLed(false);

    pinMode(PIN_BUTTON, INPUT_PULLUP);

    WiFi.onEvent(onWiFiEvent);

    gButtonQueue = xQueueCreate(5, sizeof(bool));
    xTaskCreatePinnedToCore(buttonTask, "buttonTask", 2048, nullptr, 1, nullptr, 1);

    if (!ensureWiFiConnected()) {
        logStatus("[wifi] failed to connect; rebooting in 5s");
        delay(5000);
        ESP.restart();
    }

    uint8_t healthTries = 0;
    while (healthTries < HEALTH_MAX_RETRIES) {
        if (checkHealth()) {
            gReady = true;
            setLed(true);
            logStatus("[health] PLA Node ready");
            break;
        }
        ++healthTries;
        logStatus("[health] retrying...");
        delay(1000);
    }

    if (!gReady) {
        logStatus("[health] failed; continuing but LED stays blinking");
    }
}

void loop() {
    if (!gReady && WiFi.status() != WL_CONNECTED) {
        ensureWiFiConnected();
    }

    handleButtonAndLed();

    bool pressed = false;
    if (xQueueReceive(gButtonQueue, &pressed, pdMS_TO_TICKS(100)) == pdTRUE && pressed) {
        if (WiFi.status() == WL_CONNECTED && (gReady || checkHealth())) {
            bool ok = postIngest();
            if (ok) {
                quickFlashSuccess();
            } else {
                tripleFlashFailure();
            }
        } else {
            tripleFlashFailure();
        }
    }

    // Slow blink if not ready yet.
    if (!gReady) {
        slowBlinkWhileConnecting();
    }
}
