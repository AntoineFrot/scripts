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
SPECTATOR_POS_X = -12.0  # meters, relative to vehicle
SPECTATOR_POS_Z = 3.0


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

    def safe_periodic_task(self, func):
        def wrapper():
            if self.periodic_task_active:
                return
            self.periodic_task_active = True
            func()
            self.periodic_task_active = False
        return wrapper

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

        if self.client is None:
            try:
                self.client = carla.Client('127.0.0.1', 2000)
                self.world = self.client.get_world()
                self.world.on_tick(lambda world_snapshot: self.safe_periodic_task(self.move_spectator)())
            except:
                return False

        return True

    def call_obj_method(self, obj, method):
        return getattr(getattr(self, obj), method)()

    def load_world(self, map):
        if self.client is not None:
            self.client.set_timeout(20.0)
            self.client.load_world(map)
            self.world = self.client.get_world()
            self.client.set_timeout(2.0)
            print('Selected map:', map)
        return True

    def get_maps_infos(self):
        if self.client is not None:
            return self.client.get_world().get_map().name, self.client.get_available_maps()
        return None

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

    def add_vehicle(self):
        vehicle_bp = random.choice(self.world.get_blueprint_library().filter(DEFAULT_VEHICLE))
        transform = random.choice(self.world.get_map().get_spawn_points())
        self.vehicle = self.world.try_spawn_actor(vehicle_bp, transform)
        self.vehicle.set_autopilot()
        # print('Added:', self.vehicle.id, self.vehicle)
        return True

    def destroy_all_vehicles(self):
        if self.world is not None:
            for actor in self.world.get_actors().filter('vehicle.*'):
                if actor is not None:
                    actor.destroy()
        return True

    def get_vehicles(self):
        if self.world is not None:
            vehicles = self.world.get_actors().filter('vehicle.*')
        return [veh.id for veh in vehicles]

    def select_vehicle(self, veh_id):
        if self.world is not None:
            self.vehicle = self.world.get_actor(veh_id)
            # print('Selected:', self.vehicle.id, self.vehicle)
        return True

    def get_vehicle_speed(self):
        if self.vehicle is None:
            return 0.0
        v = self.vehicle.get_velocity()
        return 3.6 * math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

    def move_spectator(self):

        if self.vehicle is not None:
            spectator = self.world.get_spectator()
            vehicle_transform = self.vehicle.get_transform()
            yaw = vehicle_transform.rotation.yaw
            spectator.set_transform(carla.Transform(vehicle_transform.location +
                                                    carla.Location(SPECTATOR_POS_X * math.cos(yaw/180.0*math.pi),
                                                                   SPECTATOR_POS_X * math.sin(yaw/180.0*math.pi),
                                                                   SPECTATOR_POS_Z),
                                                    carla.Rotation(yaw=yaw)))


def xmlrpc_serving_CarlaDaemon():

    # Create server
    with SimpleXMLRPCServer(('localhost', XMLRPC_PORT), logRequests=False) as server:

        server.register_introspection_functions()

        server.register_instance(CarlaDaemon())

        # Run the server's main loop
        server.serve_forever()
