/**
 * ESP32-S3 Dual TMC2209 Stepper Driver Test
 * 
 * Tests TWO TMC2209 drivers with NEMA16 motors (X and Y).
 * Features: speed ramping, microstepping, UART config, StallGuard homing.
 * 
 * Hardware:
 *   - ESP32-S3-N16R8
 *   - TWO TMC2209 stepper driver breakouts
 *   - TWO NEMA16 5-wire motors (bipolar mode, with shaft screws for homing)
 * 
 * Wiring - Motor X:
 *   STEP -> GPIO 4
 *   DIR  -> GPIO 5
 *   EN   -> GPIO 6
 *   MS1  -> 3.3V (16x microstepping)
 *   MS2  -> 3.3V
 *   USART-> GPIO 16 (RX) via 1kΩ from TMC PDN+USART
 * 
 * Wiring - Motor Y:
 *   STEP -> GPIO 14
 *   DIR  -> GPIO 15
 *   EN   -> GPIO 2
 *   MS1  -> 3.3V (16x microstepping)
 *   MS2  -> 3.3V
 *   USART-> GPIO 13 (RX2) via 1kΩ from TMC PDN+USART
 * 
 * Serial: 115200 baud
 */

#include <TMCStepper.h>

// === Motor X ===
#define STEP_PIN_X    4
#define DIR_PIN_X     5
#define SERIAL_PORT_X Serial1  // UART for TMC2209 X

// === Motor Y ===
#define STEP_PIN_Y    14
#define DIR_PIN_Y     15
#define SERIAL_PORT_Y Serial2  // UART for TMC2209 Y (GPIO 13 RX)

// === Shared Enable ===
#define EN_PIN        6        // Shared enable for both motors (active LOW)

// TMC2209 settings
#define R_SENSE            0.11f    // Sense resistor value (R110 = 0.11Ω)
#define DRIVER_BAUD        115200   // UART baud rate
#define DRIVER_ADDRESS_X   0b00     // MS1/MS2 address for X
#define DRIVER_ADDRESS_Y   0b01     // MS1/MS2 address for Y

// Current setting (in milliamps)
#define MOTOR_CURRENT_RUN  400      // Running current (400mA for 0.4A limit)

// Motor parameters
#define STEPS_PER_REV  200      // 1.8° motor = 200 steps/rev
#define MICROSTEPS     16       // 16x microstepping = 3200 microsteps/rev

// Homing parameters
#define STALL_THRESHOLD   64       // StallGuard threshold (0-255)
#define HOMING_SPEED      500      // Homing speed in steps/sec (slower for reliability)
#define BACKOFF_STEPS     50       // Steps to back off after stall (center position)

// Create driver instances
TMC2209Stepper driverX(&SERIAL_PORT_X, R_SENSE, DRIVER_ADDRESS_X);
TMC2209Stepper driverY(&SERIAL_PORT_Y, R_SENSE, DRIVER_ADDRESS_Y);

// State variables
volatile long stepCountX = 0, stepCountY = 0;
bool directionX = false, directionY = false;
int currentSpeedX = 1000, currentSpeedY = 1000;
bool driverEnabledX = false, driverEnabledY = false;
bool homed = false;

