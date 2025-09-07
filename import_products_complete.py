#!/usr/bin/env python3
"""
Complete Product Import Script
Fetches products from source API and creates them at destination API

Source: https://mososoup-api.onrender.com/api/products/
Destination: https://www.backend.musosoupcurator.com/api/products/

Usage: python3 import_products_complete.py
"""

import requests
import os
import time
import json

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# Source API endpoint to fetch products from
SOURCE_API_URL = "https://mososoup-api.onrender.com/api/products/"

# Destination API endpoint to create products
DESTINATION_API_URL = "https://www.backend.musosoupcurator.com/api/products/"

# Authentication tokens - UPDATE THESE!
SOURCE_AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3MDE4NjQ0LCJpYXQiOjE3NTcwMTczOTAsImp0aSI6ImFhZDRjMDJhZGEyZTQ5YTJhNjhiMGIxZjcwOGYyNDAxIiwidXNlcl9pZCI6MzMsInNpZCI6Ijc2YjJkMjhjLTc3YzktNGU0OC04ZmE4LTZjZWRkODZhNTQ1YSIsInN1cmYiOiJhZG1pbiJ9.HfrMLnWV_JkhGLZvUxWsxrWq5pzS_UF4J19JT-pmwHw"
DESTINATION_AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3MDE4NzMzLCJpYXQiOjE3NTcwMTc1MDcsImp0aSI6ImNjZDM1MTVlMDlkNzRmY2M4Y2VhNDMyYzNiNmExZmZmIiwidXNlcl9pZCI6MSwic2lkIjoiMjQ2NDMyNGEtMjJkOS00M2ZkLWIwZTUtODlhMjVkNzBkOTk2Iiwic3VyZiI6ImFkbWluIn0.CwlzjbVl3PqiQyxsRivneyixRGPKLdmXQK4nZxPKhkI"

# Delay between product creation requests (in seconds)
REQUEST_DELAY = 0.5

# Image download timeout (in seconds)
IMAGE_DOWNLOAD_TIMEOUT = 30

# ============================================================================
# FUNCTIONS
# ============================================================================

