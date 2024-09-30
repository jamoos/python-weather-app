# apprved by Or
from selenium import webdriver
from selenium.webdriver.common.by import By


def pull_location_card(location):
    service = webdriver.FirefoxService(executable_path="geckodriver")
    driver = webdriver.Firefox(service=service)
    driver.get(f"http://localhost:5000/{location}")
    try:
        driver.find_element(By.CLASS_NAME, "location-card")
    except:
        return False
    else:
        return True
    finally:
        driver.close()


def test_positive():
    assert pull_location_card("kalanit harish")


def test_negative():
    assert not pull_location_card("liraz kafri")
