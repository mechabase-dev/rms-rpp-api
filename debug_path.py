import os
import sys
import playwright
from playwright._impl._driver import compute_driver_executable

print(f"Playwright file: {playwright.__file__}")
print(f"Playwright parent: {os.path.dirname(playwright.__file__)}")

driver_path = compute_driver_executable()
print(f"Computed driver path: {driver_path}")
print(f"Driver exists: {os.path.exists(driver_path)}")

if not os.path.exists(driver_path):
    print("Listing parent directory:")
    parent = os.path.dirname(driver_path)
    if os.path.exists(parent):
        print(os.listdir(parent))
    else:
        print(f"{parent} does not exist")
