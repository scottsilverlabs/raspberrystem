echo "###################################################################"
echo ""
echo "Accelerometer / LED Matrix / Buttons / LEDSs / GPIOs Test Lid"
echo ""
echo "Lid setup:"
echo "  - Single LED matrix"
echo "      - mounted 90 deg clockwise"
echo "      - MISO connected"
echo "      - SPI Port 0 (CE0)"
echo "      - Reset unconnected"
echo "  - Accelerometer: Power, Ground, SCL, SDA"
echo "  - LEDs"
echo "      - Left LED/resistor: Positive side to 3.3, negative side to GPIO 15"
echo "      - Right LED/resistor: Positive side to 3.3, negative side to GPIO 18"
echo "  - Buttons"
echo "      - Left Button: From ground to GPIO 27"
echo "      - Right Button: From ground to GPIO 17"
echo "  - GPIO shorted from 23 to 24"
echo "  - Speaker connected to analog audio out"
echo ""
echo "###################################################################"
read
make auto-accel
make auto-gpio_loopback_23_to_24
make auto-led_matrix_1_270_no_miso
make auto-speaker

make manu-accel
make manu-gpio_loopback_23_to_24
make manu-led_matrix_1_270_no_miso
make manu-speaker
