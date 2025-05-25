import unittest
from datetime import date
from unittest.mock import patch, MagicMock
from user_session_monitor import update_daily_active_time

class TestUserSessionMonitor(unittest.TestCase):
    def setUp(self):
        # Reset the daily_active_times dictionary before each test
        self.original_daily_active_times = update_daily_active_time.__globals__['daily_active_times']
        update_daily_active_time.__globals__['daily_active_times'] = {}

    def tearDown(self):
        # Restore the original daily_active_times after each test
        update_daily_active_time.__globals__['daily_active_times'] = self.original_daily_active_times

    def test_update_daily_active_time(self):
        """Test that daily active time is updated correctly"""
        # Get today's date as a string
        today = str(date.today())
        
        # Test initial update
        result = update_daily_active_time(60)  # 60 seconds
        self.assertEqual(result, 60)
        self.assertEqual(update_daily_active_time.__globals__['daily_active_times'][today], 60)
        
        # Test subsequent update
        result = update_daily_active_time(30)  # 30 seconds
        self.assertEqual(result, 90)
        self.assertEqual(update_daily_active_time.__globals__['daily_active_times'][today], 90)
        
        # Test with floating point values
        result = update_daily_active_time(15.5)
        self.assertAlmostEqual(result, 105.5)
        self.assertAlmostEqual(update_daily_active_time.__globals__['daily_active_times'][today], 105.5)
        
    def test_update_daily_active_time_with_error(self):
        """Test error handling when updating daily active time"""
        # Test normal case first
        result = update_daily_active_time(60)
        self.assertEqual(result, 60)
        today = str(date.today())
        self.assertEqual(update_daily_active_time.__globals__['daily_active_times'][today], 60)
        
        # Now test error case
        with patch('user_session_monitor.get_current_date') as mock_get_date:
            mock_get_date.side_effect = Exception("Test error")
            result = update_daily_active_time(60)
            self.assertIsNone(result)
            self.assertEqual(len(update_daily_active_time.__globals__['daily_active_times']), 1)  # Should still have the previous entry
            self.assertEqual(update_daily_active_time.__globals__['daily_active_times'][today], 60)  # Previous value should be preserved

if __name__ == '__main__':
    unittest.main()
