#pragma once
#include <array>
#include <cmath>
#include <cstddef>

namespace sensor {
constexpr std::size_t channels = 16;
constexpr std::size_t targets = 2;
constexpr std::array<std::size_t, 5> lags{0, 1, 2, 5, 10};
#ifdef SENSOR_DOUBLE
using Real = double;  // Handy for checking against Python.
#else
using Real = float;
#endif
using Reading = std::array<Real, channels>;
using Prediction = std::array<Real, targets>;

inline bool valid(const Reading& reading) {
    for (Real value : reading) if (!std::isfinite(value)) return false;
    return true;
}

template <std::size_t N>
struct Parameters {
    // Weights go in lag, channel, gas order.
    std::array<std::array<std::array<Real, targets>, channels>, N> weights{};
    Prediction bias{};
};

inline void accumulate(Prediction& out, const Reading& reading,
                       const std::array<std::array<Real, targets>, channels>& weights) {
    for (std::size_t c = 0; c < channels; ++c)
        for (std::size_t g = 0; g < targets; ++g)
            out[g] += reading[c] * weights[c][g];
}

class CurrentModel {
public:
    // Keep the weights around while the model is in use.
    explicit CurrentModel(const Parameters<1>& parameters) : parameters_(parameters) {}
    CurrentModel(Parameters<1>&&) = delete;
    void reset() {}
    bool update(const Reading& reading, Prediction& out) {
        if (!valid(reading)) return false;
        out = parameters_.bias;
        accumulate(out, reading, parameters_.weights[0]);
        return true;
    }
private:
    const Parameters<1>& parameters_;
};

class LagModel {
public:
    explicit LagModel(const Parameters<5>& parameters) : parameters_(parameters) {}
    LagModel(Parameters<5>&&) = delete;
    void reset() { started_ = false; latest_ = 0; }

    // Feed it one reading a second. A bad reading leaves the buffer alone.
    bool update(const Reading& reading, Prediction& out) {
        if (!valid(reading)) return false;
        if (!started_) {
            // Start with copies of the first reading until we have real history.
            history_.fill(reading);
            latest_ = 0;
            started_ = true;
        } else {
            latest_ = (latest_ + 1) % history_.size();
            history_[latest_] = reading;
        }
        out = parameters_.bias;
        for (std::size_t k = 0; k < lags.size(); ++k) {
            // Count back from the newest slot and wrap around if needed.
            const auto position = (latest_ + history_.size() - lags[k]) % history_.size();
            accumulate(out, history_[position], parameters_.weights[k]);
        }
        return true;
    }
private:
    const Parameters<5>& parameters_;
    std::array<Reading, 11> history_{};
    std::size_t latest_ = 0;
    bool started_ = false;
};
} // namespace sensor