void setup() {
  // Initialize serial
  Serial.begin(115200);
  while (!Serial) delay(10);
  
  Serial.println("\n=== ESP32-S3 Dual TMC2209 Test ===");
  Serial.println("Board: ESP32-S3-N16R8");
  Serial.println("Motors: X (GPIO 4/5) + Y (GPIO 14/15) + EN (GPIO 6 shared)");
  Serial.println();

  // Configure pins - Motor X
  pinMode(STEP_PIN_X, OUTPUT);
  pinMode(DIR_PIN_X, OUTPUT);
  
  // Configure pins - Motor Y
  pinMode(STEP_PIN_Y, OUTPUT);
  pinMode(DIR_PIN_Y, OUTPUT);
  
  // Configure shared enable pin
  pinMode(EN_PIN, OUTPUT);
  
  // Set initial states
  digitalWrite(STEP_PIN_X, LOW);
  digitalWrite(DIR_PIN_X, LOW);
  
  digitalWrite(STEP_PIN_Y, LOW);
  digitalWrite(DIR_PIN_Y, LOW);
  
  digitalWrite(EN_PIN, HIGH);  // Disabled (active LOW)
  
  // Initialize UART for both drivers
  SERIAL_PORT_X.begin(DRIVER_BAUD, SERIAL_8N1, 16, -1);   // RX=16, TX=unused
  SERIAL_PORT_Y.begin(DRIVER_BAUD, SERIAL_8N1, 13, -1);   // RX=13, TX=unused
  delay(100);

  // Initialize Driver X
  driverX.begin();
  driverX.toff(5);
  driverX.rms_current(MOTOR_CURRENT_RUN);
  driverX.microsteps(MICROSTEPS);
  driverX.en_spreadCycle(false);  // StealthChop
  driverX.pwm_autoscale(true);
  driverX.SGTHRS(STALL_THRESHOLD);

  // Initialize Driver Y
  driverY.begin();
  driverY.toff(5);
  driverY.rms_current(MOTOR_CURRENT_RUN);
  driverY.microsteps(MICROSTEPS);
  driverY.en_spreadCycle(false);  // StealthChop
  driverY.pwm_autoscale(true);
  driverY.SGTHRS(STALL_THRESHOLD);

  Serial.println("TMC2209 X and Y configured:");
  Serial.print("  Microsteps: ");
  Serial.println(MICROSTEPS);
  Serial.print("  I_run: ");
  Serial.print(MOTOR_CURRENT_RUN);
  Serial.println("mA");
  Serial.println("  Mode: StealthChop");
  Serial.println();
  
  printHelp();
}

void loop() {
  // Check for serial commands
  if (Serial.available()) {
    char cmd = Serial.read();
    handleCommand(cmd);
  }
}

void handleCommand(char cmd) {
  switch (cmd) {
    case 's':  // Single step X
      singleStepX();
      break;
    
    case 'S':  // Single step Y
      singleStepY();
      break;
      
    case 'r':  // Run continuous X
      runContinuousX(3000);
      break;
      
    case 'R':  // Run continuous Y
      runContinuousY(3000);
      break;
      
    case 'd':  // Toggle direction X
      directionX = !directionX;
      digitalWrite(DIR_PIN_X, directionX);
      Serial.print("X Direction: ");
      Serial.println(directionX ? "CW" : "CCW");
      break;
      
    case 'D':  // Toggle direction Y
      directionY = !directionY;
      digitalWrite(DIR_PIN_Y, directionY);
      Serial.print("Y Direction: ");
      Serial.println(directionY ? "CW" : "CCW");
      break;
      
    case '1':  // Speed test 500 steps/s
      speedTestX(500);
      break;
    case '2':
      speedTestX(1000);
      break;
    case '3':
      speedTestX(2000);
      break;
    case '4':
      speedTestX(4000);
      break;
    case '5':
      speedTestX(8000);
      break;
      
    case 'h':  // Home to limits
      homeMotors();
      break;
      
    case 'c':  // Center (after homing)
      centerMotors();
      break;
      
    case 'i':  // Driver info
      printDriverInfo();
      break;
      
    case 'e':  // Enable both
      enableDriver(true, true);
      break;
      
    case 'x':  // Disable both
      enableDriver(false, false);
      break;
      
    case 'E':  // Enable X only
      enableDriver(true, false);
      break;
      
    case 'X':  // Disable X only
      enableDriver(false, false);
      break;
      
    case 'Y':  // Enable Y only
      enableDriver(false, true);
      break;
      
    case 'Z':  // Disable Y only
      enableDriver(false, false);
      break;
      
    case '?':
      printHelp();
      break;
      
    default:
      if (cmd != '\n' && cmd != '\r') {
        Serial.println("Unknown command. Press '?' for help.");
      }
      break;
  }
}

