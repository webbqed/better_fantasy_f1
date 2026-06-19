import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from f1.pipeline import run

if __name__ == "__main__":
    drivers = run()
    for driver in drivers:
        print(driver.full_name, round(driver.price, 2), round((1000 / driver.price) * driver.sim_mean, 2))
        print(driver.full_name, round(driver.price, 2), round((1000 / driver.price) * driver.sim_points[55], 2))
        print(driver.full_name, round(driver.price, 2), round((1000 / driver.price) * driver.sim_points[95], 2))
    print('end of simulation')
