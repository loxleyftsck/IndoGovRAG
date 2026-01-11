"""
ScrapingBee-based Document Scraper
Production-grade scraper using ScrapingBee API for 99%+ success rate

Features:
- Anti-bot bypass (handles JavaScript, CAPTCHA)
- 1000 free credits/month
- Geolocation support
- Custom headers
- JSON output
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class ScrapingBeeDocumentScraper:
    """
    Production scraper using ScrapingBee API
    
    Free tier: 1000 API credits/month
    Success rate: 99%+
    """
    
    def __init__(self, api_key: str):
        """
        Initialize scraper
        
        Args:
            api_key: ScrapingBee API key (get from https://scrapingbee.com)
        """
        self.api_key = api_key
        self.base_url = "https://app.scrapingbee.com/api/v1/"
        self.session = requests.Session()
        
    def scrape_url(
        self, 
        url: str,
        render_js: bool = True,
        premium_proxy: bool = False,
        country_code: str = "id"
    ) -> Optional[Dict]:
        """
        Scrape single URL with ScrapingBee
        
        Args:
            url: URL to scrape
            render_js: Execute JavaScript (needed for dynamic sites)
            premium_proxy: Use premium proxy (costs 10x credits)
            country_code: Geolocation (default: Indonesia)
            
        Returns:
            Dict with url, title, content, metadata
        """
        params = {
            "api_key": self.api_key,
            "url": url,
            "render_js": str(render_js).lower(),
            "country_code": country_code,
            "return_page_source": "true"
        }
        
        if premium_proxy:
            params["premium_proxy"] = "true"
        
        try:
            print(f"📡 Scraping: {url[:60]}...")
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                # Extract text content
                html = response.text
                
                # Simple title extraction
                title = self._extract_title(html, url)
                
                # Extract main content
                content = self._extract_content(html)
                
                # Get credit usage
                credits_used = response.headers.get('Spb-Cost', '1')
                
                result = {
                    "url": url,
                    "title": title,
                    "content": content,
                    "scraped_at": datetime.now().isoformat(),
                    "success": True,
                    "credits_used": int(credits_used),
                    "metadata": {
                        "render_js": render_js,
                        "country_code": country_code
                    }
                }
                
                print(f"✅ Success! ({len(content)} chars, {credits_used} credits)")
                return result
                
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                return {
                    "url": url,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "credits_used": 0
                }
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "url": url,
                "success": False,
                "error": str(e),
                "credits_used": 0
            }
    
    def _extract_title(self, html: str, url: str) -> str:
        """Extract title from HTML"""
        import re
        
        # Try <title> tag
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        
        # Try <h1> tag
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # Fallback to URL
        return url.split('/')[-1] or url
    
    def _extract_content(self, html: str) -> str:
        """Extract main content from HTML"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def scrape_batch(
        self,
        urls: List[str],
        output_file: str,
        delay: float = 2.0,
        render_js: bool = True
    ) -> Dict:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of URLs to scrape
            output_file: JSON file to save results
            delay: Delay between requests (seconds)
            render_js: Execute JavaScript
            
        Returns:
            Dict with stats and results
        """
        results = []
        stats = {
            "total_urls": len(urls),
            "successful": 0,
            "failed": 0,
            "total_credits": 0,
            "total_content_size": 0
        }
        
        print("="*60)
        print(f"🕷️  ScrapingBee Batch Scraper")
        print("="*60)
        print(f"URLs to scrape: {len(urls)}")
        print(f"JavaScript rendering: {render_js}")
        print(f"Delay: {delay}s\n")
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]", end=" ")
            
            result = self.scrape_url(url, render_js=render_js)
            results.append(result)
            
            if result.get('success'):
                stats['successful'] += 1
                stats['total_credits'] += result.get('credits_used', 0)
                stats['total_content_size'] += len(result.get('content', ''))
            else:
                stats['failed'] += 1
            
            # Rate limiting
            if i < len(urls):
                time.sleep(delay)
        
        # Save results
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        print(f"Total URLs: {stats['total_urls']}")
        print(f"Successful: {stats['successful']} ({stats['successful']/stats['total_urls']*100:.1f}%)")
        print(f"Failed: {stats['failed']}")
        print(f"Total credits used: {stats['total_credits']}")
        print(f"Total content: {stats['total_content_size']/1024:.1f}KB")
        print(f"\n✅ Results saved to: {output_path}")
        print("="*60 + "\n")
        
        return stats


def main():
    """Example usage"""
    
    # Get API key from user
    print("="*60)
    print("🕷️  ScrapingBee Document Scraper")
    print("="*60)
    print("\nTo use this scraper:")
    print("1. Sign up at https://scrapingbee.com (FREE)")
    print("2. Get your API key from dashboard")
    print("3. Free tier: 1000 credits/month\n")
    
    api_key = input("Enter your ScrapingBee API key (or 'demo' to see example): ").strip()
    
    if api_key.lower() == 'demo':
        print("\n📚 Example output structure:")
        print(json.dumps({
            "url": "https://example.go.id/page",
            "title": "Document Title",
            "content": "Full text content...",
            "success": True,
            "credits_used": 1
        }, indent=2))
        return
    
    # Priority URLs that failed with Jina/Playwright
    priority_urls = [
        "https://disdukcapil.jakarta.go.id/layanan/pembuatan-sim",
        "https://jdih.setkab.go.id/PUUdoc/176231/UU_Nomor_24_Tahun_2013.pdf",
        "https://jakarta.go.id/pelayanan/akta-kelahiran",
        # Add more...
    ]
    
    # Initialize scraper
    scraper = ScrapingBeeDocumentScraper(api_key=api_key)
    
    # Test single URL first
    print(f"\n🧪 Testing with first URL...")
    result = scraper.scrape_url(priority_urls[0])
    
    if result.get('success'):
        print(f"\n✅ Test successful! Ready to scrape all {len(priority_urls)} URLs")
        
        # Ask to proceed
        proceed = input(f"\nScrape all {len(priority_urls)} URLs? (y/n): ").strip().lower()
        
        if proceed == 'y':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/scraped/scrapingbee_{timestamp}.json"
            
            stats = scraper.scrape_batch(
                urls=priority_urls,
                output_file=output_file,
                delay=2.0
            )
            
            print(f"\n🎉 Scraping complete!")
            print(f"Next step: Categorize and ingest documents")
        else:
            print("Cancelled.")
    else:
        print("\n❌ Test failed. Check your API key and try again.")


if __name__ == "__main__":
    main()
