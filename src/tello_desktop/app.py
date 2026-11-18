"""Pygame display and control loop. Simulation is the default."""
import argparse
import json
import signal
import time
from pathlib import Path

from .control import Guard, Simulator, axis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Conectar ao drone real")
    parser.add_argument("--gamepad", type=Path, help="Perfil JSON verificado no modo de simulação")
    parser.add_argument("--inspect-controller", action="store_true")
    args = parser.parse_args()
    import pygame as pg
    pg.init()
    screen = pg.display.set_mode((960, 720))
    pg.display.set_caption("Tello Desktop — SIMULAÇÃO" if not args.live else "Tello Desktop — REAL")
    font = pg.font.Font(None, 26)
    clock = pg.time.Clock()
    drone, reader = Simulator(), None
    guard = Guard()
    running = True
    error = ""
    profile = json.loads(args.gamepad.read_text()) if args.gamepad else None
    joy = None
    if profile or args.inspect_controller:
        if not pg.joystick.get_count():
            pg.quit()
            raise SystemExit("Nenhum controle encontrado. Conecte por USB/Bluetooth e tente novamente.")
        joy = pg.joystick.Joystick(0)
        joy.init()
        if profile:
            if len(profile["axes"]) != 4 or len(profile["signs"]) != 4:
                raise SystemExit("Perfil precisa de 4 eixos e 4 sinais")
            if any(i < 0 or i >= joy.get_numaxes() for i in profile["axes"]):
                raise SystemExit("Eixo inválido no perfil")
            if any(s not in (-1, 1) for s in profile["signs"]):
                raise SystemExit("Sinais precisam ser -1 ou 1")
            for name in ("deadman", "takeoff", "land"):
                if not 0 <= profile[name] < joy.get_numbuttons():
                    raise SystemExit("Botão inválido: " + name)
            if len({profile[k] for k in ("deadman", "takeoff", "land")}) != 3:
                raise SystemExit("Use três botões distintos")
    # Inspection can never connect to real hardware.
    live = args.live and not args.inspect_controller
    def stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    last_frame = None
    last_video = time.monotonic()
    last_state_check = 0
    battery = 100
    rc = (0, 0, 0, 0)
    try:
        if live:
            from djitellopy import Tello
            drone = Tello()
            drone.connect()
            battery = drone.get_battery()
            drone.streamon()
            reader = drone.get_frame_read()
        while running:
            focused = pg.key.get_focused()
            takeoff = land = False
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        running = False
                    takeoff |= event.key == pg.K_t and bool(event.mod & pg.KMOD_SHIFT)
                    land |= event.key == pg.K_l
                elif event.type == pg.JOYDEVICEREMOVED and joy:
                    guard.land(drone)
                    raise RuntimeError("Controle desconectado; pouso solicitado")
                elif event.type == pg.JOYBUTTONDOWN and profile:
                    takeoff |= event.button == profile["takeoff"] and bool(joy.get_button(profile["deadman"]))
                    land |= event.button == profile["land"]
            keys = pg.key.get_pressed()
            rc = (0, 0, 0, 0)
            if focused and not args.inspect_controller:
                rc = (30*(keys[pg.K_d]-keys[pg.K_a]), 30*(keys[pg.K_w]-keys[pg.K_s]),
                      30*(keys[pg.K_UP]-keys[pg.K_DOWN]), 30*(keys[pg.K_RIGHT]-keys[pg.K_LEFT]))
                if profile and joy.get_button(profile["deadman"]):
                    rc = tuple(axis(joy.get_axis(i)*s) for i, s in zip(profile["axes"], profile["signs"]))
            if land or not focused or not running:
                guard.land(drone)
                takeoff = False
            if takeoff and focused and running and not args.inspect_controller:
                guard.takeoff(drone, neutral=not any(rc))
                last_video = time.monotonic()
            if guard.airborne:
                drone.send_rc_control(*rc)
            now = time.monotonic()
            if live and now-last_state_check > 1:
                battery = drone.get_battery()
                last_state_check = now
                if battery < 20:
                    guard.land(drone)
                    error = "Bateria baixa: pouso solicitado"
            screen.fill((17, 25, 38))
            if reader:
                frame = reader.frame
                if frame is not None and frame is not last_frame:
                    last_frame, last_video = frame, now
                    surface = pg.surfarray.make_surface(frame.swapaxes(0, 1))
                    screen.blit(pg.transform.scale(surface, (960, 540)), (0, 0))
                if guard.airborne and now-last_video > 3:
                    guard.land(drone)
                    raise RuntimeError("Vídeo sem novos quadros por 3s; pouso solicitado")
            lines = [f"{'REAL' if live else 'SIMULAÇÃO'} | Bateria: {battery}% | RC: {rc}",
                     "Shift+T: decolar | L: pousar | Esc/fechar: pousar e sair",
                     "W/S: frente/trás | A/D: lateral | cima/baixo: altura | esq/dir: giro",
                     f"Estado local: {'EM VOO' if guard.airborne else 'NO CHÃO'} | {error}"]
            if args.inspect_controller:
                lines = [joy.get_name(), "Eixos: " + str([round(joy.get_axis(i), 2) for i in range(joy.get_numaxes())]),
                         "Botões: " + str([i for i in range(joy.get_numbuttons()) if joy.get_button(i)]),
                         "Inspeção offline: nenhum comando enviado ao drone"]
            for i, line in enumerate(lines):
                screen.blit(font.render(line, True, (230, 240, 250)), (12, 552+i*35))
            pg.display.flip()
            clock.tick(20)
    except Exception as exc:
        print(f"Erro: {exc}")
        raise
    finally:
        try:
            guard.land(drone)
        except Exception as exc:
            print(f"Não foi possível confirmar o pouso: {exc}. Verifique o drone.")
        if live:
            try:
                drone.end()
            except Exception as exc:
                print(f"Encerramento: {exc}")
        pg.quit()


if __name__ == "__main__":
    main()
