"""
Testing combination of tools in sequence
"""

class ComboTest:
    def __init__(self):
        self.phase = "multi_edit_updated"
        self.timestamp = "combo_test"

    def step_one(self):
        """Updated via MultiEdit"""
        return f"step_one_modified_{self.phase}"

    def step_two(self):
        """Step two with logic"""
        if self.phase == "multi_edit_updated":
            return "step_two_conditional_pass"
        return "step_two_conditional_fail"

    def step_three(self):
        """Final step updated via Edit tool"""
        return f"step_three_final_{self.timestamp}"