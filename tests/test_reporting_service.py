from io import BytesIO
from unittest.mock import AsyncMock, patch

import anyio

from application.services.direction_report import DirectionReportGenerator


def test_generate_direction_report_success():
    async def run_test():
        # Arrange
        generator = DirectionReportGenerator(base_url="http://testserver")

        # We mock the playwright call within the generator
        with patch("application.services.direction_report.async_playwright") as mock_pw:
            mock_p_context = AsyncMock()
            mock_pw.return_value.__aenter__.return_value = mock_p_context

            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            mock_p_context.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page

            # Simulate PDF generation
            mock_page.pdf.return_value = b"%PDF-target-direction"

            # Act
            result = await generator.generate_direction_summary_report(direction="Finance")

            # Assert
            assert isinstance(result, BytesIO)
            assert result.getvalue() == b"%PDF-target-direction"

            # Verify navigation to the correct URL
            mock_page.goto.assert_called_once()
            args, kwargs = mock_page.goto.call_args
            assert "/reports/direction-summary/Finance" in args[0]

            # Verify print media emulation
            mock_page.emulate_media.assert_called_with(media="print")

    anyio.run(run_test)
