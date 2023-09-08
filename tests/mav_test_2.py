
import UAV as uav
def test_cam_client_server_UDP(debug=False):
    # from UAV.mavlink.cam_client_server  import CamClient, CamServer
    from fastcore.test import test_eq
    print(" ----- test_cam_client_server_UDP")
    with uav.CamClient("udpin:localhost:14445", server_system_ID=111, client_system_ID=222, debug=False) as client:
        with uav.CamServer("udpout:localhost:14445", server_system_ID=111, client_system_ID=222, debug=False) as server:
            client.wait_heartbeat()
            server.wait_heartbeat()

            for i in range(5):
                client.trigger_camera(2)
                server._test_command(2)


    # print(f"client.num_commands_sent: {client.num_commands_sent}")
    # print(f"server.num_commands_received: {server.num_commands_received}")
    # print(f"client.num_acks_received: {client.num_acks_received}")
    #
    # print()
    # print(f"server sys: {server.source_system};  msgs: {server.message_cnts}")
    # print(f"client sys: {client.source_system};  msgs: {client.message_cnts}")

    test_eq(server.server_system_ID, server.source_system)
    test_eq(client.client_system_ID, client.source_system)

    test_eq(client.num_commands_sent, server.num_commands_received)
    test_eq(client.num_acks_received, client.num_commands_sent)
    test_eq(server.message_cnts[222]['COMMAND_LONG'], client.message_cnts[111]['COMMAND_ACK'])
    assert client.message_cnts[111]['HEARTBEAT'] >= 1


def test_cam_client_server_serial(debug=False):
    from fastcore.test import test_eq
    print("   ----- test_cam_client_server_serial")
    with uav.CamServer("/dev/ttyUSB0", server_system_ID=111, client_system_ID=222, debug=debug ) as server:
        with uav.CamClient("/dev/ttyACM0", server_system_ID=111, client_system_ID=222, debug=debug ) as client:
            client.wait_heartbeat()
            server.wait_heartbeat()
            for i in range(10):
                client.trigger_camera(2)
                # server._test_command(1)
                # time.sleep(.15)


    # print(f"client.num_commands_sent: {client.num_commands_sent}")
    # print(f"server.num_commands_received: {server.num_commands_received}")
    # print(f"client.num_acks_received: {client.num_acks_received}")
    # print()
    # print(f"server sys: {server.source_system};  msgs: {server.message_cnts}")
    # print(f"client sys: {client.source_system};  msgs: {client.message_cnts}")

    test_eq(server.server_system_ID, server.source_system)
    test_eq(client.client_system_ID, client.source_system)

    test_eq(client.num_commands_sent, server.num_commands_received)
    test_eq(client.num_acks_received, client.num_commands_sent)
    test_eq(server.message_cnts[222]['COMMAND_LONG'], client.message_cnts[111]['COMMAND_ACK'])
    assert client.message_cnts[111]['HEARTBEAT'] >= 1

# def test_cam_client_server():
#     from UAV import test_cam_client_server
#     test_cam_client_server()

# from UAV.mavlink.cam_client_server import CamClient, CamServer, test_cam_client_server

# if __name__ == '__main__':
#     pass
#     # test_cam_client_server()
#     test_cam_client_server_serial(debug=True)
#     test_cam_client_server_UDP(debug=True)



from UAV.mavlink.base_1 import MAVCom, _Client, _Server, Client_Comp, Srv_Comp1, Srv_Comp2,  MAV_COMP_ID_CAMERA, MAV_COMP_ID_USER1
import time
def test_cam_client_server_UDP(debug=False):


    debug = False
    with _Client("udpin:localhost:14445", source_system=111, target_system=222, debug=debug).client() as client:
        with _Server("udpout:localhost:14445", source_system=222, target_system=111,
                     debug=debug).server() as server:
            client.add_component(Client_Comp(client, source_component=11, debug=True))

            server.add_component(Srv_Comp1(server, source_component=22, debug=False))
            server.add_component(Srv_Comp2(server, source_component=23, debug=False))

            client.start_listen()
            server.start_listen()

            for key, comp in client.component.items():
                result = comp.wait_heartbeat(timeout=0.1)
                if result: print("*** Received heartbeat **** ")
            # server.component_list[0].wait_heartbeat()
            time.sleep(0.1)

            for i in range(2):
                mav_cmd1 = client.component[11]._test_command(server.source_system, 22, 1)
                mav_cmd2 = client.component[11]._test_command(server.source_system, 23, 1)
                mav_cmd2 = client.component[11]._test_command(server.source_system, 24, 1)
                client.component[11].wait_ack(mav_cmd=mav_cmd1, timeout=0.1)
                client.component[11].wait_ack(mav_cmd=mav_cmd2, timeout=0.1)

                # client.component_list[0].wait_heartbeat()
                client.component[11].send_ping(server.source_system, MAV_COMP_ID_CAMERA)
                time.sleep(0.1)

            rst = client.component[11].wait_ack(mav_cmd=mav_cmd1, timeout=0.01)

    print()
    print(f"server.sysID: {server.source_system}, client.sysID: {client.source_system}")
    for key, comp in client.component.items():
        print(f" **** Client.{comp} system = {comp.source_system} comp = {comp.source_component} ****")
        print(f" - {comp.num_cmds_sent = }")
        print(f" - {comp.num_cmds_rcvd = }")
        print(f" - {comp.num_msgs_rcvd = }")
        print(f" - {comp.num_acks_rcvd = }")
        print(f" - msgs: {comp.message_cnts}")

    print()

    for key, comp in server.component.items():
        print(f" **** Server.{comp} system = {comp.source_system}  comp = {comp.source_component} ****")
        print(f" - {comp.num_cmds_sent = }")
        print(f" - {comp.num_cmds_rcvd = }")
        print(f" - {comp.num_msgs_rcvd = }")
        print(f" - {comp.num_acks_rcvd = }")
        print(f" - msgs: {comp.message_cnts}")

    print()

    print(f"server system = {server.source_system};  msgs: {server.message_cnts}")
    print(f"client system = {client.source_system};  msgs: {client.message_cnts}")