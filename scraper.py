"""
Madam Coco Ürün Çekme Scripti
Selenium ile tüm ürünleri çeker ve CSV'ye kaydeder
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from datetime import datetime
import os
import re

class MadamCocoScraper:
    def __init__(self):
        """Selenium başlat"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.products = []
    
    def scrape_category(self, category_url, max_pages=100):
        """Kategoriden ürünleri çek - otomatik tüm sayfalar"""
        print(f"\n🔍 Kategori taranıyor: {category_url}")
        
        page = 1
        consecutive_empty = 0
        
        while page <= max_pages:
            url = f"{category_url}?page={page}"
            print(f"\n📄 Sayfa {page} çekiliyor...")
            
            try:
                self.driver.get(url)
                time.sleep(3)
                
                prev_count = len(self.products)
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                products_found = self.extract_products()
                
                if len(self.products) == prev_count:
                    consecutive_empty += 1
                    print(f"⚠️ Bu sayfada yeni ürün yok ({consecutive_empty}/2)")
                    
                    if consecutive_empty >= 2:
                        print(f"✅ Son sayfa tespit edildi, durduruluyor")
                        break
                else:
                    consecutive_empty = 0
                    new_products = len(self.products) - prev_count
                    print(f"✅ {new_products} yeni ürün eklendi (Toplam: {len(self.products)})")
                
                page += 1
                
            except Exception as e:
                print(f"❌ Sayfa {page} hatası: {e}")
                break
        
        print(f"\n🎉 TAMAMLANDI! Toplam {len(self.products)} ürün çekildi!")
    
    def extract_products(self):
        """Sayfadaki ürünleri çıkar"""
        found = []
        
        selectors = [
            "div.product-item",
            "div.product-card",
            "article.product",
            "div[data-product-id]",
            ".product",
            "a.product-link"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"📦 {len(elements)} ürün kartı bulundu ({selector})")
                    
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
            name = None
            name_selectors = ["h3", "h2", "h4", ".product-name", ".product-title", "a.product-link", ".title"]
            for sel in name_selectors:
                try:
                    name_elem = element.find_element(By.CSS_SELECTOR, sel)
                    name = name_elem.text.strip()
                    if name:
                        break
                except:
                    continue
            
            old_price = None
            old_price_selectors = [
                ".old-price",
                ".price-old",
                "del",
                "s",
                "span[class*='old']",
                "div[class*='old']"
            ]
            for sel in old_price_selectors:
                try:
                    old_price_elem = element.find_element(By.CSS_SELECTOR, sel)
                    old_price_text = old_price_elem.text
                    old_price = self.parse_price(old_price_text)
                    if old_price:
                        break
                except:
                    continue
            
            new_price = None
            new_price_selectors = [
                ".price", 
                ".product-price", 
                "span.price-value", 
                ".sales-price",
                ".sale-price",
                ".amount",
                "span[class*='price']",
                "div[class*='price']"
            ]
            for sel in new_price_selectors:
                try:
                    new_price_elem = element.find_element(By.CSS_SELECTOR, sel)
                    new_price_text = new_price_elem.text
                    new_price = self.parse_price(new_price_text)
                    if new_price:
                        break
                except:
                    continue
            
            discount = None
            discount_selectors = [
                ".discount",
                ".badge-discount",
                ".percent",
                "span[class*='discount']",
                "div[class*='discount']",
                "span[class*='percent']"
            ]
            for sel in discount_selectors:
                try:
                    discount_elem = element.find_element(By.CSS_SELECTOR, sel)
                    discount_text = discount_elem.text
                    discount_match = re.search(r'(\d+)', discount_text)
                    if discount_match:
                        discount = int(discount_match.group(1))
                        break
                except:
                    continue
            
            if not discount and old_price and new_price and old_price > new_price:
                discount = int(((old_price - new_price) / old_price) * 100)
            
            stock_status = "Stokta Var"
            stock_selectors = [
                ".out-of-stock",
                ".stock-out",
                ".sold-out",
                "span[class*='stock']",
                "div[class*='stock']"
            ]
            for sel in stock_selectors:
                try:
                    stock_elem = element.find_element(By.CSS_SELECTOR, sel)
                    stock_text = stock_elem.text.lower()
                    if "tükendi" in stock_text or "yok" in stock_text or "out" in stock_text:
                        stock_status = "Tükendi"
                        break
                except:
                    continue
            
            link = None
            try:
                link_elem = element.find_element(By.TAG_NAME, "a")
                link = link_elem.get_attribute("href")
            except:
                pass
            
            image = None
            try:
                img = element.find_element(By.TAG_NAME, "img")
                image = img.get_attribute("src") or img.get_attribute("data-src") or img.get_attribute("data-lazy-src")
            except:
                pass
            
            if name and (new_price or old_price):
                return {
                    'Ürün Adı': name,
                    'Eski Fiyat': old_price if old_price else new_price,
                    'İndirim Oranı': f"%{discount}" if discount else "-",
                    'Yeni Fiyat': new_price if new_price else old_price,
                    'Stok Durumu': stock_status,
                    'Link': link,
                    'Görsel': image,
                    'Tarih': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        except Exception as e:
            pass
        
        return None
    
    def parse_price(self, price_text):
        """Fiyatı sayıya çevir"""
        if not price_text:
            return None
        
        numbers = re.findall(r'\d+', price_text)
        
        if not numbers:
            return None
        
        try:
            if len(numbers) == 1:
                price = float(numbers[0])
            elif len(numbers) == 2:
                price = float(f"{numbers[0]}.{numbers[1]}")
            elif len(numbers) >= 3:
                if len(numbers[0]) <= 2:
                    price = float(f"{numbers[0]}{numbers[1]}.{numbers[2]}")
                else:
                    price = float(f"{numbers[0]}.{numbers[1]}")
            else:
                return None
            
            if price > 100000:
                return None
            
            return price
        except:
            return None
    
    def save_to_csv(self, filename='output/madamcoco_products.csv'):
        """CSV'ye kaydet"""
        if not self.products:
            print("⚠️ Kaydedilecek ürün yok!")
            return
        
        df = pd.DataFrame(self.products)
        
        os.makedirs('output', exist_ok=True)
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 {len(self.products)} ürün kaydedildi: {filename}")
        
        print(f"\n📊 İlk 10 ürün:")
        print(df.head(10))
        
        print(f"\n📈 Özet İstatistikler:")
        print(f"   • Toplam Ürün: {len(df)}")
        print(f"   • İndirimli Ürün: {len(df[df['İndirim Oranı'] != '-'])}")
        print(f"   • Ortalama Fiyat: {df['Yeni Fiyat'].mean():.2f} TL")
        print(f"   • En Ucuz: {df['Yeni Fiyat'].min():.2f} TL")
        print(f"   • En Pahalı: {df['Yeni Fiyat'].max():.2f} TL")
    
    def close(self):
        """Tarayıcıyı kapat"""
        self.driver.quit()


if __name__ == "__main__":
    print("=" * 60)
    print("🛍️  MADAM COCO SCRAPER - TÜM ÜRÜNLER")
    print("=" * 60)
    
    scraper = MadamCocoScraper()
    
    categories = [
        "https://www.madamecoco.com/nevresim-takimi/"
    ]
    
    for category in categories:
        scraper.scrape_category(category, max_pages=100)
    
    scraper.save_to_csv()
    
    scraper.close()
    
    print("\n✅ İşlem tamamlandı!")
    print("📁 Dosya: output/madamcoco_products.csv")
    print("=" * 60)
