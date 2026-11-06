// Reads saved weights and plays back the sensor readings on a PC.
#include "sensor_model.hpp"
#include <cstdio>
#include <cstring>

bool read_value(FILE* file, sensor::Real& value) {
#ifdef SENSOR_DOUBLE
    return std::fscanf(file, "%lf", &value) == 1 && std::isfinite(value);
#else
    return std::fscanf(file, "%f", &value) == 1 && std::isfinite(value);
#endif
}
bool at_end(FILE* file) {
    char extra;
    return std::fscanf(file, " %c", &extra) == EOF && !std::ferror(file);
}

template <std::size_t N, typename Model>
int replay(FILE* parameters, FILE* inputs, FILE* outputs) {
    sensor::Parameters<N> p;
    for (auto& lag : p.weights)
        for (auto& channel : lag)
            for (auto& weight : channel)
                if (!read_value(parameters, weight)) return 3;
    for (auto& bias : p.bias) if (!read_value(parameters, bias)) return 3;
    if (!at_end(parameters)) return 3;
    unsigned count;
    if (std::fscanf(inputs, "%u", &count) != 1 || count == 0) return 4;
    Model model(p);
    for (unsigned i = 0; i < count; ++i) {
        sensor::Reading reading;
        sensor::Prediction prediction;
        for (auto& value : reading) if (!read_value(inputs, value)) return 4;
        if (!model.update(reading, prediction)) return 4;
        for (auto value : prediction) if (!std::isfinite(value)) return 5;
        if (std::fprintf(outputs, "%.17g %.17g\n",
                         double(prediction[0]), double(prediction[1])) < 0) return 6;
    }
    return at_end(inputs) ? 0 : 4;
}

int main(int argc, char** argv) {
    if (argc != 5 || (std::strcmp(argv[1], "current") && std::strcmp(argv[1], "lags_10s"))) {
        std::fprintf(stderr, "Usage: replay current|lags_10s model.txt inputs.txt outputs.txt\n");
        return 2;
    }
    FILE* parameters = std::fopen(argv[2], "r");
    FILE* inputs = std::fopen(argv[3], "r");
    FILE* outputs = std::fopen(argv[4], "w");
    int result = 2;
    if (parameters && inputs && outputs)
        result = std::strcmp(argv[1], "current") == 0
            ? replay<1, sensor::CurrentModel>(parameters, inputs, outputs)
            : replay<5, sensor::LagModel>(parameters, inputs, outputs);
    if (parameters) std::fclose(parameters);
    if (inputs) std::fclose(inputs);
    if (outputs && std::fclose(outputs) != 0) result = 6;
    if (result) std::fprintf(stderr, "Replay failed (code %d)\n", result);
    return result;
}
