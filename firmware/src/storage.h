#pragma once

namespace storage {

void begin();

float loadHumidityThreshold();
void saveHumidityThreshold(float value);

} // namespace storage