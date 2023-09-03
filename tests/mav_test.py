
# from UAV.mavlink.cam_client_server import CamClient, CamServer, test_cam_client_server
import UAV as uav
def test_cam_client_server_UDP(debug=False):
    # from UAV.mavlink.cam_client_server  import CamClient, CamServer
    from fastcore.test import test_eq

    with uav.CamClient("udpin:localhost:14445", debug=False) as client:
        with uav.CamServer("udpout:localhost:14445", debug=False) as server:
            client.wait_heartbeat()

            for i in range(5):
                client.trigger_camera(2)
                server._test_command(2)

    print(f"client.num_commands_sent: {client.num_commands_sent}")
    print(f"server.num_commands_received: {server.num_commands_received}")
    print(f"client.num_acks_received: {client.num_acks_received}")

    test_eq(client.num_commands_sent, server.num_commands_received)
    test_eq(client.num_acks_received, server.num_commands_received)
def test_cam_client_server_serial(debug=False):
    from fastcore.test import test_eq
    with uav.CamServer("/dev/ttyUSB0", server_system_ID=30, client_system_ID=199, debug=debug ) as server:
        with uav.CamClient("/dev/ttyACM1", server_system_ID=30, client_system_ID=199, debug=debug ) as client:
            print(client._log.level)
            client.wait_heartbeat(timeout=1)
            for i in range(10):
                client.trigger_camera(2)
                # server._test_command(1)
                # time.sleep(.15)

    print(f"server.num_commands_received: {server.num_commands_received}")
    print(f"client.num_commands_sent: {client.num_commands_sent}")
    print(f"client.num_acks_received: {client.num_acks_received}")
    print(f"server sys: {server.source_system};  msgs: {server.message_cnts}")
    print(f"client sys: {client.source_system};  msgs: {client.message_cnts}")

    test_eq(server.server_system_ID, server.source_system)
    test_eq(client.client_system_ID, client.source_system)

    assert server.num_commands_received == client.num_commands_sent
    assert  server.num_commands_received == client.num_acks_received
    assert server.message_cnts['COMMAND_LONG'] == client.message_cnts['COMMAND_ACK']
    assert 'HEARTBEAT' in client.message_cnts

# def test_cam_client_server():
#     from UAV import test_cam_client_server
#     test_cam_client_server()

from UAV.mavlink.cam_client_server import CamClient, CamServer, test_cam_client_server

if __name__ == '__main__':
    pass
    test_cam_client_server()
    test_cam_client_server_serial(debug=True)
    test_cam_client_server_UDP(debug=True)