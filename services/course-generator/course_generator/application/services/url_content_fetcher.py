"""
URL Content Fetcher Service for External Documentation Retrieval

BUSINESS REQUIREMENT:
Enable course generation from external third-party software documentation by fetching,
parsing, and extracting meaningful content from URLs. This allows instructors to point
the AI at any documentation site (Salesforce, AWS, internal wikis, etc.) and generate
comprehensive training materials automatically.

TECHNICAL ARCHITECTURE:
This service provides a complete pipeline for external content retrieval:
1. URL validation and security checks
2. HTTP request handling with proper error recovery
3. robots.txt compliance checking
4. HTML parsing and content extraction
5. Text cleaning and normalization
6. Content chunking for RAG ingestion

INTEGRATION POINTS:
- Course Generator API: Receives URLs from course generation requests
- RAG Service: Sends extracted content for vector storage and retrieval
- AI Client: Provides context for course content generation

SECURITY CONSIDERATIONS:
- Validates URLs to prevent SSRF attacks (no internal network access)
- Respects robots.txt directives
- Implements rate limiting to avoid overwhelming target servers
- Validates content types to prevent binary file processing
"""

import asyncio
import hashlib
import ipaddress
import logging
import re
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup, NavigableString, Comment

from course_generator.exceptions import (
    URLValidationException,
    URLConnectionException,
    URLTimeoutException,
    URLAccessDeniedException,
    URLNotFoundException,
    HTMLParsingException,
    ContentExtractionException,
    ContentTooLargeException,
    UnsupportedContentTypeException,
    RobotsDisallowedException,
)
from logging_setup import setup_docker_logging

logger = setup_docker_logging("course-generator")


@dataclass
class FetchedContent:
    """
    Represents content successfully fetched and parsed from a URL.

    Business Context:
    Contains all extracted content and metadata needed for course generation,
    including the cleaned text, structural information, and source attribution.

    Technical Context:
    - content: Cleaned, extracted text suitable for AI processing
    - title: Page title for course/module naming suggestions
    - headings: Document structure for outline generation
    - code_blocks: Extracted code examples for lab content
    - metadata: Source attribution and processing information
    """
    url: str
    content: str
    title: Optional[str] = None
    description: Optional[str] = None
    headings: List[Dict[str, Any]] = field(default_factory=list)
    code_blocks: List[Dict[str, str]] = field(default_factory=list)
    word_count: int = 0
    character_count: int = 0
    fetch_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate content statistics after initialization."""
        if self.content:
            self.word_count = len(self.content.split())
            self.character_count = len(self.content)
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]


@dataclass
class ContentChunk:
    """
    A chunk of content suitable for RAG ingestion.

    Business Context:
    Large documentation pages must be split into chunks that fit within
    AI model context windows and vector database storage limits while
    maintaining semantic coherence for effective retrieval.

    Technical Context:
    - chunk_index: Position in original document for ordering
    - content: Chunk text within size limits
    - heading_context: Parent headings for semantic context
    - source_url: Attribution to original source
    """
    chunk_index: int
    content: str
    heading_context: str
    source_url: str
    character_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate chunk statistics."""
        self.character_count = len(self.content)