void singleStepX() {
  if (!driverEnabledX) {
    Serial.println("X motor disabled. Press 'E' to enable.");
    return;
  }
  
  digitalWrite(STEP_PIN_X, HIGH);
  delayMicroseconds(10);
  digitalWrite(STEP_PIN_X, LOW);
  delayMicroseconds(10);
  
  stepCountX += directionX ? 1 : -1;
  Serial.print("X Step: ");
  Serial.print(stepCountX);
  Serial.print(" (");
  Serial.print((float)stepCountX / (STEPS_PER_REV * MICROSTEPS) * 360.0);
  Serial.println("°)");
}

void singleStepY() {
  if (!driverEnabledY) {
    Serial.println("Y motor disabled. Press 'Y' to enable.");
    return;
  }
  
  digitalWrite(STEP_PIN_Y, HIGH);
  delayMicroseconds(10);
  digitalWrite(STEP_PIN_Y, LOW);
  delayMicroseconds(10);
  
  stepCountY += directionY ? 1 : -1;
  Serial.print("Y Step: ");
  Serial.print(stepCountY);
  Serial.print(" (");
  Serial.print((float)stepCountY / (STEPS_PER_REV * MICROSTEPS) * 360.0);
  Serial.println("°)");
}

void runContinuousX(int steps) {
  if (!driverEnabledX) {
    Serial.println("X motor disabled. Press 'E' to enable.");
    return;
  }
  
  Serial.print("X: Running ");
  Serial.print(steps);
  Serial.print(" steps at ");
  Serial.print(currentSpeedX);
  Serial.println(" steps/s...");
  
  unsigned long delayUs = 1000000UL / currentSpeedX / 2;
  
  for (int i = 0; i < steps; i++) {
    digitalWrite(STEP_PIN_X, HIGH);
    delayMicroseconds(delayUs);
    digitalWrite(STEP_PIN_X, LOW);
    delayMicroseconds(delayUs);
    
    stepCountX += directionX ? 1 : -1;
    
    if ((i + 1) % 100 == 0) {
      Serial.print("  ");
      Serial.print(i + 1);
      Serial.print(" / ");
      Serial.println(steps);
    }
  }
  
  Serial.println("Done.");
}

void runContinuousY(int steps) {
  if (!driverEnabledY) {
    Serial.println("Y motor disabled. Press 'Y' to enable.");
    return;
  }
  
  Serial.print("Y: Running ");
  Serial.print(steps);
  Serial.print(" steps at ");
  Serial.print(currentSpeedY);
  Serial.println(" steps/s...");
  
  unsigned long delayUs = 1000000UL / currentSpeedY / 2;
  
  for (int i = 0; i < steps; i++) {
    digitalWrite(STEP_PIN_Y, HIGH);
    delayMicroseconds(delayUs);
    digitalWrite(STEP_PIN_Y, LOW);
    delayMicroseconds(delayUs);
    
    stepCountY += directionY ? 1 : -1;
    
    if ((i + 1) % 100 == 0) {
      Serial.print("  ");
      Serial.print(i + 1);
      Serial.print(" / ");
      Serial.println(steps);
    }
  }
  
  Serial.println("Done.");
}

void speedTestX(int speed) {
  currentSpeedX = speed;
  Serial.print("X: Speed test ");
  Serial.print(speed);
  Serial.println(" steps/s");
  
  runContinuousX(speed);
}

// === Homing Functions ===

