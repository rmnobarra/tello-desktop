"""Hardware-independent input and flight guards."""
from dataclasses import dataclass


def axis(value, deadzone=0.15, speed=30):
    if abs(value) <= deadzone:
        return 0
    return round(max(-1, min(1, value)) * speed)


@dataclass
class Guard:
    airborne: bool = False
    uncertain: bool = False

    def takeoff(self, drone, neutral=True):
        if self.airborne or self.uncertain or not neutral:
            return False
        if drone.get_battery() < 30:
            raise RuntimeError("Bateria abaixo de 30%; decolagem bloqueada")
        # Keep landing available even when acknowledgement is lost.
        self.uncertain = True
        drone.takeoff()
        self.airborne, self.uncertain = True, False
        return True

    def land(self, drone):
        if self.airborne or self.uncertain:
            drone.send_rc_control(0, 0, 0, 0)
            drone.land()
            self.airborne = self.uncertain = False


class Simulator:
    def get_battery(self):
        return 100

    def takeoff(self):
        print("SIM: decolar")

    def land(self):
        print("SIM: pousar")

    def send_rc_control(self, *values):
        pass
