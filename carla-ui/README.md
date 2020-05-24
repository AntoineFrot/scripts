# CARLA UI

![](doc/schematic.png)

### Usage

> Adapt **carla_egg_path** in carla_daemon.py to your environment.

```shell
try:
    carla_egg_path = '../../CARLA_0.9.9/PythonAPI/carla/dist/carla-*%d.%d-%s.egg'
    sys.path.append(glob.glob(carla_egg_path % (sys.version_info.major,
                                                sys.version_info.minor,
                                                'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    print('CARLA PythonAPI not found')
    sys.exit()
```

> Start **carla-ui.py**

```shell
python3 carla-ui.py
```
