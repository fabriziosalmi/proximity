"""
Unit tests for ReverseProxyManager.

Tests the dual-block Caddy configuration generation for the In-App Canvas feature.
This includes public access AND iframe-embeddable internal proxy paths.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.reverse_proxy_manager import ReverseProxyManager


class TestReverseProxyManagerCaddyConfig:
    """Test Caddy configuration generation for In-App Canvas."""

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

    def test_generate_caddy_config_platinum_mode(self, proxy_manager):
        """
        Test Caddy config generation for Platinum network mode (10.20.0.x).

        Critical assertions:
        1. Public handle_path block exists for standard access
        2. Internal /proxy/internal/{hostname} block exists for iframe embedding
        3. Internal block has header_down -X-Frame-Options (strips frame-busting header)
        4. Internal block has header_down -Content-Security-Policy (strips CSP)
        5. Public block does NOT have header_down directives (security)
        """
        hostname = "test-app"
        backend_ip = "10.20.0.50"  # Platinum network
        backend_port = 80

        config = proxy_manager._generate_caddy_config(hostname, backend_ip, backend_port)

        # ====================================================================
        # ASSERT 1: Public path-based access block exists
        # ====================================================================
        assert f"handle_path /{hostname}" in config, \
            "Config must include public handle_path block"

        assert f"reverse_proxy http://{backend_ip}:{backend_port}" in config, \
            "Config must proxy to correct backend"

        # ====================================================================
        # ASSERT 2: Internal iframe proxy block exists
        # ====================================================================
        assert f"handle_path /proxy/internal/{hostname}" in config, \
            "Config must include internal iframe proxy block"

        # ====================================================================
        # ASSERT 3: Internal block strips X-Frame-Options (CRITICAL)
        # ====================================================================
        # Find the internal block section (need to find closing brace of handle_path)
        internal_block_start = config.find(f"handle_path /proxy/internal/{hostname}")
        # Find the end by looking for the pattern that indicates next handle or end of :80 block
        remaining = config[internal_block_start:]
        # Count braces to find the matching close
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
        public_block_start = config.find(f"handle_path /{hostname}")
        public_block_end = config.find("}", public_block_start + 1)
        public_block = config[public_block_start:public_block_end]

        assert "header_down -X-Frame-Options" not in public_block, \
            "Public proxy must NOT strip X-Frame-Options (security requirement)"

        assert "header_down -Content-Security-Policy" not in public_block, \
            "Public proxy must NOT strip Content-Security-Policy (security requirement)"

    def test_generate_caddy_config_legacy_mode(self, proxy_manager):
        """
        Test Caddy config generation for Legacy network mode (192.168.x.x).

        Same assertions as platinum mode, just different IP range.
        """
        hostname = "legacy-app"
        backend_ip = "192.168.1.100"  # Legacy network
        backend_port = 8080

        config = proxy_manager._generate_caddy_config(hostname, backend_ip, backend_port)

        # Verify both blocks exist
        assert f"handle_path /{hostname}" in config
        assert f"handle_path /proxy/internal/{hostname}" in config

        # Verify correct backend IP/port
        assert f"http://{backend_ip}:{backend_port}" in config

        # Verify header stripping only in internal block
        internal_block_start = config.find(f"handle_path /proxy/internal/{hostname}")
        internal_block_end = config.find("}", internal_block_start + 1)
        internal_block = config[internal_block_start:internal_block_end]

        assert "header_down -X-Frame-Options" in internal_block
        assert "header_down -Content-Security-Policy" in internal_block

    def test_header_stripping_is_specific_to_iframe_proxy(self, proxy_manager):
        """
        CRITICAL SECURITY TEST: Verify header stripping only happens in iframe proxy.

        This test explicitly validates that we're not accidentally making
        the public proxy vulnerable by stripping security headers.
        """
        hostname = "security-test"
        backend_ip = "10.20.0.99"
        backend_port = 80

        config = proxy_manager._generate_caddy_config(hostname, backend_ip, backend_port)

        # Split config into public and internal sections
        lines = config.split('\n')

        in_public_block = False
        in_internal_block = False
        public_lines = []
        internal_lines = []

        for line in lines:
            if f"handle_path /{hostname}" in line and "/proxy/internal" not in line:
                in_public_block = True
                in_internal_block = False
            elif f"handle_path /proxy/internal/{hostname}" in line:
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

        # Public block must NOT have header stripping
        assert "header_down -X-Frame-Options" not in public_config, \
            "SECURITY VIOLATION: Public proxy has X-Frame-Options stripping"

        assert "header_down -Content-Security-Policy" not in public_config, \
            "SECURITY VIOLATION: Public proxy has CSP stripping"

        # Internal block MUST have header stripping
        assert "header_down -X-Frame-Options" in internal_config, \
            "Internal proxy missing X-Frame-Options stripping"

        assert "header_down -Content-Security-Policy" in internal_config, \
            "Internal proxy missing CSP stripping"

    def test_config_includes_both_network_modes_headers(self, proxy_manager):
        """
        Test that generated config includes proper headers for both modes.
        """
        hostname = "test-headers"
        backend_ip = "10.20.0.75"
        backend_port = 3000

        config = proxy_manager._generate_caddy_config(hostname, backend_ip, backend_port)

        # Both blocks should have standard proxy headers
        assert "header_up Host" in config
        assert "header_up X-Real-IP" in config
        assert "header_up X-Forwarded-For" in config
        assert "header_up X-Forwarded-Proto" in config

    def test_config_format_is_valid_caddyfile_syntax(self, proxy_manager):
        """
        Test that generated config has valid Caddyfile syntax.
        """
        config = proxy_manager._generate_caddy_config("app", "10.20.0.1", 80)

        # Check for balanced braces
        open_braces = config.count('{')
        close_braces = config.count('}')
        assert open_braces == close_braces, "Caddyfile has unbalanced braces"

        # Check for required sections
        assert ":80 {" in config, "Missing port binding"
        assert "handle_path" in config, "Missing handle_path directives"
        assert "reverse_proxy" in config, "Missing reverse_proxy directives"

    def test_multiple_apps_dont_conflict(self, proxy_manager):
        """
        Test that configs for multiple apps can coexist.
        """
        app1_config = proxy_manager._generate_caddy_config("app1", "10.20.0.1", 80)
        app2_config = proxy_manager._generate_caddy_config("app2", "10.20.0.2", 8080)

        # Each config should be independent
        assert "/app1" in app1_config
        assert "/app2" not in app1_config

        assert "/app2" in app2_config
        assert "/app1" not in app2_config

        # Internal proxy paths should be unique
        assert "/proxy/internal/app1" in app1_config
        assert "/proxy/internal/app2" in app2_config
