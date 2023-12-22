# import time

# from UAV.mavlink import MAVCom

# # utils.set_gst_debug_level(Gst.DebugLevel)
# # con1 = "udpin:localhost:14445"
# # con1 = "/dev/ttyACM0" "/dev/ttyUSB1"
# # con1, con2 = "/dev/ttyUSB0", "/dev/ttyUSB1"
# # con1 = "udpout:192.168.122.84:14445"
# # con1 = "udpin:10.42.0.1:14445"

# mav_connection = "/dev/ttyUSB0"
# source_system = 111
# target_system = 222

# with MAVCom(mav_connection, source_system=source_system, loglevel=10) as client:
#     while True:
#         time.sleep(0.1)
import asyncio
import time

from UAV.mavlink import MAVCom, mavlink, mavutil
from UAV.mavlink import Component
from UAV.utils import config_dir, get_platform, toml_load

# assert os.environ['MAVLINK20'] == '1', "Set the environment variable before from pymavlink import mavutil  library is imported"
# from pymavlink import mavutil

# from UAV.utils import config_dir, boot_time_str, toml_load
# config_dict = toml_load(config_dir() / f"{mach}_server_config.toml")
# print(config_dict)

mach = get_platform()
conf_path = config_dir()
config_dict = toml_load(conf_path / f"{mach}_server_config.toml")
mav_connection = config_dict['mavlink']['connection']

print(f"{mach = }, {conf_path = } {mav_connection = }")

def on_message(msg: mavlink.MAVLink_message):
    # print(msg)
    if msg.get_type() in ['RC_CHANNELS', 'RADIO_STATUS', 'ATTITUDE', 'STATUSTEXT']:
        print(f"***** RC {msg}")

async def main():
    with MAVCom(mav_connection, source_system=config_dict['mavlink']['source_system'], loglevel=10) as client:
        comp = client.add_component(Component(mav_type=mavlink.MAV_TYPE_GCS, source_component=1, loglevel=10))  # MAV_TYPE_GCS
        ret = await comp.wait_heartbeat(target_system=1, target_component=1, timeout=5)
        print(f"Heartbeat {ret = }")
        client.master.mav.request_data_stream_send(1, 1,
                                                   mavutil.mavlink.MAV_DATA_STREAM_ALL,
                                                   1, 1)
        time.sleep(0.1)
        client.on_message = on_message

        while True:
            time.sleep(0.1)


if __name__ == '__main__':
    asyncio.run(main())