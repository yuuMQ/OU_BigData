import scrapy
from urllib.parse import urlparse, urlunparse
import re
class OuDataCrawlingSpider(scrapy.Spider):
    name = "ou_data_crawling"
    allowed_domains = ["ou.edu.vn"]
    start_urls = ["https://ou.edu.vn/"]


    def clean_url(self, url):
        parsed_url = urlparse(url)
        return urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))

    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([,.!?;])', r'\1', text)
        return text.strip()

    def parse(self, response):
        content_type = response.headers.get(b'Content-Type', b'').decode(errors='ignore').lower()
        if 'text/html' not in content_type:
            return

        depth = response.meta.get('depth', 0)  # Lấy độ sâu của hyperlink

        for a_tag in response.css('a'):
            if a_tag.css('img'):
                continue

            link = a_tag.attrib.get('href', '').strip()
            if not link or link.startswith(('javascript:', '#', 'mailto:', 'tel:', 'ftp')):
                continue

            url = self.clean_url(response.urljoin(link))
            title = self.clean_text(' '.join(a_tag.css('*::text').getall()))
            if depth > 0:
                content_paragraphs = response.css('div.content p::text').getall()
                content_title = response.css('div.content h3.title::text').getall()
                content_data = ' '.join(p.strip() for p in content_paragraphs if p.strip())
                content_title = ' '.join(p.strip() for p in content_title if p.strip())
                content = content_title + " " + content_data
            else:
                content = title

            if not content.strip():
                content = title
            content = self.clean_text(content)
            yield {
                'url': url,
                'title': title,
                'content': content,
                'hyperlink_level': depth
            }

            if any(url.startswith(f"http://{domain}") or url.startswith(f"https://{domain}")
                   for domain in self.allowed_domains):
                yield response.follow(url, callback=self.parse, meta={'depth': depth + 1})
