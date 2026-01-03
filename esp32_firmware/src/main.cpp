#include <WiFi.h>
#include <HTTPClient.h>
#include "secrets.h"

// Pin assignments
static constexpr int LED_PIN = 2;    // Onboard LED to GND (active LOW)
static constexpr int BUTTON_PIN = 4; // Button to GND with INPUT_PULLUP

static constexpr TickType_t BUTTON_POLL_MS = 20;
static constexpr uint32_t WIFI_RETRY_DELAY_MS = 750;
static constexpr uint8_t HEALTH_MAX_RETRIES = 10;

static QueueHandle_t gButtonQueue = nullptr;
static bool gReady = false;

// LED helpers (active low because LED is tied to GND)
inline void setLed(bool on) { digitalWrite(LED_PIN, on ? LOW : HIGH); }
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

bool ensureWiFiConnected() {
    if (WiFi.status() == WL_CONNECTED) {
        return true;
    }

    logStatus("[wifi] connecting...");
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    uint8_t attempts = 0;
    while (WiFi.status() != WL_CONNECTED) {
        slowBlinkWhileConnecting();
        if (++attempts >= 40) { // ~40 * 1s = 40s guard
            logStatus("[wifi] giving up after ~40s");
            return false;
        }
    }

    Serial.print("[wifi] connected, IP: ");
    Serial.println(WiFi.localIP());
    return true;
}

bool checkHealth() {
    HTTPClient http;
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
    String url = String("http://") + PLA_HOST + ":" + PLA_PORT + "/ingest";
    String payload = String("{") +
                     "\"event_version\":\"1.0\"," +
                     "\"device_id\":\"esp32-hands-001\"," +
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