void homeMotors() {
  if (!driverEnabledX || !driverEnabledY) {
    enableDriver(true, true);
  }
  
  Serial.println("\n=== Homing X and Y Motors ===");
  Serial.println("Moving towards limits (shaft screws)...\n");
  
  // Home X
  homeAxis(STEP_PIN_X, DIR_PIN_X, driverX, 'X', stepCountX);
  delay(200);
  
  // Home Y
  homeAxis(STEP_PIN_Y, DIR_PIN_Y, driverY, 'Y', stepCountY);
  delay(200);
  
  // Reset counts to 0 (at home position)
  stepCountX = 0;
  stepCountY = 0;
  
  homed = true;
  Serial.println("\n✓ Homing complete. Motors at limits.");
  Serial.println("  Use 'c' to center both motors.");
}

void homeAxis(int stepPin, int dirPin, TMC2209Stepper &driver, char axis, long &stepCount) {
  Serial.print(axis);
  Serial.print(": Homing... ");
  
  // Set direction towards limit (CW = towards screw)
  digitalWrite(dirPin, HIGH);
  
  unsigned long delayUs = 1000000UL / HOMING_SPEED / 2;
  bool stalled = false;
  int stallCount = 0;
  
  // Move until stall detected
  for (int i = 0; i < 50000; i++) {  // Max 50k steps (~6.25 revolutions)
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(delayUs);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(delayUs);
    
    stepCount++;
    
    // Check for stall every 10 steps
    if (i % 10 == 0) {
      uint32_t sg = driver.SG_RESULT();
      if (sg < 10) {  // Stall detected (low SG_RESULT)
        stallCount++;
        if (stallCount > 3) {  // Confirm stall over multiple reads
          stalled = true;
          break;
        }
      } else {
        stallCount = 0;  // Reset counter if no stall
      }
    }
    
    // Progress indicator
    if (i % 500 == 0 && i > 0) {
      Serial.print(".");
    }
  }
  
  if (stalled) {
    Serial.println(" stalled!");
    
    // Back off from limit
    Serial.print(axis);
    Serial.print(": Backing off ");
    Serial.print(BACKOFF_STEPS);
    Serial.println(" steps...");
    
    digitalWrite(dirPin, LOW);  // Reverse direction
    
    for (int i = 0; i < BACKOFF_STEPS; i++) {
      digitalWrite(stepPin, HIGH);
      delayMicroseconds(delayUs);
      digitalWrite(stepPin, LOW);
      delayMicroseconds(delayUs);
      
      stepCount--;
    }
    
    Serial.print(axis);
    Serial.println(": Ready at home position.");
  } else {
    Serial.println(" ERROR - No stall detected!");
  }
}

void centerMotors() {
  if (!homed) {
    Serial.println("Must home first ('h'). Motors may not be at limit.");
    return;
  }
  
  Serial.println("\n=== Centering Motors ===");
  
  // Move to center (half of full range)
  // Assuming ~6000 microsteps is full range, center = 3000
  long centerPos = (STEPS_PER_REV * MICROSTEPS) / 2;
  
  moveToX(centerPos);
  moveToY(centerPos);
  
  Serial.println("✓ Both motors centered.");
}

void moveToX(long targetSteps) {
  if (!driverEnabledX) {
    enableDriver(true, false);
  }
  
  long diff = targetSteps - stepCountX;
  
  Serial.print("X: Moving ");
  Serial.print(diff > 0 ? "+" : "");
  Serial.print(diff);
  Serial.println(" steps...");
  
  digitalWrite(DIR_PIN_X, diff > 0 ? HIGH : LOW);
  
  unsigned long delayUs = 1000000UL / currentSpeedX / 2;
  
  for (long i = 0; i < abs(diff); i++) {
    digitalWrite(STEP_PIN_X, HIGH);
    delayMicroseconds(delayUs);
    digitalWrite(STEP_PIN_X, LOW);
    delayMicroseconds(delayUs);
    
    stepCountX += diff > 0 ? 1 : -1;
  }
}

