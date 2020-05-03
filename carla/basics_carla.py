#!/usr/bin/env python

"""
An example of client-side bounding boxes with basic car controls.

Controls:

    W            : throttle
    S            : brake
    AD           : steer
    Space        : hand-brake

    ESC          : quit
"""

import glob
import os
import sys
import random
import zmq
import time
import argparse
import json

import numpy as np

TIME_STEP = 0.1

ACTIVE_MAP = 'Town06'
DEFAULT_VEHICLE = 'vehicle.bmw.grandtourer'


class VehicleData(object):
    def __init__(self, i=0, x=0, y=0):
        self.i = i
        self.x = x
        self.y = y


class CarlaHandler(object):

    last_time = time.perf_counter()

    def set_timing_settings(self, synchronous_mode):
        """
        Sets timing settings.
        """

        settings = self.world.get_settings()
        settings.fixed_delta_seconds = TIME_STEP
        settings.synchronous_mode = synchronous_mode
        self.world.apply_settings(settings)

    def game_loop(self):
        """
        Main program loop.
        """

        try:

            context = zmq.Context()

            #  Socket to talk to server
            self.zmqsocket = context.socket(zmq.REP)
            self.zmqsocket.bind("tcp://*:%s" % 5555)

            self.client = carla.Client('127.0.0.1', 2000)
            self.client.load_world(ACTIVE_MAP)
            self.client.set_timeout(10.0)

            self.world = self.client.get_world()

            self.weather = self.world.get_weather()
            self.weather.cloudiness = 0
            self.weather.precipitation = 0
            self.weather.precipitation_deposits = 0
            self.weather.wind_intensity = 100
            self.weather.fog_density = 0
            self.weather.wetness = 0
            self.weather.sun_azimuth_angle = 45
            self.weather.sun_altitude_angle = 45

            self.world.set_weather(self.weather)

            self.set_timing_settings(True)

            blueprint = random.choice(self.world.get_blueprint_library().filter('vehicle.*'))
            self.map = self.world.get_map()
            spawn_points = self.map.get_spawn_points()

            vehicle_bp = random.choice(self.world.get_blueprint_library().filter(DEFAULT_VEHICLE))
            transform = random.choice(self.world.get_map().get_spawn_points())
            self.vehicle = self.world.try_spawn_actor(vehicle_bp, transform)
            # self.vehicle.set_velocity(carla.Vector3D(100, 100, 100))

            self._autopilot_active = False

            self.world.on_tick(lambda world_snapshot: self.do_something(world_snapshot))

            self.active = True

            while True:

                while not self.active:
                    time.sleep(.1)

                self.active = False

                self.zmqsocket.recv() # trigger for next carla server tick

                self.world.tick()

                if not self._autopilot_active:
                    self._autopilot_active = True
                    self.vehicle.set_autopilot()

        finally:
            self.set_timing_settings(synchronous_mode=False)
            pass

    def do_something(self, world_snapshot):

        t = self.vehicle.get_transform()
        # v = self.vehicle.get_velocity()

        crt_time = time.perf_counter()
        delta_time = crt_time - self.last_time
        time_factor = world_snapshot.timestamp.delta_seconds/delta_time
        self.last_time = crt_time

        print('Frame ID #{}, x{:.03}, {:.06f} {:.06f} {:.06f} ({:.1f}, {:.1f})'.format(world_snapshot.frame,
                                                                                           time_factor,
                                                                                           world_snapshot.timestamp.elapsed_seconds,
                                                                                           world_snapshot.timestamp.delta_seconds,
                                                                                           delta_time,
                                                                                           t.location.x,
                                                                                           t.location.y))

        self.zmqsocket.send_string(json.dumps(VehicleData(i=world_snapshot.timestamp.elapsed_seconds,
                                                          x=t.location.x,
                                                          y=t.location.y).__dict__))

        self.active = True


# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================


def main():
    """
    Initializes the client-side bounding box demo.
    """

    try:
        client = CarlaHandler()
        client.game_loop()
    finally:
        print('EXIT')


if __name__ == '__main__':

    my_parser = argparse.ArgumentParser(description='')

    # Add the arguments
    my_parser.add_argument('-c', '--carla_python_api',
                           type=str,
                           required=False,
                           default=None,
                           help='Path to CARLA PythonAPI')

    args = my_parser.parse_args()
    print(args)

    # ==============================================================================
    # -- find carla module ---------------------------------------------------------
    # ==============================================================================
    try:
        carla_egg_path = 'carla/dist/carla-*%d.%d-%s.egg'
        if args.carla_python_api is not None:
            carla_egg_path = os.path.abspath(os.path.join(args.carla_python_api, carla_egg_path))
        sys.path.append(glob.glob(carla_egg_path % (sys.version_info.major,
                                                    sys.version_info.minor,
                                                    'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
    except IndexError:
        print('CARLA PythonAPI not found')
        sys.exit()

    import carla

    main()