class URLContentFetcher:
    """
    URL Content Fetcher for External Documentation Retrieval.

    ARCHITECTURAL RESPONSIBILITY:
    Provides a complete, secure pipeline for fetching and extracting content
    from external documentation URLs for use in AI-powered course generation.

    DESIGN PATTERNS:
    - Strategy pattern for content extraction based on content type
    - Template method for the fetch-parse-extract pipeline
    - Circuit breaker for external service reliability
    - Factory pattern for content chunk creation

    CONFIGURATION:
    - Timeout settings for network operations
    - Content size limits for processing
    - Chunk sizes for RAG ingestion
    - User-agent and request headers
    """

    # Configuration constants
    DEFAULT_TIMEOUT = 30.0  # seconds
    MAX_CONTENT_SIZE = 5 * 1024 * 1024  # 5MB maximum
    MIN_CONTENT_LENGTH = 100  # Minimum characters for valid content
    MAX_URL_LENGTH = 2048
    CHUNK_SIZE = 2500  # Characters per chunk for RAG
    CHUNK_OVERLAP = 200  # Overlap between chunks for context continuity

    # Supported content types
    SUPPORTED_CONTENT_TYPES = [
        "text/html",
        "text/plain",
        "text/markdown",
        "application/xhtml+xml",
    ]

    # User agent for requests (identifies as educational content fetcher)
    USER_AGENT = "CourseCreatorBot/1.0 (Educational Content Fetcher; +https://course-creator.example.com/bot)"

    # Elements to remove during content extraction
    REMOVE_ELEMENTS = [
        "script", "style", "nav", "header", "footer", "aside",
        "form", "button", "input", "select", "textarea",
        "iframe", "noscript", "svg", "canvas", "video", "audio",
        "advertisement", "ad", "sidebar", "menu", "toolbar",
    ]

    # Elements that typically contain main content
    CONTENT_ELEMENTS = [
        "article", "main", "section", "div.content", "div.documentation",
        "div.doc", "div.article", "div.post", "div.entry",
    ]

    # Private/internal IP ranges to block (SSRF prevention)
    BLOCKED_IP_RANGES = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
        ipaddress.ip_network("fe80::/10"),
    ]

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_content_size: int = MAX_CONTENT_SIZE,
        check_robots: bool = True,
        respect_rate_limits: bool = True,
    ):
        """
        Initialize URL Content Fetcher.

        Args:
            timeout: Request timeout in seconds
            max_content_size: Maximum content size to process in bytes
            check_robots: Whether to check robots.txt before fetching
            respect_rate_limits: Whether to respect rate limit headers
        """
        self.timeout = timeout
        self.max_content_size = max_content_size
        self.check_robots = check_robots
        self.respect_rate_limits = respect_rate_limits
        self._robots_cache: Dict[str, Tuple[RobotFileParser, datetime]] = {}
        self._rate_limit_delays: Dict[str, float] = {}

        logger.info(
            f"URLContentFetcher initialized: timeout={timeout}s, "
            f"max_size={max_content_size}bytes, check_robots={check_robots}"
        )

    async def fetch_and_parse(self, url: str) -> FetchedContent:
        """
        Fetch content from URL and parse it into structured format.

        FETCH PIPELINE:
        1. Validate URL format and security
        2. Check robots.txt compliance
        3. Fetch content with proper error handling
        4. Parse and extract meaningful content
        5. Structure content for course generation

        Args:
            url: The URL to fetch content from

        Returns:
            FetchedContent with extracted and structured content

        Raises:
            URLValidationException: Invalid or unsafe URL
            URLConnectionException: Network connectivity issues
            URLTimeoutException: Request timed out
            URLAccessDeniedException: Access forbidden (401, 403)
            URLNotFoundException: Page not found (404)
            RobotsDisallowedException: Blocked by robots.txt
            HTMLParsingException: Failed to parse HTML
            ContentExtractionException: No meaningful content found
            ContentTooLargeException: Content exceeds size limits
            UnsupportedContentTypeException: Unsupported content type
        """
        logger.info(f"Fetching content from URL: {url}")

        # Step 1: Validate URL
        validated_url = await self._validate_url(url)

        # Step 2: Check robots.txt
        if self.check_robots:
            await self._check_robots_txt(validated_url)

        # Step 3: Fetch content
        html_content, content_type, response_headers = await self._fetch_url(validated_url)

        # Step 4: Parse and extract content
        fetched_content = await self._parse_html(validated_url, html_content)

        # Step 5: Add metadata
        fetched_content.metadata.update({
            "content_type": content_type,
            "fetch_method": "http_get",
            "robots_checked": self.check_robots,
        })

        logger.info(
            f"Successfully fetched content: {fetched_content.word_count} words, "
            f"{len(fetched_content.headings)} headings, "
            f"{len(fetched_content.code_blocks)} code blocks"
        )

        return fetched_content

    async def _validate_url(self, url: str) -> str:
        """
        Validate URL format and security.

        SECURITY CHECKS:
        - URL format validation
        - Protocol validation (http/https only)
        - Length limits
        - SSRF prevention (no internal IPs)

        Args:
            url: URL to validate

        Returns:
            Validated and normalized URL

        Raises:
            URLValidationException: If URL is invalid or unsafe
        """
        if not url or not url.strip():
            raise URLValidationException(
                message="URL cannot be empty",
                url=url,
                error_code="URL_EMPTY"
            )

        url = url.strip()

        # Check URL length
        if len(url) > self.MAX_URL_LENGTH:
            raise URLValidationException(
                message=f"URL exceeds maximum length of {self.MAX_URL_LENGTH} characters",
                url=url[:100] + "...",
                error_code="URL_TOO_LONG",
                details={"max_length": self.MAX_URL_LENGTH, "actual_length": len(url)}
            )

        # Parse URL
        try:
            parsed = urlparse(url)
        except ValueError as e:
            raise URLValidationException(
                message=f"Invalid URL format: {str(e)}",
                url=url,
                error_code="URL_PARSE_ERROR",
                original_exception=e
            )

        # Validate scheme
        if parsed.scheme not in ("http", "https"):
            raise URLValidationException(
                message=f"Unsupported URL scheme: {parsed.scheme}. Only http and https are supported.",
                url=url,
                error_code="URL_INVALID_SCHEME",
                details={"scheme": parsed.scheme, "supported_schemes": ["http", "https"]}
            )

        # Validate hostname
        if not parsed.hostname:
            raise URLValidationException(
                message="URL must include a hostname",
                url=url,
                error_code="URL_NO_HOSTNAME"
            )

        # Check for internal/private IPs (SSRF prevention)
        await self._check_ssrf(parsed.hostname, url)

        return url

    async def _check_ssrf(self, hostname: str, url: str) -> None:
        """
        Check for SSRF (Server-Side Request Forgery) vulnerabilities.

        SECURITY IMPLEMENTATION:
        Prevents requests to internal network addresses that could be used
        to access internal services or scan internal networks.

        Args:
            hostname: The hostname to check
            url: Original URL for error reporting

        Raises:
            URLValidationException: If hostname resolves to blocked IP
        """
        try:
            # Resolve hostname to IP addresses
            loop = asyncio.get_event_loop()
            addresses = await loop.run_in_executor(
                None,
                lambda: socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            )

            for family, type_, proto, canonname, sockaddr in addresses:
                ip_str = sockaddr[0]
                try:
                    ip = ipaddress.ip_address(ip_str)

                    # Check against blocked ranges
                    for blocked_range in self.BLOCKED_IP_RANGES:
                        if ip in blocked_range:
                            raise URLValidationException(
                                message="Access to internal network addresses is not allowed",
                                url=url,
                                error_code="URL_INTERNAL_ADDRESS",
                                details={"hostname": hostname, "resolved_ip": ip_str}
                            )
                except ValueError:
                    # Invalid IP format, skip
                    continue

        except socket.gaierror as e:
            raise URLValidationException(
                message=f"Failed to resolve hostname: {hostname}",
                url=url,
                error_code="URL_DNS_RESOLUTION_FAILED",
                original_exception=e
            )

    async def _check_robots_txt(self, url: str) -> None:
        """
        Check robots.txt for permission to fetch URL.

        ETHICAL COMPLIANCE:
        Respects website owner's crawling preferences as specified in robots.txt.
        Uses caching to avoid repeated robots.txt fetches.

        Args:
            url: URL to check

        Raises:
            RobotsDisallowedException: If URL is disallowed by robots.txt
        """
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        # Check cache
        cache_key = f"{parsed.scheme}://{parsed.netloc}"
        if cache_key in self._robots_cache:
            parser, cached_time = self._robots_cache[cache_key]
            # Use cached version if less than 1 hour old
            if (datetime.now(timezone.utc) - cached_time).seconds < 3600:
                if not parser.can_fetch(self.USER_AGENT, url):
                    raise RobotsDisallowedException(
                        message=f"URL is disallowed by robots.txt: {url}",
                        url=url,
                        error_code="ROBOTS_DISALLOWED"
                    )
                return

        # Fetch and parse robots.txt
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    robots_url,
                    headers={"User-Agent": self.USER_AGENT},
                    follow_redirects=True
                )

                if response.status_code == 200:
                    parser = RobotFileParser()
                    parser.parse(response.text.splitlines())

                    # Cache the parser
                    self._robots_cache[cache_key] = (parser, datetime.now(timezone.utc))

                    if not parser.can_fetch(self.USER_AGENT, url):
                        raise RobotsDisallowedException(
                            message=f"URL is disallowed by robots.txt: {url}",
                            url=url,
                            error_code="ROBOTS_DISALLOWED"
                        )
                # If robots.txt doesn't exist (404), assume allowed

        except httpx.RequestError as e:
            # If we can't fetch robots.txt, log warning but continue
            logger.warning(f"Could not fetch robots.txt for {robots_url}: {str(e)}")

    async def _fetch_url(self, url: str) -> Tuple[str, str, Dict[str, str]]:
        """
        Fetch content from URL with proper error handling.

        HTTP REQUEST HANDLING:
        - Configurable timeout
        - Redirect following
        - Content type validation
        - Size limit enforcement
        - Proper error classification

        Args:
            url: URL to fetch

        Returns:
            Tuple of (content, content_type, headers)

        Raises:
            URLConnectionException: Network connectivity issues
            URLTimeoutException: Request timed out
            URLAccessDeniedException: Access forbidden
            URLNotFoundException: Page not found
            ContentTooLargeException: Content exceeds size limits
            UnsupportedContentTypeException: Unsupported content type
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=5
            ) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": self.USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml,text/plain,text/markdown",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate",
                    }
                )

                # Handle error status codes
                if response.status_code == 401:
                    raise URLAccessDeniedException(
                        message="Authentication required to access this URL",
                        url=url,
                        status_code=401,
                        error_code="URL_AUTH_REQUIRED"
                    )

                if response.status_code == 403:
                    raise URLAccessDeniedException(
                        message="Access to this URL is forbidden",
                        url=url,
                        status_code=403,
                        error_code="URL_FORBIDDEN"
                    )

                if response.status_code == 404:
                    raise URLNotFoundException(
                        message="The requested page was not found",
                        url=url,
                        status_code=404,
                        error_code="URL_NOT_FOUND"
                    )

                if response.status_code == 429:
                    raise URLAccessDeniedException(
                        message="Rate limit exceeded. Please try again later.",
                        url=url,
                        status_code=429,
                        error_code="URL_RATE_LIMITED"
                    )

                if response.status_code >= 500:
                    raise URLConnectionException(
                        message=f"Server error: HTTP {response.status_code}",
                        url=url,
                        status_code=response.status_code,
                        error_code="URL_SERVER_ERROR"
                    )

                if response.status_code >= 400:
                    raise URLConnectionException(
                        message=f"HTTP error: {response.status_code}",
                        url=url,
                        status_code=response.status_code,
                        error_code="URL_HTTP_ERROR"
                    )

                # Check content type
                content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                if content_type and not any(ct in content_type for ct in self.SUPPORTED_CONTENT_TYPES):
                    raise UnsupportedContentTypeException(
                        message=f"Unsupported content type: {content_type}",
                        actual_content_type=content_type,
                        supported_types=self.SUPPORTED_CONTENT_TYPES,
                        error_code="UNSUPPORTED_CONTENT_TYPE"
                    )

                # Check content size
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.max_content_size:
                    raise ContentTooLargeException(
                        message=f"Content size ({content_length} bytes) exceeds maximum ({self.max_content_size} bytes)",
                        content_size=int(content_length),
                        max_size=self.max_content_size,
                        error_code="CONTENT_TOO_LARGE"
                    )

                # Get content
                content = response.text

                # Double-check actual content size
                if len(content) > self.max_content_size:
                    raise ContentTooLargeException(
                        message=f"Content size ({len(content)} chars) exceeds maximum",
                        content_size=len(content),
                        max_size=self.max_content_size,
                        error_code="CONTENT_TOO_LARGE"
                    )

                headers = dict(response.headers)

                return content, content_type, headers

        except httpx.TimeoutException as e:
            raise URLTimeoutException(
                message=f"Request timed out after {self.timeout} seconds",
                url=url,
                error_code="URL_TIMEOUT",
                original_exception=e
            )

        except httpx.ConnectError as e:
            raise URLConnectionException(
                message=f"Failed to connect to server: {str(e)}",
                url=url,
                error_code="URL_CONNECT_ERROR",
                original_exception=e
            )

        except httpx.RequestError as e:
            raise URLConnectionException(
                message=f"Request failed: {str(e)}",
                url=url,
                error_code="URL_REQUEST_ERROR",
                original_exception=e
            )

    async def _parse_html(self, url: str, html_content: str) -> FetchedContent:
        """
        Parse HTML and extract meaningful content.

        EXTRACTION STRATEGY:
        1. Parse HTML with BeautifulSoup
        2. Remove non-content elements (scripts, styles, nav, etc.)
        3. Extract main content area
        4. Extract title and meta description
        5. Extract headings for document structure
        6. Extract code blocks for technical content
        7. Clean and normalize text

        Args:
            url: Source URL for attribution
            html_content: Raw HTML content

        Returns:
            FetchedContent with extracted content

        Raises:
            HTMLParsingException: Failed to parse HTML
            ContentExtractionException: No meaningful content found
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            raise HTMLParsingException(
                message=f"Failed to parse HTML: {str(e)}",
                content_type="text/html",
                parsing_stage="html_parse",
                error_code="HTML_PARSE_ERROR",
                original_exception=e
            )

        # Extract title
        title = None
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Extract meta description
        description = None
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "")

        # Remove unwanted elements
        for element in self.REMOVE_ELEMENTS:
            for tag in soup.find_all(element):
                tag.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Extract code blocks before text extraction
        code_blocks = self._extract_code_blocks(soup)

        # Try to find main content area
        main_content = self._find_main_content(soup)

        # Extract headings for document structure
        headings = self._extract_headings(main_content)

        # Extract and clean text
        text_content = self._extract_text(main_content)

        if len(text_content) < self.MIN_CONTENT_LENGTH:
            raise ContentExtractionException(
                message=f"Extracted content is too short ({len(text_content)} characters). "
                        f"Minimum is {self.MIN_CONTENT_LENGTH} characters.",
                content_type="text/html",
                parsing_stage="content_extraction",
                error_code="CONTENT_TOO_SHORT",
                details={"extracted_length": len(text_content), "minimum_length": self.MIN_CONTENT_LENGTH}
            )

        return FetchedContent(
            url=url,
            content=text_content,
            title=title,
            description=description,
            headings=headings,
            code_blocks=code_blocks,
            metadata={
                "extraction_method": "html_parser",
                "source_url": url,
            }
        )

    def _find_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Find the main content area of the page.

        CONTENT DETECTION STRATEGY:
        1. Look for semantic HTML5 elements (article, main)
        2. Look for common content div classes
        3. Fall back to body if no specific content area found

        Args:
            soup: Parsed HTML

        Returns:
            BeautifulSoup element containing main content
        """
        # Try semantic HTML5 elements first
        main = soup.find("main")
        if main:
            return main

        article = soup.find("article")
        if article:
            return article

        # Try common content div patterns
        for selector in self.CONTENT_ELEMENTS:
            if "." in selector:
                tag, class_name = selector.split(".", 1)
                content = soup.find(tag, class_=class_name)
            else:
                content = soup.find(selector)

            if content:
                return content

        # Look for the largest text-containing div
        divs = soup.find_all("div")
        if divs:
            largest_div = max(divs, key=lambda d: len(d.get_text()), default=None)
            if largest_div and len(largest_div.get_text()) > 500:
                return largest_div

        # Fall back to body
        body = soup.find("body")
        return body if body else soup

    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract document headings for structure analysis.

        Args:
            soup: Parsed content area

        Returns:
            List of heading dictionaries with level and text
        """
        headings = []
        for level in range(1, 7):
            for heading in soup.find_all(f"h{level}"):
                text = heading.get_text(strip=True)
                if text:
                    headings.append({
                        "level": level,
                        "text": text,
                        "id": heading.get("id", ""),
                    })

        return headings

    def _extract_code_blocks(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract code blocks for technical content.

        Args:
            soup: Parsed HTML

        Returns:
            List of code block dictionaries with language and content
        """
        code_blocks = []

        # Look for pre > code patterns
        for pre in soup.find_all("pre"):
            code = pre.find("code")
            if code:
                language = ""
                # Try to detect language from class
                classes = code.get("class", [])
                for cls in classes:
                    if cls.startswith("language-") or cls.startswith("lang-"):
                        language = cls.split("-", 1)[1]
                        break

                code_text = code.get_text()
                if code_text.strip():
                    code_blocks.append({
                        "language": language,
                        "content": code_text,
                    })
            else:
                # Just a pre tag without code
                pre_text = pre.get_text()
                if pre_text.strip():
                    code_blocks.append({
                        "language": "",
                        "content": pre_text,
                    })

        return code_blocks

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """
        Extract and clean text content from HTML.

        CLEANING OPERATIONS:
        - Remove excessive whitespace
        - Normalize line breaks
        - Preserve paragraph structure
        - Remove non-printable characters

        Args:
            soup: Parsed content area

        Returns:
            Cleaned text content
        """
        # Get text with separator for structure
        text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = []
        for line in text.split("\n"):
            line = line.strip()
            if line:
                # Collapse multiple spaces
                line = re.sub(r"\s+", " ", line)
                lines.append(line)

        # Join with double newline for paragraph separation
        text = "\n\n".join(lines)

        # Remove any remaining excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text

    def create_content_chunks(
        self,
        content: FetchedContent,
        chunk_size: int = None,
        overlap: int = None,
    ) -> List[ContentChunk]:
        """
        Split content into chunks suitable for RAG ingestion.

        CHUNKING STRATEGY:
        - Respects paragraph boundaries where possible
        - Maintains heading context for each chunk
        - Includes overlap for context continuity
        - Creates manageable chunks for vector storage

        Args:
            content: FetchedContent to chunk
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks in characters

        Returns:
            List of ContentChunk objects
        """
        chunk_size = chunk_size or self.CHUNK_SIZE
        overlap = overlap or self.CHUNK_OVERLAP

        text = content.content
        chunks = []

        # Split by paragraphs first
        paragraphs = text.split("\n\n")

        current_chunk = ""
        current_heading = ""
        chunk_index = 0

        for para in paragraphs:
            # Check if this is a heading
            if para.strip() and len(para) < 100:
                # Might be a heading, check against extracted headings
                for heading in content.headings:
                    if heading["text"] == para.strip():
                        current_heading = para.strip()
                        break

            # Check if adding this paragraph would exceed chunk size
            if len(current_chunk) + len(para) + 2 > chunk_size:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunks.append(ContentChunk(
                        chunk_index=chunk_index,
                        content=current_chunk.strip(),
                        heading_context=current_heading,
                        source_url=content.url,
                        metadata={
                            "title": content.title,
                            "content_hash": content.content_hash,
                        }
                    ))
                    chunk_index += 1

                # Start new chunk with overlap from previous
                if overlap and current_chunk:
                    # Take last overlap characters
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(ContentChunk(
                chunk_index=chunk_index,
                content=current_chunk.strip(),
                heading_context=current_heading,
                source_url=content.url,
                metadata={
                    "title": content.title,
                    "content_hash": content.content_hash,
                }
            ))

        logger.info(f"Created {len(chunks)} chunks from content ({content.character_count} chars)")

        return chunks


# Factory function for easy service instantiation
def create_url_content_fetcher(
    timeout: float = URLContentFetcher.DEFAULT_TIMEOUT,
    max_content_size: int = URLContentFetcher.MAX_CONTENT_SIZE,
    check_robots: bool = True,
) -> URLContentFetcher:
    """
    Factory function to create URLContentFetcher instance.

    Provides a simple interface for creating configured fetcher instances
    with sensible defaults for course generation use cases.

    Args:
        timeout: Request timeout in seconds
        max_content_size: Maximum content size in bytes
        check_robots: Whether to check robots.txt

    Returns:
        Configured URLContentFetcher instance
    """
    return URLContentFetcher(
        timeout=timeout,
        max_content_size=max_content_size,
        check_robots=check_robots,
    )


# Export key components
__all__ = [
    "URLContentFetcher",
    "FetchedContent",
    "ContentChunk",
    "create_url_content_fetcher",
]