void moveToY(long targetSteps) {
  if (!driverEnabledY) {
    enableDriver(false, true);
  }
  
  long diff = targetSteps - stepCountY;
  
  Serial.print("Y: Moving ");
  Serial.print(diff > 0 ? "+" : "");
  Serial.print(diff);
  Serial.println(" steps...");
  
  digitalWrite(DIR_PIN_Y, diff > 0 ? HIGH : LOW);
  
  unsigned long delayUs = 1000000UL / currentSpeedY / 2;
  
  for (long i = 0; i < abs(diff); i++) {
    digitalWrite(STEP_PIN_Y, HIGH);
    delayMicroseconds(delayUs);
    digitalWrite(STEP_PIN_Y, LOW);
    delayMicroseconds(delayUs);
    
    stepCountY += diff > 0 ? 1 : -1;
  }
}

// === Utility Functions ===

void printDriverInfo() {
  Serial.println("\n=== TMC2209 Info ===\n");
  
  Serial.println("Motor X:");
  Serial.print("  Version: 0x");
  Serial.println(driverX.version(), HEX);
  Serial.print("  Microsteps: ");
  Serial.println(driverX.microsteps());
  Serial.print("  SG_RESULT: ");
  Serial.println(driverX.SG_RESULT());
  Serial.print("  Status: ");
  Serial.println(driverX.drv_err() ? "ERROR" : "OK");
  
  Serial.println("\nMotor Y:");
  Serial.print("  Version: 0x");
  Serial.println(driverY.version(), HEX);
  Serial.print("  Microsteps: ");
  Serial.println(driverY.microsteps());
  Serial.print("  SG_RESULT: ");
  Serial.println(driverY.SG_RESULT());
  Serial.print("  Status: ");
  Serial.println(driverY.drv_err() ? "ERROR" : "OK");
  
  Serial.println("\nPosition:");
  Serial.print("  X: ");
  Serial.print(stepCountX);
  Serial.print(" steps (");
  Serial.print((float)stepCountX / (STEPS_PER_REV * MICROSTEPS) * 360.0);
  Serial.println("°)");
  
  Serial.print("  Y: ");
  Serial.print(stepCountY);
  Serial.print(" steps (");
  Serial.print((float)stepCountY / (STEPS_PER_REV * MICROSTEPS) * 360.0);
  Serial.println("°)");
  
  Serial.println();
}

void enableDriver(bool enableX, bool enableY) {
  driverEnabledX = enableX;
  driverEnabledY = enableY;
  
  // Single EN pin controls both motors
  if (enableX || enableY) {
    digitalWrite(EN_PIN, LOW);  // Active LOW
    Serial.println("Motors: ENABLED");
  } else {
    digitalWrite(EN_PIN, HIGH);
    Serial.println("Motors: DISABLED");
  }
  
  if (enableX) Serial.println("  X: active");
  if (enableY) Serial.println("  Y: active");
}

void printHelp() {
  Serial.println("\n=== Commands ===");
  Serial.println("\nMotor X:");
  Serial.println("  s — Single step X");
  Serial.println("  r — Run continuous X (3000 steps)");
  Serial.println("  d — Toggle direction X");
  Serial.println("  1-5 — Speed test X (500, 1000, 2000, 4000, 8000 steps/s)");
  Serial.println("  E — Enable X motor");
  Serial.println("  X — Disable X motor");
  
  Serial.println("\nMotor Y:");
  Serial.println("  S — Single step Y");
  Serial.println("  R — Run continuous Y (3000 steps)");
  Serial.println("  D — Toggle direction Y");
  Serial.println("  Y — Enable Y motor");
  Serial.println("  Z — Disable Y motor");
  
  Serial.println("\nHoming (StallGuard):");
  Serial.println("  h — Home both motors (move to limits, stall detect)");
  Serial.println("  c — Center both motors (after homing)");
  
  Serial.println("\nOther:");
  Serial.println("  e — Enable both motors");
  Serial.println("  x — Disable both motors");
  Serial.println("  i — Print driver info");
  Serial.println("  ? — Help");
  Serial.println();
}