def download_image(image_url, product_name):
    """
    Download image from URL and return a temporary file path
    """
    try:
        print(f"📥 Downloading image for: {product_name}")
        
        # Add retry mechanism and better error handling
        for attempt in range(3):
            try:
                response = requests.get(
                    image_url, 
                    timeout=IMAGE_DOWNLOAD_TIMEOUT,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                )
                response.raise_for_status()
                break
            except requests.exceptions.ConnectionError as e:
                if "Failed to resolve" in str(e) or "nodename nor servname provided" in str(e):
                    print(f"🔄 DNS resolution failed, retrying... (attempt {attempt + 1}/3)")
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    raise e
            except requests.exceptions.Timeout:
                print(f"🔄 Timeout, retrying... (attempt {attempt + 1}/3)")
                time.sleep(2)
                continue
        else:
            raise Exception("Failed after 3 attempts")
        
        # Create a temporary file
        temp_filename = f"temp_{product_name.replace(' ', '_')}_{int(time.time())}.jpg"
        with open(temp_filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded image for: {product_name}")
        return temp_filename
    except Exception as e:
        print(f"❌ Failed to download image for {product_name}: {str(e)}")
        print(f"   URL: {image_url}")
        return None

def create_product(product_data, image_path, destination_url, auth_token):
    """
    Create a product at the destination API using formdata
    """
    try:
        # Prepare form data
        form_data = {
            'name': product_data['name'],
            'price': product_data['price']
        }
        
        # Make the API request to create product
        print(f"📤 Creating product at destination: {product_data['name']}")
        
        if image_path and os.path.exists(image_path):
            # Use multipart/form-data for file upload
            with open(image_path, 'rb') as img_file:
                files = {
                    'image': (f"{product_data['name'].replace(' ', '_')}.jpg", img_file, 'image/jpeg')
                }
                response = requests.post(
                    destination_url,
                    data=form_data,
                    files=files,
                    headers={'Authorization': f'Bearer {auth_token}'}
                )
        else:
            # Use form data without image
            response = requests.post(
                destination_url,
                data=form_data,
                headers={'Authorization': f'Bearer {auth_token}'}
            )
        
        if response.status_code in [200, 201]:
            result = response.json()
            if result.get('success'):
                print(f"✅ Created product: {product_data['name']} (${product_data['price']})")
                # Clean up temporary image file
                if image_path and os.path.exists(image_path):
                    os.unlink(image_path)
                return True
            else:
                print(f"❌ API returned error for {product_data['name']}: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code} for {product_data['name']}: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Failed to create product {product_data['name']}: {str(e)}")
        # Clean up temporary image file on error
        if image_path and os.path.exists(image_path):
            os.unlink(image_path)
        return False

def test_connections():
    """
    Test all connections before starting import
    """
    print("🧪 Testing Connections")
    print("=" * 50)
    
    # Test source auth token
    print("🔍 Testing source authentication token...")
    if SOURCE_AUTH_TOKEN == "YOUR_SOURCE_API_TOKEN_HERE":
        print("❌ Source Auth Token: Not configured! Please update SOURCE_AUTH_TOKEN in the script")
        return False
    else:
        print(f"✅ Source Auth Token: Configured ({SOURCE_AUTH_TOKEN[:20]}...)")
    
    # Test destination auth token
    print("🔍 Testing destination authentication token...")
    if DESTINATION_AUTH_TOKEN == "YOUR_DESTINATION_API_TOKEN_HERE":
        print("❌ Destination Auth Token: Not configured! Please update DESTINATION_AUTH_TOKEN in the script")
        return False
    else:
        print(f"✅ Destination Auth Token: Configured ({DESTINATION_AUTH_TOKEN[:20]}...)")
    
    # Test DNS resolution for Cloudinary
    print("🔍 Testing DNS resolution for Cloudinary...")
    try:
        import socket
        socket.gethostbyname('res.cloudinary.com')
        print("✅ Cloudinary DNS: Resolved successfully")
    except Exception as e:
        print(f"⚠️  Cloudinary DNS: Failed to resolve - {str(e)}")
        print("   This might cause image download issues")
    
    # Test source API
    print("🔍 Testing source API connection...")
    try:
        headers = {'Authorization': f'Bearer {SOURCE_AUTH_TOKEN}'} if SOURCE_AUTH_TOKEN != "YOUR_SOURCE_API_TOKEN_HERE" else {}
        response = requests.get(SOURCE_API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                products_count = len(data.get('data', []))
                print(f"✅ Source API: Connected successfully! Found {products_count} products")
            else:
                print(f"❌ Source API: API returned error: {data.get('message')}")
                return False
        else:
            print(f"❌ Source API: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Source API: Connection failed - {str(e)}")
        return False
    
    # Test destination API
    print("🔍 Testing destination API connection...")
    try:
        response = requests.get(DESTINATION_API_URL, timeout=10)
        if response.status_code in [200, 401, 403]:  # 401/403 means endpoint exists but needs auth
            print(f"✅ Destination API: Endpoint accessible!")
        else:
            print(f"❌ Destination API: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Destination API: Connection failed - {str(e)}")
        return False
    
    print("✅ All connection tests passed!")
    return True

def import_products():
    """
    Main function to import products from source API to destination API
    """
    print("🚀 Starting Product Import Process")
    print("=" * 60)
    
    # Validate configuration
    if SOURCE_AUTH_TOKEN == "YOUR_SOURCE_API_TOKEN_HERE":
        print("❌ ERROR: Please update the SOURCE_AUTH_TOKEN in the script!")
        print("   Replace 'YOUR_SOURCE_API_TOKEN_HERE' with your actual source API token")
        return
    
    if DESTINATION_AUTH_TOKEN == "YOUR_DESTINATION_API_TOKEN_HERE":
        print("❌ ERROR: Please update the DESTINATION_AUTH_TOKEN in the script!")
        print("   Replace 'YOUR_DESTINATION_API_TOKEN_HERE' with your actual destination API token")
        return
    
    print("🔧 Configuration:")
    print(f"   Source API: {SOURCE_API_URL}")
    print(f"   Destination API: {DESTINATION_API_URL}")
    print(f"   Source Token: {SOURCE_AUTH_TOKEN[:20]}..." if len(SOURCE_AUTH_TOKEN) > 20 else f"   Source Token: {SOURCE_AUTH_TOKEN}")
    print(f"   Destination Token: {DESTINATION_AUTH_TOKEN[:20]}..." if len(DESTINATION_AUTH_TOKEN) > 20 else f"   Destination Token: {DESTINATION_AUTH_TOKEN}")
    print("=" * 60)
    
    # Test connections first
    if not test_connections():
        print("❌ Connection tests failed. Please check your configuration.")
        return
    
    try:
        # Fetch products from source API
        print(f"\n📡 Fetching products from: {SOURCE_API_URL}")
        headers = {'Authorization': f'Bearer {SOURCE_AUTH_TOKEN}'}
        response = requests.get(SOURCE_API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('success'):
            print(f"✗ API request failed: {data.get('message', 'Unknown error')}")
            return
        
        products = data.get('data', [])
        print(f"📦 Found {len(products)} products to import")
        print("=" * 60)
        
        # Track statistics
        successful_imports = 0
        failed_imports = 0
        
        # Process each product
        for i, product_data in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}] Processing: {product_data['name']}")
            
            # Download image
            image_path = None
            if product_data.get('image'):
                image_path = download_image(product_data['image'], product_data['name'])
            
            # Create product at destination API
            if create_product(product_data, image_path, DESTINATION_API_URL, DESTINATION_AUTH_TOKEN):
                successful_imports += 1
            else:
                failed_imports += 1
            
            # Add small delay to avoid overwhelming the system
            time.sleep(REQUEST_DELAY)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 IMPORT SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully imported: {successful_imports}")
        print(f"❌ Failed: {failed_imports}")
        print(f"📦 Total processed: {len(products)}")
        
        if successful_imports > 0:
            print(f"\n🎉 Successfully imported {successful_imports} new products!")
        else:
            print("\nℹ️  No new products were imported.")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {str(e)}")
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")

def cleanup_temp_files():
    """
    Clean up any temporary files that might have been left behind
    """
    print("\n🧹 Cleaning up temporary files...")
    temp_files = [f for f in os.listdir('.') if f.startswith('temp_') and f.endswith('.jpg')]
    for temp_file in temp_files:
        try:
            os.unlink(temp_file)
            print(f"🗑️  Deleted: {temp_file}")
        except:
            pass

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    try:
        # Run the import
        import_products()
    finally:
        # Always cleanup temp files
        cleanup_temp_files()
    
    print("\n🏁 Script execution completed!")
    print("💡 You can now delete this script file if you want.")
