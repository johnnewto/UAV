
from UAV.mavlink.mavcom import MAVCom
from UAV.mavlink.component import Component, mavutil
import time

MAV_TYPE_GCS = mavutil.mavlink.MAV_TYPE_GCS
MAV_TYPE_CAMERA = mavutil.mavlink.MAV_TYPE_CAMERA

class Cam1(Component):
    def __init__(self,mav_connection, source_component, mav_type, debug=False):
        super().__init__(mav_connection=mav_connection, source_component=source_component, mav_type=mav_type,
                         debug=debug)

class Cam2(Component):
    def __init__(self,mav_connection, source_component, mav_type, debug=False):
        super().__init__(mav_connection=mav_connection, source_component=source_component, mav_type=mav_type,
                         debug=debug)
class Cli(Component):
    def __init__(self,mav_connection, source_component, mav_type, debug=False):
        super().__init__(mav_connection=mav_connection, source_component=source_component, mav_type=mav_type,
                         debug=debug)

def run_test_client_server(con1="udpin:localhost:14445", con2="udpout:localhost:14445"):

    with MAVCom(con1, source_system=111, debug=False) as client:
        with MAVCom(con2, source_system=222, debug=False) as server:

            client.add_component(Cli(client, mav_type=MAV_TYPE_GCS, source_component = 11, debug=False))
            server.add_component(Cam1(server, mav_type=MAV_TYPE_CAMERA, source_component = 22, debug=False))
            server.add_component(Cam1(server, mav_type=MAV_TYPE_CAMERA, source_component = 23, debug=False))


            for key, comp in client.component.items():
                result = comp.wait_heartbeat(target_system=222, target_component=22, timeout=0.1)
                if result: print ("*** Received heartbeat **** " )

            Num_Iters = 3
            for i in range(Num_Iters):
                client.component[11]._test_command(222, 22, 1)

                client.component[11]._test_command(222, 23, 1)

            client.component[11]._test_command(222, 24, 1)

    return client, server, Num_Iters

if __name__ == '__main__':

    client, server, Num_Iters = run_test_client_server(con1="udpin:localhost:14445", con2="udpout:localhost:14445")
    # client, server, Num_Iters = run_test_client_server(con1="/dev/ttyACM0", con2="/dev/ttyUSB0")

    print(f"{server.source_system = };  {server.message_cnts = }")
    print(f"{client.source_system = };  {client.message_cnts = }")
    print()
    print(f"{client.source_system = } \n{client.summary()} \n")
    print(f"{server.source_system = } \n{server.summary()} \n")

    assert client.component[11].num_cmds_sent == Num_Iters * 2 + 1
    print(f"{server.component[22].message_cnts[111]['COMMAND_LONG'] = }")
    assert server.component[22].message_cnts[111]['COMMAND_LONG'] == Num_Iters
    assert client.component[11].num_acks_rcvd == Num_Iters * 2
    assert client.component[11].num_acks_drop == 1
    assert server.component[22].num_cmds_rcvd == Num_Iters
    assert server.component[23].num_cmds_rcvd == Num_Iters

if __name__ == '__main__':
    print("Done")