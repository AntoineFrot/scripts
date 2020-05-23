#!/usr/bin/env python

import glob
import os
import sys
import random
import time

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# ==============================================================================
# -- find carla module ---------------------------------------------------------
# ==============================================================================
try:
    carla_egg_path = '../../CARLA_0.9.9/PythonAPI/carla/dist/carla-*%d.%d-%s.egg'
    sys.path.append(glob.glob(carla_egg_path % (sys.version_info.major,
                                                sys.version_info.minor,
                                                'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    print('CARLA PythonAPI not found')
    sys.exit()

import carla


class StatusMessage:
    def __init__(self, msg=''):
        self.value = msg


TIME_STEP = 0.1

ACTIVE_MAP = 'Town06'
DEFAULT_VEHICLE = 'vehicle.bmw.grandtourer'


def add(a, b):
    return a + b


class CarlaDaemon:

    def __init__(self):
        self.client = None
        self.world = None
        self.vehicle = None

        # self.last_time = time.perf_counter()

    def __del__(self):
        self.set_timing_settings(synchronous_mode=False)

    def set_timing_settings(self, synchronous_mode):
        """
        Sets synchronous_mode.
        """

        if self.world is not None:
            settings = self.world.get_settings()
            settings.fixed_delta_seconds = TIME_STEP
            settings.synchronous_mode = synchronous_mode
            self.world.apply_settings(settings)

    def load_client(self):
        """
        Main program loop.
        """

        self.client = carla.Client('127.0.0.1', 2000)
        #self.out_q.put(StatusMessage('Client loaded'))

        return True

    def load_world(self, map):
        if self.client is not None:
            self.client.load_world(map)
            self.client.set_timeout(10.0)
            self.world = self.client.get_world()
            #self.out_q.put(StatusMessage('World loaded'))
        else:
            #self.out_q.put(StatusMessage('Client is None'))
            pass

        return True

    def change_weather(self, value_cloudiness, value_precipitation,
                       value_deposits, value_wetness,
                       value_sun_azimuth_angle, value_sun_altitude_angle):
        if self.world is None:
            return False

        # print(value_cloudiness, value_precipitation, value_deposits, value_wetness, value_sun_azimuth_angle, value_sun_altitude_angle)
        self.weather = self.world.get_weather()
        self.weather.cloudiness = value_cloudiness
        self.weather.precipitation = value_precipitation
        self.weather.precipitation_deposits = value_deposits
        self.weather.wind_intensity = 100
        self.weather.fog_density = 0
        self.weather.wetness = value_wetness
        self.weather.sun_azimuth_angle = value_sun_azimuth_angle
        self.weather.sun_altitude_angle = value_sun_altitude_angle

        self.world.set_weather(self.weather)

        return True

    def get_status(self):
        speed = 0.0
        if self.vehicle is not None:
            speed = self.vehicle.get_velocity().x
        return '{:.02f} km/h'.format(speed)

    def main(self):

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

        # for i, waypoint in enumerate(spawn_points):
        #     self.world.debug.draw_string(waypoint.location, str(i), draw_shadow=False,
        #                             color=carla.Color(r=255, g=255, b=255), life_time=10000.2,
        #                             persistent_lines=True)

        vehicle_bp = random.choice(self.world.get_blueprint_library().filter(DEFAULT_VEHICLE))
        transform = random.choice(self.world.get_map().get_spawn_points())
        self.vehicle = self.world.try_spawn_actor(vehicle_bp, transform)
        # self.vehicle.set_velocity(carla.Vector3D(100, 100, 100))

        self._autopilot_active = False

        self.world.on_tick(lambda world_snapshot: self.do_something(world_snapshot))

        # while True:
        #
        #     if not self._autopilot_active:
        #         self._autopilot_active = True
        #         self.vehicle.set_autopilot()

        return True

    def do_something(self, world_snapshot):

        # t = self.vehicle.get_transform()
        v = self.vehicle.get_velocity()
        print(v.x)

        # crt_time = time.perf_counter()
        # delta_time = crt_time - self.last_time
        # time_factor = world_snapshot.timestamp.delta_seconds/delta_time
        # self.last_time = crt_time
        #
        # print('Frame ID #{}, x{:.03}, {:.06f} {:.06f} {:.06f} ({:.1f}, {:.1f})'.format(world_snapshot.frame,
        #                                                                                time_factor,
        #                                                                                world_snapshot.timestamp.elapsed_seconds,
        #                                                                                world_snapshot.timestamp.delta_seconds,
        #                                                                                delta_time,
        #                                                                                t.location.x,
        #                                                                                t.location.y,
        #                                                                                f.x[0],
        #                                                                                fy.x[0]))


        self.active = True


def client_thread():

    # Create server
    with SimpleXMLRPCServer(('localhost', 8000)) as server:

        server.register_introspection_functions()

        # print("Listening on port 8000...")
        # server.register_function(cd.load_client, 'load_client')
        server.register_function(add, 'add')

        server.register_instance(CarlaDaemon())

        # Run the server's main loop
        server.serve_forever()
