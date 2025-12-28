"""
Madam Coco Ürün Çekme Scripti
Selenium ile tüm ürünleri çeker ve CSV'ye kaydeder
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from datetime import datetime

class MadamCocoScraper:
    def __init__(self):
        """Selenium başlat"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.binary_location = '/usr/bin/chromium-browser'  # Ubuntu'da Chromium
    
    from selenium.webdriver.chrome.service import Service
    service = Service('/usr/bin/chromedriver')
    
    self.driver = webdriver.Chrome(service=service, options=options)
        
        self.driver = webdriver.Chrome(options=options)
        self.products = []
    
    def scrape_category(self, category_url, max_pages=5):
        """Kategoriden ürünleri çek"""
        print(f"\n🔍 Kategori taranıyor: {category_url}")
        
        for page in range(1, max_pages + 1):
            url = f"{category_url}?page={page}"
            print(f"\n📄 Sayfa {page} çekiliyor...")
            
            try:
                self.driver.get(url)
                time.sleep(3)  # Sayfa yüklensin
                
                # Scroll down - lazy loading için
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Ürün kartlarını bul
                products_found = self.extract_products()
                
                if not products_found:
                    print(f"⚠️ Sayfa {page}'de ürün bulunamadı, durduruluyor")
                    break
                
                print(f"✅ {len(products_found)} ürün çekildi")
                
            except Exception as e:
                print(f"❌ Sayfa {page} hatası: {e}")
                break
        
        print(f"\n🎉 Toplam {len(self.products)} ürün çekildi!")
    
    def extract_products(self):
        """Sayfadaki ürünleri çıkar"""
        found = []
        
        # Farklı CSS selector'ları dene
        selectors = [
            "div.product-item",
            "div.product-card", 
            "article.product",
            "div[data-product-id]",
            ".product",
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"📦 {len(elements)} ürün bulundu ({selector})")
                    
                    for element in elements:
                        product = self.parse_product(element)
                        if product:
                            self.products.append(product)
                            found.append(product)
                    
                    return found
            except:
                continue
        
        return found
    
    def parse_product(self, element):
        """Tek ürünü parse et"""
        try:
            # Ürün adı
            name = None
            name_selectors = ["h3", "h2", ".product-name", ".product-title", "a"]
            for sel in name_selectors:
                try:
                    name = element.find_element(By.CSS_SELECTOR, sel).text.strip()
                    if name:
                        break
                except:
                    continue
            
            # Fiyat
            price = None
            price_selectors = [".price", ".product-price", "span.price-value"]
            for sel in price_selectors:
                try:
                    price_text = element.find_element(By.CSS_SELECTOR, sel).text
                    price = self.parse_price(price_text)
                    if price:
                        break
                except:
                    continue
            
            # Link
            link = None
            try:
                link = element.find_element(By.TAG_NAME, "a").get_attribute("href")
            except:
                pass
            
            # Görsel
            image = None
            try:
                img = element.find_element(By.TAG_NAME, "img")
                image = img.get_attribute("src") or img.get_attribute("data-src")
            except:
                pass
            
            if name and price:
                return {
                    'Ürün Adı': name,
                    'Fiyat': price,
                    'Link': link,
                    'Görsel': image,
                    'Tarih': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        except Exception as e:
            pass
        
        return None
    
    def parse_price(self, price_text):
        """Fiyatı sayıya çevir"""
        import re
        if not price_text:
            return None
        
        # Sadece rakam ve virgül/nokta
        clean = re.sub(r'[^\d,.]', '', price_text)
        clean = clean.replace('.', '').replace(',', '.')
        
        try:
            return float(clean)
        except:
            return None
    
    def save_to_csv(self, filename='output/madamcoco_products.csv'):
        """CSV'ye kaydet"""
        if not self.products:
            print("⚠️ Kaydedilecek ürün yok!")
            return
        
        df = pd.DataFrame(self.products)
        
        # Klasör yoksa oluştur
        import os
        os.makedirs('output', exist_ok=True)
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 {len(self.products)} ürün kaydedildi: {filename}")
        
        # Önizleme
        print(f"\n📊 İlk 5 ürün:")
        print(df.head())
    
    def close(self):
        """Tarayıcıyı kapat"""
        self.driver.quit()


# KULLANIM
if __name__ == "__main__":
    print("🛍️ MADAM COCO SCRAPER")
    print("=" * 50)
    
    scraper = MadamCocoScraper()
    
    # Kategoriler
    categories = [
        "https://www.madamcoco.com.tr/ev-tekstili",
        # Buraya daha fazla kategori ekleyebilirsiniz
    ]
    
    for category in categories:
        scraper.scrape_category(category, max_pages=3)
    
    # CSV'ye kaydet
    scraper.save_to_csv()
    
    scraper.close()
    
    print("\n✅ İşlem tamamlandı!")
