"""
Unit tests for ReverseProxyManager.

Tests the port-based Caddy configuration generation for Platinum Edition.
Each app gets two dedicated ports:
- Public port (30000-30999): Standard access via http://appliance_ip:30xxx
- Internal port (40000-40999): iframe-embeddable access via http://appliance_ip:40xxx
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.reverse_proxy_manager import ReverseProxyManager


class TestReverseProxyManagerCaddyConfig:
    """Test Caddy configuration generation for port-based architecture."""

    @pytest.fixture
    def mock_proxmox_service(self):
        """Create a mock ProxmoxService."""
        mock = MagicMock()
        mock.execute_in_container = AsyncMock(return_value="success")
        return mock

    @pytest.fixture
    def proxy_manager(self, mock_proxmox_service):
        """Create ReverseProxyManager instance."""
        return ReverseProxyManager(
            appliance_vmid=100,
            proxmox_service=mock_proxmox_service
        )

    def test_generate_caddy_config_port_based(self, proxy_manager):
        """
        Test Caddy config generation for port-based architecture.

        Critical assertions:
        1. Public port block (:{public_port}) exists for standard access
        2. Internal port block (:{internal_port}) exists for iframe embedding
        3. Internal block has header_down -X-Frame-Options (strips frame-busting header)
        4. Internal block has header_down -Content-Security-Policy (strips CSP)
        5. Public block does NOT have header_down directives (security)
        6. No handle_path or strip_prefix directives (path-based routing removed)
        """
        hostname = "test-app"
        backend_ip = "10.20.0.50"
        backend_port = 80
        public_port = 30001
        internal_port = 40001

        config = proxy_manager._generate_caddy_config(
            hostname, backend_ip, backend_port, public_port, internal_port
        )

        # ====================================================================
        # ASSERT 1: Public port-based access block exists
        # ====================================================================
        assert f":{public_port} {{" in config, \
            "Config must include public port block"

        assert f"reverse_proxy http://{backend_ip}:{backend_port}" in config, \
            "Config must proxy to correct backend"

        # ====================================================================
        # ASSERT 2: Internal iframe proxy port block exists
        # ====================================================================
        assert f":{internal_port} {{" in config, \
            "Config must include internal iframe proxy port block"

        # ====================================================================
        # ASSERT 3: Internal block strips X-Frame-Options (CRITICAL)
        # ====================================================================
        # Find the internal block section
        internal_block_start = config.find(f":{internal_port} {{")
        assert internal_block_start != -1, "Internal port block not found"
        
        # Find the end of the internal block
        remaining = config[internal_block_start:]
        brace_count = 0
        pos = 0
        for i, char in enumerate(remaining):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    pos = i
                    break
        internal_block = remaining[:pos]

        assert "header_down -X-Frame-Options" in internal_block, \
            "Internal proxy MUST strip X-Frame-Options to allow iframe embedding"

        # ====================================================================
        # ASSERT 4: Internal block strips Content-Security-Policy
        # ====================================================================
        assert "header_down -Content-Security-Policy" in internal_block, \
            "Internal proxy MUST strip Content-Security-Policy for iframe embedding"

        # ====================================================================
        # ASSERT 5: Public block does NOT strip headers (security)
        # ====================================================================
        public_block_start = config.find(f":{public_port} {{")
        public_block_end = config.find("}", public_block_start + 1)
        public_block = config[public_block_start:public_block_end]

        assert "header_down -X-Frame-Options" not in public_block, \
            "Public proxy must NOT strip X-Frame-Options (security requirement)"

        assert "header_down -Content-Security-Policy" not in public_block, \
            "Public proxy must NOT strip Content-Security-Policy (security requirement)"

        # ====================================================================
        # ASSERT 6: No path-based routing (handle_path, strip_prefix removed)
        # ====================================================================
        assert "handle_path" not in config, \
            "Config must NOT contain handle_path (legacy path-based routing)"
        
        assert "strip_prefix" not in config, \
            "Config must NOT contain strip_prefix (legacy path-based routing)"

    def test_generate_caddy_config_different_ports(self, proxy_manager):
        """
        Test Caddy config generation with different port assignments.
        """
        hostname = "another-app"
        backend_ip = "10.20.0.100"
        backend_port = 8080
        public_port = 30050
        internal_port = 40050

        config = proxy_manager._generate_caddy_config(
            hostname, backend_ip, backend_port, public_port, internal_port
        )

        # Verify both port blocks exist with correct ports
        assert f":{public_port} {{" in config
        assert f":{internal_port} {{" in config

        # Verify correct backend IP/port
        assert f"http://{backend_ip}:{backend_port}" in config

        # Verify header stripping exists in internal block only
        assert "header_down -X-Frame-Options" in config
        assert "header_down -Content-Security-Policy" in config

    def test_header_stripping_is_specific_to_iframe_port(self, proxy_manager):
        """
        CRITICAL SECURITY TEST: Verify header stripping only happens on internal port.

        This test explicitly validates that we're not accidentally making
        the public port vulnerable by stripping security headers.
        """
        hostname = "security-test"
        backend_ip = "10.20.0.99"
        backend_port = 80
        public_port = 30099
        internal_port = 40099

        config = proxy_manager._generate_caddy_config(
            hostname, backend_ip, backend_port, public_port, internal_port
        )

        # Split config into public and internal port blocks
        lines = config.split('\n')

        in_public_block = False
        in_internal_block = False
        public_lines = []
        internal_lines = []

        for line in lines:
            if f":{public_port} {{" in line:
                in_public_block = True
                in_internal_block = False
            elif f":{internal_port} {{" in line:
                in_internal_block = True
                in_public_block = False
            elif line.strip() == '}' and line.count('}') == 1:
                in_public_block = False
                in_internal_block = False

            if in_public_block:
                public_lines.append(line)
            elif in_internal_block:
                internal_lines.append(line)

        public_config = '\n'.join(public_lines)
        internal_config = '\n'.join(internal_lines)

        # Public port block must NOT have header stripping
        assert "header_down -X-Frame-Options" not in public_config, \
            "SECURITY VIOLATION: Public port has X-Frame-Options stripping"

        assert "header_down -Content-Security-Policy" not in public_config, \
            "SECURITY VIOLATION: Public port has CSP stripping"

        # Internal port block MUST have header stripping
        assert "header_down -X-Frame-Options" in internal_config, \
            "Internal port missing X-Frame-Options stripping"

        assert "header_down -Content-Security-Policy" in internal_config, \
            "Internal port missing CSP stripping"

    def test_config_includes_proxy_headers(self, proxy_manager):
        """
        Test that generated config includes proper headers for both port blocks.
        """
        hostname = "test-headers"
        backend_ip = "10.20.0.75"
        backend_port = 3000
        public_port = 30075
        internal_port = 40075

        config = proxy_manager._generate_caddy_config(
            hostname, backend_ip, backend_port, public_port, internal_port
        )

        # Both blocks should have standard proxy headers
        assert "header_up Host" in config
        assert "header_up X-Real-IP" in config
        assert "header_up X-Forwarded-For" in config
        assert "header_up X-Forwarded-Proto" in config

    def test_config_format_is_valid_caddyfile_syntax(self, proxy_manager):
        """
        Test that generated config has valid Caddyfile syntax.
        """
        config = proxy_manager._generate_caddy_config(
            "app", "10.20.0.1", 80, 30001, 40001
        )

        # Check for balanced braces
        open_braces = config.count('{')
        close_braces = config.count('}')
        assert open_braces == close_braces, "Caddyfile has unbalanced braces"

        # Check for required sections (port blocks)
        assert ":30001 {" in config, "Missing public port binding"
        assert ":40001 {" in config, "Missing internal port binding"
        assert "reverse_proxy" in config, "Missing reverse_proxy directives"
        
        # Verify NO path-based routing
        assert "handle_path" not in config, "Found legacy handle_path directive"
        assert "strip_prefix" not in config, "Found legacy strip_prefix directive"

    def test_multiple_apps_have_unique_ports(self, proxy_manager):
        """
        Test that configs for multiple apps use different ports.
        """
        app1_config = proxy_manager._generate_caddy_config(
            "app1", "10.20.0.1", 80, 30001, 40001
        )
        app2_config = proxy_manager._generate_caddy_config(
            "app2", "10.20.0.2", 8080, 30002, 40002
        )

        # Each config should have its own unique ports
        assert ":30001 {" in app1_config
        assert ":40001 {" in app1_config
        assert ":30002" not in app1_config
        assert ":40002" not in app1_config

        assert ":30002 {" in app2_config
        assert ":40002 {" in app2_config
        assert ":30001" not in app2_config
        assert ":40001" not in app2_config

    def test_port_based_urls_generation(self, proxy_manager):
        """
        Test that port-based URLs are correctly formatted.
        """
        hostname = "port-test"
        backend_ip = "10.20.0.123"
        backend_port = 8080
        public_port = 30123
        internal_port = 40123
        
        config = proxy_manager._generate_caddy_config(
            hostname, backend_ip, backend_port, public_port, internal_port
        )
        
        # Verify port numbers are correctly used in port blocks
        assert f":{public_port} {{" in config
        assert f":{internal_port} {{" in config
        
        # Verify no path-based routing (no handle_path with hostname in routing)
        assert "handle_path" not in config, "Config should not contain handle_path directive"
        assert "/proxy/internal/" not in config, "Config should not contain legacy /proxy/internal/ path"
        
        # Hostname may appear in comments, but not in routing directives
        # Check that /{hostname} doesn't appear in a routing context by ensuring
        # it's not part of handle_path or URL path routing
        lines = config.split('\n')
        for line in lines:
            # Skip comment lines
            if line.strip().startswith('#'):
                continue
            # Check that we don't have path-based routing in actual config
            if hostname in line:
                assert 'handle_path' not in line, f"Found path-based routing: {line}"
                assert 'redir' not in line or hostname not in line, f"Found path-based redirect: {line}"
