# Carmen Hardware Guide

## Complete Starter Kit (1 Plant)

### Shopping List

| Item | Specifications | Quantity | Unit Price | Total | Where to Buy |
|------|----------------|----------|------------|-------|--------------|
| **ESP32-WROOM-32D Development Board** | 38-pin, WiFi + Bluetooth | 1 | $8 | $8 | Amazon, AliExpress, DigiKey, Mouser |
| **Capacitive Soil Moisture Sensor** | v1.2 or v2.0, corrosion-resistant | 1 | $3 | $3 | Amazon, AliExpress, Adafruit |
| **DHT22 (AM2302) Sensor** | Temperature & Humidity | 1 | $10 | $10 | Amazon, AliExpress, Adafruit, SparkFun |
| **BH1750 Light Sensor** | Digital light intensity | 1 | $5 | $5 | Amazon, AliExpress, Adafruit |
| **USB Power Adapter** | 5V, 2A minimum | 1 | $7 | $7 | Amazon, local electronics store |
| **Micro-USB Cable** | Data + Power (1m minimum) | 1 | $3 | $3 | Amazon, local electronics store |
| **Breadboard** | 400 or 830 points | 1 | $5 | $5 | Amazon, AliExpress, Adafruit |
| **Jumper Wires** | Male-to-Female (20cm) | 10 | $0.50 | $5 | Amazon, AliExpress |
| **Jumper Wires** | Male-to-Male (20cm) | 5 | $0.50 | - | (included in pack above) |
| | | | **TOTAL** | **~$46** | |

### Optional Components

| Item | Purpose | Quantity | Unit Price | Where to Buy |
|------|---------|----------|------------|--------------|
| **Waterproof Case** | Outdoor protection for ESP32 | 1 | $8 | Amazon, AliExpress |
| **10kΩ Resistor** | Pull-up for DHT22 (often included) | 1 | $0.10 | Local electronics store |
| **Power Bank** | Portable power (for testing) | 1 | $15 | Amazon |

---

## Wiring Connections

### Capacitive Soil Moisture Sensor → ESP32
- **VCC** → 3.3V
- **GND** → GND
- **AOUT** → GPIO34 (analog input)

### DHT22 Sensor → ESP32
- **VCC** → 3.3V (or 5V)
- **GND** → GND
- **DATA** → GPIO4 (with 10kΩ pull-up resistor to VCC)

### BH1750 Light Sensor → ESP32
- **VCC** → 3.3V
- **GND** → GND
- **SDA** → GPIO21
- **SCL** → GPIO22

---

## Power Requirements

- **Total current draw**: ~150-200mA during active reading
- **Deep sleep mode**: <1mA
- **Recommended power**: 5V, 2A USB adapter for stable operation

---

## Assembly Notes

1. **Start with the breadboard** - no soldering required for prototyping
2. **Connect one sensor at a time** - test each before adding the next
3. **Use color-coded wires** - Red (VCC), Black (GND), other colors for data
4. **Keep wires short** - reduces electromagnetic interference
5. **Waterproof outdoor sensors** - use heat shrink or waterproof coating on connections

---

## Scaling to Multiple Plants

For each additional plant, add:
- **1x Capacitive Soil Moisture Sensor** ($3)
- **1x Set of jumper wires** ($1)

The same ESP32 can monitor up to **5-8 plants** using different GPIO pins:
- GPIO34, GPIO35, GPIO32, GPIO33, GPIO25, GPIO26, GPIO27, GPIO14

---

## Alternative Sensors (Budget Options)

### Lower Cost Option
Replace **DHT22** with **DHT11**:
- Temperature & Humidity: $2-4 (less accurate but functional)

Replace **BH1750** with **Photoresistor**:
- Light sensor: $0.50-1 (analog, less precise)

**Budget Total**: ~$30

### Premium Option
Replace **DHT22** with **BME280**:
- Temperature, Humidity, Pressure: $12-15 (more accurate, I2C)

**Premium Total**: ~$50

---

## Next Steps After Purchase

1. **Verify all components** work individually
2. **Flash the Carmen firmware** to ESP32
3. **Calibrate sensors** (especially soil moisture)
4. **Test for 24-48 hours** before permanent installation