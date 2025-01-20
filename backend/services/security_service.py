from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp
import ssl
import certifi
from typing import Dict, List, Optional
import os

class SecurityHeaders(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        allowed_hosts: Optional[List[str]] = None,
        hsts_max_age: int = 31536000
    ):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or []
        self.hsts_max_age = hsts_max_age
        
        # Initialize CSP directives
        self.csp_directives = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://unpkg.com"],
            'style-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
            'img-src': ["'self'", "data:", "https:", "blob:"],
            'font-src': ["'self'", "https:", "data:"],
            'connect-src': ["'self'", "https:"],
            'frame-ancestors': ["'none'"],
            'form-action': ["'self'"],
            'base-uri': ["'self'"],
            'object-src': ["'none'"]
        }

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        # Check if host is allowed
        if self.allowed_hosts:
            host = request.headers.get('host', '').split(':')[0]
            if host not in self.allowed_hosts:
                return Response(
                    content='Invalid host header',
                    status_code=400
                )

        response = await call_next(request)

        # Add security headers
        headers = {
            'Strict-Transport-Security': f'max-age={self.hsts_max_age}; includeSubDomains; preload',
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(self), microphone=(), camera=()',
            'Content-Security-Policy': self._build_csp_header(),
            'X-Permitted-Cross-Domain-Policies': 'none',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin'
        }

        # Add headers to response
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value

        return response

    def _build_csp_header(self) -> str:
        """Build Content Security Policy header from directives"""
        csp_parts = []
        for directive, sources in self.csp_directives.items():
            if sources:
                csp_parts.append(f"{directive} {' '.join(sources)}")
        return '; '.join(csp_parts)

class SSLConfig:
    @staticmethod
    def get_ssl_context() -> ssl.SSLContext:
        """Create SSL context with secure configuration"""
        context = ssl.create_default_context(
            purpose=ssl.Purpose.CLIENT_AUTH,
            cafile=certifi.where()
        )
        
        # Set secure protocols and ciphers
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        context.set_ciphers(':'.join([
            'ECDHE-ECDSA-AES128-GCM-SHA256',
            'ECDHE-RSA-AES128-GCM-SHA256',
            'ECDHE-ECDSA-AES256-GCM-SHA384',
            'ECDHE-RSA-AES256-GCM-SHA384',
            'ECDHE-ECDSA-CHACHA20-POLY1305',
            'ECDHE-RSA-CHACHA20-POLY1305'
        ]))
        
        # Enable OCSP stapling
        context.options |= ssl.OP_NO_COMPRESSION
        context.options |= ssl.OP_SINGLE_DH_USE
        context.options |= ssl.OP_SINGLE_ECDH_USE
        
        return context

class CORSConfig:
    def __init__(
        self,
        allowed_origins: List[str],
        allow_credentials: bool = True,
        allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allowed_headers: List[str] = ["*"]
    ):
        self.allowed_origins = allowed_origins
        self.allow_credentials = allow_credentials
        self.allowed_methods = allowed_methods
        self.allowed_headers = allowed_headers

    def get_cors_config(self) -> Dict:
        """Get CORS configuration for FastAPI"""
        return {
            "allow_origins": self.allowed_origins,
            "allow_credentials": self.allow_credentials,
            "allow_methods": self.allowed_methods,
            "allow_headers": self.allowed_headers,
            "expose_headers": ["Content-Length", "Content-Range"]
        }

def setup_ssl_cert():
    """Setup SSL certificate using Let's Encrypt"""
    from acme import client, messages
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import josepy as jose
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Save private key
    with open("privkey.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Create CSR
    csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
        x509.NameAttribute(x509.NameOID.COMMON_NAME, "hoteltracker.org")
    ])).sign(private_key, hashes.SHA256())
    
    # TODO: Complete ACME protocol implementation for Let's Encrypt
    # This requires implementing HTTP-01 or DNS-01 challenge
    # and handling certificate issuance
    
    return {
        "status": "Certificate setup initiated",
        "next_steps": [
            "Complete ACME challenge",
            "Obtain certificate",
            "Install certificate"
        ]
    }
