"""
Test Write tool to check for hook issues and post-tool responsiveness
"""

def test_write_function():
    return "Testing Write tool hook behavior"

class WriteTestClass:
    def __init__(self):
        self.status = "write_test_created"

    def get_status(self):
        """Updated via Edit tool to test hook behavior"""
        return f"Status: {self.status} - Updated via Edit"