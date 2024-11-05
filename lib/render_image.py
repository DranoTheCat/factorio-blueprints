import asyncio
import sys
import base64
import re
from playwright.async_api import async_playwright

async def render_image(blueprint_string: str, output_path: str = "output_image.png"):
    """
    Automates a headless browser to navigate to a specified URL, paste an input string,
    wait for processing to complete, capture an image, and save it locally.

    Args:
        blueprint_string (str): The input string to paste into the webpage.
        output_path (str): The file path where the captured image will be saved.
    """
    async with async_playwright() as p:
        # Launch Chromium browser in headless mode with no-sandbox argument
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to the specified URL
        target_url = "https://storage.googleapis.com/factorio-blueprints-assets/fbe/index.html"
        print(f"Navigating to {target_url}...")
        await page.goto(target_url)
        
        # Wait for the page to load completely by checking window.app_loaded
        print("Waiting for the page to fully load...")
        try:
            await page.wait_for_function("window.app_loaded === true", timeout=30000)  # 30 seconds timeout
            print("Page loaded successfully.")
        except asyncio.TimeoutError:
            print("Timeout: The page did not load within the expected time.")
            await browser.close()
            sys.exit(1)

        # Paste the blueprint string into the page by invoking window.pasteBPString
        print("Pasting blueprint string into the page...")
        try:
            #print(f"Pasting blueprint string {blueprint_string}")
            await page.evaluate("window.pasteBPString", blueprint_string)
            print("Blueprint string pasted successfully.")
        except Exception as e:
            print(f"Not processing this file.  Error while pasting blueprint string: {e}")
            await browser.close()
            sys.exit(1)

        # Wait for processing to complete
        # This can be customized based on how the page indicates completion
        # For example, waiting for a specific element to appear/disappear
        # Here, we wait for window.savePicture to become available
        print("Waiting for processing to complete...")
        try:
            await page.wait_for_function("typeof window.savePicture === 'function'", timeout=60000)  # 60 seconds timeout
            print("Processing complete.")
        except asyncio.TimeoutError:
            print("Timeout: Processing did not complete within the expected time.")
            await browser.close()
            sys.exit(1)

        # Invoke window.savePicture and retrieve the image as a Data URL
        print("Retrieving image data from the page...")
        try:
            image_data_url = await page.evaluate("""
                () => window.savePicture().then(blob => {
                    return new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = () => resolve(reader.result);
                        reader.onerror = () => reject('Error reading blob');
                        reader.readAsDataURL(blob);
                    });
                })
            """)
            print("Image data retrieved successfully.")
        except Exception as e:
            print(f"Error while retrieving image data: {e}")
            await browser.close()
            sys.exit(1)

        # Extract base64 data from Data URL
        print("Processing image data...")
        match = re.match(r'data:(image/\w+);base64,(.*)', image_data_url)
        if not match:
            print("Failed to parse image data.")
            await browser.close()
            sys.exit(1)

        image_type = match.group(1).split('/')[1]  # e.g., 'png'
        image_base64 = match.group(2)
        image_binary = base64.b64decode(image_base64)

        # Save the image to the specified output path
        try:
            with open(output_path, "wb") as f:
                f.write(image_binary)
            print(f"Image saved to {output_path}.")
        except Exception as e:
            print(f"Error while saving image: {e}")
            await browser.close()
            sys.exit(1)

        # Close the browser
        await browser.close()
        print("Browser closed. Process completed successfully.")

def main():
    """
    Entry point for the script. Parses command-line arguments and invokes the render_image coroutine.
    """
    if len(sys.argv) < 2:
        print("Usage: python render_image.py <blueprint_string> [output_path]")
        sys.exit(1)
    
    blueprint_string = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output_image.png"

    asyncio.run(render_image(blueprint_string, output_path))

if __name__ == "__main__":
    main()

