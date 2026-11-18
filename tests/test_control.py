import unittest
from tello_desktop.control import Guard, Simulator, axis


class Fake(Simulator):
    def __init__(self):
        self.calls = []
    def takeoff(self):
        self.calls.append("takeoff")
    def land(self):
        self.calls.append("land")


class Tests(unittest.TestCase):
    def test_deadzone_and_clamp(self):
        self.assertEqual(axis(.1), 0)
        self.assertEqual(axis(2), 30)
        self.assertEqual(axis(-1), -30)

    def test_non_neutral_and_duplicate_takeoff(self):
        d, g = Fake(), Guard()
        self.assertFalse(g.takeoff(d, neutral=False))
        g.takeoff(d)
        g.takeoff(d)
        g.land(d)
        self.assertEqual(d.calls, ["takeoff", "land"])

    def test_low_battery(self):
        d, g = Fake(), Guard()
        d.get_battery = lambda: 29
        with self.assertRaises(RuntimeError):
            g.takeoff(d)
        self.assertEqual(d.calls, [])

    def test_lost_ack_keeps_landing_available(self):
        d, g = Fake(), Guard()
        def fail():
            raise TimeoutError()
        d.takeoff = fail
        with self.assertRaises(TimeoutError):
            g.takeoff(d)
        self.assertTrue(g.uncertain)
        self.assertFalse(g.takeoff(d))
        g.land(d)
        self.assertEqual(d.calls, ["land"])

    def test_failed_land_can_retry(self):
        d, g = Fake(), Guard(airborne=True)
        d.land = lambda: (_ for _ in ()).throw(TimeoutError())
        with self.assertRaises(TimeoutError):
            g.land(d)
        self.assertTrue(g.airborne)
