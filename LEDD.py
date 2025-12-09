from jnius import autoclass, cast
from time import sleep

# Android classes
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Context = autoclass('android.content.Context')
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothManager = autoclass('android.bluetooth.BluetoothManager')

# Get Bluetooth service
activity = PythonActivity.mActivity
bluetooth_service = cast(BluetoothManager, activity.getSystemService(Context.BLUETOOTH_SERVICE))
adapter = bluetooth_service.getAdapter()

# Enable adapter if not already
if not adapter.isEnabled():
    adapter.enable()
    print("🔌 Bluetooth enabled")

# Callback for scan results
ScanCallback = autoclass('android.bluetooth.le.ScanCallback')
ScanResult = autoclass('android.bluetooth.le.ScanResult')

class MyScanCallback(ScanCallback):
    def onScanResult(self, callbackType, result):
        device = result.getDevice()
        print(f"Found device: {device.getName()} - {device.getAddress()}")

# Start scanning
scanner = adapter.getBluetoothLeScanner()
callback = MyScanCallback()
scanner.startScan(callback)
print("🔎 Scanning for 10 seconds...")
sleep(10)
scanner.stopScan(callback)
print("✅ Scan complete")
