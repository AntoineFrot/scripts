#!/usr/bin/env python

import glob
import os
import sys
import random
import math
import time
from datetime import datetime

from xmlrpc.server import SimpleXMLRPCServer
# from xmlrpc.server import SimpleXMLRPCRequestHandler

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

XMLRPC_PORT = 8123
PERIOD_SPECTATOR_MOVEMENT = 0.01  # s


class StatusMessage:
    def __init__(self, msg=''):
        self.value = msg


TIME_STEP = 0.1

ACTIVE_MAP = 'Town06'
DEFAULT_VEHICLE = 'vehicle.bmw.grandtourer'


class CarlaDaemon:

    def __init__(self):
        self.client = None
        self.world = None
        self.vehicle = None

        # self.last_time = time.perf_counter()

        self.periodic_task_active = False

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
        # now = datetime.now()
        # print('{}: load client'.format(now.strftime("%d/%m/%Y %H:%M:%S.%f")))

        if self.client is None:
            try:
                self.client = carla.Client('127.0.0.1', 2000)
            except:
                return False
            #self.out_q.put(StatusMessage('Client loaded'))

        try:
            self.world = self.client.get_world()
            self.world.on_tick(lambda world_snapshot: self.move_spectator(world_snapshot))

        except:
            return False
        # now = datetime.now()
        # print('{}: loaded'.format(now.strftime("%d/%m/%Y %H:%M:%S.%f")))

        return True

    def call_obj_method(self, obj, method):
        return getattr(getattr(self, obj), method)()

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
        if self.vehicle is None:
            return '({:.02f}, {:.02f}) '.format(0.0, 0.0)

        loc = self.vehicle.get_location()
        return '({:.02f}, {:.02f}) '.format(loc.x, loc.y)

    def get_vehicle_speed(self):
        if self.vehicle is None:
            return 0.0
        v = self.vehicle.get_velocity()
        return 3.6 * math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

    def add_vehicle(self):
        vehicle_bp = random.choice(self.world.get_blueprint_library().filter(DEFAULT_VEHICLE))
        transform = random.choice(self.world.get_map().get_spawn_points())
        self.vehicle = self.world.try_spawn_actor(vehicle_bp, transform)
        self.vehicle.set_autopilot()

        return True

    # def main(self):
    #
    #     self.weather = self.world.get_weather()
    #     self.weather.cloudiness = 0
    #     self.weather.precipitation = 0
    #     self.weather.precipitation_deposits = 0
    #     self.weather.wind_intensity = 100
    #     self.weather.fog_density = 0
    #     self.weather.wetness = 0
    #     self.weather.sun_azimuth_angle = 45
    #     self.weather.sun_altitude_angle = 45
    #
    #     self.world.set_weather(self.weather)
    #
    #     self.set_timing_settings(True)
    #
    #     blueprint = random.choice(self.world.get_blueprint_library().filter('vehicle.*'))
    #     self.map = self.world.get_map()
    #     spawn_points = self.map.get_spawn_points()
    #
    #     # for i, waypoint in enumerate(spawn_points):
    #     #     self.world.debug.draw_string(waypoint.location, str(i), draw_shadow=False,
    #     #                             color=carla.Color(r=255, g=255, b=255), life_time=10000.2,
    #     #                             persistent_lines=True)
    #
    #     vehicle_bp = random.choice(self.world.get_blueprint_library().filter(DEFAULT_VEHICLE))
    #     transform = random.choice(self.world.get_map().get_spawn_points())
    #     self.vehicle = self.world.try_spawn_actor(vehicle_bp, transform)
    #     # self.vehicle.set_velocity(carla.Vector3D(100, 100, 100))
    #
    #     self._autopilot_active = False
    #
    #     self.world.on_tick(lambda world_snapshot: self.do_something(world_snapshot))
    #
    #     while True:
    #
    #         if not self._autopilot_active:
    #             self._autopilot_active = True
    #             self.vehicle.set_autopilot()
    #
    #     return True

    def move_spectator(self, world_snapshot):

        # crt_time = time.perf_counter()
        # delta_time = crt_time - self.last_time
        # if delta_time < PERIOD_SPECTATOR_MOVEMENT:
        #     return

        # time_factor = world_snapshot.timestamp.delta_seconds/delta_time
        # self.last_time = crt_time

        if self.periodic_task_active:
            return
        self.periodic_task_active = True

        if self.vehicle is not None:
            spectator = self.world.get_spectator()
            vehicle_transform = self.vehicle.get_transform()
            yaw = vehicle_transform.rotation.yaw
            spectator.set_transform(carla.Transform(vehicle_transform.location + carla.Location(-12.0 * math.cos(yaw/180.0*math.pi),
                                                                                                -12.0 * math.sin(yaw/180.0*math.pi),
                                                                                                3.0),
                                                    carla.Rotation(yaw=yaw)))

        self.periodic_task_active = False

    # def do_something(self, world_snapshot):
    #     # t = self.vehicle.get_transform()
    #     v = self.vehicle.get_velocity()
    #     print(v.x)
    #
    #     #
    #     # print('Frame ID #{}, x{:.03}, {:.06f} {:.06f} {:.06f} ({:.1f}, {:.1f})'.format(world_snapshot.frame,
    #     #                                                                                time_factor,
    #     #                                                                                world_snapshot.timestamp.elapsed_seconds,
    #     #                                                                                world_snapshot.timestamp.delta_seconds,
    #     #                                                                                delta_time,
    #     #                                                                                t.location.x,
    #     #                                                                                t.location.y,
    #     #                                                                                f.x[0],
    #     #                                                                                fy.x[0]))
    #
    #
    #     self.active = True


def xmlrpc_serving_CarlaDaemon():

    # Create server
    with SimpleXMLRPCServer(('localhost', XMLRPC_PORT), logRequests=False) as server:

        server.register_introspection_functions()

        server.register_instance(CarlaDaemon())

        # Run the server's main loop
        server.serve_forever()
