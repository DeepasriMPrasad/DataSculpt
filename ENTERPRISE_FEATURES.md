# Enterprise-Grade Web Crawling Features

CrawlOps Studio now includes enterprise-grade features inspired by AWS Bedrock Web Crawler specifications, bringing professional-level crawling capabilities to the platform.

## 🏢 AWS Bedrock-Inspired Features

### Scope Control (Enterprise URL Filtering)
- **Default**: Same host + same initial path (most restrictive)
  - Example: `https://aws.amazon.com/bedrock/` only crawls `/bedrock/*` paths
- **Host Only**: Same host, any path 
  - Example: `https://aws.amazon.com/bedrock/` crawls all `aws.amazon.com` paths
- **Subdomains**: Same primary domain including subdomains
  - Example: `https://aws.amazon.com/` crawls `docs.aws.amazon.com`, `console.aws.amazon.com`

### URL Pattern Filtering
- **Include Patterns**: Regex patterns for URLs to include
- **Exclude Patterns**: Regex patterns for URLs to exclude (takes precedence)
- **Pattern Examples**:
  - Include only documentation: `.*docs.*`, `.*documentation.*`
  - Exclude API endpoints: `.*api.*`, `.*json.*`
  - Exclude media files: `.*\.(jpg|png|mp4|pdf)$`

### Rate Limiting & Control
- **URLs per Host per Minute**: Configurable rate limiting (default: 60/min)
- **Maximum Pages**: Up to 25,000 pages per crawl (AWS Bedrock limit)
- **Intelligent Queue Management**: Prevents runaway crawling

### Robots.txt Compliance
- **RFC 9309 Standard**: Full compliance with robots.txt directives
- **User-Agent Support**: Custom user agent with configurable suffix
- **Allow/Disallow Rules**: Respects standard robots.txt patterns
- **Fallback Behavior**: Allow crawling if robots.txt not found

### Enhanced File Type Filtering
- **Static Website Focus**: Optimized for static content crawling
- **Binary File Exclusion**: Automatically excludes PDFs, executables, media files
- **Supported Content**: HTML, text, JSON-LD, structured data

## 🛠️ API Usage Examples

### Basic Enterprise Crawl
```json
{
  "url": "https://example.com/docs/",
  "max_depth": 2,
  "max_pages": 50,
  "scope": "default",
  "respect_robots_txt": true,
  "user_agent_suffix": "CrawlOps-Enterprise/1.0"
}
```

### Advanced Filtering
```json
{
  "url": "https://company.com/",
  "max_depth": 3,
  "max_pages": 100,
  "scope": "host_only",
  "include_patterns": [".*docs.*", ".*help.*"],
  "exclude_patterns": [".*api.*", ".*admin.*"],
  "max_urls_per_host_per_minute": 30,
  "respect_robots_txt": true
}
```

### Subdomain Crawling
```json
{
  "url": "https://main.example.com/",
  "max_depth": 2,
  "max_pages": 200,
  "scope": "subdomains",
  "exclude_patterns": [".*\.(pdf|zip|exe)$"],
  "max_urls_per_host_per_minute": 45
}
```

## 📊 Enterprise Benefits

### Scalability
- Handles large-scale crawling operations up to 25,000 pages
- Intelligent rate limiting prevents server overload
- Memory-efficient queue management

### Compliance
- RFC 9309 robots.txt compliance for legal crawling
- Configurable user agent identification
- Respect for website crawling policies

### Precision
- Fine-grained scope control prevents scope creep
- Regex-based URL filtering for targeted crawling
- Enterprise-grade pattern matching

### Reliability
- Comprehensive error handling and fallback mechanisms
- Detailed logging for audit trails
- Professional-grade crawling behavior

## 🚀 Use Cases

### Corporate Documentation
- Crawl internal knowledge bases with path restrictions
- Extract documentation while respecting robots.txt
- Filter out non-documentation content

### Competitor Analysis
- Focused crawling of specific website sections
- Rate-limited crawling to avoid detection
- Subdomain discovery and crawling

### Content Auditing
- Large-scale website content extraction
- Pattern-based content filtering
- Compliance with crawling policies

### Research & Intelligence
- Targeted data collection with precise scope control
- Professional crawling with proper identification
- Scalable extraction for analysis pipelines

---

*These enterprise features bring CrawlOps Studio to professional-grade standards, matching the capabilities of cloud-based crawling services like AWS Bedrock Web Crawler.*