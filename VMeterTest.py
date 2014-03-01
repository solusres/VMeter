import VMeter
import unittest

class ManualTests(unittest.TestCase):                          
    def assertState(self, assertion):
        """
        Prompts for user input to verify manual tests case.
        Empty input (single return) succeeds.
        Non-empty input fails.
        """
        print 
        print "??\n??"
        print assertion
        
        result = raw_input(">>>")

        if result:
            self.fail("!!! This was not so:\n%s" % assertion)
        else:
            print "OK"

    def test_known_state(self):                          
        """.boilerplate."""
        # do some state changes
        #assertState("Interaction should behave like x.")
        # prompts for user input to confirm or disconfirm x-like behaviour.
        pass

    def test_assert_state(self):                          
        """see if assertState works"""
        self.assertState("This will fail if you say anything.\n...anything at all.")                   

class AutomatedTests(unittest.TestCase):
    def setUp(self):
        pass
        #self.v = VMeter.VMeter()

    def tearDown(self):
        pass
        #self.v.close()
        #self.v = None

    def test_read_settings(self):                    
        """verify output of read_settings"""
        #settings = v.read_settings()
        # perform validations on size, values of settings returned
        pass

    def test_store_settings(self):
        """set some settings, write to VMeter, test against read_settings"""
        pass

    def test_bad_input(self):                                          
        """THIS IS TO SHOW YOU HOW TO ASSERT EXCEPTIONS"""                   
        #self.assertRaises(OutOfRangeError, functionToCall, arguments)
        pass

if __name__ == "__main__":
    unittest.main()   