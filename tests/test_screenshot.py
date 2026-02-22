import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import base64

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import client (might print startup logs)
try:
    import client
except ImportError:
    # Handle if dependencies are missing in test env
    client = None

class TestScreenshot(unittest.TestCase):
    def setUp(self):
        if not client:
            self.skipTest("Client module could not be imported")
        
        self.mock_socket = MagicMock()
        self.gatherer = client.SystemInfoGatherer(self.mock_socket, "test_agent")
        
    @patch('builtins.print')  # Suppress print output
    @patch('mss.mss')
    @patch('mss.tools.to_png')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=b'fake_png_bytes')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.remove')
    def test_mss_success(self, mock_remove, mock_getsize, mock_exists, mock_file, mock_to_png, mock_mss_cls, mock_print):
        # Simulate successful MSS capture
        mock_sct = MagicMock()
        mock_mss_cls.return_value.__enter__.return_value = mock_sct
        
        # Mock monitors and grab
        mock_sct.monitors = [{'top': 0, 'left': 0, 'width': 1920, 'height': 1080}]
        mock_screenshot = MagicMock()
        mock_screenshot.rgb = b'fake_rgb'
        mock_screenshot.size = (1920, 1080)
        mock_sct.grab.return_value = mock_screenshot
        
        # Mock file system checks
        mock_exists.return_value = True
        mock_getsize.return_value = 1024 # Valid size
        
        # Call method
        result = self.gatherer.capture_screen_base64()
        
        # Verify
        expected_base64 = base64.b64encode(b'fake_png_bytes').decode('utf-8')
        self.assertEqual(result, expected_base64)
        mock_sct.grab.assert_called_once()
        # Verify to_png called with output file
        args, kwargs = mock_to_png.call_args
        self.assertEqual(kwargs.get('output'), "full_desktop_ss.png")

    @patch('builtins.print')  # Suppress print output
    @patch('mss.mss')
    def test_fallback_to_synthetic(self, mock_mss_cls, mock_print):
        # Simulate MSS failure
        mock_mss_cls.side_effect = ImportError("MSS not found")
        
        # Execute
        result = self.gatherer.capture_screen_base64()
        
        # Verify result is valid base64 (synthetic)
        self.assertTrue(len(result) > 0)
        try:
            base64.b64decode(result)
        except:
            self.fail("Result is not valid base64")

if __name__ == '__main__':
    unittest.main()
