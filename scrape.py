from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Set up Chrome WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

url = "https://www.sofascore.com/football/2025-03-06"

try:
    driver.get(url)
    
    # Wait for page to load completely
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    
    # Find main tag within body
    main_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "main"))
    )
    
    # Initial div traversal path
    div_path = [0, 2, 1, 0, 0, 1, 0]
    current_element = main_element
    for index in div_path:
        children = WebDriverWait(current_element, 10).until(
            lambda e: e.find_elements(By.XPATH, "./div")
        )
        current_element = children[index]
    
    # Process blocks
    all_bdi_contents = []
    blocks = WebDriverWait(current_element, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "./div"))
    )
    
    for block in blocks:
        try:
            # Start with <a> tag in block
            a_element = WebDriverWait(block, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            
            # Traverse path: 0 → 0 → 3 → 0 → 0 → 1
            path = [0, 0, 3, 0, 0, 1]
            current_node = a_element
            for idx in path:
                children = WebDriverWait(current_node, 10).until(
                    lambda e: e.find_elements(By.XPATH, "./*")
                )
                current_node = children[idx]
            
            # Handle both 0 and 1 indices
            final_nodes = []
            for final_idx in [0, 1]:
                children = WebDriverWait(current_node, 10).until(
                    lambda e: e.find_elements(By.XPATH, "./*")
                )
                final_nodes.append(children[final_idx])
            
            # Collect bdi elements
            for node in final_nodes:
                bdi_element = WebDriverWait(node, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "bdi"))
                )
                all_bdi_contents.append(bdi_element.get_attribute("innerHTML"))
                
        except Exception as e:
            print(f"Error processing block: {str(e)}")
            continue
    
    # Save results
    with open("bdi_contents.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_bdi_contents))
    print(f"Saved {len(all_bdi_contents)} bdi elements")

finally:
    driver.quit()