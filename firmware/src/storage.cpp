#include "storage.h"
#include <Preferences.h>
#include "config.h"

namespace storage {

static Preferences prefs;
static const char* NAMESPACE = "irrigador";
static const char* KEY_THRESHOLD = "hum_thresh";

void begin() {
    prefs.begin(NAMESPACE, /* readOnly = */ false);
}

float loadHumidityThreshold() {
    return prefs.getFloat(KEY_THRESHOLD, DEFAULT_HUMIDITY_THRESHOLD);
}

void saveHumidityThreshold(float value) {
    prefs.putFloat(KEY_THRESHOLD, value);
}

} // namespace storage