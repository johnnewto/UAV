
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
        with uav.CamClient("/dev/ttyACM1", server_system_ID=111, client_system_ID=222, debug=debug ) as client:
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