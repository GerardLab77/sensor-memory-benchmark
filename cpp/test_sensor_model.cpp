#include "sensor_model.hpp"
#include <cstdio>
#include <cstdlib>
#include <limits>

void check(bool condition, int line) {
    if (!condition) {
        std::fprintf(stderr, "Check failed at line %d\n", line);
        std::abort();
    }
}
#define CHECK(condition) check((condition), __LINE__)

int main() {
    sensor::Parameters<1> current_parameters;
    current_parameters.weights[0][0] = {2, -1};
    current_parameters.weights[0][15] = {3, 4};
    current_parameters.bias = {1, 2};
    sensor::CurrentModel current(current_parameters);
    sensor::Reading reading{};
    reading[0] = 3; reading[15] = 5;
    sensor::Prediction out{};
    CHECK(current.update(reading, out));
    CHECK(out[0] == 22 && out[1] == 19);

    sensor::Parameters<5> lag_parameters;
    for (std::size_t k = 0; k < 5; ++k)
        lag_parameters.weights[k][0][0] = sensor::Real(1 << k);
    lag_parameters.weights[4][1][1] = 1;
    lag_parameters.bias[1] = 1;
    sensor::LagModel lag(lag_parameters);
    for (int pass = 0; pass < 2; ++pass) {
        lag.reset();
        for (int i = 0; i < 40; ++i) {
            reading = {};
            reading[0] = sensor::Real(i + 7);
            reading[1] = sensor::Real(3 * (i + 7));
            sensor::Real expected = 0;
            for (std::size_t k = 0; k < 5; ++k) {
                const int age = i - int(sensor::lags[k]);
                expected += sensor::Real((1 << k) * ((age > 0 ? age : 0) + 7));
            }
            const int old = i > 10 ? i - 10 : 0;
            CHECK(lag.update(reading, out));
            CHECK(out[0] == expected && out[1] == 3 * (old + 7) + 1);
            const auto before = out;
            auto bad = reading;
            bad[3] = std::numeric_limits<sensor::Real>::quiet_NaN();
            CHECK(!lag.update(bad, out));
            CHECK(out == before);
            bad[3] = std::numeric_limits<sensor::Real>::infinity();
            CHECK(!current.update(bad, out));
            CHECK(out == before);
        }
    }
    return 0;
}
